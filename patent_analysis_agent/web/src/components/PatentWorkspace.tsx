"use client";

// Phase 3 웹 UI — 소스: patent_analysis_agent/web/src/components (백엔드: patent_analysis_agent/backend)

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ComparisonTableMarkdown } from "@/components/ComparisonTableMarkdown";
import { DeepAnalysisMarkdown } from "@/components/DeepAnalysisMarkdown";
import { InventionSummaryMarkdown } from "@/components/InventionSummaryMarkdown";
import { consumeSseBuffer } from "@/lib/sse";

type Lang = "ko" | "en";

/** `/api/v1/index/build` 응답의 본 발명 클레임 파싱·청크 미리보기 */
export type InventionIndexPreview = {
  claim_parsing: Array<{
    source_file?: string;
    jurisdiction?: string;
    claim1_char_count: number;
    claim1_excerpt: string;
  }>;
  invention_claim_chunks: Array<{
    chunk_id?: string;
    source_file?: string;
    limitation_id?: string;
    limitation_role?: string;
    limitation_order?: number;
    limitation_sub_type?: string;
    section_type?: string;
    metadata_schema_version?: string;
    content_char_count: number;
    content_preview: string;
  }>;
  invention_body_chunk_count: number;
};

function apiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (raw) return raw.replace(/\/$/, "");
  return "http://127.0.0.1:8000";
}

/** fetch 네트워크/CORS 실패 시 브라우저가 TypeError: Failed to fetch 를 던짐 */
function formatApiNetworkError(e: unknown, base: string, lang: Lang): string {
  const s = String(e);
  if (
    e instanceof TypeError &&
    (s.includes("fetch") || s.includes("Failed to fetch") || s.includes("NetworkError"))
  ) {
    return lang === "ko"
      ? `연결 실패: ${base} 에 도달하지 못했습니다. (1) backend 폴더에서 uvicorn 실행 여부 확인 — 브라우저에서 ${base}/docs 가 열리는지 (2) .env.local 의 NEXT_PUBLIC_API_BASE_URL 이 백엔드 주소와 같은지 (localhost vs 127.0.0.1 혼용 시 둘 다 켜져 있어도 됨). 원본: ${s}`
      : `Cannot reach API at ${base}. (1) Run uvicorn from backend — open ${base}/docs in the browser. (2) Match NEXT_PUBLIC_API_BASE_URL in web/.env.local. Raw: ${s}`;
  }
  return s;
}

type StagedFile = { id: string; file: File };

