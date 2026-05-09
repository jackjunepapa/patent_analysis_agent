"""Phase 2: jurisdiction-aware claim parsing + pre-index chunk preview."""
from __future__ import annotations

import re
from typing import List, Literal, Optional

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from patent_parse import (
    infer_jurisdiction,
    load_text_from_uploaded,
    parse_patent_document,
    patent_text_splitter,
)


class LimitationItem(BaseModel):
    limitation_id: str
    text: str
    role: Literal["preamble", "element", "condition", "conclusion"]
    sub_type: Literal["structure", "function", "material", "condition", "other"] = "other"
    order: int
    depends_on: list[str] = Field(default_factory=list)
    is_wherein: bool = False


class StructuredClaim(BaseModel):
    claim_id: str = "claim_1"
    jurisdiction: str
    preamble: str
    limitations: list[LimitationItem]
    parser_version: str = "phase2-jurisdiction-aware-v2"
    parser_confidence: float
    parse_warnings: list[str] = Field(default_factory=list)


REFINE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You normalize patent claim parsing output into a strict JSON schema.\n"
            "Rules:\n"
            "- Keep semantic meaning from claim text; do not invent limitations.\n"
            "- Jurisdiction-aware behavior: KR uses connective patterns, US uses semicolon/wherein/comprising patterns.\n"
            "- No duplicate limitations. Merge near-identical duplicates.\n"
            "- role must be one of: preamble, element, condition, conclusion.\n"
            "- sub_type must be one of: structure, function, material, condition, other.\n"
            "- wherein clauses must set is_wherein=true and role=condition.\n"
            "- Return JSON only, no markdown.\n"
            "{format_instructions}",
        ),
        (
            "human",
            "Jurisdiction: {jurisdiction}\n\n"
            "Claim text:\n{claim_text}\n\n"
            "Rule-based seed JSON:\n{seed_json}\n\n"
            "Return normalized JSON now.",
        ),
    ]
)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _split_preamble_and_body_us(claim_text: str) -> tuple[str, str]:
    t = (claim_text or "").strip()
    if not t:
        return "", ""
    t = re.sub(r"(?is)^\s*(?:claim\s*)?1\s*[.)]?\s*", "", t)
    m = re.search(r"(?is)\b(comprising|including|consisting\s+of)\b\s*:?", t)
    if m:
        head = _clean(t[: m.end()])
        body = t[m.end() :].strip(" \n\r:;")
        return head, body
    first_break = min([idx for idx in (t.find(":"), t.find(";")) if idx >= 0] or [len(t)])
    head = _clean(t[: first_break + 1]) if first_break < len(t) else _clean(t)
    body = t[first_break + 1 :].strip() if first_break < len(t) else ""
    return head, body


def _split_preamble_and_body_kr(claim_text: str) -> tuple[str, str]:
    t = (claim_text or "").strip()
    if not t:
        return "", ""
    t = re.sub(r"^\s*제\s*1\s*항\s*", "", t)
    m = re.search(r"(?:에\s*있어서|에\s*관한\s*것으로서|을\s*포함(?:하며|하고))", t)
    if m:
        pivot = m.end()
        return _clean(t[:pivot]), t[pivot:].strip(" \n\r,:;")
    first_break = min([idx for idx in (t.find(","), t.find(":"), t.find(";")) if idx >= 0] or [len(t)])
    head = _clean(t[: first_break + 1]) if first_break < len(t) else _clean(t)
    body = t[first_break + 1 :].strip() if first_break < len(t) else ""
    return head, body


def _split_body_us(body_text: str) -> list[str]:
    if not body_text.strip():
        return []
    body = body_text.strip()
    # US core split: semicolon-driven element boundaries.
    raw = [x.strip(" \n\r;") for x in re.split(r";\s*", body) if x.strip(" \n\r;")]
    out: list[str] = []
    for seg in raw:
        # Keep 'and' glue as element tail, normalize whitespace.
        seg = _clean(re.sub(r"(?is)^(and|or)\s+", "", seg))
        if seg:
            out.append(seg)
    return out


def _split_body_kr(body_text: str) -> list[str]:
    if not body_text.strip():
        return []
    body = body_text.strip()
    # KR core split: connective endings and condition clauses.
    candidates = re.split(
        r"(?<=,)\s*(?=상기|또는|그리고)|"
        r"(?<=\.)\s*(?=상기)|"
        r"(?<=하며)\s*(?=상기)|"
        r"(?<=이고)\s*(?=상기)|"
        r"(?<=고)\s*(?=상기)",
        body,
    )
    out: list[str] = []
    for seg in candidates:
        seg = _clean(seg.strip(" \n\r,;"))
        if seg:
            out.append(seg)
    return out or [_clean(body)]


