from __future__ import annotations

from patent_parse import extract_all_independent_claims


def test_kr_two_independent_claims():
    claims = """
제1항  장치에 있어서, 하우징을 포함하는 것을 특징으로 하는 장치.

제2항  제1항에 있어서, 상기 하우징은 금속인 것을 특징으로 하는 장치.

제10항  방법에 있어서, 상기 장치를 조립하는 단계를 포함하는 것을 특징으로 하는 방법.
""".strip()
    out = extract_all_independent_claims(claims, "KR")
    nums = [x["claim_num"] for x in out]
    assert 1 in nums
    assert 10 in nums
    assert 2 not in nums


def test_us_independent_claim_numbered():
    claims = """
1. A widget comprising a housing.

2. The widget of claim 1, wherein the housing is metal.

13. A method comprising assembling the widget of claim 1.
""".strip()
    out = extract_all_independent_claims(claims, "US")
    nums = sorted(x["claim_num"] for x in out)
    assert 1 in nums
    assert 2 not in nums
    assert all(n in (1, 13) for n in nums)
