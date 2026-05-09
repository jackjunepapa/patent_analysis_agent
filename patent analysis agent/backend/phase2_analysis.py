"""Phase 2–3: 하이브리드 검색 → 압축 → Reasoning·Strategy 심층 분석(LLM). 세션 비교표 생성."""
from __future__ import annotations

import json
from typing import Any

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

from chroma_schema import collection_name_for_session
from comparison_table import (
    build_comparison_table_markdown_for_session,
    list_invention_independent_claim_entries,
)
from config import OPENAI_MODEL
from ingest_phase2_merge import merge_documents_with_phase2_claims
from ingest_pipeline import ingest_uploads, new_session_id
from patent_parse import (
    claim1_or_claims_section_fallback,
    infer_jurisdiction,
    load_text_from_uploaded,
    parse_patent_document,
)
from phase2_description_mapping import link_claim_segments_to_chunks
from prompts_phase2 import (
    CONTEXT_COMPRESSION_PROMPT,
    TECH_FEATURES_PROMPT,
    analysis_guidelines_block,
)
from prompts_phase3 import REASONING_AGENT_PROMPT, STRATEGY_GENERATOR_PROMPT
from retrieval import format_context, invoke_hybrid, make_ensemble_retriever
from session_store import SessionData, get_session, put_session
from vector_store_chroma import build_chroma_from_documents, get_openai_embeddings, load_chroma_store


def _sse_bytes(event: str, data: dict) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n".encode("utf-8")


def invention_index_preview(
    merged: list[Document],
    invention_claim1_meta: list[dict],
) -> dict[str, Any]:
    """
    본 발명 제1항(Claim 1) 추출 요약 + 인덱스에 올라간 `invention_claims` 청크 요약.
    Build index 직후 확인·pytest·Swagger 디버깅용.
    """
    inv_files = {row.get("source_file") for row in invention_claim1_meta if row.get("source_file")}
    claim_parsing: list[dict[str, Any]] = []
    for row in invention_claim1_meta:
        c1 = (row.get("claim1_full") or "").strip()
        claim_parsing.append(
            {
                "source_file": row.get("source_file"),
                "jurisdiction": row.get("jurisdiction"),
                "claim1_char_count": len(c1),
                "claim1_excerpt": c1[:500],
            }
        )
    invention_claim_chunks: list[dict[str, Any]] = []
    invention_body_chunk_count = 0
    for d in merged:
        m = d.metadata or {}
        sf = m.get("source_file")
        if inv_files and sf not in inv_files:
            continue
        dtype = m.get("doc_type")
        if dtype == "invention":
            invention_body_chunk_count += 1
            continue
        if dtype != "invention_claims":
            continue
        pc = d.page_content or ""
        invention_claim_chunks.append(
            {
                "chunk_id": m.get("chunk_id"),
                "source_file": sf,
                "limitation_id": m.get("limitation_id"),
                "limitation_role": m.get("limitation_role"),
                "limitation_order": m.get("limitation_order"),
                "limitation_sub_type": m.get("limitation_sub_type"),
                "section_type": m.get("section_type"),
                "metadata_schema_version": m.get("metadata_schema_version"),
                "content_char_count": len(pc),
                "content_preview": pc.replace("\n", " ").strip()[:420],
            }
        )
    return {
        "claim_parsing": claim_parsing,
        "invention_claim_chunks": invention_claim_chunks,
        "invention_body_chunk_count": invention_body_chunk_count,
    }


def _lang_label(lang: str) -> str:
    return "Korean" if (lang or "").lower().startswith("ko") else "English"


def get_chat_llm(temperature: float = 0.2) -> ChatOpenAI:
    return ChatOpenAI(model=OPENAI_MODEL, temperature=temperature)


def prior_claim_meta_from_files(
    prior_files: list[tuple[str, bytes]],
) -> list[dict]:
    out: list[dict] = []
    for name, data in prior_files:
        row: dict[str, Any] = {"source_file": name, "jurisdiction": "unknown", "claim1_full": ""}
        try:
            text = load_text_from_uploaded(name, data)
            j = infer_jurisdiction(name, text)
            parsed = parse_patent_document(text, j, name)
            row["jurisdiction"] = j
            row["claim1_full"] = claim1_or_claims_section_fallback(parsed.claims_text, j)[
                :50000
            ]
        except Exception:
            pass
        out.append(row)
    return out


