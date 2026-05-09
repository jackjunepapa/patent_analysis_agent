from __future__ import annotations

from patent_parse import claim1_or_claims_section_fallback, extract_invention_claim_one


def test_claim1_fallback_uses_claims_block_when_extract_returns_none():
    """제1항 패턴이 없어도 청구 블록이 길면 폴백으로 앞부분을 반환."""
    claims = "무작위 청구 텍스트 " * 30
    assert extract_invention_claim_one(claims, "KR") is None
    fb = claim1_or_claims_section_fallback(claims, "KR")
    assert "무작위" in fb
    assert len(fb) >= 80