def _classify_sub_type(text: str, role: str) -> Literal["structure", "function", "material", "condition", "other"]:
    t = text.lower()
    if role in {"condition", "conclusion"}:
        return "condition"
    if re.search(r"configured to|emit|display|동작|작동|표시|구성되", t):
        return "function"
    if re.search(r"layer|electrode|organic|금속|층|전극|재료", t):
        return "material"
    if re.search(r"line|vertex|center|배열|배치|교차|거리|형성", t):
        return "structure"
    return "other"


def _dedupe_segments(segments: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for seg in segments:
        key = _clean(seg).lower().strip(" ,.;")
        if not key:
            continue
        # Prevent near-duplicate full-span segment if already covered by finer pieces.
        if any(key in s or s in key for s in seen):
            if len(key) > 120 and any(len(s) < len(key) for s in seen):
                continue
        if key in seen:
            continue
        seen.add(key)
        out.append(_clean(seg))
    return out


def _split_body_by_jurisdiction(body_text: str, jurisdiction: str) -> list[str]:
    if not body_text.strip():
        return []
    j = (jurisdiction or "unknown").upper()
    if j == "KR":
        return _dedupe_segments(_split_body_kr(body_text))
    if j == "US":
        return _dedupe_segments(_split_body_us(body_text))
    return _dedupe_segments(_split_body_us(body_text) + _split_body_kr(body_text))


def structure_claim_text(claim_text: str, jurisdiction: str) -> StructuredClaim:
    txt = (claim_text or "").strip()
    if not txt:
        return StructuredClaim(
            jurisdiction=jurisdiction or "unknown",
            preamble="",
            limitations=[],
            parser_confidence=0.0,
            parse_warnings=["empty claim text"],
        )

    j = (jurisdiction or "unknown").upper()
    if j == "KR":
        preamble, body = _split_preamble_and_body_kr(txt)
    elif j == "US":
        preamble, body = _split_preamble_and_body_us(txt)
    else:
        preamble, body = _split_preamble_and_body_us(txt)
        if not body:
            preamble, body = _split_preamble_and_body_kr(txt)

    body_segments = _split_body_by_jurisdiction(body, j)
    limitations: list[LimitationItem] = []
    parse_warnings: list[str] = []

    order = 1
    if preamble:
        limitations.append(
            LimitationItem(
                limitation_id=f"L{order}",
                text=preamble,
                role="preamble",
                sub_type="other",
                order=order,
                depends_on=[],
                is_wherein=False,
            )
        )
        order += 1
    else:
        parse_warnings.append("preamble not clearly detected")

    previous_ids: list[str] = [x.limitation_id for x in limitations]
    for idx, seg in enumerate(body_segments):
        is_wherein = bool(re.search(r"(?is)\bwherein\b", seg))
        is_condition = bool(
            re.search(r"(?is)\bwherein\b|보다\s*크|보다\s*작|if\b|when\b|경우|조건", seg)
        )
        is_conclusion = idx == len(body_segments) - 1 and bool(
            re.search(r"(?is)구조\.?$|장치\.?$|system\.?$|device\.?$", seg)
        )
        role: Literal["element", "condition", "conclusion"]
        if is_conclusion and not is_wherein:
            role = "conclusion"
        elif is_wherein or is_condition:
            role = "condition"
        else:
            role = "element"
        dep = previous_ids[-2:] if role in {"condition", "conclusion"} else []
        item = LimitationItem(
            limitation_id=f"L{order}",
            text=_clean(seg),
            role=role,
            sub_type=_classify_sub_type(seg, role),
            order=order,
            depends_on=dep,
            is_wherein=is_wherein,
        )
        limitations.append(item)
        previous_ids.append(item.limitation_id)
        order += 1

    if len(limits := [x for x in limitations if x.role != "preamble"]) == 0:
        parse_warnings.append("no body limitations detected")

    confidence = 0.92 if limits and preamble and j in {"KR", "US"} else 0.78 if limits else 0.4
    return StructuredClaim(
        jurisdiction=j,
        preamble=preamble,
        limitations=limitations,
        parser_confidence=confidence,
        parse_warnings=parse_warnings,
    )


def refine_structured_claim_with_llm(
    *,
    claim_text: str,
    jurisdiction: str,
    seed: StructuredClaim,
    llm,
) -> StructuredClaim:
    parser = PydanticOutputParser(pydantic_object=StructuredClaim)
    chain = REFINE_PROMPT | llm | parser
    refined = chain.invoke(
        {
            "jurisdiction": (jurisdiction or "unknown").upper(),
            "claim_text": claim_text,
            "seed_json": seed.model_dump_json(ensure_ascii=False, indent=2),
            "format_instructions": parser.get_format_instructions(),
        }
    )
    # Safety: keep required identity fields aligned with runtime context.
    refined.claim_id = "claim_1"
    refined.jurisdiction = (jurisdiction or "unknown").upper()
    return refined


def build_phase2_preview_json(
    *,
    claim_text: str,
    jurisdiction: str,
    source_file: str,
    session_id: str,
    llm=None,
    use_llm_refine: bool = False,
    invention_title: str | None = None,
    application_number: str | None = None,
    **kwargs,
) -> dict:
    # Backward/forward compatibility for hot-reload mismatches.
    if "llm" in kwargs and llm is None:
        llm = kwargs["llm"]
    if "use_llm_refine" in kwargs:
        use_llm_refine = bool(kwargs["use_llm_refine"])
    if "invention_title" in kwargs and invention_title is None:
        invention_title = kwargs.get("invention_title")
    if "application_number" in kwargs and application_number is None:
        application_number = kwargs.get("application_number")
    rule_structured = structure_claim_text(claim_text, jurisdiction)
    structured = rule_structured
    refine_status = "skipped"
    if use_llm_refine and llm is not None:
        try:
            structured = refine_structured_claim_with_llm(
                claim_text=claim_text,
                jurisdiction=jurisdiction,
                seed=rule_structured,
                llm=llm,
            )
            refine_status = "applied"
        except Exception as e:
            structured = rule_structured
            refine_status = "fallback_rule_only"
            structured.parse_warnings.append(f"llm_refine_failed: {e}")

    splitter = patent_text_splitter()
    docs: list[dict] = []
    for lim in structured.limitations:
        for ci, chunk in enumerate(splitter.split_text(lim.text)):
            docs.append(
                {
                    "page_content": chunk,
                    "page_content_preview": chunk[:280],
                    "page_content_length": len(chunk),
                    "metadata": {
                        "jurisdiction": structured.jurisdiction,
                        "source_file": source_file,
                        "session_id": session_id,
                        "doc_type": "invention_claims",
                        "section_type": "claims",
                        "claim_scope": "independent_claim_1",
                        "claim_number": 1,
                        "independent_claim": True,
                        "invention_title": (invention_title or "").strip(),
                        "application_number": (application_number or "").strip(),
                        "claim_id": structured.claim_id,
                        "limitation_id": lim.limitation_id,
                        "limitation_role": lim.role,
                        "limitation_sub_type": lim.sub_type,
                        "limitation_order": lim.order,
                        "depends_on": lim.depends_on,
                        "is_wherein": lim.is_wherein,
                        "parser_version": structured.parser_version,
                        "chunk_id": f"{session_id}_{source_file}_claim1_{lim.limitation_id}_{ci}",
                    },
                }
            )

    doc_payload = [
        d
        for d in docs
    ]
    return {
        "mode": "phase2_claim_text_input",
        "input": {
            "jurisdiction": jurisdiction,
            "source_file": source_file,
            "claim_text_length": len(claim_text or ""),
        },
        "refine": {
            "use_llm_refine": use_llm_refine,
            "status": refine_status,
        },
        "structured_claim": structured.model_dump(),
        "vector_db_ready_documents": {
            "count": len(doc_payload),
            "documents": doc_payload,
        },
    }


class ClaimElement(BaseModel):
    claim_no: int = Field(description="청구항 번호 (정수만)")
    claim_type: str = Field(description="independent 또는 dependent")
    parent_claims: Optional[List[int]] = Field(
        default=None,
        description="종속항일 경우 인용하는 상위 청구항 번호 리스트",
    )
    claim_text: str = Field(description="청구항 내용 전체")


class StructuredClaims(BaseModel):
    claims: List[ClaimElement] = Field(description="추출된 청구항 객체 리스트")


def _trim_claims_tail_at_sections(raw: str) -> str:
    """Claims 구간 뒤로 섞인 abstract·description·reference 목록 등을 잘라낸다."""
    t = raw.strip()
    if not t:
        return t
    m = re.search(
        r"(?is)(?=\n\s*(?:abstract|description|description\s+of\s+the|detailed\s+description|"
        r"background|brief\s+description)\b|【\s*(?:요약|발명의\s*설명)\s*】|"
        r"\n\s*reference\s+numerals?\b)",
        t,
    )
    if m:
        t = t[: m.start()]
    return t[:120000].strip()


def _extract_claims_section_for_hybrid(full_text: str, jurisdiction: str) -> str | None:
    """
    Step 1: 정규식으로 Claims 절두어 이후(또는 US 식 What is claimed is)를 잡는다.
    KR(【청구항】, 제n항) / US(What is claimed, Claims) 모두 시도.
    """
    t = (full_text or "").strip()
    if not t:
        return None
    j = (jurisdiction or "unknown").upper()
    if j == "KR":
        pats: list[re.Pattern[str]] = [
            re.compile(r"【\s*청구항\s*】"),
            re.compile(r"(?im)^\s*청구항\s*$"),
            re.compile(r"(?m)(?:^|[\n\r])\s*제\s*1\s*항"),
        ]
    elif j == "US":
        pats = [
            re.compile(r"(?is)What\s+is\s+claimed\s+is\s*:?"),
            re.compile(r"(?im)^\s*CLAIMS\s*$"),
            re.compile(r"(?im)^\s*Claims\s*$"),
        ]
    else:
        pats = [
            re.compile(r"(?is)What\s+is\s+claimed\s+is\s*:?"),
            re.compile(r"(?im)^\s*CLAIMS\s*$"),
            re.compile(r"(?im)^\s*Claims\s*$"),
            re.compile(r"【\s*청구항\s*】"),
            re.compile(r"(?im)^\s*청구항\s*$"),
        ]
    # 사용자 스니펫과 유사: 키워드 이후 전체; 여기서는 앵커 start만 사용
    best: re.Match[str] | None = None
    for p in pats:
        m = p.search(t)
        if m and (best is None or m.start() < best.start()):
            best = m
    if not best:
        wide = re.compile(
            r"(?:What\s+is\s+claimed\s+is\s*:?|^\s*CLAIMS\s*$|^\s*Claims\s*$|"
            r"【\s*청구항\s*】|^\s*청구항\s*$)",
            re.IGNORECASE | re.DOTALL | re.MULTILINE,
        )
        m2 = wide.search(t)
        if not m2:
            return None
        best = m2
    tail = t[best.start() :]
    out = _trim_claims_tail_at_sections(tail)
    if len(out) < 20:
        return None
    return out


def _normalize_hybrid_claims(claims: list[ClaimElement]) -> list[ClaimElement]:
    by_no: dict[int, ClaimElement] = {}
    for c in claims:
        if c.claim_no < 1:
            continue
        by_no[c.claim_no] = c
    out: list[ClaimElement] = []
    for no in sorted(by_no.keys()):
        c = by_no[no]
        p = [x for x in (c.parent_claims or []) if x in by_no and x < no]
        p = sorted(set(p))
        ct = (c.claim_type or "").lower()
        if ct not in {"independent", "dependent"}:
            ct = "dependent" if p else "independent"
        else:
            if p and ct == "independent":
                ct = "dependent"
            if not p and ct == "dependent":
                ct = "independent"
        txt = (c.claim_text or "").strip()
        if not txt:
            continue
        out.append(
            ClaimElement(
                claim_no=no,
                claim_type=ct,
                parent_claims=p if p else None,
                claim_text=txt,
            )
        )
    return out


def extract_claims_hybrid(full_text: str, llm) -> StructuredClaims | None:
    """
    Step 1: 정규식으로 Claims(또는 US 식) 구간을 잘라내고,
    Step 2: LangChain Chat + Pydantic Structured output으로 ClaimElement 리스트를 확정한다.
    """
    if llm is None:
        return None
    j = "unknown"
    try:
        j = infer_jurisdiction("inline.txt", full_text)
    except Exception:
        pass
    claims_raw = _extract_claims_section_for_hybrid(full_text, j)
    if not claims_raw:
        return None
    ex_llm = llm
    try:
        ex_llm = llm.bind(temperature=0)  # type: ignore[union-attr]
    except Exception:
        pass
    try:
        structured_llm = ex_llm.with_structured_output(StructuredClaims)
    except Exception:
        return None
    prompt = f"""
    아래 텍스트는 특허의 Claims 섹션이야.
    도면 부호(예: 100, 200)와 청구항 번호를 엄격히 구분해서 청구항만 추출해줘.

    [규칙]
    1. '100 have a quadrilateral shape'와 같은 문구는 본문 설명이지 청구항이 아니므로 제외할 것.
    2. 청구항은 반드시 '1. ', '2. ' 처럼 숫자로 시작하며 법적 권리 범위를 정의하거나, 한국어의 경우 '제1항' … 형식으로 둘 수 있다.
    3. 종속항(Dependent claim)인 경우 인용 번호를 찾아 parent_claims에 넣을 것(미국: claim 1, of claim 2 등, 한국: 제1항, 제2항 인용).
    4. parent_claims는 해당 청구항이 직접 인용하는 상위 항만 포함할 것(정수).
    5. claim_type은 parent_claims가 비어 있으면 independent, 아니면 dependent.

    [텍스트]
    {claims_raw}
    """
    try:
        result = structured_llm.invoke(prompt)
    except Exception:
        return None
    if not result or not getattr(result, "claims", None):
        return None
    norm = _normalize_hybrid_claims(list(result.claims))
    if not norm:
        return None
    return StructuredClaims(claims=norm)


class ClaimSupportRow(BaseModel):
    limitation_id: str
    limitation_text: str
    limitation_role: str
    support_summary: str
    evidence_snippets: list[str] = Field(default_factory=list)
    evidence_score: float = 0.0


SUPPORT_SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You map one claim limitation to supporting disclosure in specification.\n"
            "Use only the provided evidence snippets. If support is weak, say so.\n"
            "Return one concise paragraph in Korean.",
        ),
        (
            "human",
            "Limitation:\n{limitation}\n\nEvidence snippets:\n{evidence}\n\n"
            "Write concise support summary.",
        ),
    ]
)


