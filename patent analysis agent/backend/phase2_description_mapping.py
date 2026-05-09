"""Phase 2: 청구 구간과 검색된 명세·선행 청크 간 휴리스틱 매핑(근거 후보)."""
from __future__ import annotations

import re
from typing import Any

from langchain_core.documents import Document

from patent_parse import regex_split_claim_limitations


def _claim_segments(claim_text: str, jurisdiction: str) -> list[str]:
    t = (claim_text or "").strip()
    if not t:
        return []
    lims = regex_split_claim_limitations(t, jurisdiction)
    segs: list[str] = []
    for x in lims:
        s = x.strip()
        if len(s) < 14:
            continue
        for part in re.split(r"[;；]\s*", s):
            p = part.strip()
            if len(p) >= 14:
                segs.append(p[:400])
    return segs[:24]


def link_claim_segments_to_chunks(
    claim_text: str,
    jurisdiction: str,
    retrieved: list[Document],
    *,
    body_doc_types: frozenset[str] | None = None,
) -> list[dict[str, Any]]:
    """
    청구 세그먼트가 검색 결과 청크 본문에 부분 문자열로 등장하면 매칭.
    `paragraph_anchor` 메타가 있으면 Citation 후보로 포함.
    """
    bdt = body_doc_types or frozenset({"invention", "prior_art"})
    segs = _claim_segments(claim_text, jurisdiction)
    out: list[dict[str, Any]] = []
    for seg in segs:
        needle = seg[:120].lower()
        if len(needle) < 10:
            continue
        words = re.findall(r"[a-z0-9]+", seg.lower())
        bigrams = [f"{words[i]} {words[i + 1]}" for i in range(len(words) - 1) if len(words[i]) + len(words[i + 1]) >= 6]
        hits: list[dict[str, Any]] = []
        for d in retrieved:
            m = d.metadata or {}
            if m.get("doc_type") not in bdt:
                continue
            pc = (d.page_content or "").lower()
            sub_ok = needle in pc or seg[:60].lower() in pc
            if not sub_ok and bigrams:
                sub_ok = any(len(bg) >= 8 and bg in pc for bg in bigrams[:40])
            if not sub_ok:
                continue
            hits.append(
                {
                    "source_file": m.get("source_file"),
                    "doc_type": m.get("doc_type"),
                    "chunk_id": m.get("chunk_id"),
                    "paragraph_anchor": m.get("paragraph_anchor") or "",
                    "match_excerpt": (d.page_content or "")[:220].replace("\n", " ").strip(),
                }
            )
        if hits:
            out.append({"claim_segment": seg[:240], "citation_hits": hits[:5]})
    return out[:20]
