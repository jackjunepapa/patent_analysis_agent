"""본 발명만 대상 요약·청구-명세 매핑 (세션 내 invention 청크만 사용)."""
from __future__ import annotations

import json
from typing import Any

from langchain_openai import ChatOpenAI

from patent_parse import (
    claim_mapping_claim_column_label,
    extract_claim_preamble_plain,
    regex_split_claim_limitations,
)
from phase2_analysis import _lang_label, get_chat_llm
from prompts_invention import CLAIM_MAPPING_EXPLAIN_PROMPT, INVENTION_SUMMARY_PROMPT, invention_analysis_guidelines
from session_store import SessionData, get_session


def _inv_source_files(meta_rows: list[dict]) -> set[str]:
    return {str(row.get("source_file") or "") for row in meta_rows if row.get("source_file")}


def format_independent_claims_briefing(meta_rows: list[dict], *, max_per_claim: int = 10000) -> str:
    """
    발명 요약 프롬프트용: 세션 내 파일별 독립항 전문(번호 순).
    제1항이 independent_claims에 없으면 claim1_full로 보강.
    """
    if not meta_rows:
        return "(독립항 메타 없음 — 아래 통합 청구 텍스트만 사용)"
    parts: list[str] = []
    for row in meta_rows:
        sf = str(row.get("source_file") or "?")
        j = str(row.get("jurisdiction") or "?")
        by_num: dict[int, str] = {}
        for c in row.get("independent_claims") or []:
            n = int(c.get("claim_num") or 0)
            t = (c.get("text") or "").strip()
            if n >= 1 and t:
                by_num[n] = t
        c1 = (row.get("claim1_full") or "").strip()
        if 1 not in by_num and c1:
            by_num[1] = c1
        if not by_num:
            parts.append(f"### 파일: `{sf}`\n**관할:** {j}\n\n_(독립항 추출 없음 — 통합 청구 블록 참조)_\n")
            continue
        buf = [f"### 파일: `{sf}`\n**관할:** {j}\n\n"]
        for n in sorted(by_num.keys()):
            body = by_num[n]
            if len(body) > max_per_claim:
                body = body[:max_per_claim] + "\n[… 청구 전문 잘림 …]"
            buf.append(f"#### 독립항 제{n}항 (Claim {n})\n\n```\n{body}\n```\n\n")
        parts.append("".join(buf))
    return "\n---\n\n".join(parts)


def _limitations_seed_from_claim(claim_blob: str, j: str) -> str:
    lims = regex_split_claim_limitations(claim_blob, str(j))
    seed_lines = [f"- {x.strip()[:400]}" for x in lims if len(x.strip()) > 12][:40]
    return "\n".join(seed_lines) if seed_lines else "(한계 자동 분할 결과 없음 — 청구 전문 참조)"


def gather_invention_text_blobs(data: SessionData) -> tuple[str, str, str]:
    """
    Returns:
        claim_blob — invention_claim1_meta claim1_full 연결
        description_concat — invention body 청크 병합 (글자 상한 적용)
        limitations_seed — 정규식 기반 한계 나열 (시드)
    """
    meta = data.invention_claim1_meta or []
    claim_blob = "\n\n".join(
        (m.get("claim1_full") or "").strip()
        for m in meta
        if (m.get("claim1_full") or "").strip()
    )
    inv_files = _inv_source_files(meta)
    body_parts: list[str] = []
    claim_chunks: list[str] = []
    for d in data.bm25_documents:
        m = d.metadata or {}
        if inv_files and m.get("source_file") not in inv_files:
            continue
        dt = m.get("doc_type")
        pc = (d.page_content or "").strip()
        if not pc:
            continue
        if dt == "invention":
            pa = (m.get("paragraph_anchor") or "").strip()
            tag = f"[chunk_begin_anchor={pa}]\n" if pa else ""
            body_parts.append(tag + pc)
        elif dt == "invention_claims":
            claim_chunks.append(pc)
    desc = "\n\n---\n\n".join(body_parts) if body_parts else ""
    max_desc = 28000
    if len(desc) > max_desc:
        desc = desc[:max_desc] + "\n\n[… 명세 발췌 잘림 …]"
    j = (meta[0].get("jurisdiction") if meta else None) or "unknown"
    limitations_seed = _limitations_seed_from_claim(claim_blob, str(j))
    if claim_chunks and len(claim_blob) < 80:
        claim_blob = "\n\n".join(claim_chunks[:12])
    return claim_blob.strip(), desc.strip(), limitations_seed