def _extract_claim_blocks(claims_text: str, jurisdiction: str) -> list[tuple[int, str]]:
    t = (claims_text or "").strip()
    if not t:
        return []
    j = (jurisdiction or "unknown").upper()
    out: list[tuple[int, str]] = []
    if j == "KR":
        matches = list(re.finditer(r"(?:^|[\n\r])\s*제\s*(\d+)\s*항\b", t))
        for i, m in enumerate(matches):
            no = int(m.group(1))
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(t)
            out.append((no, _clean(t[start:end])))
        return out
    matches = list(
        re.finditer(
            r"(?im)(?:^|[\n\r])\s*(?:claim\s*)?(\d+)\s*(?:[\.\)]\s+|\s+)(?=[A-Z\(]|[a-z])",
            t,
        )
    )
    # fallback: some PDFs flatten lines; allow inline boundary before number.
    if len(matches) <= 1:
        matches = list(
            re.finditer(
                r"(?i)(?:(?<=\s)|^)(?:claim\s*)?(\d{1,3})\s*(?:[\.\)]\s+|\s+)(?=[A-Z\(]|[a-z])",
                t,
            )
        )
    for i, m in enumerate(matches):
        no = int(m.group(1))
        if no <= 0:
            continue
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(t)
        out.append((no, _clean(t[start:end])))
    return _filter_and_validate_claim_blocks(out, j)


