"""Phase 3: Reasoning Agent (KIPO/MPEP 참고 톤) + Strategy Generator 프롬프트."""
from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate


REASONING_AGENT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "{guidelines}\n\n"
            "역할: Reasoning Agent — 신규성·진보성 **리스크 관점의 참고용** 논증 초안만 작성합니다. 법적 확정 판단은 금지합니다.\n\n"
            "출력 언어: {lang_label}\n\n"
            "반드시 다음 Markdown 섹션 제목을 사용하세요:\n"
            "## 요약\n"
            "## 구성요소별 매핑 요약 (본 발명 한계 ↔ 검색된 선행 발췌)\n"
            "## 차별 가능성이 높은 지점\n"
            "## 신규성 관련 논점 (단일 선행 문헌 대비, 발췌에 근거)\n"
            "## 진보성(통상 당업자) 관련 논점 (KIPO/MPEP 참고 틀, 발췌에 근거)\n"
            "## 리스크 요약표 (낮음/중간/높음 등 정성 표현만)\n"
            "## 변리사·출원인 검토 체크리스트\n\n"
            "각 단락은 제공된 **청구 텍스트**와 **압축된 검색 컨텍스트**에 근거해야 합니다. "
            "근거 없는 구체 인용(존재하지 않는 단락 번호 등)은 쓰지 마세요.\n\n"
            "가독성: 위 섹션 제목은 모두 `##` 한 단계로 유지하고, 결론적 문장·위험도·차별 후보 구절은 본문에서 `**굵게**` 처리하세요. "
            "(영문 출력 시 동일: `##` titles only; bold **key** risk/differentiation phrases.)",
        ),
        (
            "human",
            "독립 청구 텍스트:\n{claim_text}\n\n"
            "압축·검색 컨텍스트:\n{compressed_context}\n\n"
            "위 구조로 리포트를 작성하세요.",
        ),
    ]
)


STRATEGY_GENERATOR_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "{guidelines}\n\n"
            "역할: Strategy Generator — 위 분석 초안을 바탕으로 **청구 수정(Amendment) 후보**와 "
            "**회피 설계(design-around)** 검토 포인트를 제안합니다. 법적 조언이 아닙니다.\n\n"
            "출력 언어: {lang_label}\n\n"
            "Markdown 구조:\n"
            "## 청구 수정 방향 초안\n"
            "- 제안별로 \"현재 표현\", \"수정안 초안\", \"기대 효과(참고)\", \"유의사항\" 소항목을 `- ` 불릿으로.\n"
            "## 회피·회피 설계 검토\n"
            "- 기능·구조·재료 대안 축으로 불릿.\n"
            "## 분쟁·심사 대응 시 추가 증거 제안\n"
            "- 명세·도면·실험 데이터 등 일반적 예시만.\n\n"
            "과장된 단정을 피하고, 마지막에 반드시 '특허 전문가 검토 필요' 문구를 넣고 본문과 문단을 구분하세요.\n\n"
            "가독성: 제목은 `##`만 사용하고, 수정안·유의사항·기대 효과 등 핵심 구절은 `**굵게**`로 강조하세요. "
            "(영문 출력 시 동일 규칙.)",
        ),
        (
            "human",
            "독립 청구:\n{claim_text}\n\n"
            "검색 컨텍스트 발췌(참고):\n{compressed_context}\n\n"
            "선행 Reasoning 요약:\n{reasoning_summary}\n\n"
            "위를 바탕으로 전략 섹션만 작성하세요.",
        ),
    ]
)
