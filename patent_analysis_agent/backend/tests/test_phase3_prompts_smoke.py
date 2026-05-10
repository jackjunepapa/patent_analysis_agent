"""Phase 3: 프롬프트 템플릿 로드·필수 변수 바인딩 (API 호출 없음)."""
from __future__ import annotations

import pytest

from prompts_phase3 import REASONING_AGENT_PROMPT, STRATEGY_GENERATOR_PROMPT

pytestmark = pytest.mark.phase3


def test_reasoning_prompt_formats() -> None:
    msgs = REASONING_AGENT_PROMPT.format_messages(
        guidelines="G",
        lang_label="Korean",
        claim_text="제1항 예시",
        compressed_context="컨텍스트 발췌",
    )
    assert len(msgs) >= 2
    blob = "".join(str(m.content) for m in msgs)
    assert "신규성" in blob or "novelty" in blob.lower()


def test_strategy_prompt_formats() -> None:
    msgs = STRATEGY_GENERATOR_PROMPT.format_messages(
        guidelines="G",
        lang_label="Korean",
        claim_text="제1항",
        compressed_context="ctx",
        reasoning_summary="요약 초안",
    )
    assert len(msgs) >= 2
    blob = "".join(str(m.content) for m in msgs)
    assert "청구" in blob or "amendment" in blob.lower()
