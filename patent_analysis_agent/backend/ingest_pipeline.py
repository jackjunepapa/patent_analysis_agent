"""업로드 바이트 → ParsedPatent → LangChain Document 리스트 + 인덱스 경고 문자열."""
from __future__ import annotations

import uuid

from langchain_core.documents import Document

from patent_parse import (
    claim1_or_claims_section_fallback,
    documents_from_parsed,
    extract_all_independent_claims,
    infer_jurisdiction,
    invention_claim_one_warnings,
    load_text_from_uploaded,
    parse_patent_document,
)


def ingest_uploads(
    invention_files: list[tuple[str, bytes]],
    prior_files: list[tuple[str, bytes]],
    session_id: str,
) -> tuple[list[Document], list[str], list[dict]]:
    """
    invention_files: [(filename, raw_bytes), ...]
    prior_files: [(filename, raw_bytes), ...] — KR/US 혼합·다중 업로드 가능. 관할은 파일별 자동 추정.

    Returns:
        (documents, warnings, invention_claim1_meta)
        invention_claim1_meta: [{"source_file", "jurisdiction", "claim1_full", "invention_title", "application_number"}, ...] — 분석 시 Claim 1 전문·메타 주입용.
    """
    all_docs: list[Document] = []
    warnings: list[str] = []
    invention_claim1_meta: list[dict] = []

    def _load_or_warn(name: str, data: bytes, bucket: str) -> str:
        try:
            return load_text_from_uploaded(name, data)
        except Exception as e:
            warnings.append(f"[{bucket}] `{name}`: 텍스트 추출 실패 - {e}")
            return ""

    for name, data in invention_files:
        text = _load_or_warn(name, data, "본 발명")
        if not text.strip():
            warnings.append(f"[본 발명] `{name}`: 추출된 텍스트가 비어 있어 건너뜁니다.")
            continue
        j = infer_jurisdiction(name, text)
        parsed = parse_patent_document(text, j, name)
        warnings.extend(invention_claim_one_warnings(name, parsed))
        claim1_full = claim1_or_claims_section_fallback(parsed.claims_text, j)[:50000]
        ind_claims = extract_all_independent_claims(parsed.claims_text or "", j)
        if not ind_claims and claim1_full.strip():
            pv = claim1_full if len(claim1_full) <= 220 else claim1_full[:217].rstrip() + "…"
            ind_claims = [{"claim_num": 1, "text": claim1_full.strip(), "preview": pv}]
        invention_claim1_meta.append(
            {
                "source_file": name,
                "jurisdiction": j,
                "claim1_full": claim1_full,
                "independent_claims": ind_claims,
                "invention_title": parsed.invention_title or "",
                "application_number": (parsed.application_number or "").strip(),
            }
        )
        docs = documents_from_parsed(
            parsed,
            doc_type_base="invention",
            jurisdiction=j,
            source_file=name,
            session_id=session_id,
        )
        if not docs:
            warnings.append(f"[본 발명] `{name}`: 생성된 청크가 없어 인덱싱에서 제외됩니다.")
            continue
        all_docs.extend(docs)

    for name, data in prior_files:
        text = _load_or_warn(name, data, "선행 문헌")
        if not text.strip():
            warnings.append(f"[선행 문헌] `{name}`: 추출된 텍스트가 비어 있어 건너뜁니다.")
            continue
        j = infer_jurisdiction(name, text)
        parsed = parse_patent_document(text, j, name)
        docs = documents_from_parsed(
            parsed,
            doc_type_base="prior_art",
            jurisdiction=j,
            source_file=name,
            session_id=session_id,
        )
        if not docs:
            warnings.append(f"[선행 문헌] `{name}`: 생성된 청크가 없어 인덱싱에서 제외됩니다.")
            continue
        all_docs.extend(docs)

    return all_docs, warnings, invention_claim1_meta


def new_session_id() -> str:
    return uuid.uuid4().hex