def _independent_claims_briefing_from_session(data: SessionData) -> str:
    return format_independent_claims_briefing(data.invention_claim1_meta or [], max_per_claim=10000)


def prepare_invention_analysis(session_id: str) -> dict[str, Any]:
    data = get_session(session_id.strip())
    if data is None:
        return {"error": "session_not_found", "detail": session_id}
    claim_blob, description_excerpt, limitations_seed = gather_invention_text_blobs(data)
    if len(claim_blob) < 12 and len(description_excerpt) < 80:
        return {
            "error": "insufficient_invention_content",
            "detail": "본 발명 청구·명세 발췌가 부족합니다. 인덱스를 다시 빌드하세요.",
        }
    llm = get_chat_llm()
    briefing = _independent_claims_briefing_from_session(data)
    if len(briefing) > 48000:
        briefing = briefing[:48000] + "\n\n[… 독립항 브리핑 잘림 …]"
    return {
        "llm": llm,
        "claim_text": claim_blob[:16000],
        "description_excerpt": description_excerpt or "(명세 청크 없음)",
        "limitations_seed": limitations_seed[:12000],
        "independent_claims_briefing": briefing,
        "lang_hint": (data.invention_claim1_meta[0].get("jurisdiction") if data.invention_claim1_meta else "unknown"),
    }


def prepare_claim_mapping_stream(session_id: str, source_file: str, claim_num: int) -> dict[str, Any]:
    """단일 독립항에 대한 청구-명세 매핑 스트리밍 준비."""
    sid = session_id.strip()
    sf = (source_file or "").strip()
    data = get_session(sid)
    if data is None:
        return {"error": "session_not_found", "detail": sid}
    if not sf or claim_num < 1:
        return {"error": "bad_request", "detail": "source_file and claim_num required"}
    _claim_blob, desc, _ = gather_invention_text_blobs(data)
    resolved: str | None = None
    j = "unknown"
    for row in data.invention_claim1_meta or []:
        if (row.get("source_file") or "") != sf:
            continue
        j = str(row.get("jurisdiction") or "unknown")
        for c in row.get("independent_claims") or []:
            if int(c.get("claim_num") or -1) == int(claim_num):
                resolved = (c.get("text") or "").strip() or None
                break
        if resolved:
            break
        if int(claim_num) == 1:
            c1 = (row.get("claim1_full") or "").strip()
            if c1:
                resolved = c1
                break
    if not resolved:
        return {"error": "claim_not_found", "detail": f"{sf} / claim {claim_num}"}
    seed = _limitations_seed_from_claim(resolved, j)
    llm = get_chat_llm()
    return {
        "llm": llm,
        "claim_text": resolved[:16000],
        "limitations_seed": seed[:12000],
        "description_excerpt": desc or "(명세 청크 없음)",
        "lang_hint": j,
    }


def list_invention_independent_claims(session_id: str) -> dict[str, Any]:
    """UI: 독립항 번호·미리보기 (전문은 세션에만)."""
    data = get_session(session_id.strip())
    if data is None:
        return {"error": "session_not_found", "detail": session_id}
    files: list[dict[str, Any]] = []
    for row in data.invention_claim1_meta or []:
        claims_out: list[dict[str, Any]] = []
        for c in row.get("independent_claims") or []:
            claims_out.append(
                {
                    "claim_num": int(c.get("claim_num") or 0),
                    "preview": str(c.get("preview") or "")[:400],
                }
            )
        files.append(
            {
                "source_file": row.get("source_file"),
                "jurisdiction": row.get("jurisdiction"),
                "claims": claims_out,
            }
        )
    return {"session_id": session_id, "files": files}


def run_invention_analysis_markdown(session_id: str, lang: str) -> dict[str, Any]:
    prep = prepare_invention_analysis(session_id)
    if prep.get("error"):
        return prep
    data = get_session(session_id.strip())
    llm: ChatOpenAI = prep["llm"]
    g = invention_analysis_guidelines(lang)
    ll = _lang_label(lang)

    sum_msg = (INVENTION_SUMMARY_PROMPT | llm).invoke(
        {
            "guidelines": g,
            "lang_label": ll,
            "claim_text": prep["claim_text"],
            "description_excerpt": prep["description_excerpt"],
            "independent_claims_briefing": prep.get("independent_claims_briefing") or "",
        }
    )
    invention_summary_md = (sum_msg.content or "").strip()

    return {
        "session_id": session_id,
        "invention_summary_markdown": invention_summary_md,
        "claim_mapping_markdown": "",
    }


