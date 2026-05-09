"""Patent Analysis Agent — Phase 2 HTTP API."""
from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response, StreamingResponse
from pydantic import BaseModel, Field

from phase2_analysis import (
    build_search_index,
    combine_report_markdown,
    invention_index_preview,
    iter_sse_analysis,
    run_analysis,
)
from phase_invention_analysis import (
    iter_sse_claim_mapping_stream,
    iter_sse_invention_analysis,
    list_invention_independent_claims,
    run_invention_analysis_markdown,
)
from session_store import get_session
from phase3_export import markdown_report_to_docx_bytes

app = FastAPI(
    title="Patent Analysis Agent API",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# 로컬 개발: Next 포트 변경(3001 등)·IPv6(::1) Origin 허용 (fullmatch)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://[::1]:3000",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    """브라우저에서 루트 접속 시 API 문서로 이동."""
    return RedirectResponse(url="/docs")


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    """브라우저 기본 요청으로 인한 불필요한 404 로그 방지."""
    return Response(status_code=204)


async def _read_uploads(files: list[UploadFile]) -> list[tuple[str, bytes]]:
    out: list[tuple[str, bytes]] = []
    for f in files:
        raw = await f.read()
        out.append((f.filename or "unnamed", raw))
    return out


# Swagger UI가 multipart 배열을 `array<string>` 텍스트 칸으로 그리는 경우가 있어
# `format: binary`를 명시해 파일 선택 UI로 나오게 한다.
_INDEX_BUILD_OPENAPI_EXTRA = {
    "requestBody": {
        "content": {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "required": ["invention"],
                    "properties": {
                        "invention": {
                            "type": "array",
                            "items": {"type": "string", "format": "binary"},
                            "description": "본 발명 파일 (PDF, TXT, DOCX). 여러 개면 항목 추가 후 각각 파일 선택.",
                        },
                        "prior": {
                            "type": "array",
                            "items": {"type": "string", "format": "binary"},
                            "description": "선행 문헌 (선택). 비교 분석 전에 포함하면 됩니다.",
                        },
                        "use_llm_refine": {
                            "type": "boolean",
                            "default": False,
                            "description": "Phase2 클레임 LLM 보정 사용 여부",
                        },
                    },
                }
            }
        }
    }
}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "phase": 3}


@app.post("/api/v1/index/build", openapi_extra=_INDEX_BUILD_OPENAPI_EXTRA)
async def index_build(
    invention: list[UploadFile] = File(default=[]),
    prior: list[UploadFile] = File(default=[]),
    use_llm_refine: bool = Form(False),
) -> dict:
    if not invention:
        raise HTTPException(
            status_code=400,
            detail="At least one invention file is required.",
        )
    inv = await _read_uploads(invention)
    pr = await _read_uploads(prior)
    result = build_search_index(inv, pr, use_llm_refine_phase2=use_llm_refine)
    if not result.get("indexed"):
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Indexing produced no chunks.",
                "warnings": result.get("warnings", []),
                "invention_index_preview": result.get("invention_index_preview"),
            },
        )
    return result


@app.get("/api/v1/session/{session_id}/invention-index-preview")
def session_invention_index_preview(session_id: str) -> dict:
    """현재 세션에 올라간 본 발명 클레임 파싱·청크 요약 (인덱스 빌드 이후)."""
    data = get_session(session_id.strip())
    if data is None:
        raise HTTPException(status_code=404, detail="session_not_found")
    return invention_index_preview(data.bm25_documents, data.invention_claim1_meta)


class AnalyzeBody(BaseModel):
    session_id: str = Field(..., min_length=8)
    language: str = "ko"


class ClaimMappingStreamBody(BaseModel):
    session_id: str = Field(..., min_length=8)
    language: str = "ko"
    source_file: str = Field(..., min_length=1, max_length=512)
    claim_num: int = Field(..., ge=1, le=999)


@app.post("/api/v1/analyze")
async def analyze(body: AnalyzeBody) -> dict:
    out = run_analysis(body.session_id.strip(), body.language or "ko")
    if out.get("error") == "session_not_found":
        raise HTTPException(status_code=404, detail=out.get("detail"))
    if out.get("error") == "prior_art_required":
        raise HTTPException(status_code=422, detail=out.get("detail"))
    return out


@app.post("/api/v1/analyze/invention")
async def analyze_invention(body: AnalyzeBody) -> dict:
    out = run_invention_analysis_markdown(body.session_id.strip(), body.language or "ko")
    if out.get("error") == "session_not_found":
        raise HTTPException(status_code=404, detail=out.get("detail"))
    if out.get("error"):
        raise HTTPException(status_code=422, detail=out.get("detail"))
    return out


@app.post("/api/v1/analyze/invention/stream")
async def analyze_invention_stream(body: AnalyzeBody) -> StreamingResponse:
    sid = body.session_id.strip()
    lang = body.language or "ko"

    def byte_iter():
        yield from iter_sse_invention_analysis(sid, lang)

    return StreamingResponse(
        byte_iter(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/v1/session/{session_id}/independent-claims")
def session_independent_claims(session_id: str) -> dict:
    """본 발명 세션의 독립항 목록(번호·미리보기). 청구항 설명 SSE 선택용."""
    out = list_invention_independent_claims(session_id.strip())
    if out.get("error") == "session_not_found":
        raise HTTPException(status_code=404, detail=out.get("detail"))
    return out


@app.post("/api/v1/analyze/invention/claim-mapping/stream")
async def analyze_invention_claim_mapping_stream(body: ClaimMappingStreamBody) -> StreamingResponse:
    sid = body.session_id.strip()
    lang = body.language or "ko"
    sf = body.source_file.strip()
    cn = int(body.claim_num)

    def byte_iter():
        yield from iter_sse_claim_mapping_stream(sid, lang, sf, cn)

    return StreamingResponse(
        byte_iter(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/v1/analyze/stream")
async def analyze_stream(body: AnalyzeBody) -> StreamingResponse:
    sid = body.session_id.strip()
    lang = body.language or "ko"

    def byte_iter():
        yield from iter_sse_analysis(sid, lang)

    return StreamingResponse(
        byte_iter(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


class ExportDocxBody(BaseModel):
    markdown: str = Field(..., min_length=1)


@app.post("/api/v1/export/docx")
async def export_docx(body: ExportDocxBody) -> Response:
    try:
        raw = markdown_report_to_docx_bytes(body.markdown)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return Response(
        content=raw,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": 'attachment; filename="patent-analysis-report.docx"',
        },
    )


class ExportCombinedBody(BaseModel):
    analysis_markdown: str = ""
    comparison_table_markdown: str = ""
    language: str = "ko"


@app.post("/api/v1/export/docx/combined")
async def export_docx_combined(body: ExportCombinedBody) -> Response:
    md = combine_report_markdown(
        body.analysis_markdown,
        body.comparison_table_markdown,
        body.language or "ko",
    )
    try:
        raw = markdown_report_to_docx_bytes(md)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return Response(
        content=raw,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": 'attachment; filename="patent-analysis-combined.docx"',
        },
    )
