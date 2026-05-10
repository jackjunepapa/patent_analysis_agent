"""Ensemble: Vector(Chroma) + BM25. chunk_id 기준 중복 제거."""
from __future__ import annotations

import hashlib

from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever

from config import ENSEMBLE_WEIGHT_BM25, ENSEMBLE_WEIGHT_VECTOR


def dedupe_by_chunk_id(docs: list[Document]) -> list[Document]:
    seen: set[str] = set()
    out: list[Document] = []
    for d in docs:
        meta = d.metadata or {}
        fallback = hashlib.sha1(
            f"{meta.get('source_file','')}|{meta.get('doc_type','')}|{d.page_content[:400]}".encode(
                "utf-8",
                errors="ignore",
            )
        ).hexdigest()
        cid = meta.get("chunk_id") or fallback
        if cid in seen:
            continue
        seen.add(cid)
        out.append(d)
    return out


def make_ensemble_retriever(
    vectorstore: Chroma,
    bm25_documents: list[Document],
    *,
    k_vector: int = 8,
    k_bm25: int = 8,
    weight_vector: float | None = None,
    weight_bm25: float | None = None,
) -> EnsembleRetriever:
    wv = weight_vector if weight_vector is not None else ENSEMBLE_WEIGHT_VECTOR
    wb = weight_bm25 if weight_bm25 is not None else ENSEMBLE_WEIGHT_BM25
    vret = vectorstore.as_retriever(search_kwargs={"k": k_vector})
    bm25 = BM25Retriever.from_documents(bm25_documents)
    bm25.k = k_bm25
    return EnsembleRetriever(
        retrievers=[vret, bm25],
        weights=[wv, wb],
    )


def invoke_hybrid(ensemble: EnsembleRetriever, query: str, final_k: int = 12) -> list[Document]:
    docs = ensemble.invoke(query)
    return dedupe_by_chunk_id(docs)[:final_k]


def format_context(docs: list[Document]) -> str:
    parts = []
    for i, d in enumerate(docs, 1):
        meta = d.metadata or {}
        src = meta.get("source_file", "?")
        dtype = meta.get("doc_type", "?")
        cscope = meta.get("claim_scope")
        para = meta.get("paragraph_anchor")
        head = f"[{i}] doc_type={dtype} file={src}"
        if cscope:
            head += f" claim_scope={cscope}"
        if para:
            head += f" paragraph_anchor={para}"
        parts.append(f"{head}\n{d.page_content[:3500]}")
    return "\n\n---\n\n".join(parts)


def retrieve_claims_first(
    vectorstore: Chroma,
    query: str,
    k_claims: int = 6,
    k_general: int = 6,
) -> list[Document]:
    """청구항 청크 우선 검색 후 일반 본문 보강."""
    r_claims = vectorstore.as_retriever(
        search_kwargs={
            "k": k_claims,
            "filter": {
                "doc_type": {"$in": ["invention_claims", "prior_art_claims"]},
            },
        }
    )
    r_all = vectorstore.as_retriever(search_kwargs={"k": k_general})
    try:
        a = r_claims.invoke(query)
    except Exception:
        a = []
    b = r_all.invoke(query)
    return dedupe_by_chunk_id(list(a) + list(b))[: k_claims + k_general]