/** 일부 환경(구형 브라우저·비보안 컨텍스트 등)에서 crypto.randomUUID 미지원 시 대비 */
function newStagedRowId(): string {
  try {
    const c = globalThis.crypto;
    if (c && typeof c.randomUUID === "function") return c.randomUUID();
  } catch {
    /* ignore */
  }
  return `f-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
}

function appendStaged(prev: StagedFile[], list: FileList | null): StagedFile[] {
  if (!list?.length) return prev;
  const add: StagedFile[] = [];
  for (let i = 0; i < list.length; i++) {
    const f = list.item(i);
    if (f) add.push({ id: newStagedRowId(), file: f });
  }
  return [...prev, ...add];
}

/** 같은 파일 재선택·일부 브라우저에서 동기 초기화 시 예외 방지 */
function resetFileInputSoon(input: HTMLInputElement): void {
  requestAnimationFrame(() => {
    try {
      input.value = "";
    } catch {
      /* IE/레거시 등에서 무시 */
    }
  });
}

async function readErrorDetail(res: Response): Promise<string> {
  try {
    const j = (await res.json()) as { detail?: unknown };
    return typeof j.detail === "string"
      ? j.detail
      : JSON.stringify(j.detail ?? res.statusText);
  } catch {
    return res.statusText;
  }
}

/** 로딩 중 액션 버튼용 (밝은 테두리·흰색 상단 스트로크 — 진한 단색 CTA 위에서 표시) */
function ActionButtonSpinner() {
  const ring = "border-white/45 border-t-white dark:border-zinc-500/60 dark:border-t-zinc-900";
  return (
    <span
      aria-hidden
      className={`inline-block size-[1.05rem] shrink-0 animate-spin rounded-full border-2 ${ring}`}
    />
  );
}

function CtaIconBuild() {
  return (
    <svg className="size-5 shrink-0 text-white opacity-95" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375"
      />
    </svg>
  );
}

function CtaIconInvention() {
  return (
    <svg className="size-5 shrink-0 text-white opacity-95" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
      />
    </svg>
  );
}

function CtaIconCompare() {
  return (
    <svg className="size-5 shrink-0 text-white opacity-95" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
    </svg>
  );
}

export function PatentWorkspace() {
  const [lang, setLang] = useState<Lang>("ko");
  const [inventionStaged, setInventionStaged] = useState<StagedFile[]>([]);
  const [priorStaged, setPriorStaged] = useState<StagedFile[]>([]);
  const inventionInputRef = useRef<HTMLInputElement>(null);
  const priorInputRef = useRef<HTMLInputElement>(null);
  const [status, setStatus] = useState<string>("");
  /** Build Search Index 오류·안내 텍스트(성공 시에는 비우고 lastBuildSuccess 사용) */
  const [buildStatus, setBuildStatus] = useState<string>("");
  /** 마지막 성공 빌드 메타(분석 준비도·경고 배지 등) */
  const [lastBuildSuccess, setLastBuildSuccess] = useState<{
    chunkCount: number;
    warnings: string[];
    hasPriorArt: boolean;
  } | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [hasPriorArt, setHasPriorArt] = useState(false);
  const [busyBuild, setBusyBuild] = useState(false);
  const [busyAnalyze, setBusyAnalyze] = useState(false);
  const [busyInventionAnalyze, setBusyInventionAnalyze] = useState(false);
  const [comparisonMd, setComparisonMd] = useState<string>("");
  const [reasoningMd, setReasoningMd] = useState<string>("");
  const [strategyMd, setStrategyMd] = useState<string>("");
  const [inventionSummaryMd, setInventionSummaryMd] = useState<string>("");
  const [inventionSummaryOpen, setInventionSummaryOpen] = useState(true);
  const [streamPhaseLabel, setStreamPhaseLabel] = useState<string>("");
  const [inventionPreview, setInventionPreview] = useState<InventionIndexPreview | null>(null);
  const [sessionCopyHint, setSessionCopyHint] = useState<string>("");
  /** null = probing */
  const [apiReachable, setApiReachable] = useState<boolean | null>(null);

  const apiBase = useMemo(() => apiBaseUrl(), []);

  const probeBackendHealth = useCallback(async (): Promise<boolean> => {
    const ac = new AbortController();
    const t = window.setTimeout(() => ac.abort(), 4000);
    try {
      const res = await fetch(`${apiBase}/health`, { method: "GET", signal: ac.signal });
      return res.ok;
    } catch {
      return false;
    } finally {
      window.clearTimeout(t);
    }
  }, [apiBase]);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const ok = await probeBackendHealth();
      if (!cancelled) setApiReachable(ok);
    })();
    return () => {
      cancelled = true;
    };
  }, [probeBackendHealth]);

  const recheckBackendHealth = useCallback(() => {
    setApiReachable(null);
    void (async () => {
      setApiReachable(await probeBackendHealth());
    })();
  }, [probeBackendHealth]);

  const labels =
    lang === "ko"
      ? {
          title: "Patent Analysis Agent",
          subtitle:
            "본 발명과 선행 특허 비교 — Phase 3: FastAPI 연동, 비교 표, 스트리밍 분석, DOCX 내보내기.",
          lang: "답변 언어",
          inv: "본 발명 파일",
          prior: "선행 문헌 (KR/US 혼합 가능)",
          actionsHeading: "🔬 분석 단계",
          build: "Build Search Index",
          buildDesc:
            "업로드한 본 발명·선행 문헌에서 텍스트를 추출하고, 청구항·본문을 논리 단위 청크로 나눈 뒤 벡터 DB(Chroma)에 임베딩합니다.",
          run: "분석 실행",
          runDesc:
            "인덱스를 사용해 하이브리드 검색 후 SSE로 분석 리포트를 스트리밍합니다. 비교 표는 먼저 표시됩니다.",
          comparison: "Comparison Table",
          analysis: "심층 분석 (스트리밍)",
          exportDocx: "DOCX로 내보내기",
          exportDocxDesc:
            "선행 특허 비교 표와 심층 분석·전략 제안 내용을 Word(.docx) 파일로 저장합니다. 본 발명 요약은 이 내보내기에 포함되지 않습니다.",
          hint: "PDF·TXT·DOCX",
          needFiles:
            "본 발명 파일을 하나 이상 선택하세요.",
          workspaceTitle: "📊 분석 워크스페이스",
          outputsInvention: "📋 본 발명 분석 결과",
          outputsPrior: "🔎 선행 특허 비교 결과",
          runInvention: "본 발명 분석 실행",
          runInventionDesc:
            "발명 요약을 스트리밍합니다. 독립항이 여러 개면 `주요 구성·작용` 안에 항목별 심층 표·전략 코멘트·근거 단락 링크가 포함됩니다.",
          runPrior: "선행 특허 비교 실행",
          priorOptionalHint:
            "선행 파일은 선택입니다. 비교 분석 전에 업로드해 같은 인덱스로 빌드하면 됩니다.",
          priorCompareBlocked:
            "선행 문헌이 인덱스에 없습니다. 선행 파일을 포함해 인덱스를 다시 빌드한 뒤 실행하세요.",
          analyzingInvention: "본 발명 분석 스트리밍 중…",
          inventionSummary: "본 발명 요약",
          inventionSummaryToggleTitle: "클릭하여 본 발명 요약을 펼치거나 닫습니다.",
          building: "인덱스 빌드 중…",
          analyzing: "선행 비교 스트리밍 중…",
          session: "세션",
          apiHint:
            "백엔드: 별도 터미널에서 backend 폴더로 이동 후 uvicorn 실행 · 미설정 시 API는 http://127.0.0.1:8000",
          backendChecking: "백엔드 연결 확인 중…",
          backendUnreachable:
            "백엔드에 연결되지 않았습니다. FastAPI가 떠 있어야 Build Search Index가 동작합니다. 다른 터미널에서 backend로 이동한 뒤 run_backend.ps1 또는 uvicorn을 실행하고, 브라우저에서 아래 주소의 /docs 가 열리는지 확인하세요.",
          backendRecheck: "연결 다시 확인",
          exportBusy: "DOCX 생성 중…",
          buildResultSection: "빌드 결과",
          buildResultEmpty:
            "아직 인덱스를 빌드하지 않았습니다. 빌드가 끝나면 세션·청크 요약이 여기에 표시됩니다.",
          buildSuccessLabel: "빌드 완료",
          analysisReadinessTitle: "분석 준비도",
          buildWarningBadge: "경고",
          technicalSummary: "기술 요약",
          strategicPriorTitle: "선행 문헌·비교 기능 안내",
          strategicPriorBody:
            "선행 문헌 없이 본 발명만 인덱싱된 상태입니다. 이 상태에서는 본 발명 단독 분석은 가능하나, 선행 특허 비교 표·심층 비교(진보성 중심)는 제한됩니다. 선행 PDF를 추가한 뒤 다시 Build Search Index를 실행하세요.",
          swaggerLink: "Swagger UI에서 API 테스트",
          indexPreview: "본 발명 인덱싱 (파싱·청크)",
          indexPreviewHint:
            "제1항 추출 요약과 Phase2 한정 단위 청크 미리보기. GET /api/v1/session/{id}/invention-index-preview 로도 조회 가능.",
          removeFile: "삭제",
          clearFiles: "전체 비우기",
          stagedFiles: "선택된 파일",
          sessionIdFull: "세션 ID (전체)",
          copySessionId: "복사",
          sessionIdCopied: "클립보드에 복사했습니다.",
          sessionIdCopyFail: "복사에 실패했습니다. 아래 ID를 직접 선택해 복사하세요.",
          reasoningPanel: "Reasoning — 신규성·진보성 (KIPO/MPEP 참고 톤)",
          strategyPanel: "전략·청구 수정 제안",
          strategyAiColumn: "🤖 전략 AI · 심층 분석",
          streamPhase: "스트리밍 단계",
        }
      : {
          title: "Patent Analysis Agent",
          subtitle:
            "Compare invention vs prior art — Phase 3: API wiring, comparison table, streamed analysis, DOCX export.",
          lang: "Response language",
          inv: "Invention files",
          prior: "Prior art (KR/US mix)",
          actionsHeading: "🔬 Workflow",
          build: "Build Search Index",
          buildDesc:
            "Extract text, chunk, embed into Chroma for hybrid retrieval.",
          run: "Run analysis",
          runDesc:
            "Hybrid search then streamed Markdown report (SSE). Comparison table arrives first.",
          comparison: "Comparison Table",
          analysis: "Deep analysis (streamed)",
          exportDocx: "Export DOCX",
          exportDocxDesc:
            "Downloads the prior-art comparison table and streamed deep analysis / strategy notes as a Word (.docx) file. The invention summary is not included in this export.",
          hint: "PDF, TXT, DOCX",
          needFiles: "Select at least one invention file.",
          workspaceTitle: "📊 Analysis workspace",
          outputsInvention: "📋 Invention analysis results",
          outputsPrior: "🔎 Prior-art comparison results",
          runInvention: "Run invention analysis",
          runInventionDesc:
            "Streams the invention summary. Multiple independent claims get per-claim deep tables, strategy notes, and paragraph links under “Main structure & operation”.",
          runPrior: "Run prior-art comparison",
          priorOptionalHint:
            "Prior-art uploads are optional. Include them in the same index build before comparison.",
          priorCompareBlocked:
            "No prior art in this session. Rebuild the index including prior-art files.",
          analyzingInvention: "Streaming invention analysis…",
          inventionSummary: "Invention summary",
          inventionSummaryToggleTitle: "Click to expand or collapse the invention summary.",
          building: "Building index…",
          analyzing: "Streaming prior-art comparison…",
          session: "Session",
          apiHint:
            "Backend: open a second terminal, cd to backend, run uvicorn · Default API http://127.0.0.1:8000",
          backendChecking: "Checking API connection…",
          backendUnreachable:
            "Cannot reach the API. Start FastAPI (run_backend.ps1 or uvicorn from backend), then confirm /docs loads at the URL below. Without it, Build Search Index will fail.",
          backendRecheck: "Check again",
          exportBusy: "Generating DOCX…",
          buildResultSection: "Index build result",
          buildResultEmpty:
            "No index built yet. After a successful build, session and chunk summary appear here.",
          buildSuccessLabel: "Build complete",
          analysisReadinessTitle: "Analysis readiness",
          buildWarningBadge: "Warning",
          technicalSummary: "Technical summary",
          strategicPriorTitle: "Prior art & comparison scope",
          strategicPriorBody:
            "Only the invention is indexed—no prior-art files were included. Invention-only analysis is available, but the prior-art comparison table and deep comparative review are limited. Add prior PDFs (or other documents) and run Build Search Index again.",
          quickStartInvention: "Run invention analysis now",
          quickAddPrior: "Go to prior-art upload",
          quickGoWorkflow: "Go to workflow",
          swaggerLink: "Test API (Swagger UI)",
          indexPreview: "Invention index (parse & chunks)",
          indexPreviewHint:
            "Claim 1 extract summary and Phase2 limitation chunks. Also: GET /api/v1/session/{id}/invention-index-preview",
          removeFile: "Remove",
          clearFiles: "Clear all",
          stagedFiles: "Selected files",
          sessionIdFull: "Session ID (full)",
          copySessionId: "Copy",
          sessionIdCopied: "Copied to clipboard.",
          sessionIdCopyFail: "Copy failed — select the ID below manually.",
          reasoningPanel: "Reasoning — novelty / inventive step (KIPO/MPEP-style framing)",
          strategyPanel: "Strategy & amendment sketch",
          strategyAiColumn: "🤖 Strategy AI · deep analysis",
          streamPhase: "Streaming stage",
        };

  const combinedAnalysisMarkdown = useMemo(() => {
    if (!strategyMd.trim()) return reasoningMd;
    const sep =
      lang === "ko"
        ? "\n\n---\n\n## 전략·청구 수정 제안\n\n"
        : "\n\n---\n\n## Strategy & amendment sketch\n\n";
    return reasoningMd + sep + strategyMd;
  }, [reasoningMd, strategyMd, lang]);

  const buildReadinessSummary = useMemo(() => {
    if (!lastBuildSuccess || !inventionPreview) return null;
    const invN = inventionStaged.length;
    const priorN = priorStaged.length;
    const unitN = inventionPreview.invention_claim_chunks.length;
    const bodyN = inventionPreview.invention_body_chunk_count;
    const cc = lastBuildSuccess.chunkCount;
    if (lang === "ko") {
      return `본 발명 ${invN}건(청구 구조화 단위 ${unitN}개·본문·기타 세그먼트 ${bodyN}개), 선행 문헌 ${priorN}건이 반영되었습니다. 검색 인덱스 총 ${cc}개 청크로 분석 준비가 되었습니다.`;
    }
    return `Invention: ${invN} file(s) — ${unitN} claim-limitation unit(s), ${bodyN} body/other segment(s). Prior art: ${priorN} file(s). Search index: ${cc} chunk(s) — ready to analyze.`;
  }, [lastBuildSuccess, inventionPreview, lang, inventionStaged.length, priorStaged.length]);

  const onBuildIndex = useCallback(async () => {
    setStatus("");
    setBuildStatus("");
    setLastBuildSuccess(null);
    setComparisonMd("");
    setReasoningMd("");
    setStrategyMd("");
    setInventionSummaryMd("");
    setStreamPhaseLabel("");
    setSessionId(null);
    setHasPriorArt(false);
    setInventionPreview(null);
    if (!inventionStaged.length) {
      setBuildStatus(labels.needFiles);
      return;
    }
    const base = apiBaseUrl();
    setBusyBuild(true);
    try {
      const fd = new FormData();
      inventionStaged.forEach(({ file: f }) => fd.append("invention", f));
      priorStaged.forEach(({ file: f }) => fd.append("prior", f));
      fd.append("use_llm_refine", "false");
      const res = await fetch(`${base}/api/v1/index/build`, {
        method: "POST",
        body: fd,
      });
      const raw = await res.text();
      let parsed: unknown;
      try {
        parsed = JSON.parse(raw) as { detail?: unknown; session_id?: string };
      } catch {
        setInventionPreview(null);
        setLastBuildSuccess(null);
        setBuildStatus(raw.trim() || res.statusText);
        return;
      }
      if (!res.ok) {
        const j = parsed as {
          detail?: {
            message?: string;
            invention_index_preview?: InventionIndexPreview;
            warnings?: string[];
          };
        };
        const d = j.detail;
        if (
          res.status === 422 &&
          d &&
          typeof d === "object" &&
          d.invention_index_preview
        ) {
          setInventionPreview(d.invention_index_preview);
          setLastBuildSuccess(null);
          setBuildStatus(
            lang === "ko"
              ? `인덱스 실패: ${d.message ?? ""} (아래 ${labels.indexPreview} 참고)`
              : `Index failed: ${d.message ?? ""} (see ${labels.indexPreview} below)`,
          );
          return;
        }
        setInventionPreview(null);
        setLastBuildSuccess(null);
        setBuildStatus(
          typeof j.detail === "string"
            ? j.detail
            : JSON.stringify(j.detail ?? res.statusText),
        );
        return;
      }
      const data = parsed as {
        session_id: string;
        warnings?: string[];
        chunk_count?: number;
        invention_index_preview?: InventionIndexPreview;
        has_prior_art?: boolean;
      };
      setSessionId(data.session_id);
      setHasPriorArt(data.has_prior_art === true);
      setInventionPreview(data.invention_index_preview ?? null);
      setBuildStatus("");
      setLastBuildSuccess({
        chunkCount: data.chunk_count ?? 0,
        warnings: data.warnings ?? [],
        hasPriorArt: data.has_prior_art === true,
      });
    } catch (e) {
      setLastBuildSuccess(null);
      setBuildStatus(formatApiNetworkError(e, base, lang));
    } finally {
      setBusyBuild(false);
    }
  }, [inventionStaged, priorStaged, lang, labels.indexPreview, labels.needFiles]);

  const copySessionIdToClipboard = useCallback(async () => {
    if (!sessionId) return;
    try {
      await navigator.clipboard.writeText(sessionId);
      setSessionCopyHint(labels.sessionIdCopied);
      window.setTimeout(() => setSessionCopyHint(""), 2200);
    } catch {
      setSessionCopyHint(labels.sessionIdCopyFail);
      window.setTimeout(() => setSessionCopyHint(""), 4000);
    }
  }, [sessionId, labels.sessionIdCopied, labels.sessionIdCopyFail]);

  const onInventionAnalyze = useCallback(async () => {
    setInventionSummaryMd("");
    setStreamPhaseLabel("");
    setStatus("");
    if (!sessionId) {
      setStatus(lang === "ko" ? "먼저 인덱스를 빌드하세요." : "Build the index first.");
      return;
    }
    const base = apiBaseUrl();
    setBusyInventionAnalyze(true);
    try {
      const res = await fetch(`${base}/api/v1/analyze/invention/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, language: lang }),
      });
      if (!res.ok || !res.body) {
        setStatus(await readErrorDetail(res));
        setBusyInventionAnalyze(false);
        return;
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const { remainder, events } = consumeSseBuffer(buf);
        buf = remainder;
        for (const ev of events) {
          if (ev.event === "phase") {
            try {
              const payload = JSON.parse(ev.data) as { label?: string; id?: string };
              setStreamPhaseLabel(payload.label || payload.id || "");
            } catch {
              /* ignore */
            }
          } else if (ev.event === "delta") {
            try {
              const payload = JSON.parse(ev.data) as { t?: string; phase?: string };
              if (!payload.t) continue;
              setInventionSummaryMd((prev) => prev + payload.t);
            } catch {
              /* ignore */
            }
          } else if (ev.event === "error") {
            try {
              const err = JSON.parse(ev.data) as { detail?: string; error?: string };
              setStatus(err.detail ?? err.error ?? ev.data);
            } catch {
              setStatus(ev.data);
            }
          }
        }
      }
      setStreamPhaseLabel("");
    } catch (e) {
      setStatus(formatApiNetworkError(e, base, lang));
    } finally {
      setBusyInventionAnalyze(false);
    }
  }, [sessionId, lang]);

  const onAnalyze = useCallback(async () => {
    setComparisonMd("");
    setReasoningMd("");
    setStrategyMd("");
    setStreamPhaseLabel("");
    setStatus("");
    if (!sessionId) {
      setStatus(lang === "ko" ? "먼저 인덱스를 빌드하세요." : "Build the index first.");
      return;
    }
    if (!hasPriorArt) {
      setStatus(labels.priorCompareBlocked);
      return;
    }
    const base = apiBaseUrl();
    setBusyAnalyze(true);
    try {
      const res = await fetch(`${base}/api/v1/analyze/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, language: lang }),
      });
      if (!res.ok || !res.body) {
        setStatus(await readErrorDetail(res));
        setBusyAnalyze(false);
        return;
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const { remainder, events } = consumeSseBuffer(buf);
        buf = remainder;
        for (const ev of events) {
          if (ev.event === "meta") {
            try {
              const payload = JSON.parse(ev.data) as {
                comparison_table_markdown?: string;
              };
              setComparisonMd(payload.comparison_table_markdown ?? "");
            } catch {
              /* ignore */
            }
          } else if (ev.event === "phase") {
            try {
              const payload = JSON.parse(ev.data) as { label?: string; id?: string };
              setStreamPhaseLabel(payload.label || payload.id || "");
            } catch {
              /* ignore */
            }
          } else if (ev.event === "delta") {
            try {
              const payload = JSON.parse(ev.data) as { t?: string; phase?: string };
              if (!payload.t) continue;
              if (payload.phase === "strategy") {
                setStrategyMd((prev) => prev + payload.t);
              } else {
                setReasoningMd((prev) => prev + payload.t);
              }
            } catch {
              /* ignore */
            }
          } else if (ev.event === "error") {
            try {
              const err = JSON.parse(ev.data) as { detail?: string; error?: string };
              setStatus(err.detail ?? err.error ?? ev.data);
            } catch {
              setStatus(ev.data);
            }
          }
        }
      }
      setStreamPhaseLabel("");
    } catch (e) {
      setStatus(formatApiNetworkError(e, base, lang));
    } finally {
      setBusyAnalyze(false);
    }
  }, [sessionId, lang, hasPriorArt, labels.priorCompareBlocked]);

  const onExportDocx = useCallback(async () => {
    if (!comparisonMd.trim() && !combinedAnalysisMarkdown.trim()) return;
    const base = apiBaseUrl();
    setStatus(labels.exportBusy);
    try {
      const res = await fetch(`${base}/api/v1/export/docx/combined`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          analysis_markdown: combinedAnalysisMarkdown,
          comparison_table_markdown: comparisonMd,
          language: lang,
        }),
      });
      if (!res.ok) {
        setStatus(await readErrorDetail(res));
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download =
        lang === "ko" ? "patent-analysis-report.docx" : "patent-analysis-report.docx";
      a.click();
      URL.revokeObjectURL(url);
      setStatus(lang === "ko" ? "DOCX 저장됨." : "DOCX saved.");
    } catch (e) {
      setStatus(formatApiNetworkError(e, base, lang));
    }
  }, [combinedAnalysisMarkdown, comparisonMd, lang, labels.exportBusy]);

  const mdWrap =
    "rounded-md border border-[#E2E8F0] bg-white p-3 text-sm leading-relaxed text-[#334155] shadow-sm dark:border-slate-700 dark:bg-[#0F172A] dark:text-[#E2E8F0] [&_table]:w-full [&_table]:border-collapse [&_th]:border [&_td]:border [&_th]:border-[#E2E8F0] [&_td]:border-[#E2E8F0] [&_th]:bg-[#F1F5F9] [&_th]:px-2 [&_td]:px-2 [&_th]:py-1 [&_td]:py-1 dark:[&_th]:border-slate-700 dark:[&_td]:border-slate-700 dark:[&_th]:bg-slate-800";

  const langPill = (active: boolean) =>
    `rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
      active
        ? "bg-slate-900 text-white shadow-sm dark:bg-zinc-100 dark:text-zinc-900"
        : "text-slate-600 hover:bg-slate-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
    }`;

  return (
    <div className="min-h-screen w-full bg-[#F8FAFC] dark:bg-[#0F172A]">
      <div className="mx-auto max-w-[1400px] px-4 py-10 pb-16">
        <header className="mb-10 flex flex-col gap-5 border-b border-slate-200/90 pb-8 dark:border-zinc-700/90">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="min-w-0">
              <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-zinc-50">{labels.title}</h1>
              <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600 dark:text-zinc-400">{labels.subtitle}</p>
            </div>
            <div className="flex shrink-0 flex-col gap-2 sm:flex-row sm:items-center">
              <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-zinc-500">
                {labels.lang}
              </span>
              <div className="inline-flex rounded-full border border-slate-200/90 bg-white p-1 shadow-sm dark:border-zinc-600 dark:bg-zinc-900/80">
                <button type="button" onClick={() => setLang("ko")} className={langPill(lang === "ko")}>
                  한국어
                </button>
                <button type="button" onClick={() => setLang("en")} className={langPill(lang === "en")}>
                  English
                </button>
              </div>
              <Link
                href="/api-test"
                className="text-sm font-medium text-[#3B82F6] underline decoration-blue-400/50 underline-offset-2 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
              >
                {labels.swaggerLink} →
              </Link>
            </div>
          </div>
          <p className="text-xs leading-relaxed text-slate-500 dark:text-zinc-500">{labels.apiHint}</p>
          {apiReachable === null ? (
            <p className="text-xs text-slate-400 dark:text-zinc-500">{labels.backendChecking}</p>
          ) : null}
          {apiReachable === false ? (
            <div className="rounded-lg border border-amber-400/80 bg-amber-50 px-3 py-2.5 text-sm text-amber-950 shadow-sm dark:border-amber-700 dark:bg-amber-950/35 dark:text-amber-50">
              <p className="leading-snug">{labels.backendUnreachable}</p>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <code className="rounded bg-white/80 px-2 py-0.5 text-xs dark:bg-zinc-900">{apiBase}</code>
                <button
                  type="button"
                  onClick={() => recheckBackendHealth()}
                  className="rounded-md bg-amber-800 px-3 py-1 text-xs font-medium text-white hover:bg-amber-900 dark:bg-amber-600 dark:hover:bg-amber-500"
                >
                  {labels.backendRecheck}
                </button>
              </div>
            </div>
          ) : null}
        </header>

        <div className="mb-6 grid gap-5 lg:grid-cols-2">
          <div className="overflow-hidden rounded-2xl border border-[#E2E8F0] bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900/40">
            <div className="border-b border-[#E2E8F0] bg-[#F8FAFC] px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70">
              <label className="text-sm font-semibold text-[#334155] dark:text-slate-100">{labels.inv}</label>
            </div>
            <div className="space-y-3 bg-white p-4 dark:bg-[#0F172A]/80">
              <input
                id="patent-upload-invention"
                ref={inventionInputRef}
                type="file"
                multiple
                accept=".pdf,.txt,.docx,.PDF,.TXT,.DOCX"
                onChange={(e) => {
                  const el = e.currentTarget;
                  try {
                    setInventionStaged((p) => appendStaged(p, el.files));
                  } catch (err) {
                    console.error(err);
                  }
                  resetFileInputSoon(el);
                }}
                className="block w-full text-sm text-[#334155] file:mr-4 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-sm file:font-medium file:text-[#334155] hover:file:bg-slate-200 dark:text-slate-300 dark:file:bg-slate-800 dark:file:text-slate-100 dark:hover:file:bg-slate-700"
              />
              <p className="text-xs text-slate-600 dark:text-slate-400">{labels.hint}</p>
              {inventionStaged.length > 0 ? (
                <div className="space-y-1.5 rounded-xl border border-[#E2E8F0] bg-[#F8FAFC] p-2 dark:border-slate-700 dark:bg-slate-900/50">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-medium text-[#334155] dark:text-slate-200">
                      {labels.stagedFiles} ({inventionStaged.length})
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        setInventionStaged([]);
                        if (inventionInputRef.current) inventionInputRef.current.value = "";
                      }}
                      className="text-xs font-medium text-red-700 underline-offset-2 hover:underline dark:text-red-400"
                    >
                      {labels.clearFiles}
                    </button>
                  </div>
                  <ul className="max-h-40 space-y-1 overflow-y-auto text-xs">
                    {inventionStaged.map((row) => (
                      <li
                        key={row.id}
                        className="flex items-center justify-between gap-2 rounded-lg border border-[#E2E8F0] bg-white px-2 py-1.5 dark:border-slate-700 dark:bg-slate-950"
                      >
                        <span className="min-w-0 truncate text-[#334155] dark:text-slate-200" title={row.file.name}>
                          {row.file.name}
                        </span>
                        <button
                          type="button"
                          onClick={() => setInventionStaged((p) => p.filter((x) => x.id !== row.id))}
                          className="shrink-0 rounded border border-zinc-200 bg-zinc-50 px-2 py-0.5 text-[11px] font-medium text-zinc-700 hover:bg-red-50 hover:text-red-800 dark:border-zinc-600 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-red-950/40 dark:hover:text-red-300"
                        >
                          {labels.removeFile}
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-[#E2E8F0] bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900/40">
            <div className="border-b border-[#E2E8F0] bg-[#F8FAFC] px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70">
              <label className="text-sm font-semibold text-[#334155] dark:text-slate-100">{labels.prior}</label>
            </div>
            <div className="space-y-3 bg-white p-4 dark:bg-[#0F172A]/80">
              <input
                id="patent-upload-prior"
                ref={priorInputRef}
                type="file"
                multiple
                accept=".pdf,.txt,.docx,.PDF,.TXT,.DOCX,application/pdf,text/plain,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={(e) => {
                  const el = e.currentTarget;
                  try {
                    setPriorStaged((p) => appendStaged(p, el.files));
                  } catch (err) {
                    console.error(err);
                  }
                  resetFileInputSoon(el);
                }}
                className="block w-full text-sm text-[#334155] file:mr-4 file:rounded-md file:border-0 file:bg-amber-50 file:px-3 file:py-2 file:text-sm file:font-medium file:text-amber-950 hover:file:bg-amber-100 dark:text-slate-300 dark:file:bg-amber-950/40 dark:file:text-amber-100 dark:hover:file:bg-amber-950/60"
              />
              <p className="text-xs leading-relaxed text-slate-600 dark:text-slate-400">{labels.priorOptionalHint}</p>
              {priorStaged.length > 0 ? (
                <div className="space-y-1.5 rounded-xl border border-[#E2E8F0] bg-[#FFFBEB]/80 p-2 dark:border-slate-700 dark:bg-amber-950/20">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-medium text-[#92400E] dark:text-amber-100">
                      {labels.stagedFiles} ({priorStaged.length})
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        setPriorStaged([]);
                        if (priorInputRef.current) priorInputRef.current.value = "";
                      }}
                      className="text-xs font-medium text-red-700 underline-offset-2 hover:underline dark:text-red-400"
                    >
                      {labels.clearFiles}
                    </button>
                  </div>
                  <ul className="max-h-40 space-y-1 overflow-y-auto text-xs">
                    {priorStaged.map((row) => (
                      <li
                        key={row.id}
                        className="flex items-center justify-between gap-2 rounded-lg border border-[#E2E8F0] bg-white px-2 py-1.5 dark:border-slate-700 dark:bg-slate-950"
                      >
                        <span className="min-w-0 truncate text-[#334155] dark:text-slate-200" title={row.file.name}>
                          {row.file.name}
                        </span>
                        <button
                          type="button"
                          onClick={() => setPriorStaged((p) => p.filter((x) => x.id !== row.id))}
                          className="shrink-0 rounded border border-zinc-200 bg-zinc-50 px-2 py-0.5 text-[11px] font-medium text-zinc-700 hover:bg-red-50 hover:text-red-800 dark:border-zinc-600 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-red-950/40 dark:hover:text-red-300"
                        >
                          {labels.removeFile}
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          </div>
        </div>

        <section className="mb-10 rounded-2xl border border-[#E2E8F0] bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900/50">
          <p className="mb-3 text-[11px] font-bold uppercase tracking-[0.12em] text-slate-500 dark:text-zinc-500">
            {labels.build}
          </p>
          <p className="mb-4 text-sm font-medium text-[#334155] dark:text-slate-200">
            {lang === "ko"
              ? `선택된 파일: 본 발명 ${inventionStaged.length}개, 선행 ${priorStaged.length}개`
              : `Selected: invention ${inventionStaged.length}, prior ${priorStaged.length}`}
          </p>
          <button
            type="button"
            disabled={busyBuild}
            aria-busy={busyBuild}
            onClick={() => void onBuildIndex()}
            className="w-full rounded-xl border border-slate-700/35 bg-slate-600 px-5 py-4 text-base font-bold tracking-tight text-white shadow-[0_6px_20px_-4px_rgba(71,85,105,0.5)] ring-2 ring-slate-400/45 ring-offset-2 ring-offset-white transition hover:scale-[1.01] hover:bg-slate-700 hover:shadow-[0_10px_28px_-6px_rgba(71,85,105,0.45)] hover:ring-slate-300/55 active:scale-[0.99] disabled:pointer-events-none disabled:opacity-45 dark:bg-slate-600 dark:hover:bg-slate-500 dark:ring-slate-500/35 dark:ring-offset-[#0F172A]"
          >
            <span className="inline-flex w-full items-center justify-center gap-2.5">
              {busyBuild ? <ActionButtonSpinner /> : <CtaIconBuild />}
              <span>{busyBuild ? labels.building : labels.build}</span>
            </span>
          </button>
          <p className="mt-4 text-xs leading-relaxed text-slate-600 dark:text-zinc-400">{labels.buildDesc}</p>
          <div className="mt-5 border-t border-[#E2E8F0] pt-4 dark:border-slate-600">
            <p className="mb-2 text-xs font-semibold text-slate-600 dark:text-slate-400">{labels.buildResultSection}</p>
            {busyBuild ? (
              <div className="flex items-center gap-2 text-sm font-medium text-slate-600 dark:text-slate-300">
                <span
                  className="inline-block size-4 shrink-0 animate-spin rounded-full border-2 border-slate-400 border-t-transparent dark:border-slate-500 dark:border-t-transparent"
                  aria-hidden
                />
                {labels.building}
              </div>
            ) : lastBuildSuccess && inventionPreview && buildReadinessSummary ? (
              <div className="space-y-4">
                <div className="rounded-xl border border-emerald-200/90 bg-emerald-50/90 px-4 py-3 shadow-sm dark:border-emerald-800/50 dark:bg-emerald-950/35">
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <span className="rounded-md bg-emerald-600 px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide text-white dark:bg-emerald-500">
                      {labels.buildSuccessLabel}
                    </span>
                    {sessionId ? (
                      <span className="text-xs font-mono text-emerald-900/90 dark:text-emerald-100/90">
                        {lang === "ko" ? "세션" : "Session"}: {sessionId.slice(0, 12)}…
                      </span>
                    ) : null}
                  </div>
                  <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-emerald-900/80 dark:text-emerald-200/90">
                    {labels.analysisReadinessTitle}
                  </p>
                  <p className="text-sm leading-relaxed text-emerald-950 dark:text-emerald-50">{buildReadinessSummary}</p>
                  <p className="mt-3 border-t border-emerald-200/70 pt-2 text-[11px] text-emerald-900/75 dark:border-emerald-800/50 dark:text-emerald-200/80">
                    <span className="font-semibold">{labels.technicalSummary}:</span>{" "}
                    {lang === "ko" ? "총 청크" : "Total chunks"} {lastBuildSuccess.chunkCount}
                    {sessionId ? ` · ID ${sessionId.slice(0, 8)}…` : ""}
                  </p>
                </div>

                {lastBuildSuccess.warnings.length > 0 ? (
                  <div className="rounded-xl border border-amber-300/90 bg-amber-50 px-3 py-2.5 dark:border-amber-700/60 dark:bg-amber-950/40">
                    <div className="mb-1.5 flex flex-wrap items-center gap-2">
                      <span className="rounded-full bg-amber-500 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white shadow-sm">
                        {labels.buildWarningBadge}
                      </span>
                      <span className="text-xs text-amber-950 dark:text-amber-100">
                        {lang === "ko"
                          ? `파싱·인덱싱 중 참고 사항 ${lastBuildSuccess.warnings.length}건`
                          : `${lastBuildSuccess.warnings.length} parser/index note(s)`}
                      </span>
                    </div>
                    <ul className="list-inside list-disc space-y-1 text-xs leading-snug text-amber-950 dark:text-amber-100">
                      {lastBuildSuccess.warnings.map((w, i) => (
                        <li key={`${i}-${w.slice(0, 24)}`}>{w}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                {!lastBuildSuccess.hasPriorArt ? (
                  <div className="rounded-xl border border-amber-400/70 bg-[#FFFBEB] px-3 py-3 dark:border-amber-700/50 dark:bg-amber-950/30">
                    <p className="mb-1.5 text-xs font-bold text-amber-950 dark:text-amber-100">
                      {labels.strategicPriorTitle}
                    </p>
                    <p className="text-sm leading-relaxed text-amber-950/95 dark:text-amber-50/95">
                      {labels.strategicPriorBody}
                    </p>
                  </div>
                ) : null}
              </div>
            ) : buildStatus ? (
              <p className="whitespace-pre-wrap break-words text-sm leading-relaxed text-slate-800 dark:text-slate-100">
                {buildStatus}
              </p>
            ) : (
              <p className="text-sm leading-relaxed text-slate-500 dark:text-slate-500">{labels.buildResultEmpty}</p>
            )}
          </div>
        </section>

        <section className="mb-10 space-y-5">
          <h2 className="text-xl font-semibold tracking-tight text-slate-900 dark:text-zinc-50">{labels.actionsHeading}</h2>
          <div className="grid gap-5 lg:grid-cols-2">
            <div className="flex flex-col gap-4 rounded-2xl border border-[#E2E8F0] bg-[#F8FAFC] p-5 shadow-sm dark:border-slate-700 dark:bg-slate-900/40">
              <button
                type="button"
                disabled={busyInventionAnalyze || !sessionId || busyAnalyze}
                aria-busy={busyInventionAnalyze}
                onClick={() => void onInventionAnalyze()}
                className="w-full rounded-xl border border-blue-700/30 bg-blue-600 px-5 py-4 text-base font-bold tracking-tight text-white shadow-[0_6px_20px_-4px_rgba(37,99,235,0.5)] ring-2 ring-blue-400/45 ring-offset-2 ring-offset-[#F8FAFC] transition hover:scale-[1.01] hover:bg-blue-700 hover:shadow-[0_10px_28px_-6px_rgba(37,99,235,0.45)] hover:ring-blue-300/55 active:scale-[0.99] disabled:pointer-events-none disabled:opacity-45 dark:bg-blue-600 dark:hover:bg-blue-500 dark:ring-blue-500/35 dark:ring-offset-slate-900"
              >
                <span className="inline-flex w-full items-center justify-center gap-2.5">
                  {busyInventionAnalyze ? (
                    <ActionButtonSpinner />
                  ) : (
                    <CtaIconInvention />
                  )}
                  <span>{busyInventionAnalyze ? labels.analyzingInvention : labels.runInvention}</span>
                </span>
              </button>
              <p className="text-xs leading-relaxed text-[#334155] dark:text-slate-300">{labels.runInventionDesc}</p>
            </div>
            <div className="flex flex-col gap-4 rounded-2xl border border-[#E2E8F0] bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-[#0F172A]/80">
              <button
                type="button"
                disabled={busyAnalyze || !sessionId || !hasPriorArt || busyInventionAnalyze}
                aria-busy={busyAnalyze}
                title={!hasPriorArt ? labels.priorCompareBlocked : undefined}
                onClick={() => void onAnalyze()}
                className="w-full rounded-xl border border-orange-700/30 bg-orange-600 px-5 py-4 text-base font-bold tracking-tight text-white shadow-[0_6px_20px_-4px_rgba(234,88,12,0.5)] ring-2 ring-orange-400/45 ring-offset-2 ring-offset-white transition hover:scale-[1.01] hover:bg-orange-700 hover:shadow-[0_10px_28px_-6px_rgba(234,88,12,0.45)] hover:ring-orange-300/55 active:scale-[0.99] disabled:pointer-events-none disabled:opacity-45 dark:bg-orange-600 dark:hover:bg-orange-500 dark:ring-orange-500/35 dark:ring-offset-[#0F172A]"
              >
                <span className="inline-flex w-full items-center justify-center gap-2.5">
                  {busyAnalyze ? <ActionButtonSpinner /> : <CtaIconCompare />}
                  <span>{busyAnalyze ? labels.analyzing : labels.runPrior}</span>
                </span>
              </button>
              <p className="text-xs leading-relaxed text-[#334155] dark:text-slate-300">{labels.runDesc}</p>
            </div>
          </div>
        </section>

        {status ? (
          <p className="mb-6 rounded-xl border border-amber-200/80 bg-amber-50/90 px-4 py-3 text-sm text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/35 dark:text-amber-100">
            {status}
          </p>
        ) : null}

        {sessionId ? (
          <div className="mb-6 rounded-xl border border-slate-200/90 bg-slate-50/80 px-4 py-3 dark:border-zinc-700 dark:bg-zinc-900/50">
            <div className="mb-1.5 flex flex-wrap items-center justify-between gap-2">
              <span className="text-xs font-medium text-slate-600 dark:text-zinc-400">{labels.sessionIdFull}</span>
              <button
                type="button"
                onClick={() => void copySessionIdToClipboard()}
                className="rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-xs font-medium text-slate-800 hover:bg-slate-100 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-100 dark:hover:bg-zinc-700"
              >
                {labels.copySessionId}
              </button>
            </div>
            <code className="block break-all font-mono text-xs leading-relaxed text-slate-900 dark:text-zinc-100">
              {sessionId}
            </code>
            {sessionCopyHint ? (
              <p
                className={
                  sessionCopyHint === labels.sessionIdCopyFail
                    ? "mt-1.5 text-xs text-red-700 dark:text-red-400"
                    : "mt-1.5 text-xs text-emerald-700 dark:text-emerald-400"
                }
              >
                {sessionCopyHint}
              </p>
            ) : null}
          </div>
        ) : null}

        {inventionPreview ? (
          <details className="mb-8 rounded-xl border border-slate-200/90 bg-white/70 dark:border-zinc-700 dark:bg-zinc-900/40">
            <summary className="cursor-pointer select-none px-4 py-3 text-sm font-medium text-slate-800 dark:text-zinc-200">
              {labels.indexPreview}
            </summary>
            <div className="space-y-2 border-t border-slate-200 px-4 py-3 dark:border-zinc-700">
              <p className="text-xs text-slate-500 dark:text-zinc-400">{labels.indexPreviewHint}</p>
              <pre className="max-h-[min(70vh,520px)] overflow-auto rounded-lg border border-slate-200 bg-white p-3 text-xs leading-snug text-slate-800 dark:border-zinc-600 dark:bg-zinc-950 dark:text-zinc-200">
                {JSON.stringify(inventionPreview, null, 2)}
              </pre>
            </div>
          </details>
        ) : null}

        <section className="mb-12 space-y-5">
          <h3 className="text-xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">{labels.workspaceTitle}</h3>
          <div className="flex flex-col gap-8">
            {/* 1. 본 발명 분석 결과 */}
            <div className="flex flex-col gap-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-base font-semibold tracking-tight text-[#334155] sm:text-lg dark:text-slate-200">
                  {labels.outputsInvention}
                </span>
                {streamPhaseLabel && busyInventionAnalyze ? (
                  <span className="max-w-[min(100%,220px)] truncate rounded-full bg-blue-100 px-2.5 py-0.5 text-[10px] font-medium text-blue-900 dark:bg-blue-950/55 dark:text-blue-100">
                    {labels.streamPhase}: {streamPhaseLabel}
                  </span>
                ) : null}
              </div>
              <div className="overflow-hidden rounded-xl border border-[#E2E8F0] bg-[#F8FAFC] shadow-sm dark:border-slate-700 dark:bg-slate-900/60">
                <details
                  className="group/invs"
                  open={inventionSummaryOpen}
                  onToggle={(e) => setInventionSummaryOpen(e.currentTarget.open)}
                >
                  <summary
                    title={labels.inventionSummaryToggleTitle}
                    className="relative flex cursor-pointer list-none items-center justify-center gap-3 border-b border-[#E2E8F0] bg-white px-3 py-3 marker:content-none [&::-webkit-details-marker]:hidden dark:border-slate-700 dark:bg-slate-900/80"
                  >
                    <span className="text-center text-lg font-bold tracking-tight text-[#334155] dark:text-slate-100 sm:text-xl">
                      {labels.inventionSummary}
                    </span>
                    <span
                      className="absolute right-2 flex size-8 shrink-0 items-center justify-center rounded-lg border border-[#E2E8F0] bg-[#F8FAFC] text-[#3B82F6] shadow-sm dark:border-slate-600 dark:bg-slate-800 dark:text-blue-400"
                      aria-hidden
                    >
                      <svg
                        viewBox="0 0 20 20"
                        fill="currentColor"
                        className="size-4 transition-transform duration-200 -rotate-90 group-open/invs:rotate-0"
                      >
                        <path
                          fillRule="evenodd"
                          d="M5.22 8.22a.75.75 0 011.06 0L10 11.94l3.72-3.72a.75.75 0 111.06 1.06l-4.25 4.25a.75.75 0 01-1.06 0L5.22 9.28a.75.75 0 010-1.06z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </span>
                  </summary>
                  <div className="max-h-[min(70vh,560px)] min-h-[200px] overflow-y-auto bg-white p-3 dark:bg-[#0F172A]">
                    <InventionSummaryMarkdown markdown={inventionSummaryMd} />
                  </div>
                </details>
              </div>
            </div>

            {/* 2. 선행 특허 비교 결과 */}
            <div className="flex flex-col gap-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-base font-semibold tracking-tight text-[#334155] sm:text-lg dark:text-slate-200">
                  {labels.outputsPrior}
                </span>
                {streamPhaseLabel && busyAnalyze ? (
                  <span className="max-w-[min(100%,260px)] truncate rounded-full bg-amber-100 px-2.5 py-0.5 text-[10px] font-medium text-amber-950 dark:bg-amber-950/45 dark:text-amber-100">
                    {labels.streamPhase}: {streamPhaseLabel}
                  </span>
                ) : null}
              </div>
              <div className="overflow-hidden rounded-xl border border-[#E2E8F0] bg-white shadow-sm dark:border-slate-700 dark:bg-[#0F172A]/90">
                <div className="border-b border-[#E2E8F0] bg-[#F1F5F9] px-4 py-3.5 text-center dark:border-slate-700 dark:bg-slate-800/90">
                  <p className="text-lg font-bold tracking-tight text-[#334155] dark:text-slate-100 sm:text-xl">
                    {labels.comparison}
                  </p>
                </div>
                <div className="min-h-[180px] p-3">
                  <ComparisonTableMarkdown markdown={comparisonMd} />
                </div>
              </div>
            </div>

            {/* 3. 전략 AI · 심층 분석 */}
            <div className="flex flex-col gap-4">
              <span className="text-base font-semibold tracking-tight text-[#334155] sm:text-lg dark:text-slate-200">
                {labels.strategyAiColumn}
              </span>
              <div className="overflow-hidden rounded-xl border border-[#E2E8F0] bg-white shadow-sm dark:border-slate-700 dark:bg-[#0F172A]/80">
                <div className="border-b border-[#E2E8F0] bg-white px-3 py-3 dark:border-slate-700 dark:bg-slate-900/90">
                  <p className="text-base font-semibold text-[#334155] sm:text-lg dark:text-slate-100">{labels.analysis}</p>
                  <p className="mt-1.5 text-sm font-medium leading-snug text-slate-600 dark:text-slate-400">
                    {labels.reasoningPanel}
                  </p>
                </div>
                <div className={`max-h-[min(52vh,520px)] min-h-[140px] overflow-y-auto p-3 ${mdWrap} border-0 shadow-none`}>
                  <DeepAnalysisMarkdown markdown={reasoningMd} variant="reasoning" />
                </div>
              </div>
              <div className="overflow-hidden rounded-xl border border-[#E2E8F0] bg-white shadow-sm dark:border-slate-700 dark:bg-[#0F172A]/80">
                <div className="border-b border-[#E2E8F0] bg-white px-3 py-3 dark:border-slate-700 dark:bg-slate-900/90">
                  <p className="text-base font-semibold text-[#2563EB] sm:text-lg dark:text-blue-400">
                    {labels.strategyPanel}
                  </p>
                </div>
                <div className={`max-h-[min(44vh,420px)] min-h-[120px] overflow-y-auto bg-white p-3 dark:bg-[#0F172A] ${mdWrap} border-0 shadow-none`}>
                  <DeepAnalysisMarkdown markdown={strategyMd} variant="strategy" />
                </div>
              </div>
            </div>
          </div>

          <div className="mt-2 rounded-xl border border-[#E2E8F0] bg-[#F8FAFC] p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900/45">
            <p className="mb-3 text-sm leading-relaxed text-[#334155] dark:text-slate-300">{labels.exportDocxDesc}</p>
            <button
              type="button"
              disabled={!comparisonMd.trim() && !combinedAnalysisMarkdown.trim()}
              onClick={() => void onExportDocx()}
              className="rounded-xl border border-[#E2E8F0] bg-white px-5 py-2.5 text-sm font-medium text-[#334155] shadow-sm transition hover:bg-slate-50 disabled:opacity-45 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
            >
              {labels.exportDocx}
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
