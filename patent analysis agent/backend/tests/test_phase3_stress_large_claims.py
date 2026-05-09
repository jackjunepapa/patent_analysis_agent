"""Phase 3 Test 3: 다중 청구 블록 스트레스 — 표 생성이 완료되는지."""
from __future__ import annotations

import pytest

from comparison_table import build_comparison_table_markdown

pytestmark = pytest.mark.phase3
from patent_parse import parse_patent_document


def _kr_claims_block(count: int) -> str:
    lines = ["【특허청구의 범위】", "제1항  장치에 있어서, 하우징과 센서를 포함한다."]
    for i in range(2, count + 1):
        lines.append(f"제{i}항  제{i - 1}항에 있어서, 추가 한정 내용 {i}.")
    return "\n".join(lines)


def test_parse_and_comparison_with_many_dependent_claims() -> None:
    claims = _kr_claims_block(52)
    raw = "【발명의 명칭】스트레스 테스트\n" + claims + "\n본문\n" + ("단락 " * 400)
    parsed = parse_patent_document(raw, "KR", "stress.txt")
    assert parsed.claims_text
    assert parsed.invention_claim_one
    priors = [
        {
            "source_file": "prior.txt",
            "jurisdiction": "KR",
            "claim1_full": "제1항  장치에 있어서, 하우징만 포함한다.",
        }
    ]
    md = build_comparison_table_markdown(
        parsed.invention_claim_one or "",
        "KR",
        priors,
        lang="ko",
    )
    assert "|" in md
    assert "경고" in md or "Disclaimer" in md
