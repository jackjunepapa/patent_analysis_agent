"""환경 변수·경로 (Phase 1: OpenAI 임베딩 + Chroma)."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Hybrid retrieval (retrieval.py)
ENSEMBLE_WEIGHT_VECTOR = float(os.getenv("ENSEMBLE_WEIGHT_VECTOR", "0.55"))
ENSEMBLE_WEIGHT_BM25 = float(os.getenv("ENSEMBLE_WEIGHT_BM25", "0.45"))

CHROMA_API_KEY = os.getenv("CHROMA_API_KEY")
CHROMA_TENANT = os.getenv("CHROMA_TENANT")
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE")
CHROMA_HOST = os.getenv("CHROMA_HOST")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "443"))

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "350"))

LOCAL_CHROMA_FALLBACK_DIR = Path(
    os.getenv(
        "LOCAL_CHROMA_FALLBACK_DIR",
        str(PROJECT_ROOT / ".chroma_patent_analysis"),
    )
)


def chroma_cloud_configured() -> bool:
    return bool(CHROMA_API_KEY and CHROMA_TENANT and CHROMA_DATABASE)


def chroma_http_configured() -> bool:
    return bool(CHROMA_HOST and CHROMA_API_KEY)
