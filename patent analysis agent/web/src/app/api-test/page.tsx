import Link from "next/link";

function apiDocsUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  const base = raw ? raw.replace(/\/$/, "") : "http://127.0.0.1:8000";
  return `${base}/docs`;
}

export default function ApiTestPage() {
  const docsUrl = apiDocsUrl();

  return (
    <div className="mx-auto flex min-h-full max-w-6xl flex-col gap-4 px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-200 pb-4 dark:border-zinc-800">
        <div>
          <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
            API 테스트 (Swagger UI)
          </h1>
          <p className="mt-1 max-w-3xl text-sm text-zinc-600 dark:text-zinc-400">
            아래는 FastAPI가 제공하는{" "}
            <strong>OpenAPI / Swagger</strong> 화면입니다. 인덱스 빌드·분석·DOCX
            등은 여기서 직접 호출해 시험할 수 있습니다.
          </p>
        </div>
        <Link
          href="/"
          className="text-sm font-medium text-emerald-700 hover:underline dark:text-emerald-400"
        >
          ← 메인으로
        </Link>
      </div>

      <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-100">
        <p className="font-medium">먼저 백엔드를 실행했는지 확인하세요.</p>
        <p className="mt-1 font-mono text-xs opacity-90">
          cd backend · python -m uvicorn api:app --reload --host 127.0.0.1 --port 8000
        </p>
        <p className="mt-2">
          Swagger 주소:{" "}
          <a
            href={docsUrl}
            className="break-all font-medium text-emerald-800 underline dark:text-emerald-300"
            target="_blank"
            rel="noopener noreferrer"
          >
            {docsUrl}
          </a>{" "}
          (503·빈 화면이면 서버 미기동 또는 포트 불일치)
        </p>
        <p className="mt-2">
          <a
            href={docsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex rounded-md bg-emerald-700 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-800"
          >
            새 탭에서 Swagger 열기
          </a>
        </p>
      </div>

      <div className="overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <p className="border-b border-zinc-100 px-3 py-2 text-xs text-zinc-500 dark:border-zinc-800">
          내장 미리보기 (브라우저·보안 설정에 따라 비어 보일 수 있음 → 위 링크 사용)
        </p>
        <iframe
          title="Swagger UI"
          src={docsUrl}
          className="h-[calc(100vh-320px)] min-h-[560px] w-full bg-white dark:bg-zinc-950"
          referrerPolicy="no-referrer-when-downgrade"
        />
      </div>
    </div>
  );
}