def _looks_like_us_claim_text(block_text: str) -> bool:
    b = (block_text or "").lower()
    claim_markers = [
        "comprising",
        "consisting of",
        "including",
        "wherein",
        "the ",
    ]
    return any(x in b for x in claim_markers)


def _is_reference_or_figure_noise(block_text: str) -> bool:
    b = (block_text or "").lower()
    # common figure/reference sections accidentally captured as claims
    if re.search(r"\b(fig\.?|figure|reference numerals?|drawing)\b", b):
        return True
    # dense "110: pixel electrode" style lists
    if len(re.findall(r"\b\d{2,4}\s*[:：\-]", b)) >= 2:
        return True
    return False


def _validate_claim_number_sequence(nums: list[int]) -> bool:
    if not nums:
        return False
    if nums[0] != 1:
        return False
    prev = nums[0]
    for n in nums[1:]:
        if n <= prev:
            return False
        if n - prev > 5:  # too large a jump likely noise capture
            return False
        prev = n
    return True


def _filter_and_validate_claim_blocks(
    blocks: list[tuple[int, str]],
    jurisdiction: str,
) -> list[tuple[int, str]]:
    if not blocks:
        return []
    j = (jurisdiction or "unknown").upper()
    filtered: list[tuple[int, str]] = []
    for no, txt in blocks:
        if len((txt or "").strip()) < 30:
            continue
        if _is_reference_or_figure_noise(txt):
            continue
        if j == "US" and not _looks_like_us_claim_text(txt):
            continue
        filtered.append((no, txt))
    if not filtered:
        return []
    nums = [n for n, _ in filtered]
    if _validate_claim_number_sequence(nums):
        return filtered
    # salvage strictly increasing subset from 1
    salvage: list[tuple[int, str]] = []
    expected = 1
    for n, txt in filtered:
        if n == expected:
            salvage.append((n, txt))
            expected += 1
        elif n > expected and salvage:
            break
    return salvage if salvage else []