def extract_technical_feature_query(llm: ChatOpenAI, claim_text: str, lang: str) -> str:
    blob = (claim_text or "").strip()
    if len(blob) < 20:
        return (
            "patent independent claim structural functional limitations "
            "prior art retrieval"
        )
    msg = (TECH_FEATURES_PROMPT | llm).invoke(
        {"claim_text": blob[:14000], "lang_label": _lang_label(lang)}
    )
    bullets = (msg.content or "").strip()
    head = blob[:900].replace("\n", " ")
    return f"{bullets}\n\nClaim excerpt: {head}"


def compress_retrieved_context(
    llm: ChatOpenAI,
    docs: list,
    lang: str,
    query: str,
    *,
    max_chars_before_compress: int = 14000,
) -> str:
    raw = format_context(docs)
    if len(raw) <= max_chars_before_compress:
        return raw
    truncated = raw[:48000]
    msg = (CONTEXT_COMPRESSION_PROMPT | llm).invoke(
        {
            "query": query[:4000],
            "context": truncated,
            "lang_label": _lang_label(lang),
        }
    )
    out = (msg.content or "").strip()
    return out if out else raw[:max_chars_before_compress]


def run_deep_analysis_llm(
    llm: ChatOpenAI,
    *,
    claim_text: str,
    compressed_context: str,
    lang: str,
) -> str:
    """Phase 3: Reasoning Agent → Strategy Generator 순차 호출 후 하나의 Markdown으로 결합."""
    guidelines = analysis_guidelines_block(lang)
    ll = _lang_label(lang)
    claim_c = (claim_text or "")[:16000]
    comp_c = compressed_context[:28000]
    reasoning_msg = (REASONING_AGENT_PROMPT | llm).invoke(
        {
            "guidelines": guidelines,
            "lang_label": ll,
            "claim_text": claim_c,
            "compressed_context": comp_c,
        }
    )
    reasoning = (reasoning_msg.content or "").strip()
    rs = reasoning[:14000]
    strategy_msg = (STRATEGY_GENERATOR_PROMPT | llm).invoke(
        {
            "guidelines": guidelines,
            "lang_label": ll,
            "claim_text": claim_c,
            "compressed_context": comp_c[:12000],
            "reasoning_summary": rs,
        }
    )
    strategy = (strategy_msg.content or "").strip()
    sep = (
        "\n\n---\n\n## 전략·청구 수정 제안\n\n"
        if (lang or "").lower().startswith("ko")
        else "\n\n---\n\n## Strategy & amendment sketch\n\n"
    )
    return reasoning + sep + strategy


