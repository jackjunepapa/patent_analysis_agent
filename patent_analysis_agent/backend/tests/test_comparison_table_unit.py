from __future__ import annotations

import pytest

from comparison_table import (
    build_comparison_table_markdown,
    build_comparison_table_markdown_for_session,
)

pytestmark = pytest.mark.phase3


def test_comparison_table_requires_inputs():
    md = build_comparison_table_markdown("", "KR", [], lang="ko")
    assert "본 발명" in md or "모두" in md

    md2 = build_comparison_table_markdown(
        "제1항  장치에 있어서, 예시.",
        "KR",
        [{"source_file": "x.txt", "jurisdiction": "KR", "claim1_full": ""}],
        lang="ko",
    )
    assert "선행" in md2

    md3 = build_comparison_table_markdown(
        "",
        "KR",
        [
            {
                "source_file": "p.txt",
                "jurisdiction": "KR",
                "claim1_full": "제1항  장치에 있어서, 예시.",
            }
        ],
        lang="ko",
    )
    assert "본 발명" in md3


def test_comparison_table_multi_prior_markdown_shape():
    inv = (
        "제1항  장치에 있어서, 하우징과 센서를 포함하는 것을 특징으로 하는 장치."
    )
    priors = [
        {
            "source_file": "p1.txt",
            "jurisdiction": "KR",
            "claim1_full": "제1항  장치에 있어서, 하우징만을 포함하는 것을 특징으로 하는 장치.",
        },
        {
            "source_file": "p2.txt",
            "jurisdiction": "KR",
            "claim1_full": "제1항  장치에 있어서, 하우징과 센서를 포함하는 것을 특징으로 하는 장치.",
        },
    ]
    md = build_comparison_table_markdown(inv, "KR", priors, lang="ko")
    assert "|" in md
    assert "청구항 구성 요소" in md
    assert "구성요소(한계)" not in md
    assert "p1.txt" in md or "p2.txt" in md
    assert "경고" in md or "Disclaimer" in md


def test_session_comparison_lists_multiple_independent_claims() -> None:
    inv_meta = [
        {
            "source_file": "inv/USx.pdf",
            "jurisdiction": "US",
            "claim1_full": "1. A device comprising: a housing;",
            "independent_claims": [
                {"claim_num": 11, "text": "11. A method comprising: step A; step B.", "preview": ""},
            ],
        }
    ]
    priors = [
        {
            "source_file": "p1.txt",
            "jurisdiction": "US",
            "claim1_full": "1. A device comprising: a housing.",
        }
    ]
    md = build_comparison_table_markdown_for_session(inv_meta, priors, lang="ko")
    assert "Claim 1" in md
    assert "Claim 11" in md
    assert "청구항 구성 요소" in md