def _fallback_extract_claims_from_fulltext(raw_text: str, jurisdiction: str) -> str:
    """
    split_claims_and_body 실패 시 전체 텍스트에서 청구항 후보 구간을 관대한 규칙으로 복구.
    """
    t = (raw_text or "").strip()
    if not t:
        return ""
    j = (jurisdiction or "unknown").upper()

    # 1) section header anchor
    header_patterns = []
    if j == "KR":
        header_patterns = [
            r"【\s*청구항\s*】",
            r"(?im)^\s*청구항\s*$",
        ]
    elif j == "US":
        header_patterns = [
            r"(?i)what\s+is\s+claimed\s+is\s*[:：]?",
            r"(?im)^\s*claims?\s*$",
            r"(?i)\bclaims?\b",
        ]
    else:
        header_patterns = [
            r"【\s*청구항\s*】",
            r"(?im)^\s*청구항\s*$",
            r"(?i)what\s+is\s+claimed\s+is\s*[:：]?",
            r"(?im)^\s*claims?\s*$",
            r"(?i)\bclaims?\b",
        ]

    start = -1
    used_header_anchor = False
    for pat in header_patterns:
        m = re.search(pat, t)
        if m:
            start = m.end()
            used_header_anchor = True
            break

    # 2) if no header, try first claim marker
    if start < 0:
        claim_start_patterns = [
            r"(?im)(?:^|[\n\r])\s*제\s*1\s*항\b",
            r"(?im)(?:^|[\n\r])\s*(?:claim\s*)?1\s*[\.\)]\s+",
            r"(?i)\bclaim\s*1\b",
        ]
        for pat in claim_start_patterns:
            m = re.search(pat, t)
            if m:
                start = m.start()
                break

    if start < 0:
        return ""

    tail = t[start:].strip()
    # if we anchored on header, Claim 1 should appear early; otherwise likely wrong section.
    if used_header_anchor:
        early = tail[:2000]
        if not re.search(
            r"(?im)(?:^|[\n\r])\s*(?:claim\s*)?1\s*[\.\)]\s+|\bclaim\s*1\b|(?:^|[\n\r])\s*제\s*1\s*항\b",
            early,
        ):
            return ""
    # 3) cut before description sections if present
    end_patterns = [
        r"(?im)^\s*(?:abstract|description|detailed\s+description|background)\b",
        r"【\s*(?:요약|발명의\s*설명|상세한\s*설명|도면의\s*간단한\s*설명)\s*】",
    ]
    end_idx = len(tail)
    for pat in end_patterns:
        m = re.search(pat, tail)
        if m:
            end_idx = min(end_idx, m.start())
    out = tail[:end_idx].strip()

    # 4) sanity: must look like claims
    if not re.search(
        r"(?im)\bclaim\s*\d+\b|(?:^|[\n\r])\s*(?:claim\s*)?\d+\s*[\.\)]|(?:^|[\n\r])\s*제\s*\d+\s*항\b",
        out,
    ):
        # if only one claim marker exists in full text, fallback to wider tail
        if re.search(
            r"(?im)\bclaim\s*1\b|(?:^|[\n\r])\s*(?:claim\s*)?1\s*[\.\)]|(?:^|[\n\r])\s*제\s*1\s*항\b",
            t,
        ):
            return tail[: min(len(tail), 120000)].strip()
        return ""
    # final sanitation: reduce to claim-like lines only if likely polluted
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    if len(lines) > 8:
        kept: list[str] = []
        for ln in lines:
            l = ln.lower()
            if _is_reference_or_figure_noise(l):
                continue
            kept.append(ln)
        if kept:
            out = "\n".join(kept)
    return out[:120000]


