"""Phase 3 Test 3: 비교표·분석 근거 단순 Cross-check (결정적 휴리스틱)."""
from __future__ import annotations

import re
from typing import Any


def verify_limitation_rows_substrings_of_claim(
    limitation_texts: list[str],
    invention_claim_full: str,
) -> dict[str, Any]:
    """
    비교 표 원천 한계 문자열들이 본 발명 청구 전문에 (부분)포함되는지 검사.
    `_md_cell` 축약 전 원문 리스트를 넘길 것.
    """
    claim = (invention_claim_full or "").strip()
    failures: list[str] = []
    for raw in limitation_texts:
        el = (raw or "").strip()
        if len(el) < 8:
            continue
        if el in claim:
            continue
        head = el[: min(48, len(el))]
        if head and head in claim:
            continue
        failures.append(el[:120])
    return {
        "ok": len(failures) == 0,
        "checked": len(limitation_texts),
        "failures": failures,
    }


def extract_double_quoted_spans(md: str, min_len: int = 14) -> list[str]:
    """마크다운 본문에서 큰따옴표 구간 후보 (환각 인용 검사용)."""
    pat = re.compile(rf'"([^"\n]{{{min_len},}})"')
    return [m.group(1).strip() for m in pat.finditer(md or "")]


def hallucination_quote_cross_check(analysis_md: str, source_bundle: list[str]) -> dict[str, Any]:
    """
    분석 마크다운 내 긴 따옴표 문자열이 제공된 원문 합집합에 존재하는지 검사.
    LLM이 따옴표를 적게 쓰면 검출 건수가 0일 수 있음.
    """
    blob = "\n".join(source_bundle).lower()
    quotes = extract_double_quoted_spans(analysis_md or "")
    missing = [q for q in quotes if q.lower() not in blob]
    return {
        "quote_count": len(quotes),
        "missing_in_sources": missing[:20],
        "ok": len(missing) == 0,
    }


def comparison_table_consistency_hash(markdown_table: str) -> str:
    """동일 입력 재실행 시 표 문자열 동일성 확인용 단순 해시 대체(공백 정규화)."""
    import hashlib

    norm = re.sub(r"\s+", " ", (markdown_table or "").strip())
    return hashlib.sha256(norm.encode("utf-8", errors="ignore")).hexdigest()[:16]