def prepare_analysis_context(session_id: str, lang: str) -> dict[str, Any]:
    """검색·압축·비교표까지 준비. 오류 시 `error` 키 포함."""
    data = get_session(session_id)
    if data is None:
        return {"error": "session_not_found", "detail": session_id}
    prior_nonempty = any(
        (m.get("claim1_full") or "").strip() for m in (data.prior_claim_meta or [])
    )
    if not prior_nonempty:
        return {
            "error": "prior_art_required",
            "detail": (
                "선행 문헌이 인덱스에 없습니다. 선행 파일을 포함해 인덱스를 다시 빌드한 뒤 "
                "「선행 특허 비교」분석을 실행하세요."
            ),
        }
    emb = get_openai_embeddings()
    store = load_chroma_store(emb, data.collection_name)
    llm = get_chat_llm()
    inv_entries = list_invention_independent_claim_entries(data.invention_claim1_meta or [])
    if inv_entries:
        claim_blob = "\n\n---\n\n".join((e["text"] or "").strip()[:12000] for e in inv_entries)
        if len(claim_blob) > 20000:
            claim_blob = claim_blob[:20000] + "\n\n[… 본 발명 독립항 발췌 잘림 …]"
    else:
        claim_blob = "\n\n".join(
            (m.get("claim1_full") or "").strip()
            for m in data.invention_claim1_meta or []
            if (m.get("claim1_full") or "").strip()
        )
    inv_j = (
        (inv_entries[0]["jurisdiction"] if inv_entries else None)
        or (data.invention_claim1_meta[0].get("jurisdiction") if data.invention_claim1_meta else None)
        or "unknown"
    )
    query = extract_technical_feature_query(llm, claim_blob, lang)
    ensemble = make_ensemble_retriever(store, data.bm25_documents)
    retrieved = invoke_hybrid(ensemble, query, final_k=14)
    compressed = compress_retrieved_context(llm, retrieved, lang, query)
    comparison_md = build_comparison_table_markdown_for_session(
        data.invention_claim1_meta or [],
        data.prior_claim_meta or [],
        lang=lang,
    )
    src_preview = []
    for d in retrieved[:8]:
        m = d.metadata or {}
        src_preview.append(
            {
                "source_file": m.get("source_file"),
                "doc_type": m.get("doc_type"),
                "chunk_id": m.get("chunk_id"),
                "paragraph_anchor": m.get("paragraph_anchor") or "",
            }
        )
    desc_hints = link_claim_segments_to_chunks(
        claim_blob,
        (inv_j or "unknown").upper(),
        retrieved,
    )
    return {
        "llm": llm,
        "claim_blob": claim_blob or "(claim text unavailable)",
        "compressed": compressed,
        "comparison_md": comparison_md,
        "sources_preview": src_preview,
        "query": query,
        "retrieved_count": len(retrieved),
        "description_mapping_hints": desc_hints,
    }


def build_search_index(
    invention_files: list[tuple[str, bytes]],
    prior_files: list[tuple[str, bytes]],
    *,
    use_llm_refine_phase2: bool = False,
) -> dict:
    session_id = new_session_id()
    coll = collection_name_for_session(session_id)
    prior_meta = prior_claim_meta_from_files(prior_files)
    docs, warnings, inv_meta = ingest_uploads(
        invention_files,
        prior_files,
        session_id,
    )
    llm_opt = get_chat_llm() if use_llm_refine_phase2 else None
    merged, w_merge = merge_documents_with_phase2_claims(
        docs,
        inv_meta,
        session_id,
        llm=llm_opt,
        use_llm_refine=use_llm_refine_phase2,
    )
    warnings.extend(w_merge)
    preview = invention_index_preview(merged, inv_meta)
    if not merged:
        has_prior_fail = bool(prior_files) and any(len(pb) > 0 for _fn, pb in prior_files)
        return {
            "session_id": session_id,
            "collection": coll,
            "warnings": warnings + ["no documents to index"],
            "chunk_count": 0,
            "indexed": False,
            "invention_index_preview": preview,
            "has_prior_art": has_prior_fail,
        }
    emb = get_openai_embeddings()
    build_chroma_from_documents(merged, emb, coll)
    put_session(
        session_id,
        SessionData(
            collection_name=coll,
            bm25_documents=merged,
            invention_claim1_meta=inv_meta,
            warnings=warnings,
            prior_claim_meta=prior_meta,
        ),
    )
    has_prior = bool(prior_files) and any(len(pb) > 0 for _fn, pb in prior_files)
    return {
        "session_id": session_id,
        "collection": coll,
        "warnings": warnings,
        "chunk_count": len(merged),
        "indexed": True,
        "invention_index_preview": preview,
        "has_prior_art": has_prior,
    }


def run_analysis(session_id: str, lang: str = "ko") -> dict[str, Any]:
    prep = prepare_analysis_context(session_id, lang)
    if prep.get("error") == "session_not_found":
        return {"error": "session_not_found", "detail": prep.get("detail")}
    if prep.get("error") == "prior_art_required":
        return {"error": "prior_art_required", "detail": prep.get("detail")}
    llm: ChatOpenAI = prep["llm"]
    markdown = run_deep_analysis_llm(
        llm,
        claim_text=prep["claim_blob"],
        compressed_context=prep["compressed"],
        lang=lang,
    )
    return {
        "session_id": session_id,
        "retrieval_query_excerpt": prep["query"][:2000],
        "source_count": prep["retrieved_count"],
        "sources_preview": prep["sources_preview"],
        "comparison_table_markdown": prep["comparison_md"],
        "analysis_markdown": markdown,
        "description_mapping_hints": prep.get("description_mapping_hints") or [],
    }