def _extract_parent_claims(claim_text: str, jurisdiction: str, claim_no: int) -> list[int]:
    t = (claim_text or "").lower()
    j = (jurisdiction or "unknown").upper()
    parents: set[int] = set()
    if j == "KR":
        for m in re.finditer(r"제\s*(\d+)\s*항", t):
            parents.add(int(m.group(1)))
    else:
        for m in re.finditer(r"\bclaim\s*(\d+)\b", t):
            parents.add(int(m.group(1)))
        # flattened style: "The device of 1 ..." / "according to 1"
        for m in re.finditer(r"\bof\s+(\d+)\b|\baccording\s+to\s+(\d+)\b", t):
            n = m.group(1) or m.group(2)
            if n:
                parents.add(int(n))
        for m in re.finditer(r"\bclaims\s*(\d+)\s*[-~]\s*(\d+)\b", t):
            a, b = int(m.group(1)), int(m.group(2))
            lo, hi = min(a, b), max(a, b)
            for n in range(lo, hi + 1):
                parents.add(n)
    parents.discard(claim_no)
    return sorted(parents)


def parse_claim_hierarchy(claims_text: str, jurisdiction: str) -> list[ClaimElement]:
    nodes: list[ClaimElement] = []
    blocks = _extract_claim_blocks(claims_text, jurisdiction)
    claim_nos = {n for n, _ in blocks}
    for no, txt in blocks:
        parents = _extract_parent_claims(txt, jurisdiction, no)
        # dependent reference must target existing earlier claims
        parents = [p for p in parents if p in claim_nos and p < no]
        nodes.append(
            ClaimElement(
                claim_no=no,
                claim_text=txt,
                claim_type="dependent" if parents else "independent",
                parent_claims=parents if parents else None,
            )
        )
    return nodes


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9가-힣]{2,}", (text or "").lower())
    stop = {"the", "and", "for", "that", "with", "상기", "및", "또는", "그리고"}
    return {w for w in words if w not in stop}


