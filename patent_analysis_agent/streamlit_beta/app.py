"""Patent Analysis Agent — Phase 4 Streamlit 베타 UI.

FastAPI 백엔드만 호출합니다. 백엔드가 꺼져 있으면 오류 메시지로 안내합니다.
실행: `patent_analysis_agent` 폴더에서 run_streamlit.ps1 / run_streamlit.bat
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

import requests
import streamlit as st

DEFAULT_API = os.environ.get("PATENT_AGENT_API_BASE", "http://127.0.0.1:8000").rstrip("/")


def _markdown_sig(a: str, b: str) -> str:
    h = hashlib.sha256()
    h.update((a or "").encode("utf-8"))
    h.update(b"|".encode("utf-8"))
    h.update((b or "").encode("utf-8"))
    return h.hexdigest()


def _fmt_http_error(resp: requests.Response) -> str:
    try:
        data = resp.json()
        detail = data.get("detail")
        if isinstance(detail, dict):
            msg = detail.get("message")
            if msg:
                extra = {k: v for k, v in detail.items() if k != "message"}
                if extra:
                    return f"{msg}\n\n{json.dumps(extra, ensure_ascii=False, indent=2)}"
                return str(msg)
            return json.dumps(detail, ensure_ascii=False, indent=2)
        if isinstance(detail, list):
            return json.dumps(detail, ensure_ascii=False, indent=2)
        if detail is not None:
            return str(detail)
    except Exception:
        pass
    body = (resp.text or "").strip()
    if body:
        return body[:8000]
    return f"HTTP {resp.status_code}"


def _post_multipart_index(
    api_base: str,
    invention_parts: list[tuple[str, bytes, str]],
    prior_parts: list[tuple[str, bytes, str]],
    use_llm_refine: bool,
    timeout: int,
) -> dict[str, Any]:
    url = f"{api_base}/api/v1/index/build"
    files: list[tuple[str, tuple[str, bytes, str]]] = []
    for name, raw, ctype in invention_parts:
        files.append(("invention", (name, raw, ctype)))
    for name, raw, ctype in prior_parts:
        files.append(("prior", (name, raw, ctype)))
    data = {"use_llm_refine": "true" if use_llm_refine else "false"}
    r = requests.post(url, files=files, data=data, timeout=timeout)
    if not r.ok:
        raise RuntimeError(_fmt_http_error(r))
    return r.json()


def _post_analyze(api_base: str, session_id: str, language: str, timeout: int) -> dict[str, Any]:
    url = f"{api_base}/api/v1/analyze"
    r = requests.post(
        url,
        json={"session_id": session_id, "language": language},
        timeout=timeout,
    )
    if not r.ok:
        raise RuntimeError(_fmt_http_error(r))
    return r.json()


def _post_export_docx(
    api_base: str,
    analysis_md: str,
    comparison_md: str,
    language: str,
    timeout: int,
) -> bytes:
    url = f"{api_base}/api/v1/export/docx/combined"
    r = requests.post(
        url,
        json={
            "analysis_markdown": analysis_md,
            "comparison_table_markdown": comparison_md,
            "language": language,
        },
        timeout=timeout,
    )
    if not r.ok:
        raise RuntimeError(_fmt_http_error(r))
    return r.content


def _file_parts(uploaded) -> tuple[str, bytes, str]:
    name = uploaded.name or "upload"
    raw = uploaded.getvalue()
    ct = getattr(uploaded, "type", None) or "application/octet-stream"
    return (name, raw, str(ct))


def main() -> None:
    st.set_page_config(
        page_title="Patent Analysis Agent (Beta)",
        page_icon="⚗️",
        layout="wide",
    )

    ko = st.session_state.get("ui_lang", "ko") == "ko"

    def T(ko_text: str, en_text: str) -> str:
        return ko_text if ko else en_text

    with st.sidebar:
        st.radio(
            "UI / 언어",
            options=["ko", "en"],
            format_func=lambda x: "한국어" if x == "ko" else "English",
            key="ui_lang",
            horizontal=True,
        )
        api_base = st.text_input(
            T("API 베이스 URL", "API base URL"),
            value=DEFAULT_API,
            help=T(
                "uvicorn으로 띄운 FastAPI 주소입니다. 예: http://127.0.0.1:8000",
                "FastAPI URL from uvicorn, e.g. http://127.0.0.1:8000",
            ),
        ).rstrip("/")

        analyze_lang = st.selectbox(
            T("분석 출력 언어", "Analysis language"),
            options=["ko", "en"],
            format_func=lambda x: "한국어" if x == "ko" else "English",
        )

        use_llm = st.checkbox(
            T("Phase2 클레임 LLM 보정 (use_llm_refine)", "Phase 2 claim LLM refine"),
            value=False,
        )

        idx_timeout = st.number_input(
            T("인덱스 빌드 타임아웃(초)", "Index build timeout (s)"),
            min_value=60,
            max_value=3600,
            value=600,
            step=60,
        )
        an_timeout = st.number_input(
            T("분석 타임아웃(초)", "Analysis timeout (s)"),
            min_value=120,
            max_value=7200,
            value=1800,
            step=60,
        )

        feedback_url = os.environ.get("STREAMLIT_FEEDBACK_URL", "").strip()
        if feedback_url:
            st.link_button(T("피드백 링크", "Feedback"), feedback_url)

        if st.button(T("헬스 확인", "Health check")):
            try:
                h = requests.get(f"{api_base}/health", timeout=10)
                if h.ok:
                    st.success(json.dumps(h.json(), ensure_ascii=False))
                else:
                    st.error(_fmt_http_error(h))
            except requests.RequestException as e:
                st.error(f"{type(e).__name__}: {e}")

        with st.expander(T("베타 안내", "Beta notes")):
            st.markdown(
                T(
                    "- 백엔드 세션은 **메모리**에만 있어 서버 재시작 시 사라집니다.\n"
                    "- 베타 UI는 **동기 분석**만 사용합니다(Progress는 스피너). "
                    "실시간 스트리밍은 Next.js 웹을 사용하세요.\n"
                    "- 최종 법적 판단은 전문가 자문이 필요합니다.",
                    "- Backend sessions are **in-memory**; restarting uvicorn clears them.\n"
                    "- This beta uses **synchronous** `/analyze` only (spinner progress). "
                    "Use the Next.js app for SSE streaming.\n"
                    "- Not legal advice.",
                )
            )

    st.title(T("Patent Analysis Agent — Streamlit 베타", "Patent Analysis Agent — Streamlit beta"))
    st.caption(
        T(
            "본 발명·선행 파일 업로드 → 인덱스 빌드 → 분석 → DOCX",
            "Upload invention & prior art → build index → analyze → DOCX",
        )
    )

    inv_files = st.file_uploader(
        T("본 발명 파일 (필수)", "Invention files (required)"),
        type=["pdf", "txt", "docx"],
        accept_multiple_files=True,
        help=T("PDF / TXT / DOCX", "PDF / TXT / DOCX"),
    )
    prior_files = st.file_uploader(
        T("선행 문헌 (선택)", "Prior art (optional)"),
        type=["pdf", "txt", "docx"],
        accept_multiple_files=True,
    )

    col_a, col_b = st.columns(2)
    with col_a:
        build = st.button(T("인덱스 빌드", "Build search index"), type="primary")
    with col_b:
        run_an = st.button(T("분석 실행", "Run analysis"), disabled=not st.session_state.get("session_id"))

    if build:
        if not inv_files:
            st.error(T("본 발명 파일을 하나 이상 선택하세요.", "Select at least one invention file."))
        else:
            inv_parts = [_file_parts(f) for f in inv_files]
            pr_parts = [_file_parts(f) for f in prior_files] if prior_files else []
            with st.spinner(T("인덱스 빌드 중… (시간이 걸릴 수 있습니다)", "Building index… (may take a while)")):
                try:
                    out = _post_multipart_index(
                        api_base,
                        inv_parts,
                        pr_parts,
                        use_llm,
                        timeout=int(idx_timeout),
                    )
                except requests.Timeout:
                    st.error(T("타임아웃: 파일이 크거나 서버가 바쁩니다.", "Timeout: large files or busy server."))
                    st.stop()
                except requests.RequestException as e:
                    st.error(f"{type(e).__name__}: {e}")
                    st.stop()
                except RuntimeError as e:
                    st.error(str(e))
                    st.stop()

            st.session_state["session_id"] = out.get("session_id")
            st.session_state["last_index"] = out
            st.success(
                T(
                    f"세션: `{out.get('session_id')}` · 청크 {out.get('chunk_count')}",
                    f"Session: `{out.get('session_id')}` · chunks {out.get('chunk_count')}",
                )
            )
            warns = out.get("warnings") or []
            if warns:
                with st.expander(T("경고", "Warnings")):
                    for w in warns:
                        st.text(str(w))
            preview = out.get("invention_index_preview")
            if preview is not None:
                with st.expander(T("본 발명 인덱스 미리보기", "Invention index preview")):
                    st.json(preview)

    sid = st.session_state.get("session_id")
    if sid:
        st.info(T(f"현재 세션: `{sid}`", f"Current session: `{sid}`"))

    if run_an:
        if not sid:
            st.error(T("먼저 인덱스 빌드를 실행하세요.", "Run index build first."))
        else:
            with st.spinner(
                T(
                    "심층 분석 중… (동기 API, 수 분 걸릴 수 있음)",
                    "Running analysis… (sync API, may take several minutes)",
                )
            ):
                try:
                    result = _post_analyze(api_base, sid, analyze_lang, timeout=int(an_timeout))
                except requests.Timeout:
                    st.error(
                        T(
                            "분석 타임아웃. 타임아웃 값을 늘리거나 파일·선행 개수를 줄여 보세요.",
                            "Analysis timed out. Increase timeout or reduce uploads.",
                        )
                    )
                    st.stop()
                except requests.RequestException as e:
                    st.error(f"{type(e).__name__}: {e}")
                    st.stop()
                except RuntimeError as e:
                    st.error(str(e))
                    st.stop()

            st.session_state["last_analysis"] = result
            st.session_state.pop("docx_cache_key", None)
            st.session_state.pop("docx_bytes", None)
            st.session_state.pop("docx_export_error", None)
            st.success(T("분석 완료", "Analysis complete"))

    result = st.session_state.get("last_analysis")
    if isinstance(result, dict) and result:
        comparison_md = result.get("comparison_table_markdown") or ""
        analysis_md = result.get("analysis_markdown") or ""

        tab1, tab2, tab3 = st.tabs(
            (
                T("비교 표", "Comparison table"),
                T("분석 리포트", "Analysis report"),
                T("메타 / 출처", "Meta / sources"),
            )
        )
        with tab1:
            st.markdown(comparison_md or "_empty_")
        with tab2:
            st.markdown(analysis_md or "_empty_")
        with tab3:
            st.metric("source_count", result.get("source_count", "—"))
            st.text_area(
                "retrieval_query_excerpt",
                value=result.get("retrieval_query_excerpt") or "",
                height=120,
                disabled=True,
            )
            sp = result.get("sources_preview")
            if sp:
                st.json(sp)

        cache_key = (api_base, analyze_lang, _markdown_sig(analysis_md, comparison_md))
        if st.session_state.get("docx_cache_key") != cache_key:
            try:
                docx = _post_export_docx(
                    api_base,
                    analysis_md,
                    comparison_md,
                    analyze_lang,
                    timeout=min(300, int(an_timeout)),
                )
                st.session_state["docx_bytes"] = docx
                st.session_state["docx_cache_key"] = cache_key
                st.session_state.pop("docx_export_error", None)
            except RuntimeError as e:
                st.session_state["docx_export_error"] = str(e)
                st.session_state.pop("docx_bytes", None)

        err = st.session_state.get("docx_export_error")
        if err:
            st.warning(T("DOCX 생성 실패: ", "DOCX export failed: ") + str(err))
        docx_bytes = st.session_state.get("docx_bytes")
        if docx_bytes:
            st.download_button(
                T("DOCX 내려받기", "Download DOCX"),
                data=docx_bytes,
                file_name="patent-analysis-combined.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )


main()
