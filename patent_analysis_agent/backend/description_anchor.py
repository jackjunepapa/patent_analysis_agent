"""Phase 2: 명세 단락·문단 표기(인용 앵커) 추출 — Element-to-Description 매핑 보조."""
from __future__ import annotations

import re

# US/EPO 등: 줄 시작(또는 개행 직후)의 [0045]만 단락 앵커로 본다(본문 중 교차인용 제외).
_RX_BRACKET_LINE = re.compile(r"(?:^|[\n\r])\s*\[\s*(\d{1,4})\s*\]")
# KR 공보 등: (0001) 형태
_RX_PAREN_LINE = re.compile(r"(?:^|[\n\r])\s*\(\s*(\d{4})\s*\)\s*")


def normalize_anchor_bracket(num: str) -> str:
    n = (num or "").strip()
    if not n.isdigit():
        return f"[{n}]"
    if len(n) <= 4:
        return f"[{n.zfill(4)}]"
    return f"[{n}]"


def paragraph_anchor_from_text(text: str) -> str | None:
    """청크 본문에서 첫 단락 표식을 찾아 정규화된 문자열로 반환."""
    if not (text or "").strip():
        return None
    m = _RX_BRACKET_LINE.search(text)
    if m:
        return normalize_anchor_bracket(m.group(1))
    m2 = _RX_PAREN_LINE.search(text)
    if m2:
        return f"({m2.group(1)})"
    return None
