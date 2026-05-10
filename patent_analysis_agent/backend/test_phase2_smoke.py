"""Phase 2 스모크: 인덱스 빌드 → 하이브리드 검색 → 압축 → 분석(LLM).

OPENAI_API_KEY 없으면 스킵.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

from config import OPENAI_API_KEY  # noqa: E402
from phase2_analysis import build_search_index, run_analysis  # noqa: E402


def _kr_inv() -> bytes:
    return """【발명의 명칭】
테스트 발명 장치

【청구항】
제1항  테스트 발명 장치에 있어서,
하우징과, 상기 하우징에 결합된 프로세서 및 온도 센서를 포함하는 것을 특징으로 하는 테스트 발명 장치.

【발명의 상세한 설명】
본 발명은 테스트용이다.
""".encode(
        "utf-8"
    )


def _kr_prior() -> bytes:
    return """【발명의 명칭】
선행 기술 장치

【청구항】
제1항  선행 기술 장치에 있어서,
하우징만을 포함하는 것을 특징으로 하는 선행 기술 장치.

【발명의 상세한 설명】
종래에는 하우징만 있었다.
""".encode(
        "utf-8"
    )


def main() -> int:
    if not OPENAI_API_KEY:
        print("SKIP: OPENAI_API_KEY 없음")
        return 0
    built = build_search_index(
        [("invention_sample.txt", _kr_inv())],
        [("prior_sample.txt", _kr_prior())],
        use_llm_refine_phase2=False,
    )
    assert built.get("indexed"), built
    sid = built["session_id"]
    out = run_analysis(sid, "ko")
    assert out.get("analysis_markdown"), out
    print("OK phase2 smoke session=", sid[:12], "... chars=", len(out["analysis_markdown"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
