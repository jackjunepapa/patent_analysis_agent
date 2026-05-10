"""본 발명 단독 분석: 발명 요약·청구항-명세 매핑 설명 (선행 비교 전 단계)."""
from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate


def invention_analysis_guidelines(lang: str) -> str:
    if lang.startswith("ko"):
        return (
            "당신은 특허 명세서 구조화 요약 도구입니다. 법률 자문·등록 가능성 확정 판단은 하지 않습니다.\n"
            "반드시 제공된 청구·명세 발췌에 근거하고, 추측으로 새로운 기술 사실을 만들지 마세요.\n"
            "마지막에 '특허 전문가 검토 필요' 문구를 넣고, 본문과 한 줄 이상 띄워 문단을 구분하세요."
        )
    return (
        "You summarize patent disclosure structure only; this is not legal advice.\n"
        "Ground every statement in the provided claim/description excerpts.\n"
        "End with a note that a patent attorney/agent must validate."
    )


INVENTION_SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "{guidelines}\n\n"
            "Task: Write a structured Markdown report **발명 요약** for the inventor-facing workspace.\n"
            "Language: {lang_label}\n\n"
            "Every section title must be Markdown `## Title` only (## level; shown bold in the UI).\n"
            "Use sections:\n"
            "## 기술 과제·배경 (발췌에 근거)\n"
            "## 발명의 핵심 아이디어 (독립항과 명세를 통합하여 요약)\n"
            "## 주요 구성·작용\n"
            "## 도면·부호가 보이면 간단히 언급\n"
            "## 한 줄 로그라인\n\n"
            "Within `## 주요 구성·작용`, you MUST include the following subsection **in this order**:\n"
            "### 주요 구성 요소(독립항) 심층 분석\n\n"
            "**Multi-independent-claim rule (Option B):** For **each** independent claim block provided under "
            "\"독립항 전문\", output one analysis block in ascending claim number order for that file.\n"
            "- Start each block with a `####` heading: match **that file's jurisdiction** — for `KR` use "
            "`#### 제N항 (독립)`; for `US` or other use `#### Claim N (independent)`. When {lang_label} is English but "
            "the claim file is KR, you may keep the Korean-style heading or use bilingual `#### 제11항 / Claim 11`.\n"
            "- If **more than one** independent claim exists for the same file and the current claim number is **not** "
            "the smallest independent claim number in that file, insert **one short line** immediately under the `####` "
            "heading comparing to the first independent claim of that file, e.g. "
            "`> **제1항 대비 추가·차별 구성:** 전압 제어부, …` (adapt to the actual claim; ground in claim text only).\n"
            "- Then output **one** GitHub-flavored Markdown table with **exactly** these four column headers "
            "(copy verbatim):\n"
            "  `| 주요 구성 요소 (Element) | 기능 및 역할 (Function & Role) | 특허적 중요도 | 근거 단락 |`\n"
            "- Rows: decompose that independent claim into technical elements (apparatus/method steps/pixel structures, "
            "etc.). Element column: concise Korean name plus English in parentheses when helpful.\n"
            "- **특허적 중요도** column MUST use **exactly one** of these tokens (no brackets): `필수`, `핵심`, `보조`, `참고`.\n"
            "- **근거 단락** column: only paragraph markers that **literally appear** in the description excerpt "
            "(including `[chunk_begin_anchor=…]` or line-initial `[####]` / `(####)`). If unknown, use `—`. "
            "For each non-empty anchor, use a Markdown link so the reader can click: "
            "example `[0045](#spec-ref-0045)` (repeat the number inside the link text). Do not invent paragraph numbers.\n"
            "- Immediately **below each table**, for **every** row whose 특허적 중요도 is **핵심**, output one line in a "
            "blockquote starting with `> **전략 (` then the element name then `):**` followed by **one** Korean sentence "
            "linking that element to prior-art comparison / narrowing / claim strategy (informational only; not legal "
            "advice). Example tone: 핵심 차별화 요소이므로 선행기술 비교 시 수치·한정 여부를 중점 검토하십시오.\n"
            "- If {lang_label} is English, write the comparison line, table cell prose (except the fixed column headers), "
            "and strategy blockquote sentences in **English**.\n",
        ),
        (
            "human",
            "**독립항 전문 (번호·파일별, 분석의 주 입력):**\n{independent_claims_briefing}\n\n"
            "**통합 청구 참고 블록 (검색·인덱스용, 독립항과 중복될 수 있음):**\n{claim_text}\n\n"
            "**상세한 설명·명세 발췌 (청크 순):**\n{description_excerpt}\n\n"
            "위 발췌·청구만 사용하여 요약을 작성하세요.",
        ),
    ]
)


CLAIM_MAPPING_EXPLAIN_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "{guidelines}\n\n"
            "Task: **청구항 설명** — 청구 문장(서두·한계)이 상세한 설명의 어느 부분과 연결되는지 표 형태와 설명으로 정리합니다.\n"
            "Language: {lang_label}\n\n"
            "출력 규칙:\n"
            "- Markdown 표 헤더는 반드시 한 줄로 다음 **정확한 열 이름**을 사용합니다.\n"
            "  `| {claim_column} | 명세서 근거 발췌 | 단락 표시 |`\n"
            "- **첫 번째 데이터 행**은 아래에 주어진 **청구 서두(preamble)** 를 `{claim_column}` 열에 그대로 넣습니다(별도 인용 블록으로 출력하지 않음).\n"
            "- 그 다음 행부터는 청구 한계(시드·청구 전문 순)를 한 행당 한 한계로 나눕니다.\n"
            "- **단락 표시** 열에는 명세 발췌 본문에 **실제로 등장**하는 단락 표식만 적습니다. 발췌 앞에 붙은 `[chunk_begin_anchor=…]` 또는 본문 **줄 시작** 형태의 `[####]`, `(####)` 만 인정합니다. 발췌에 표식이 없으면 `—`.\n"
            "- 본문 중간의 교차인용만 보고 단락 번호를 추측하지 마세요. 존재하지 않는 [0045] 등을 만들지 마세요.\n"
            "- 명세에 직접 대응이 약하면 솔직히 '직접 근거 발췌 제한적'이라고 적습니다.\n",
        ),
        (
            "human",
            "**청구 서두 (표 첫 행 {claim_column} 열에 반드시 포함):**\n{preamble_plain}\n\n"
            "**청구 텍스트:**\n{claim_text}\n\n"
            "**구조화 한계 시드(JSON 또는 불릿이면 참고만):**\n{limitations_seed}\n\n"
            "**상세한 설명 발췌:**\n{description_excerpt}\n\n"
            "위 규칙에 맞는 표와 단락 설명을 작성하세요.",
        ),
    ]
)
