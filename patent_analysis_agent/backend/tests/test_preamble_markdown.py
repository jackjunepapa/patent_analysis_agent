"""extract_claim_preamble_plain, claim_mapping_claim_column_label."""

from patent_parse import claim_mapping_claim_column_label, extract_claim_preamble_plain


def test_us_claim_preamble_plain_includes_comprising():
    c = (
        "11. A method of fabricating a liquid crystal panel comprising:\n"
        "forming a gate line and a data line crossing each other to define a pixel;"
    )
    out = extract_claim_preamble_plain(c)
    assert "liquid crystal panel" in out
    assert "comprising" in out.lower()


def test_kr_preamble_ends_at_characteristic():
    c = "청구항1. 액정 패널에 있어서, 게이트 라인을 형성하는 것을 특징으로 하는 액정 패널."
    out = extract_claim_preamble_plain(c)
    assert "특징으로 하는" in out


def test_claim_column_label_by_jurisdiction():
    assert claim_mapping_claim_column_label("KR") == "청구항"
    assert claim_mapping_claim_column_label("US") == "Claim"
    assert claim_mapping_claim_column_label("us") == "Claim"
