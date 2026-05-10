"""Phase 3: Deep analysis helpers for claim element comparison."""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

from phase2_claim_structuring import StructuredClaim, structure_claim_text
from patent_parse import (
    infer_jurisdiction,
    load_text_from_uploaded,
    parse_patent_document,
)


class ElementMatchRow(BaseModel):
    invention_limitation_id: str
    invention_text: str
    invention_role: str
    best_prior_limitation_id: str | None = None
    best_prior_text: str | None = None
    best_prior_role: str | None = None
    best_prior_source_file: str | None = None
    score: float = 0.0
    status: Literal["matched", "partial", "missing"]


class ElementComparisonResult(BaseModel):
    invention_structured: StructuredClaim
    prior_structured: StructuredClaim
    rows: list[ElementMatchRow] = Field(default_factory=list)
    coverage_summary: dict = Field(default_factory=dict)


_STOPWORDS = {
    "a",
    "an",
    "the",
    "of",
    "to",
    "and",
    "or",
    "with",
    "for",
    "that",
    "is",
    "are",
    "상기",
    "및",
    "또는",
    "그리고",
    "하는",
    "있다",
}


def _tokens(text: str) -> set[str]:
    t = (text or "").lower()
    words = re.findall(r"[a-z0-9가-힣]{2,}", t)
    return {w for w in words if w not in _STOPWORDS}


def _score_overlap(a: str, b: str) -> float:
    ta = _tokens(a)
    tb = _tokens(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta.intersection(tb))
    return inter / max(len(ta), 1)


def _status_from_score(score: float) -> Literal["matched", "partial", "missing"]:
    if score >= 0.55:
        return "matched"
    if score >= 0.30:
        return "partial"
    return "missing"


def overlap_evidence_snippet(el_text: str, prior_text: str, *, max_len: int = 72) -> str:
    """비교 표용: 한계 텍스트와 선행 청구에 공통으로 나타나는 의미 있는 토큰 나열(근거 단서)."""
    tb = (prior_text or "").lower()
    if not tb.strip():
        return ""
    picks = sorted(
        (w for w in _tokens(el_text) if len(w) >= 4 and w in tb),
        key=len,
        reverse=True,
    )
    if not picks:
        return ""
    out: list[str] = []
    seen: set[str] = set()
    for w in picks:
        if w in seen:
            continue
        seen.add(w)
        out.append(w)
        blob = " ".join(out)
        if len(blob) >= max_len:
            break
    return blob[:max_len].strip()


def compare_claim_elements(
    *,
    invention_claim_text: str,
    prior_claim_text: str,
    invention_jurisdiction: str = "US",
    prior_jurisdiction: str = "US",
) -> ElementComparisonResult:
    inv = structure_claim_text(invention_claim_text, invention_jurisdiction)
    prior = structure_claim_text(prior_claim_text, prior_jurisdiction)

    rows: list[ElementMatchRow] = []
    prior_limits = [x for x in prior.limitations if x.role != "preamble"]

    for inv_lim in inv.limitations:
        if inv_lim.role == "preamble":
            continue
        best = None
        best_score = 0.0
        for pr_lim in prior_limits:
            s = _score_overlap(inv_lim.text, pr_lim.text)
            if s > best_score:
                best_score = s
                best = pr_lim
        rows.append(
            ElementMatchRow(
                invention_limitation_id=inv_lim.limitation_id,
                invention_text=inv_lim.text,
                invention_role=inv_lim.role,
                best_prior_limitation_id=(best.limitation_id if best else None),
                best_prior_text=(best.text if best else None),
                best_prior_role=(best.role if best else None),
                score=round(best_score, 4),
                status=_status_from_score(best_score),
            )
        )

    total = len(rows)
    matched = len([r for r in rows if r.status == "matched"])
    partial = len([r for r in rows if r.status == "partial"])
    missing = len([r for r in rows if r.status == "missing"])
    coverage = round((matched + partial * 0.5) / total, 4) if total else 0.0

    return ElementComparisonResult(
        invention_structured=inv,
        prior_structured=prior,
        rows=rows,
        coverage_summary={
            "total_elements": total,
            "matched": matched,
            "partial": partial,
            "missing": missing,
            "coverage_score": coverage,
        },
    )