def _score_overlap(a: str, b: str) -> float:
    ta = _tokens(a)
    tb = _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta.intersection(tb)) / max(len(ta), 1)


def _spec_sentences(spec_text: str) -> list[str]:
    items = re.split(r"(?<=[\.\?!다])\s+|\n{2,}", (spec_text or "").strip())
    out: list[str] = []
    for x in items:
        s = _clean(x)
        if len(s) >= 20:
            out.append(s)
    return out


def _top_evidence(limitation_text: str, spec_text: str, top_k: int = 2) -> list[tuple[str, float]]:
    scored: list[tuple[str, float]] = []
    for sent in _spec_sentences(spec_text):
        sc = _score_overlap(limitation_text, sent)
        if sc > 0:
            scored.append((sent, sc))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


def build_claim_support_rows(
    *,
    claim_text: str,
    claim_jurisdiction: str,
    specification_text: str,
    llm=None,
    use_llm: bool = False,
) -> list[ClaimSupportRow]:
    structured = structure_claim_text(claim_text, claim_jurisdiction)
    rows: list[ClaimSupportRow] = []
    for lim in [x for x in structured.limitations if x.role != "preamble"]:
        evidence = _top_evidence(lim.text, specification_text, top_k=2)
        snippets = [e[0] for e in evidence]
        best_score = evidence[0][1] if evidence else 0.0
        if not snippets:
            summary = "명세서에서 해당 구성요소를 직접 지지하는 문장을 찾지 못했습니다."
        else:
            summary = (
                f"명세서에서 해당 구성요소를 지지하는 문장이 확인됩니다. "
                f"핵심 근거: '{snippets[0][:120]}'."
            )
        if use_llm and llm is not None and snippets:
            try:
                chain = SUPPORT_SUMMARY_PROMPT | llm
                out = chain.invoke(
                    {
                        "limitation": lim.text,
                        "evidence": "\n".join(f"- {x}" for x in snippets),
                    }
                )
                summary = (out.content if hasattr(out, "content") else str(out)).strip() or summary
            except Exception:
                pass
        rows.append(
            ClaimSupportRow(
                limitation_id=lim.limitation_id,
                limitation_text=lim.text,
                limitation_role=lim.role,
                support_summary=summary,
                evidence_snippets=snippets,
                evidence_score=round(best_score, 4),
            )
        )
    return rows


