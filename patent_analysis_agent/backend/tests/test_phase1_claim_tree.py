"""Phase 1: 청구 트리·구성요소 정규식 분해."""
from __future__ import annotations

from claim_tree import ClaimTreeNode, build_claim_tree, split_claim_elements_regex


KR_SAMPLE = """【특허청구의 범위】
제1항. 본 발명은 A를 포함하는 장치에 관한 것이다.

제2항. 제1항에 있어서, 상기 A는 B를 더 포함하는 것을 특징으로 하는 장치.

제3항. 제2항에 있어서, 상기 B는 C인 것을 특징으로 하는 장치.
"""


def test_build_claim_tree_kr_independent_and_dependent_parents() -> None:
    nodes = build_claim_tree(KR_SAMPLE, "KR")
    byn: dict[int, ClaimTreeNode] = {n.claim_number: n for n in nodes}
    assert len(byn) == 3
    assert byn[1].is_independent is True
    assert byn[1].parent_claim_numbers == ()
    assert byn[2].is_independent is False
    assert byn[2].parent_claim_numbers == (1,)
    assert byn[3].is_independent is False
    assert byn[3].parent_claim_numbers == (2,)


US_SAMPLE = """1. A method comprising:
receiving data;
processing the data;
wherein the processing includes filtering.

2. The method of claim 1, wherein the filtering uses a Kalman filter.
"""


def test_build_claim_tree_us_dependent_refs_claim_1() -> None:
    nodes = build_claim_tree(US_SAMPLE, "US")
    byn = {n.claim_number: n for n in nodes}
    assert 1 in byn and 2 in byn
    assert byn[1].is_independent is True
    assert byn[2].is_independent is False
    assert 1 in byn[2].parent_claim_numbers


def test_split_claim_elements_us_semicolon_and_wherein() -> None:
    claim = (
        "1. An apparatus comprising: a first module; a second module; "
        "wherein the first module communicates with the second module."
    )
    parts = split_claim_elements_regex(claim, "US")
    assert len(parts) >= 3
    assert any("first module" in p.lower() for p in parts)
    assert any("wherein" in p.lower() for p in parts)
