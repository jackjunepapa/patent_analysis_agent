"""Phase 2: 독립항 한계(limitation) 단위 하이브리드 청킹 결과를 인덱스 문서에 병합."""
from __future__ import annotations

from langchain_core.documents import Document

from chroma_schema import sanitize_chroma_metadata
from phase2_claim_structuring import build_phase2_preview_json


def hybrid_claim_documents_for_inventions(
    invention_claim1_meta: list[dict],
    session_id: str,
    *,
    llm=None,
    use_llm_refine: bool = False,
) -> tuple[list[Document], list[str]]:
    warnings: list[str] = []
    out: list[Document] = []
    for meta in invention_claim1_meta:
        ct = (meta.get("claim1_full") or "").strip()
        if len(ct) < 12:
            continue
        j = meta.get("jurisdiction") or "unknown"
        sf = meta.get("source_file") or "unknown"
        try:
            preview = build_phase2_preview_json(
                claim_text=ct,
                jurisdiction=j,
                source_file=sf,
                session_id=session_id,
                llm=llm,
                use_llm_refine=use_llm_refine,
                invention_title=meta.get("invention_title"),
                application_number=meta.get("application_number"),
            )
        except Exception as e:
            warnings.append(f"phase2 hybrid chunk failed `{sf}`: {e}")
            continue
        payload = preview.get("vector_db_ready_documents") or {}
        rows = payload.get("documents") or []
        if not rows:
            warnings.append(f"phase2 produced no chunks for `{sf}`")
            continue
        for row in rows:
            meta_dict = sanitize_chroma_metadata(
                dict(row.get("metadata") or {}),
            )
            meta_dict.setdefault("metadata_schema_version", "v2_phase2")
            pc = row.get("page_content") or ""
            out.append(Document(page_content=pc, metadata=meta_dict))
        for w in (preview.get("structured_claim") or {}).get("parse_warnings") or []:
            warnings.append(f"[{sf}] {w}")
    return out, warnings


def drop_legacy_invention_claim_chunks(
    docs: list[Document],
    *,
    invention_source_files: set[str],
) -> list[Document]:
    kept: list[Document] = []
    for d in docs:
        m = d.metadata or {}
        if (
            m.get("doc_type") == "invention_claims"
            and m.get("source_file") in invention_source_files
        ):
            continue
        kept.append(d)
    return kept


def merge_documents_with_phase2_claims(
    base_docs: list[Document],
    invention_claim1_meta: list[dict],
    session_id: str,
    *,
    llm=None,
    use_llm_refine: bool = False,
) -> tuple[list[Document], list[str]]:
    hybrid_docs, warns = hybrid_claim_documents_for_inventions(
        invention_claim1_meta,
        session_id,
        llm=llm,
        use_llm_refine=use_llm_refine,
    )
    covered_files = {
        (d.metadata or {}).get("source_file")
        for d in hybrid_docs
        if (d.metadata or {}).get("source_file")
    }
    trimmed = drop_legacy_invention_claim_chunks(
        base_docs,
        invention_source_files=covered_files,
    )
    return trimmed + hybrid_docs, warns