def iter_sse_invention_analysis(session_id: str, lang: str) -> Any:
    """발명 요약 SSE(독립항별 심층 표는 요약 내 `## 주요 구성·작용`에 포함)."""
    prep = prepare_invention_analysis(session_id)
    if prep.get("error") == "session_not_found":
        err = {"error": prep.get("error"), "detail": prep.get("detail")}
        yield f"event: error\ndata: {json.dumps(err, ensure_ascii=False)}\n\n".encode("utf-8")
        return
    if prep.get("error"):
        err = {"error": prep.get("error"), "detail": prep.get("detail")}
        yield f"event: error\ndata: {json.dumps(err, ensure_ascii=False)}\n\n".encode("utf-8")
        return

    llm: ChatOpenAI = prep["llm"]
    g = invention_analysis_guidelines(lang)
    ll = _lang_label(lang)
    ko = (lang or "").lower().startswith("ko")

    meta = {"session_id": session_id, "mode": "invention_only", "invention_summary": "includes_independent_claim_tables"}
    yield f"event: meta\ndata: {json.dumps(meta, ensure_ascii=False)}\n\n".encode("utf-8")

    yield _sse_local(
        "phase",
        {
            "id": "invention_summary",
            "label": "발명 요약 (스트리밍)" if ko else "Invention summary (streaming)",
        },
    )
    chain_s = INVENTION_SUMMARY_PROMPT | llm
    payload_s = {
        "guidelines": g,
        "lang_label": ll,
        "claim_text": prep["claim_text"],
        "description_excerpt": prep["description_excerpt"],
        "independent_claims_briefing": prep.get("independent_claims_briefing") or "",
    }
    for chunk in chain_s.stream(payload_s):
        piece = getattr(chunk, "content", None) or ""
        if piece:
            yield _sse_local("delta", {"t": piece, "phase": "invention_summary"})
    yield b"event: done\ndata: {}\n\n"


def iter_sse_claim_mapping_stream(session_id: str, lang: str, source_file: str, claim_num: int) -> Any:
    prep = prepare_claim_mapping_stream(session_id, source_file, claim_num)
    if prep.get("error") == "session_not_found":
        err = {"error": prep.get("error"), "detail": prep.get("detail")}
        yield f"event: error\ndata: {json.dumps(err, ensure_ascii=False)}\n\n".encode("utf-8")
        return
    if prep.get("error"):
        err = {"error": prep.get("error"), "detail": prep.get("detail")}
        yield f"event: error\ndata: {json.dumps(err, ensure_ascii=False)}\n\n".encode("utf-8")
        return

    llm: ChatOpenAI = prep["llm"]
    g = invention_analysis_guidelines(lang)
    ll = _lang_label(lang)
    ko = (lang or "").lower().startswith("ko")

    meta = {
        "session_id": session_id,
        "source_file": source_file,
        "claim_num": claim_num,
        "mode": "claim_mapping_only",
    }
    yield f"event: meta\ndata: {json.dumps(meta, ensure_ascii=False)}\n\n".encode("utf-8")

    yield _sse_local(
        "phase",
        {
            "id": "claim_mapping",
            "label": "청구항 설명·매핑 (스트리밍)" if ko else "Claim-to-description mapping (streaming)",
        },
    )
    j_map = str(prep.get("lang_hint") or "unknown")
    claim_col = claim_mapping_claim_column_label(j_map)
    preamble_plain = extract_claim_preamble_plain(prep["claim_text"]).strip() or "(서두 추출 없음 — 청구 전문 참조)"
    chain_m = CLAIM_MAPPING_EXPLAIN_PROMPT | llm
    payload_m = {
        "guidelines": g,
        "lang_label": ll,
        "claim_text": prep["claim_text"],
        "limitations_seed": prep["limitations_seed"],
        "description_excerpt": prep["description_excerpt"],
        "preamble_plain": preamble_plain,
        "claim_column": claim_col,
    }
    try:
        for chunk in chain_m.stream(payload_m):
            piece = getattr(chunk, "content", None) or ""
            if piece:
                yield _sse_local("delta", {"t": piece, "phase": "claim_mapping"})
    except Exception as e:
        note = f"\n\n[청구 매핑 오류] {e}" if ko else f"\n\n[Claim mapping error] {e}"
        yield _sse_local("delta", {"t": note, "phase": "claim_mapping"})
    yield b"event: done\ndata: {}\n\n"


def _sse_local(event: str, data: dict) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n".encode("utf-8")
