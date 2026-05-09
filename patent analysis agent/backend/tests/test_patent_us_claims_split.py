from __future__ import annotations

from patent_parse import _extract_claim_one_us, parse_patent_document, split_claims_and_body


def test_split_claims_us_glued_claims_and_one():
    raw = "ABSTRACT\nShort.\n\nCLAIMS 1. An apparatus comprising a housing.\n2. The apparatus of claim 1.\n"
    claims, _body = split_claims_and_body(raw, "US")
    assert "1. An apparatus" in claims
    c1 = _extract_claim_one_us(claims)
    assert c1 and "housing" in c1


def test_split_claims_uses_last_claims_marker():
    raw = (
        "INTRO\nClaims may appear in prose.\n\n"
        "DETAILED DESCRIPTION\nMore text.\n\n"
        "CLAIMS\n\n1. A first independent limitation block.\n"
        "2. The method of claim 1.\n"
    )
    claims, _ = split_claims_and_body(raw, "US")
    assert "1. A first independent" in claims


def test_extract_claim_one_when_block_starts_with_one():
    claims = "1. A method comprising:\n(a) receiving;\n2. The method of claim 1."
    out = _extract_claim_one_us(claims)
    assert out and "1. A method" in out


def test_parse_us_without_claims_word_uses_tail_pattern():
    intro = "Preamble " + ("word " * 500) + "\n"
    tail = "1. Independent claim body one two three four five six.\n2. Dependent.\n"
    raw = intro + tail
    parsed = parse_patent_document(raw, "US", "x.pdf")
    assert (parsed.claims_text or "").strip()
    assert parsed.invention_claim_one or "Independent" in (parsed.claims_text or "")
