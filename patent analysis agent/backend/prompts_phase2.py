"""MPEP·KIPO 관점을 참고한 Phase 2 분석·압축 프롬프트 (교육·보조용, 법률 자문 아님)."""
from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate


def analysis_guidelines_block(lang: str) -> str:
    if lang.startswith("ko"):
        return (
            "당신은 특허 비교 분석 보조 도구입니다. 최종 법적 판단을 대신하지 않습니다.\n"
            "참고 관점(일반적 심사 프레임, 비배타적):\n"
            "- 신규성: 1개의 인용 문헌만으로 청구 범위가 전부 노출되는지(단일 문서 기준).\n"
            "- 진보성: 통상의 당업자가 선행 조합·단순 변경으로 도출할 수 있는지.\n"
            "- US: MPEP가 정리한 novelty / obviousness 평가 틀을 참고하되, 본 출력은 요약입니다.\n"
            "- KR: 특허청 심사지침에서 말하는 신규성·진보성의 큰 흐름을 참고하되, 본 출력은 요약입니다.\n"
            "출력에는 반드시 '전문가 확인 필요' 문구를 포함하세요.\n"
            "근거 없는 단정은 피하고, 제공된 인용 발췌와 청구항 텍스트에 근거해 논리적으로 서술하세요."
        )
    return (
        "You assist with patent comparison. You do not provide legal advice.\n"
        "Reference framing only (non-authoritative):\n"
        "- Novelty (US/KR analogues): whether a single reference teaches every limitation.\n"
        "- Inventive step / non-obviousness: whether a skilled person would arrive at the claim "
        "from cited art without inventive effort.\n"
        "- US: reflect general MPEP-style novelty/obviousness organization as rough guidance.\n"
        "- KR: reflect high-level KIPO examination practice themes similarly.\n"
        "Always state that a registered patent attorney/agent must validate conclusions.\n"
        "Avoid definitive legal conclusions; tie reasoning to the excerpts and claim text provided."
    )


TECH_FEATURES_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Read the independent patent claim (KR or US). Extract 5–12 concise technical "
            "feature phrases useful for prior-art retrieval (nouns, structural relationships, "
            "functions). Output one bullet per line starting with '- '. No preamble.",
        ),
        (
            "human",
            "Claim text:\n{claim_text}\n\nWrite bullets in {lang_label}.",
        ),
    ]
)


CONTEXT_COMPRESSION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Compress overlapping patent excerpts for downstream analysis. "
            "Preserve: technical nouns, reference numerals, structural relationships. "
            "Remove redundancy. Output in {lang_label}. Max ~900 words.",
        ),
        (
            "human",
            "Retrieval focus:\n{query}\n\nExcerpts:\n{context}",
        ),
    ]
)


DEEP_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "{guidelines}\n\n"
            "Produce a structured Markdown report with sections:\n"
            "## Summary\n"
            "## Mapping hints (invention vs retrieved prior excerpts)\n"
            "## Potential differentiation angles\n"
            "## Novelty / inventive-step style discussion (qualified, excerpt-grounded)\n"
            "## Risk notes & next steps for counsel review\n"
            "Use {lang_label} throughout.",
        ),
        (
            "human",
            "Independent claim text (may be excerpted):\n{claim_text}\n\n"
            "Compressed retrieved context:\n{compressed_context}\n\n"
            "Write the report.",
        ),
    ]
)