def _build_phase2_payload(
    *,
    raw_text: str,
    source_file: str,
    jurisdiction_hint: str,
    llm=None,
    use_llm: bool = False,
    input_mode: str,
) -> dict:
    j = (
        jurisdiction_hint.upper()
        if (jurisdiction_hint or "").lower() in {"kr", "us"}
        else infer_jurisdiction(source_file, raw_text)
    )
    parsed = parse_patent_document(raw_text, j, source_file)
    claims_text = (parsed.claims_text or "").strip()
    if not claims_text:
        claims_text = _fallback_extract_claims_from_fulltext(raw_text, j)
    spec_text = (parsed.body_text or raw_text).strip()
    # claims를 fallback으로 복구한 경우 spec_text도 과도하게 claims를 포함하지 않도록 재보정
    if claims_text and spec_text.startswith(claims_text[: min(200, len(claims_text))]):
        spec_text = raw_text.replace(claims_text, "", 1).strip() or spec_text
    hierarchy_source = "regex"
    hierarchy: list[ClaimElement] = []
    if llm is not None:
        try:
            hybrid = extract_claims_hybrid(raw_text, llm)
            if hybrid and hybrid.claims:
                hierarchy = _normalize_hybrid_claims(list(hybrid.claims))
                if hierarchy:
                    hierarchy_source = "hybrid_llm"
        except Exception:
            hierarchy = []
    if not hierarchy:
        hierarchy = parse_claim_hierarchy(claims_text, j)
        hierarchy_source = "regex"
    # 계층을 전혀 못 만든 경우 claim1 단일 노드라도 제공해 UI 동작을 유지
    if not hierarchy:
        claim1 = (parsed.invention_claim_one or "").strip()
        if claim1:
            hierarchy = [
                ClaimElement(
                    claim_no=1,
                    claim_text=claim1,
                    claim_type="independent",
                    parent_claims=None,
                )
            ]
            hierarchy_source = "claim1_fallback"
    return {
        "input_mode": input_mode,
        "source_file": source_file,
        "jurisdiction": j,
        "claims_text": claims_text,
        "spec_text": spec_text,
        "claim_hierarchy": [n.model_dump() for n in hierarchy],
        "claim_hierarchy_source": hierarchy_source,
        "llm_support_enabled": use_llm,
        "selected_claim_support": None,
    }


def build_phase2_invention_payload_from_upload(
    *,
    invention_file: tuple[str, bytes],
    jurisdiction_hint: str = "unknown",
    llm=None,
    use_llm: bool = False,
) -> dict:
    name, data = invention_file
    raw = load_text_from_uploaded(name, data)
    return _build_phase2_payload(
        raw_text=raw,
        source_file=name,
        jurisdiction_hint=jurisdiction_hint,
        llm=llm,
        use_llm=use_llm,
        input_mode="upload",
    )


def build_phase2_invention_payload_from_text(
    *,
    invention_text: str,
    jurisdiction_hint: str = "unknown",
    virtual_source: str = "invention_text_input.txt",
    llm=None,
    use_llm: bool = False,
) -> dict:
    return _build_phase2_payload(
        raw_text=invention_text or "",
        source_file=virtual_source,
        jurisdiction_hint=jurisdiction_hint,
        llm=llm,
        use_llm=use_llm,
        input_mode="text",
    )


def build_selected_claim_support(
    *,
    payload: dict,
    claim_no: int,
    llm=None,
    use_llm: bool = False,
) -> dict:
    node = next(
        (n for n in (payload.get("claim_hierarchy") or []) if int(n.get("claim_no", -1)) == int(claim_no)),
        None,
    )
    out = dict(payload)
    if node is None:
        out["selected_claim_support"] = {"claim_no": claim_no, "error": "selected claim not found", "rows": []}
        return out
    rows = build_claim_support_rows(
        claim_text=node.get("claim_text", ""),
        claim_jurisdiction=payload.get("jurisdiction", "unknown"),
        specification_text=payload.get("spec_text", ""),
        llm=llm,
        use_llm=use_llm,
    )
    out["selected_claim_support"] = {
        "claim_no": claim_no,
        "claim_type": node.get("claim_type"),
        "parent_claims": node.get("parent_claims", []),
        "rows": [r.model_dump() for r in rows],
    }
    return out

