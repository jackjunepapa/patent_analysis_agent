"""Phase 3 Test 3: Hallucination cross-check 휴리스틱 단위 테스트."""
from __future__ import annotations

import pytest

from phase2_claim_structuring import structure_claim_text

pytestmark = pytest.mark.phase3
from phase3_verification import (
    comparison_table_consistency_hash,
    hallucination_quote_cross_check,
    verify_limitation_rows_substrings_of_claim,
)


def test_verify_limitation_rows_grounded_in_claim() -> None:
    inv = (
        "제1항  테스트 장치에 있어서, 하우징과 센서 및 프로세서를 포함하는 것을 특징으로 하는 장치."
    )
    structured = structure_claim_text(inv, "KR")
    texts = [x.text for x in structured.limitations if x.role != "preamble"]
    assert texts
    out = verify_limitation_rows_substrings_of_claim(texts, inv)
    assert out["ok"]


def test_hallucination_quote_cross_check_finds_missing_quote() -> None:
    md = '발췌에 따르면 "thequickbrownfoxjumpsover lazydog" 라고 한다.'
    sources = ["unrelated text without the quoted phrase"]
    r = hallucination_quote_cross_check(md, sources)
    assert r["quote_count"] >= 1
    assert r["ok"] is False


def test_hallucination_quote_ok_when_in_bundle() -> None:
    phrase = "verifiedquotedsubstringhere"
    md = f'문헌은 "{phrase}" 라고 개시한다.'
    assert hallucination_quote_cross_check(md, [phrase, "noise"])["ok"]


def test_comparison_table_consistency_same_hash_twice() -> None:
    inv = "제1항  장치에 있어서, 하우징과 센서를 포함한다."
    priors = [
        {
            "source_file": "p.txt",
            "jurisdiction": "KR",
            "claim1_full": "제1항  장치에 있어서, 하우징만 포함한다.",
        }
    ]
    from comparison_table import build_comparison_table_markdown

    m1 = build_comparison_table_markdown(inv, "KR", priors, lang="ko")
    m2 = build_comparison_table_markdown(inv, "KR", priors, lang="ko")
    assert comparison_table_consistency_hash(m1) == comparison_table_consistency_hash(m2)
