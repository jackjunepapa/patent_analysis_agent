"""Phase 1: Chroma 적재용 Document 메타데이터."""
from __future__ import annotations

from patent_parse import documents_from_parsed, parse_patent_document


def test_invention_chunks_carry_application_and_claim_flags() -> None:
    raw = (
        "출원번호: 10-2019-0001111\n"
        "【발명의 명칭】 메타 검증\n"
        "【특허청구의 범위】\n"
        "제1항. 본 발명은 시험 장치에 관한 것으로서, X를 포함한다.\n"
        "본문 단락 " * 40
    )
    p = parse_patent_document(raw, "KR", "inv.txt")
    docs = documents_from_parsed(
        p,
        doc_type_base="invention",
        jurisdiction="KR",
        source_file="inv.txt",
        session_id="sess1",
    )
    assert docs
    claim_docs = [d for d in docs if d.metadata.get("doc_type") == "invention_claims"]
    body_docs = [d for d in docs if d.metadata.get("doc_type") == "invention"]
    assert claim_docs
    assert body_docs
    m0 = claim_docs[0].metadata
    assert m0.get("application_number") == "10-2019-0001111"
    assert m0.get("invention_title")
    assert m0.get("claim_number") == 1
    assert m0.get("independent_claim") is True
    mb = body_docs[0].metadata
    assert mb.get("application_number") == "10-2019-0001111"
    assert mb.get("claim_number") == 0
    assert mb.get("independent_claim") is False


def test_phase2_preview_metadata_includes_phase1_fields() -> None:
    from phase2_claim_structuring import build_phase2_preview_json

    out = build_phase2_preview_json(
        claim_text="1. A widget comprising: a body; wherein the body is hollow.",
        jurisdiction="US",
        source_file="u.txt",
        session_id="s",
        use_llm_refine=False,
        invention_title="Hollow Widget",
        application_number="US 2023/0000001 A1",
    )
    rows = (out.get("vector_db_ready_documents") or {}).get("documents") or []
    assert rows
    meta = rows[0].get("metadata") or {}
    assert meta.get("invention_title") == "Hollow Widget"
    assert meta.get("application_number") == "US 2023/0000001 A1"
    assert meta.get("claim_number") == 1
    assert meta.get("independent_claim") is True
