"use client";

import { Children, isValidElement, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";

/** 스트리밍·구버전 응답 호환 + 문단 구분 */
export function normalizeInventionSummaryMarkdown(md: string): string {
  return md.replace(/등록 변리사 검토 필요/g, "\n\n**특허 전문가 검토 필요**");
}

function flattenText(node: ReactNode): string {
  if (node == null || typeof node === "boolean") return "";
  if (typeof node === "string" || typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(flattenText).join("");
  if (isValidElement(node)) {
    const p = node.props as { children?: ReactNode };
    return flattenText(p.children);
  }
  return "";
}

function isCoreImportanceRow(children: ReactNode): boolean {
  const cells = Children.toArray(children).filter(isValidElement);
  const third = cells[2];
  if (!third || !isValidElement(third)) return false;
  const p = third.props as { children?: ReactNode };
  const t = flattenText(p.children);
  return /\b핵심\b/.test(t) || /\bCore\b/i.test(t);
}

const inventionSummaryComponents: Components = {
  h1({ children }) {
    return (
      <h1 className="mb-3 mt-0 text-lg font-bold tracking-tight text-[#334155] dark:text-slate-100">{children}</h1>
    );
  },
  h2({ children }) {
    return (
      <h2 className="mb-2 mt-6 border-b border-[#E2E8F0] pb-1.5 text-base font-bold text-[#334155] first:mt-0 dark:border-slate-600 dark:text-slate-100">
        {children}
      </h2>
    );
  },
  h3({ children }) {
    return (
      <h3 className="mb-1.5 mt-4 text-sm font-bold text-slate-800 dark:text-slate-100">{children}</h3>
    );
  },
  h4({ children }) {
    return (
      <h4 className="mb-1 mt-3 text-sm font-bold text-slate-800 dark:text-slate-200">{children}</h4>
    );
  },
  p({ children }) {
    return <p className="mb-3 text-[13px] leading-relaxed text-[#334155] last:mb-0 dark:text-[#E2E8F0]">{children}</p>;
  },
  strong({ children }) {
    return <strong className="font-bold text-[#334155] dark:text-slate-50">{children}</strong>;
  },
  ul({ children }) {
    return <ul className="mb-3 list-disc space-y-1.5 pl-5 text-[13px] text-[#334155] dark:text-[#E2E8F0]">{children}</ul>;
  },
  ol({ children }) {
    return <ol className="mb-3 list-decimal space-y-1.5 pl-5 text-[13px] text-[#334155] dark:text-[#E2E8F0]">{children}</ol>;
  },
  li({ children }) {
    return <li className="leading-relaxed">{children}</li>;
  },
  hr() {
    return <hr className="my-5 border-t border-[#E2E8F0] dark:border-slate-600" />;
  },
  blockquote({ children }) {
    return (
      <blockquote className="mb-3 border-l-[3px] border-[#3B82F6] bg-[#EFF6FF]/80 py-2 pl-3 pr-2 text-[13px] leading-relaxed text-[#334155] dark:border-blue-400 dark:bg-blue-950/30 dark:text-slate-100">
        {children}
      </blockquote>
    );
  },
  a({ href, children }) {
    const h = href || "";
    if (h.startsWith("#spec-ref-")) {
      return (
        <a
          href={h}
          className="font-mono text-[12px] font-medium text-[#3B82F6] underline decoration-blue-400/70 underline-offset-2 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
        >
          {children}
        </a>
      );
    }
    return (
      <a href={h} className="text-[#3B82F6] underline underline-offset-2 hover:text-blue-700 dark:text-blue-400">
        {children}
      </a>
    );
  },
  table({ children }) {
    return (
      <div className="mb-4 max-w-full overflow-x-auto rounded-lg border border-[#E2E8F0] shadow-sm dark:border-slate-700">
        <table className="min-w-full border-collapse text-left text-[12px] text-[#334155] dark:text-[#E2E8F0]">
          {children}
        </table>
      </div>
    );
  },
  thead({ children }) {
    return <thead className="bg-[#F1F5F9] dark:bg-slate-800/90">{children}</thead>;
  },
  tbody({ children }) {
    return <tbody className="divide-y divide-[#E2E8F0] dark:divide-slate-700">{children}</tbody>;
  },
  tr({ children }) {
    const core = isCoreImportanceRow(children);
    return (
      <tr
        className={
          core
            ? "bg-[#FFF7ED] hover:bg-[#FFEDD5] dark:bg-orange-950/25 dark:hover:bg-orange-950/35"
            : "bg-white odd:bg-slate-50/60 dark:bg-[#0F172A] dark:odd:bg-slate-900/40"
        }
      >
        {children}
      </tr>
    );
  },
  th({ children }) {
    return (
      <th className="border border-[#E2E8F0] px-2 py-1.5 font-semibold text-[#334155] dark:border-slate-700 dark:text-slate-100">
        {children}
      </th>
    );
  },
  td({ children }) {
    return (
      <td className="border border-[#E2E8F0] px-2 py-1.5 align-top leading-snug dark:border-slate-700">
        {children}
      </td>
    );
  },
};

export function InventionSummaryMarkdown({ markdown }: { markdown: string }) {
  if (!markdown.trim()) {
    return <span className="text-slate-400 dark:text-slate-500">—</span>;
  }
  const source = normalizeInventionSummaryMarkdown(markdown);
  return (
    <div className="invention-summary-md text-sm">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={inventionSummaryComponents}>
        {source}
      </ReactMarkdown>
    </div>
  );
}