def iter_sse_analysis(session_id: str, lang: str) -> Any:
    """SSE 바이트 청크: event meta → delta → done."""
    prep = prepare_analysis_context(session_id, lang)
    if prep.get("error") == "session_not_found":
        err = {"error": prep.get("error"), "detail": prep.get("detail")}
        yield f"event: error\ndata: {json.dumps(err, ensure_ascii=False)}\n\n".encode("utf-8")
        return
    if prep.get("error") == "prior_art_required":
        err = {"error": prep.get("error"), "detail": prep.get("detail")}
        yield f"event: error\ndata: {json.dumps(err, ensure_ascii=False)}\n\n".encode("utf-8")
        return
    meta = {
        "comparison_table_markdown": prep["comparison_md"],
        "sources_preview": prep["sources_preview"],
        "retrieval_query_excerpt": prep["query"][:2000],
        "source_count": prep["retrieved_count"],
        "session_id": session_id,
        "description_mapping_hints": prep.get("description_mapping_hints") or [],
    }
    yield f"event: meta\ndata: {json.dumps(meta, ensure_ascii=False)}\n\n".encode("utf-8")

    llm: ChatOpenAI = prep["llm"]
    guidelines = analysis_guidelines_block(lang)
    ll = _lang_label(lang)
    claim_c = prep["claim_blob"][:16000]
    comp_c = prep["compressed"][:28000]

    ko = (lang or "").lower().startswith("ko")
    yield _sse_bytes(
        "phase",
        {
            "id": "reasoning",
            "label": "심층 분석 — 신규성·진보성 (스트리밍)" if ko else "Deep reasoning — novelty / inventive step",
        },
    )
    reasoning_acc = ""
    chain_r = REASONING_AGENT_PROMPT | llm
    payload_r = {
        "guidelines": guidelines,
        "lang_label": ll,
        "claim_text": claim_c,
        "compressed_context": comp_c,
    }
    for chunk in chain_r.stream(payload_r):
        piece = getattr(chunk, "content", None) or ""
        if piece:
            reasoning_acc += piece
            yield _sse_bytes("delta", {"t": piece, "phase": "reasoning"})

    yield _sse_bytes(
        "phase",
        {
            "id": "strategy",
            "label": "전략·청구 수정 제안 (스트리밍)" if ko else "Strategy & amendments (streaming)",
        },
    )
    rs = reasoning_acc.strip()[:14000]
    chain_s = STRATEGY_GENERATOR_PROMPT | llm
    payload_s = {
        "guidelines": guidelines,
        "lang_label": ll,
        "claim_text": claim_c,
        "compressed_context": comp_c[:12000],
        "reasoning_summary": rs,
    }
    try:
        for chunk in chain_s.stream(payload_s):
            piece = getattr(chunk, "content", None) or ""
            if piece:
                yield _sse_bytes("delta", {"t": piece, "phase": "strategy"})
    except Exception as e:
        note = f"\n\n[전략 생성 오류] {e}" if ko else f"\n\n[Strategy generation error] {e}"
        yield _sse_bytes("delta", {"t": note, "phase": "strategy"})
    yield b"event: done\ndata: {}\n\n"


def combine_report_markdown(analysis_md: str, comparison_md: str, lang: str) -> str:
    if lang.startswith("ko"):
        head = "## Comparison Table\n\n"
        foot = "\n\n---\n\n## 심층 분석 리포트\n\n"
    else:
        head = "## Comparison Table\n\n"
        foot = "\n\n---\n\n## Analysis report\n\n"
    return head + (comparison_md or "") + foot + (analysis_md or "")
