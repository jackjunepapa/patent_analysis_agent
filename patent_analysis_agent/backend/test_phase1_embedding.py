"""Phase 1: 파서 → 인제스트 → Chroma 적재 → 유사도 검색 스모크 테스트.

실행 (프로젝트 루트 또는 backend 폴더에서 모두 가능):
  python backend/test_phase1_embedding.py
  cd backend && python test_phase1_embedding.py

OPENAI_API_KEY가 없으면 스킵 메시지만 출력하고 종료 코드 0.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.chdir(BACKEND)

from chroma_schema import collection_name_for_session  # noqa: E402
from config import OPENAI_API_KEY  # noqa: E402
from ingest_pipeline import ingest_uploads, new_session_id  # noqa: E402
from vector_store_chroma import (  # noqa: E402
    build_chroma_from_documents,
    get_openai_embeddings,
    load_chroma_store,
)


def _sample_kr_invention() -> bytes:
    return """【발명의 명칭】
테스트 발명 장치

【청구항】
제1항  테스트 발명 장치에 있어서,
하우징과, 상기 하우징에 결합된 프로세서 및 온도 센서를 포함하는 것을 특징으로 하는 테스트 발명 장치.

제2항에 있어서, 상기 온도 센서는 적외선 방식인 것을 특징으로 하는 제1항에 따른 테스트 발명 장치.

【발명의 상세한 설명】
본 발명은 테스트용이다. 하우징과 프로세서 및 온도 센서를 포함한다.
""".encode(
        "utf-8"
    )


def _sample_kr_prior() -> bytes:
    return """【발명의 명칭】
선행 기술 장치

【청구항】
제1항  선행 기술 장치에 있어서,
하우징만을 포함하는 것을 특징으로 하는 선행 기술 장치.

【발명의 상세한 설명】
종래에는 하우징만 있었다.
""".encode(
        "utf-8"
    )


def main() -> int:
    if not OPENAI_API_KEY:
        print("SKIP: OPENAI_API_KEY 없음 — .env에 키를 설정한 뒤 다시 실행하세요.")
        return 0

    session = new_session_id()
    coll = collection_name_for_session(session)

    docs, warnings, inv_meta = ingest_uploads(
        invention_files=[("invention_sample.txt", _sample_kr_invention())],
        prior_files=[("prior_sample.txt", _sample_kr_prior())],
        session_id=session,
    )
    assert docs, "인제스트 결과 문서가 비어 있음"
    for w in warnings:
        print("WARN:", w)

    emb = get_openai_embeddings()
    store = build_chroma_from_documents(docs, emb, coll)
    raw = store.get(include=["metadatas"])
    n = len(raw["ids"]) if raw.get("ids") else 0
    assert n > 0, "Chroma 문서 수가 0"
    print("indexed_chunks:", n)

    store2 = load_chroma_store(emb, coll)
    hits = store2.similarity_search("온도 센서 하우징", k=3)
    assert hits, "similarity_search 결과 없음"
    print("top_hit_doc_type:", hits[0].metadata.get("doc_type"))
    print("top_hit_preview:", hits[0].page_content[:120].replace("\n", " "), "...")
    print("OK phase1 embedding + chroma smoke test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
