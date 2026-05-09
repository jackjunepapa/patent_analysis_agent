from __future__ import annotations

from patent_parse import _extract_claim_one_us, extract_reference_terms_block


def test_us_skips_dependent_claim_one_for_next_independent():
    claims = """
1. The liquid crystal panel of claim 13 wherein the compensation layer is organic.

13. A method of fabricating a liquid crystal panel comprising:
forming a gate line on a substrate;
etching a semiconductor layer.

14. The method of claim 13 wherein the etching comprises dry etching.
"""
    out = _extract_claim_one_us(claims)
    assert out
    assert "method of fabricating" in out.lower()
    assert "comprising" in out.lower()
    assert "claim 13 wherein" not in out.lower()[:80]


def test_reference_terms_includes_object_hint():
    text = (
        "ABSTRACT\nShort.\n\n"
        "DETAILED DESCRIPTION\n"
        "An object of the present invention is to provide a thin film transistor array.\n"
        "More body.\n"
    )
    ref = extract_reference_terms_block(text)
    assert "INV_OBJECT_HINT" in ref or "thin film" in ref.lower()