def _split_spec_disclosures(text: str) -> list[str]:
    src = (text or "").strip()
    if not src:
        return []
    parts = re.split(r"(?<=[\.\?!])\s+|\n{2,}", src)
    out: list[str] = []
    for p in parts:
        s = re.sub(r"\s+", " ", p).strip()
        if len(s) < 25:
            continue
        out.append(s)
    return out


def compare_claim_to_prior_spec_disclosures(
    *,
    invention_claim_text: str,
    prior_spec_docs: list[tuple[str, str]],
    invention_jurisdiction: str = "US",
) -> dict:
    inv = structure_claim_text(invention_claim_text, invention_jurisdiction)
    rows: list[ElementMatchRow] = []

    prior_pool: list[tuple[str, str]] = []
    for source_file, spec_text in prior_spec_docs:
        for snippet in _split_spec_disclosures(spec_text):
            prior_pool.append((source_file, snippet))

    for inv_lim in [x for x in inv.limitations if x.role != "preamble"]:
        best_score = 0.0
        best_file = None
        best_text = None
        for src, snippet in prior_pool:
            s = _score_overlap(inv_lim.text, snippet)
            if s > best_score:
                best_score = s
                best_file = src
                best_text = snippet
        rows.append(
            ElementMatchRow(
                invention_limitation_id=inv_lim.limitation_id,
                invention_text=inv_lim.text,
                invention_role=inv_lim.role,
                best_prior_limitation_id=None,
                best_prior_text=best_text,
                best_prior_role="spec_disclosure" if best_text else None,
                best_prior_source_file=best_file,
                score=round(best_score, 4),
                status=_status_from_score(best_score),
            )
        )

    total = len(rows)
    matched = len([r for r in rows if r.status == "matched"])
    partial = len([r for r in rows if r.status == "partial"])
    missing = len([r for r in rows if r.status == "missing"])
    coverage = round((matched + partial * 0.5) / total, 4) if total else 0.0
    return {
        "analysis_mode": "claim_vs_prior_spec_disclosures",
        "invention_structured": inv.model_dump(),
        "rows": [r.model_dump() for r in rows],
        "coverage_summary": {
            "total_elements": total,
            "matched": matched,
            "partial": partial,
            "missing": missing,
            "coverage_score": coverage,
        },
    }


def build_phase3_test_payload(
    *,
    invention_claim_text: str,
    prior_claim_text: str,
    invention_jurisdiction: str = "US",
    prior_jurisdiction: str = "US",
) -> dict:
    result = compare_claim_elements(
        invention_claim_text=invention_claim_text,
        prior_claim_text=prior_claim_text,
        invention_jurisdiction=invention_jurisdiction,
        prior_jurisdiction=prior_jurisdiction,
    )
    return result.model_dump()


def build_phase3_upload_payload(
    *,
    invention_file: tuple[str, bytes],
    prior_files: list[tuple[str, bytes]],
    invention_jurisdiction_hint: str = "unknown",
) -> dict:
    inv_name, inv_data = invention_file
    inv_raw = load_text_from_uploaded(inv_name, inv_data)
    inv_j = (
        invention_jurisdiction_hint.upper()
        if invention_jurisdiction_hint.lower() in {"kr", "us"}
        else infer_jurisdiction(inv_name, inv_raw)
    )
    inv_parsed = parse_patent_document(inv_raw, inv_j, inv_name)
    invention_claim = (
        (inv_parsed.invention_claim_one or "").strip()
        or (inv_parsed.claims_text or "").strip()
        or inv_raw.strip()
    )

    prior_specs: list[tuple[str, str]] = []
    prior_meta: list[dict] = []
    for name, data in prior_files:
        raw = load_text_from_uploaded(name, data)
        j = infer_jurisdiction(name, raw)
        parsed = parse_patent_document(raw, j, name)
        spec = (parsed.body_text or raw).strip()
        prior_specs.append((name, spec))
        prior_meta.append(
            {
                "source_file": name,
                "jurisdiction": j,
                "spec_length": len(spec),
            }
        )

    result = compare_claim_to_prior_spec_disclosures(
        invention_claim_text=invention_claim,
        prior_spec_docs=prior_specs,
        invention_jurisdiction=inv_j,
    )
    result["invention_input"] = {
        "source_file": inv_name,
        "jurisdiction": inv_j,
        "claim_text_length": len(invention_claim),
    }
    result["prior_inputs"] = prior_meta
    return result

