"""Chroma 컬렉션 이름·문서 메타데이터 스키마 (Phase 1).

인덱스 빌드 시 `patent_parse.documents_from_parsed`가 부여하는 metadata 키와
일치시킨다. Hybrid BM25 등 후속 단계에서 동일 키를 사용한다.
"""
from __future__ import annotations

# 세션별 컬렉션 (동시 사용자·세션 격리)
COLLECTION_PREFIX = "patent_analysis_v1"


def collection_name_for_session(session_id: str) -> str:
    sid = (session_id or "default").replace("/", "_")[:80]
    return f"{COLLECTION_PREFIX}_{sid}"


# Document.metadata (langchain_core.documents.Document) — v1
METADATA_KEYS = frozenset(
    {
        "jurisdiction",
        "source_file",
        "session_id",
        "uploaded_at",
        "metadata_schema_version",
        "doc_type",
        "section_type",
        "chunk_id",
        "invention_title",
        "claim_scope",
        # Phase 1: contextual retrieval / claim identity
        "application_number",
        "claim_number",
        "independent_claim",
        # Phase 2 invention_claims chunks
        "claim_id",
        "limitation_id",
        "limitation_role",
        "limitation_sub_type",
        "limitation_order",
        "depends_on",
        "is_wherein",
        "parser_version",
        # Phase 2: 명세 단락 표식(검색·매핑)
        "paragraph_anchor",
    }
)

# doc_type 값 예시
DOC_TYPE_INVENTION = "invention"
DOC_TYPE_INVENTION_CLAIMS = "invention_claims"
DOC_TYPE_PRIOR = "prior_art"
DOC_TYPE_PRIOR_CLAIMS = "prior_art_claims"


def sanitize_chroma_metadata(metadata: dict | None) -> dict:
    """Chroma upsert 규칙: 빈 list 등 비허용 값 제거·직렬화."""
    if not metadata:
        return {}
    out: dict = {}
    for k, v in metadata.items():
        if v is None:
            continue
        if isinstance(v, list):
            if len(v) == 0:
                continue
            out[k] = [str(x) for x in v]
            continue
        if isinstance(v, (str, int, float, bool)):
            out[k] = v
            continue
        out[k] = str(v)
    return out
