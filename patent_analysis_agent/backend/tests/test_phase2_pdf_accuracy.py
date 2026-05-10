"""
Phase 2: 실제 PDF 바이트 기반 파싱·메타·(선택) 검색 정확도.

- fpdf2로 생성한 US 스타일 PDF를 PyPDF/Unstructured 경로로 읽어 검증합니다.
- OpenAI 키가 있으면 Chroma 인덱스 + 하이브리드 검색으로 선행 문헌 적중을 추가 검증합니다.
"""
from __future__ import annotations

import os

import pytest

from description_anchor import paragraph_anchor_from_text
from ingest_phase2_merge import merge_documents_with_phase2_claims
from patent_parse import (
    documents_from_parsed,
    infer_jurisdiction,
    load_text_from_uploaded,
    parse_patent_document,
)
from tests.fixtures_pdf_phase2 import (
    invention_us_patent_pdf_bytes,
    prior_us_patent_pdf_bytes,
    require_fpdf,
)


def test_paragraph_anchor_extracts_bracket_form() -> None:
    assert paragraph_anchor_from_text("Intro\n[0045] body text") == "[0045]"
    assert paragraph_anchor_from_text("[0045] body at chunk start") == "[0045]"
    assert paragraph_anchor_from_text("(0001) 본문") == "(0001)"


def test_paragraph_anchor_ignores_inline_cross_reference() -> None:
    """본문 중 'see [0045]' 형태는 단락 앵커로 쓰지 않는다."""
    assert paragraph_anchor_from_text("The prior art in [0045] is cited.") is None


def test_pdf_patent_text_extract_and_claim_parse() -> None:
    require_fpdf()
    inv = invention_us_patent_pdf_bytes()
    text = load_text_from_uploaded("invention_acc.pdf", inv)
    assert "PHASE2INV99MARK" in text
    assert "[0045]" in text
    j = infer_jurisdiction("invention_acc.pdf", text)
    assert j == "US"
    parsed = parse_patent_document(text, j, "invention_acc.pdf")
    assert parsed.invention_claim_one
    c1 = (parsed.invention_claim_one or "").lower()
    assert "capacitor" in c1 and "200" in c1


def test_pdf_body_chunks_carry_paragraph_anchor_metadata() -> None:
    require_fpdf()
    inv = invention_us_patent_pdf_bytes()
    text = load_text_from_uploaded("invention_acc.pdf", inv)
    j = infer_jurisdiction("invention_acc.pdf", text)
    parsed = parse_patent_document(text, j, "invention_acc.pdf")
    docs = documents_from_parsed(
        parsed,
        doc_type_base="invention",
        jurisdiction=j,
        source_file="invention_acc.pdf",
        session_id="acc_sess",
    )
    merged, _warns = merge_documents_with_phase2_claims(
        docs,
        [
            {
                "source_file": "invention_acc.pdf",
                "jurisdiction": j,
                "claim1_full": (parsed.invention_claim_one or "")[:50000],
                "invention_title": parsed.invention_title or "",
                "application_number": (parsed.application_number or "").strip(),
            }
        ],
        "acc_sess",
        llm=None,
        use_llm_refine=False,
    )
    body = [
        d
        for d in merged
        if (d.metadata or {}).get("doc_type") == "invention"
        and (d.metadata or {}).get("section_type") == "body"
    ]
    assert body
    anchors = [((d.metadata or {}).get("paragraph_anchor") or "") for d in body]
    assert "[0045]" in anchors


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY 없음")
def test_pdf_index_hybrid_retrieval_surfaces_prior_overlap() -> None:
    """임베딩·BM25로 선행 PDF 청크가 질의에 포함되는지(검색 정확도)."""
    require_fpdf()
    from phase2_analysis import build_search_index
    from retrieval import invoke_hybrid, make_ensemble_retriever
    from session_store import get_session
    from vector_store_chroma import get_openai_embeddings, load_chroma_store

    inv = invention_us_patent_pdf_bytes()
    pr = prior_us_patent_pdf_bytes()
    out = build_search_index(
        [("invention_acc.pdf", inv)],
        [("prior_acc.pdf", pr)],
        use_llm_refine_phase2=False,
    )
    assert out.get("indexed") is True
    sid = out["session_id"]
    data = get_session(sid)
    assert data is not None
    emb = get_openai_embeddings()
    store = load_chroma_store(emb, data.collection_name)
    ensemble = make_ensemble_retriever(store, data.bm25_documents)
    # 도면 부호·단락·선행 고유 마커를 함께 넣어 BM25·벡터 모두 신호를 받게 함
    query = "capacitor 200 reference numeral [0045] PRIORUNIQUE998MARK voltage compensation display"
    hits = invoke_hybrid(ensemble, query, final_k=16)
    prior_hits = [
        d
        for d in hits
        if (d.metadata or {}).get("source_file") == "prior_acc.pdf"
        and "PRIORUNIQUE998MARK" in (d.page_content or "")
    ]
    assert prior_hits, "하이브리드 검색이 선행 PDF의 중첩 구간을 상위 히트에 포함해야 합니다"
