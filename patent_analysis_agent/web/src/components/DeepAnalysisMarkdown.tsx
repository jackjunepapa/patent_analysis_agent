"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";

export type DeepAnalysisVariant = "reasoning" | "strategy";

/** 스트리밍 누락·구형 모델 호환 */
export function normalizeDeepAnalysisMarkdown(md: string): string {
  let s = md.trim();
  if (!s) return s;
  s = s.replace(/등록 변리사 검토 필요/g, "**특허 전문가 검토 필요**");
  return s;
}

function buildComponents(variant: DeepAnalysisVariant): Components {
  const sky = variant === "reasoning";

  const h2Shell = sky
    ? "border-l-[5px] border-slate-400 bg-gradient-to-r from-slate-100/95 via-slate-50/80 to-transparent pl-3 pr-2 py-2 shadow-sm dark:border-slate-500 dark:from-slate-900/80 dark:via-slate-900/45 dark:to-transparent"
    : "border-l-[5px] border-blue-600 bg-gradient-to-r from-[#EFF6FF]/95 via-white to-transparent pl-3 pr-2 py-2 shadow-sm dark:border-blue-500 dark:from-blue-950/55 dark:via-slate-900/40 dark:to-transparent";

  const h2Text = sky
    ? "text-[15px] font-bold tracking-tight text-[#334155] dark:text-slate-100"
    : "text-[15px] font-bold tracking-tight text-[#334155] dark:text-slate-100";

  const h3Shell = sky
    ? "border-b border-[#E2E8F0] pb-1 dark:border-slate-600"
    : "border-b border-[#E2E8F0] pb-1 dark:border-slate-600";

  const h3Text = sky
    ? "text-[13px] font-bold text-slate-800 dark:text-slate-100"
    : "text-[13px] font-bold text-slate-800 dark:text-slate-100";

  const strongCls = sky
    ? "font-bold text-[#334155] dark:text-slate-50"
    : "font-bold text-[#2563EB] dark:text-blue-400";

  const linkCls = sky
    ? "font-medium text-[#3B82F6] underline decoration-blue-400/60 underline-offset-2 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
    : "font-medium text-[#2563EB] underline decoration-blue-400/70 underline-offset-2 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300";

  const blockBorder = sky ? "border-l-slate-400/90 dark:border-slate-500/70" : "border-l-blue-500 dark:border-blue-400/80";

  const theadBg = sky
    ? "bg-[#F1F5F9] dark:bg-slate-800/90"
    : "bg-[#F1F5F9] dark:bg-slate-800/90";

  const codeCls = sky
    ? "rounded bg-slate-100/90 px-1 py-0.5 font-mono text-[11px] text-[#334155] dark:bg-slate-800 dark:text-slate-100"
    : "rounded bg-[#EFF6FF] px-1 py-0.5 font-mono text-[11px] text-[#2563EB] dark:bg-blue-950/60 dark:text-blue-100";

  return {
    h1({ children }) {
      return <h1 className={`mb-4 mt-0 first:mt-0 ${h2Text} text-lg`}>{children}</h1>;
    },
    h2({ children }) {
      return (
        <h2 className={`mb-3 mt-8 scroll-mt-4 first:mt-0 ${h2Shell} rounded-r-lg`}>
          <span className={h2Text}>{children}</span>
        </h2>
      );
    },
    h3({ children }) {
      return (
        <h3 className={`mb-2 mt-5 first:mt-0 ${h3Shell}`}>
          <span className={h3Text}>{children}</span>
        </h3>
      );
    },
    h4({ children }) {
      return (
        <h4 className="mb-1.5 mt-4 text-[12px] font-semibold text-[#334155] dark:text-slate-200">{children}</h4>
      );
    },
    p({ children }) {
      return (
        <p className="mb-3 text-[13px] leading-relaxed text-[#334155] last:mb-0 dark:text-[#E2E8F0]">{children}</p>
      );
    },
    strong({ children }) {
      return <strong className={strongCls}>{children}</strong>;
    },
    em({ children }) {
      return <em className="italic text-slate-700 dark:text-slate-300">{children}</em>;
    },
    a({ href, children }) {
      const h = (href || "").trim();
      if (!h)
        return <span className="font-medium text-slate-700 dark:text-slate-200">{children}</span>;
      return (
        <a href={h} className={linkCls} rel="noopener noreferrer" target={h.startsWith("http") ? "_blank" : undefined}>
          {children}
        </a>
      );
    },
    ul({ children }) {
      return (
        <ul className="mb-3 list-disc space-y-2 pl-5 text-[13px] leading-relaxed text-[#334155] marker:text-slate-400 dark:text-[#E2E8F0] dark:marker:text-slate-500">
          {children}
        </ul>
      );
    },
    ol({ children }) {
      return (
        <ol className="mb-3 list-decimal space-y-2 pl-5 text-[13px] leading-relaxed text-[#334155] marker:font-semibold dark:text-[#E2E8F0]">
          {children}
        </ol>
      );
    },
    li({ children }) {
      return <li className="leading-relaxed [&_p]:mb-2 [&_p:last-child]:mb-0">{children}</li>;
    },
    blockquote({ children }) {
      return (
        <blockquote
          className={`mb-4 border-l-[3px] ${blockBorder} py-2 pl-3 pr-2 text-[13px] leading-relaxed ${
            sky
              ? "bg-slate-50/95 text-[#334155] dark:bg-slate-900/50 dark:text-slate-200"
              : "bg-[#EFF6FF] text-[#334155] dark:bg-blue-950/35 dark:text-slate-100"
          }`}
        >
          {children}
        </blockquote>
      );
    },
    hr() {
      return <hr className="my-6 border-t border-[#E2E8F0] dark:border-slate-700/80" />;
    },
    table({ children }) {
      return (
        <div className="mb-4 max-w-full overflow-x-auto rounded-lg border border-[#E2E8F0] shadow-sm dark:border-slate-700/70">
          <table className="min-w-full border-collapse text-left text-[12px]">{children}</table>
        </div>
      );
    },
    thead({ children }) {
      return <thead className={theadBg}>{children}</thead>;
    },
    tbody({ children }) {
      return <tbody className="divide-y divide-[#E2E8F0] dark:divide-slate-800">{children}</tbody>;
    },
    tr({ children }) {
      return (
        <tr className="bg-white odd:bg-slate-50/70 dark:bg-[#0F172A] dark:odd:bg-slate-900/45">{children}</tr>
      );
    },
    th({ children }) {
      return (
        <th className="border border-[#E2E8F0] px-2.5 py-1.5 font-bold text-[#334155] dark:border-slate-700 dark:text-slate-100">
          {children}
        </th>
      );
    },
    td({ children }) {
      return (
        <td className="border border-[#E2E8F0] px-2.5 py-1.5 align-top leading-snug text-[#334155] dark:border-slate-700 dark:text-[#E2E8F0]">
          {children}
        </td>
      );
    },
    code({ className, children }) {
      const isFence = Boolean(className?.startsWith("language-"));
      if (!isFence) {
        return <code className={codeCls}>{children}</code>;
      }
      return <code className={`font-mono text-[11px] text-zinc-100 ${className ?? ""}`}>{children}</code>;
    },
    pre({ children }) {
      return (
        <pre className="mb-4 overflow-x-auto rounded-lg border border-zinc-700 bg-zinc-900 p-3 text-[11px] leading-relaxed text-zinc-100 shadow-inner dark:border-zinc-600 dark:bg-zinc-950">
          {children}
        </pre>
      );
    },
  };
}

const cache = {
  reasoning: buildComponents("reasoning"),
  strategy: buildComponents("strategy"),
} as const;

export function DeepAnalysisMarkdown({
  markdown,
  variant,
}: {
  markdown: string;
  variant: DeepAnalysisVariant;
}) {
  if (!markdown.trim()) {
    return <span className="text-slate-400 dark:text-slate-500">—</span>;
  }
  const source = normalizeDeepAnalysisMarkdown(markdown);
  return (
    <div
      className={`deep-analysis-md ${variant === "reasoning" ? "deep-analysis-md--reasoning" : "deep-analysis-md--strategy"} [&_strong]:tracking-tight`}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={cache[variant]}>
        {source}
      </ReactMarkdown>
    </div>
  );
}
