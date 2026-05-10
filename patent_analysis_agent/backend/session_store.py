"""인메모리 세션 (개발용). 프로덕션에서는 Redis 등으로 교체."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field

from langchain_core.documents import Document


@dataclass
class SessionData:
    collection_name: str
    bm25_documents: list[Document]
    invention_claim1_meta: list[dict]
    warnings: list[str] = field(default_factory=list)
    prior_claim_meta: list[dict] = field(default_factory=list)


_lock = threading.Lock()
_SESSIONS: dict[str, SessionData] = {}


def put_session(session_id: str, data: SessionData) -> None:
    with _lock:
        _SESSIONS[session_id] = data


def get_session(session_id: str) -> SessionData | None:
    with _lock:
        return _SESSIONS.get(session_id)


def delete_session(session_id: str) -> None:
    with _lock:
        _SESSIONS.pop(session_id, None)
