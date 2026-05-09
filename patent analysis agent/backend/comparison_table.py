"""Comparison Table: 다수 선행 특허 대비 청구 구성요소 스코어 → Markdown 표."""
from __future__ import annotations

import html
import re
from typing import Any

from phase2_claim_structuring import structure_claim_text
from phase3_deep_analysis import _score_overlap, _status_from_score, overlap_evidence_snippet


def _label_status(st: str, lang: str) -> str:
    if lang.startswith("ko"):
        return {"matched": "일치", "partial": "부분", "missing": "미확인"}.get(st, st)
    return st


def _short_name(path: str, col: int) -> str:
    base = path.rsplit("/", 1)[-1].replace("\\", "/").rsplit("/", 1)[-1]
    if len(base) > 28:
        return base[:25] + "…"
    return base or f"prior_{col}"


def _md_cell(text: str, max_len: int = 100) -> str:
    t = re.sub(r"\s+", " ", (text or "").strip()).replace("|", "\\|")
    if len(t) > max_len:
        return t[: max_len - 1] + "…"
    return t or "—"


def list_invention_independent_claim_entries(inv_meta: list[dict]) -> list[dict[str, Any]]:
    """
    세션 invention_claim1_meta에서 독립항 전문 목록 (번호 순, 파일별).

    `independent_claims`에 제1항이 없으면 `claim1_full`로 보강.
    """
    out: list[dict[str, Any]] = []
    for row in inv_meta or []:
        sf = str(row.get("source_file") or "")
        j = str(row.get("jurisdiction") or "unknown").upper()
        base = sf.rsplit("/", 1)[-1].replace("\\", "/").rsplit("/", 1)[-1]
        by_num: dict[int, str] = {}
        for c in row.get("independent_claims") or []:
            n = int(c.get("claim_num") or 0)
            t = (c.get("text") or "").strip()
            if n >= 1 and t:
                by_num[n] = t
        c1 = (row.get("claim1_full") or "").strip()
        if 1 not in by_num and c1:
            by_num[1] = c1
        for n in sorted(by_num.keys()):
            out.append(
                {
                    "source_file": sf,
                    "file_base": base or "?",
                    "jurisdiction": j,
                    "claim_num": n,
                    "text": by_num[n],
                }
            )
    return out


def _comparison_caption(lang: str, *, include_overlap_evidence: bool) -> str:
    ko = lang.startswith("ko")
    if ko:
        note_ev = (
            " 괄호 안 발췌는 해당 선행 청구와 겹치는 토큰 단서입니다."
            if include_overlap_evidence
            else ""
        )
        return (
            f"\n\n**표 해석 경고:** 토큰 기반 유사도이며 법적 신규성·진보성 판단이 아닙니다.{note_ev}\n\n"
            "특허 전문가 검토 필요.\n"
        )
    note_ev = (
        " Parenthetical snippets highlight overlapping tokens vs prior claim."
        if include_overlap_evidence
        else ""
    )
    return (
        f"\n\n**Disclaimer:** Token overlap only; not a legal novelty/obviousness determination.{note_ev}\n\n"
        "Consult a patent professional.\n"
    )


