"""Chroma 적재·로드. Cloud / HTTP / 로컬 persist. Phase 1: OpenAI 임베딩."""
from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from config import (
    CHROMA_API_KEY,
    CHROMA_DATABASE,
    CHROMA_HOST,
    CHROMA_PORT,
    CHROMA_TENANT,
    LOCAL_CHROMA_FALLBACK_DIR,
    OPENAI_EMBEDDING_MODEL,
    chroma_cloud_configured,
    chroma_http_configured,
)

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings


def get_openai_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)


def _chroma_kwargs(collection_name: str) -> dict:
    if chroma_cloud_configured():
        return {
            "collection_name": collection_name,
            "chroma_cloud_api_key": CHROMA_API_KEY,
            "tenant": CHROMA_TENANT,
            "database": CHROMA_DATABASE,
        }
    if chroma_http_configured():
        return {
            "collection_name": collection_name,
            "host": CHROMA_HOST,
            "port": CHROMA_PORT,
            "ssl": True,
            "headers": {"X-Chroma-Token": CHROMA_API_KEY or ""},
        }
    LOCAL_CHROMA_FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
    persist = str(LOCAL_CHROMA_FALLBACK_DIR / collection_name.replace("/", "_"))
    return {
        "collection_name": collection_name,
        "persist_directory": persist,
    }


def build_chroma_from_documents(
    documents: list[Document],
    embeddings: Embeddings,
    collection_name: str,
) -> Chroma:
    kwargs = _chroma_kwargs(collection_name)
    return Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        **kwargs,
    )


def load_chroma_store(embeddings: Embeddings, collection_name: str) -> Chroma:
    kwargs = _chroma_kwargs(collection_name)
    return Chroma(
        embedding_function=embeddings,
        **kwargs,
    )
