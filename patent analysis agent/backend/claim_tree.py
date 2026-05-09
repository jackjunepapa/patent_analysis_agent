"""Phase 1: 청구항 트리(부모–자식) 및 구성요소(정규식) 분해.

LLM 하이브리드는 Phase 2 `structure_claim_text` / refine 경로에서 담당한다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from patent_parse import (
    _kr_block_marked_cancelled,
    _kr_body_after_claim_label,
    _kr_enumerate_claim_blocks,
    _kr_opening_refs_parent_claim,
    _us_block_looks_independent_claim,
    _us_enumerated_claim_blocks,
    _us_first_line_looks_dependent_claim,
    regex_split_claim_limitations,
)


@dataclass(frozen=True)
class ClaimTreeNode:
    """단일 청구항 노드."""

    claim_number: int
    parent_claim_numbers: tuple[int, ...]
    text: str
    is_independent: bool


def _kr_parent_numbers(inner_after_label: str) -> tuple[int, ...]:
    s = (inner_after_label or "").strip()[:500]
    if not s or not _kr_opening_refs_parent_claim(s):
        return ()
    m = re.search(r"제\s*(\d+)\s*항\s*에\s*있어서", s)
    if m:
        return (int(m.group(1)),)
    nums = [int(x.group(1)) for x in re.finditer(r"제\s*(\d+)\s*항", s[:240])]
    return tuple(dict.fromkeys(nums))


def _us_parent_numbers(block: str) -> tuple[int, ...]:
    head = (block or "").strip()[:600]
    if not _us_first_line_looks_dependent_claim(head):
        return ()
    nums: list[int] = []
    for m in re.finditer(r"(?i)\bclaim\s*(\d+)\b", head):
        nums.append(int(m.group(1)))
    if not nums:
        return ()
    return tuple(dict.fromkeys(nums))


def build_claim_tree(claims_text: str, jurisdiction: str) -> list[ClaimTreeNode]:
    """
    KR: `제n항` 경계. US: `n.` 번호 블록.
    부모 번호는 종속 서두에서 추출; 독립항은 빈 부모.
    """
    j = (jurisdiction or "unknown").upper()
    if j == "KR" or (j == "UNKNOWN" and re.search(r"제\s*\d+\s*항", claims_text or "")):
        out: list[ClaimTreeNode] = []
        for num, _s, _e, blk in _kr_enumerate_claim_blocks(claims_text or ""):
            if _kr_block_marked_cancelled(blk):
                continue
            inner = _kr_body_after_claim_label(blk)
            indep = not _kr_opening_refs_parent_claim(inner)
            parents = () if indep else _kr_parent_numbers(inner)
            out.append(
                ClaimTreeNode(
                    claim_number=num,
                    parent_claim_numbers=parents,
                    text=blk.strip(),
                    is_independent=indep,
                )
            )
        return out

    blocks = _us_enumerated_claim_blocks(claims_text or "")
    out_us: list[ClaimTreeNode] = []
    for num, _s, _e, blk in blocks:
        b = blk.strip()
        if not b:
            continue
        head = b[:520]
        indep = _us_block_looks_independent_claim(b)
        parents = () if indep else _us_parent_numbers(b)
        if not indep and not parents and _us_first_line_looks_dependent_claim(head):
            parents = (1,)
        out_us.append(
            ClaimTreeNode(
                claim_number=num,
                parent_claim_numbers=parents,
                text=b,
                is_independent=indep,
            )
        )
    return out_us


def split_claim_elements_regex(claim_text: str, jurisdiction: str) -> list[str]:
    """
    세미콜론·wherein(US)·KR 연결 구문 등 정규식 기반 구성요소 분할.
    `regex_split_claim_limitations` 위에 세미콜론 추가 분해(US body)를 얹는다.
    """
    t = (claim_text or "").strip()
    if not t:
        return []
    lims = regex_split_claim_limitations(t, jurisdiction)
    j = (jurisdiction or "unknown").upper()
    out: list[str] = []
    for seg in lims:
        s = seg.strip()
        if not s:
            continue
        if j == "US" or (j == "UNKNOWN" and re.search(r"(?is)\bwherein\b", s)):
            parts = [p.strip() for p in re.split(r";\s*", s) if p.strip()]
            if len(parts) > 1:
                out.extend(parts)
            else:
                out.append(s)
        elif j == "KR":
            if re.search(r"(?is)\bwherein\b", s):
                parts = [p.strip() for p in re.split(r";\s*", s) if p.strip()]
                out.extend(parts if len(parts) > 1 else [s])
            else:
                parts = [p.strip() for p in re.split(r"[;；]\s*", s) if p.strip()]
                if len(parts) > 1:
                    out.extend(parts)
                else:
                    out.append(s)
        else:
            parts = [p.strip() for p in re.split(r"[;；]\s*", s) if p.strip()]
            out.extend(parts if len(parts) > 1 else [s])
    return [x for x in out if x]