def build_comparison_table_markdown(
    invention_claim_text: str,
    invention_jurisdiction: str,
    prior_claim_meta: list[dict],
    *,
    lang: str = "ko",
    include_overlap_evidence: bool = True,
    append_caption: bool = True,
) -> str:
    """
    prior_claim_meta: [{"source_file", "jurisdiction", "claim1_full"}, ...]
    """
    inv = (invention_claim_text or "").strip()
    priors = [
        {
            "file": m.get("source_file") or "?",
            "j": (m.get("jurisdiction") or "unknown").upper(),
            "claim": (m.get("claim1_full") or "").strip(),
        }
        for m in (prior_claim_meta or [])
        if (m.get("claim1_full") or "").strip()
    ]
    if not inv or not priors:
        if lang.startswith("ko"):
            if not inv and not priors:
                msg = (
                    "본 발명·선행 문헌 모두에서 제1항/Claim 1에 쓸 텍스트를 확보하지 못했습니다. "
                    "비교 표는 청구항 추출 결과에 의존합니다. 인덱스 `chunks=`는 본문·선행 전체 청크를 포함할 수 있어 숫자와 무관할 수 있습니다."
                )
            elif not inv:
                msg = (
                    "본 발명에서 독립항(제1항/Claim 1) 또는 청구항 구간을 비교 표에 쓸 만큼 확보하지 못했습니다. "
                    "PDF에서 【청구항】·Claims 구간이 비어 있거나 텍스트 추출이 깨졌는지 확인하세요."
                )
            else:
                msg = (
                    "선행 문헌에서 Claim 1 또는 청구항 구간을 비교 표에 쓸 만큼 확보하지 못했습니다. "
                    "선행 파일의 청구항 추출을 확인하세요."
                )
        elif not inv and not priors:
            msg = (
                "Could not obtain Claim 1 / claims text for both invention and prior art. "
                "The comparison table depends on claim extraction; chunk counts may still include body text."
            )
        elif not inv:
            msg = (
                "Could not obtain the invention independent claim (or usable claims block) for the table. "
                "Check PDF claims section / text extraction."
            )
        else:
            msg = (
                "Could not obtain prior-art Claim 1 (or usable claims block) for any prior file. "
                "Check prior PDF claims extraction."
            )
        return msg

    structured = structure_claim_text(inv, invention_jurisdiction or "unknown")
    # preamble·wherein·본문 한계 모두 표에 포함 (이전에는 preamble을 제외해 서두가 누락됨)
    elements = list(structured.limitations)
    if not elements:
        return (
            "구조화된 한계 요소가 없습니다."
            if lang.startswith("ko")
            else "No structured limitation elements."
        )

    ko = lang.startswith("ko")
    headers = (
        ["청구항 구성 요소", *[_short_name(p["file"], i) for i, p in enumerate(priors)], "차별화 포인트"]
        if ko
        else ["Claim element", *[_short_name(p["file"], i) for i, p in enumerate(priors)], "Differentiation hint"]
    )

    rows_md: list[str] = []
    rows_md.append("| " + " | ".join(headers) + " |")
    rows_md.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for el in elements:
        scores: list[float] = []
        statuses: list[str] = []
        cells = [_md_cell(el.text, 420)]
        for p in priors:
            sc = _score_overlap(el.text, p["claim"])
            scores.append(sc)
            st = _status_from_score(sc)
            statuses.append(st)
            lab = _label_status(st, lang)
            if include_overlap_evidence:
                ev = overlap_evidence_snippet(el.text, p["claim"])
                if ev:
                    lab = f"{lab} ({ev})"
            cells.append(_md_cell(lab, 160))
        all_matched = bool(statuses) and all(s == "matched" for s in statuses)
        if all_matched:
            diff = ""
        else:
            mn = min(scores) if scores else 0.0
            if mn >= 0.55:
                diff = (
                    "모든 열에서 높은 유사도 — 차별 논점은 명세·종속항·동작 조건을 검토하세요."
                    if ko
                    else "High overlap across columns — review spec, dependents, and operational nuances."
                )
            elif mn >= 0.30:
                diff = (
                    "일부 한계에서 선행 매칭이 약함 — 해당 한계를 중심으로 신규성·진보성 논점 후보."
                    if ko
                    else "Weak match on some limits — candidate angles around those limitations."
                )
            else:
                diff = (
                    "선행 대비 표현 차이 큼 — 단, 명세 공개 범위는 별도 검토."
                    if ko
                    else "Substantial textual divergence — still verify disclosure breadth."
                )
        diff_cell = "" if not (diff or "").strip() else _md_cell(diff, 160)
        cells.append(diff_cell)
        rows_md.append("| " + " | ".join(cells) + " |")

    body = "\n".join(rows_md)
    cap = _comparison_caption(lang, include_overlap_evidence=include_overlap_evidence) if append_caption else ""
    return body + cap


def build_comparison_table_markdown_for_session(
    invention_claim1_meta: list[dict],
    prior_claim_meta: list[dict],
    *,
    lang: str = "ko",
    include_overlap_evidence: bool = True,
) -> str:
    """본 발명 세션 메타의 모든 독립항에 대해 표를 나열하고, 맨 아래 경고 문구는 한 번만 붙인다."""
    entries = list_invention_independent_claim_entries(invention_claim1_meta)
    if not entries:
        fallback = "\n\n".join(
            (m.get("claim1_full") or "").strip()
            for m in (invention_claim1_meta or [])
            if (m.get("claim1_full") or "").strip()
        )
        inv_j = (
            str((invention_claim1_meta[0] or {}).get("jurisdiction") or "unknown")
            if invention_claim1_meta
            else "unknown"
        )
        return build_comparison_table_markdown(
            fallback,
            inv_j,
            prior_claim_meta,
            lang=lang,
            include_overlap_evidence=include_overlap_evidence,
            append_caption=True,
        )
    parts: list[str] = []
    for e in entries:
        ju = e["jurisdiction"]
        base = e["file_base"]
        n = int(e["claim_num"])
        txt = str(e["text"])
        if ju == "KR":
            parts.append(f"### {base} · 제{n}항 (독립)\n\n")
        else:
            parts.append(f"### {base} · Claim {n} (independent)\n\n")
        parts.append(
            build_comparison_table_markdown(
                txt,
                ju,
                prior_claim_meta,
                lang=lang,
                include_overlap_evidence=include_overlap_evidence,
                append_caption=False,
            )
        )
        parts.append("\n\n")
    parts.append(_comparison_caption(lang, include_overlap_evidence=include_overlap_evidence))
    return "".join(parts).strip()


def comparison_table_html_escape(markdown_table: str) -> str:
    """`<pre>` 안전 이스케이프 HTML 조각."""
    return f'<section class="comparison-table"><pre>{html.escape(markdown_table)}</pre></section>'
