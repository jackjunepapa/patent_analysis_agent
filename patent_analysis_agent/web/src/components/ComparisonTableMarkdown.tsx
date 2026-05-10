"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";

export type ComparisonTableVariant = "comparison" | "claimMapping";

function flattenText(node: React.ReactNode): string {
  if (node == null || typeof node === "boolean") return "";
  if (typeof node === "string" || typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(flattenText).join("");
  if (typeof node === "object" && "props" in node && node.props) {
    const p = node.props as { children?: React.ReactNode };
    return flattenText(p.children);
  }
  return "";
}

function isThElement(node: React.ReactNode): boolean {
  return React.isValidElement(node) && node.type === "th";
}

/** 선행 매칭 열(가운데): 일치도·미검출 등 배지 톤 (Slate & Amber 워크스페이스 스펙) */
function matchCellTone(text: string): string {
  const t = text.trim();
  const emerald =
    "bg-[#DCFCE7] text-[#166534] shadow-sm ring-1 ring-emerald-500/15 dark:bg-emerald-950/45 dark:text-emerald-100 dark:ring-emerald-500/25";
  const softAmber =
    "bg-[#FEF3C7] text-[#92400E] shadow-sm ring-1 ring-amber-500/15 dark:bg-amber-950/40 dark:text-amber-100 dark:ring-amber-500/20";
  const rose =
    "bg-[#FEE2E2] text-[#991B1B] shadow-sm ring-1 ring-rose-500/15 dark:bg-rose-950/45 dark:text-rose-100 dark:ring-rose-500/25";
  if (/✅/.test(t)) return emerald;
  if (/❌|미확인|미검출|missing|none/i.test(t)) return rose;
  if (/⚠|부분|partial|약함|weak/i.test(t)) return softAmber;
  if (/일치|matched|high/i.test(t) && !/부분|partial|약함|weak/i.test(t)) return emerald;
  return "bg-[#F1F5F9] text-[#334155] ring-1 ring-slate-300/40 dark:bg-slate-800/90 dark:text-slate-100 dark:ring-slate-600/30";
}

function isCoreComparisonRow(firstCellText: string): boolean {
  return /\b핵심\b/i.test(firstCellText) || /\bCore\b/i.test(firstCellText);
}

function buildComponents(variant: ComparisonTableVariant): Components {
  const isComp = variant === "comparison";

  const scrollWrap = isComp
    ? "border-[#E2E8F0] bg-white shadow-sm dark:border-slate-700 dark:bg-[#0F172A]"
    : "border-violet-200/75 bg-white/95 dark:border-violet-800/50 dark:bg-zinc-900/90";

  const theadBg = isComp
    ? "border-[#E2E8F0] bg-[#F1F5F9] dark:border-slate-600 dark:bg-slate-800/95"
    : "border-violet-300/70 from-violet-100 to-violet-50/95 dark:border-violet-800 dark:from-violet-950 dark:to-violet-950/88";

  const thText = isComp
    ? "border-[#E2E8F0] text-[#334155] dark:border-slate-600 dark:text-slate-100"
    : "border-violet-200/60 text-violet-950 dark:border-violet-800/50 dark:text-violet-100";

  const tbodyDivide = isComp
    ? "divide-[#E2E8F0] dark:divide-slate-700"
    : "divide-violet-100/80 dark:divide-violet-900/45";

  const rowHover = isComp
    ? "odd:bg-white even:bg-slate-50/70 hover:bg-slate-100/80 dark:odd:bg-[#0F172A] dark:even:bg-slate-900/50 dark:hover:bg-slate-800/70"
    : "odd:bg-white even:bg-violet-50/25 hover:bg-violet-100/35 dark:odd:bg-zinc-950/35 dark:even:bg-violet-950/15 dark:hover:bg-violet-950/35";

  const tdBase = isComp
    ? "border-b border-r border-[#E2E8F0] text-[#334155] dark:border-slate-700 dark:text-slate-100"
    : "border-b border-r border-violet-100/90 text-zinc-800 dark:border-violet-900/40 dark:text-zinc-100";

  const tdFirst = isComp
    ? "min-w-[12rem] max-w-[min(52rem,94vw)] border-l-0 font-medium leading-snug text-[#334155] dark:text-slate-100 [overflow-wrap:anywhere]"
    : "min-w-[11rem] max-w-[min(22rem,40vw)] border-l-0 font-medium leading-snug text-violet-950 dark:text-violet-100";

  const tdMiddleMatch =
    "max-w-[11rem] min-w-[6.5rem] rounded-md px-2 py-1.5 text-center text-xs font-medium leading-tight tabular-nums";

  const tdMiddleMapping =
    "max-w-[min(26rem,46vw)] text-left text-[13px] font-normal leading-snug [overflow-wrap:anywhere]";

  const tdLast = isComp
    ? "max-w-[min(26rem,48vw)] border-l border-[#E2E8F0] bg-white pl-3 font-normal text-[#334155] dark:border-slate-700 dark:bg-[#0F172A] dark:text-slate-100"
    : "max-w-[min(14rem,22vw)] border-l-2 border-violet-300/70 bg-gradient-to-br from-violet-50/95 to-white pl-3 font-normal text-zinc-900 dark:border-violet-700/50 dark:from-violet-950/40 dark:to-zinc-950/85 dark:text-zinc-50";

  const paraBorder = isComp ? "border-slate-300/80 dark:border-slate-600/60" : "border-violet-400/70 dark:border-violet-600/50";
  const strongText = isComp ? "text-[#334155] dark:text-slate-100" : "text-violet-900 dark:text-violet-200";

  return {
    table({ children }) {
      return (
        <div
          className={`comparison-table-scroll -mx-0.5 max-h-[min(65vh,560px)] overflow-x-auto overflow-y-auto rounded-xl border shadow-inner ${scrollWrap}`}
        >
          <table className="comparison-md-table min-w-[min(960px,100%)] w-full border-collapse text-left">
            {children}
          </table>
        </div>
      );
    },
    thead({ children }) {
      return (
        <thead className={`sticky top-0 z-[1] border-b shadow-sm ${isComp ? theadBg : `bg-gradient-to-b ${theadBg}`}`}>
          {children}
        </thead>
      );
    },
    tbody({ children }) {
      return <tbody className={`divide-y ${tbodyDivide}`}>{children}</tbody>;
    },
    tr({ children }) {
      const els = React.Children.toArray(children).filter(React.isValidElement) as React.ReactElement[];
      if (els.length > 0 && isThElement(els[0])) {
        return <tr>{children}</tr>;
      }
      const n = els.length;
      const firstText =
        els.length > 0 ? flattenText((els[0].props as { children?: React.ReactNode }).children) : "";
      const coreRow = isComp && isCoreComparisonRow(firstText);
      const trCls = coreRow
        ? "transition-colors bg-[#FFF7ED] hover:bg-[#FFEDD5] dark:bg-orange-950/20 dark:hover:bg-orange-950/30"
        : `transition-colors ${rowHover}`;
      return (
        <tr className={trCls}>
          {els.map((cell, i) => {
            const isFirst = i === 0;
            const isLast = i === n - 1;
            const text = flattenText((cell.props as { children?: React.ReactNode }).children);
            let colClass = `${tdBase} border-r px-3 py-2.5 align-top text-[13px] leading-snug last:border-r-0`;
            if (isFirst) colClass = `${colClass} ${tdFirst}`;
            else if (isLast) colClass = `${colClass} ${tdLast}`;
            else if (isComp) colClass = `${colClass} ${tdMiddleMatch} ${matchCellTone(text)}`;
            else colClass = `${colClass} ${tdMiddleMapping} bg-violet-50/25 dark:bg-violet-950/15`;
            return React.cloneElement(cell as React.ReactElement<{ className?: string }>, {
              className: colClass,
            });
          })}
        </tr>
      );
    },
    th({ children }) {
      return (
        <th
          className={`whitespace-normal break-words border-r px-3 py-2.5 text-left text-[11px] font-bold uppercase leading-tight tracking-wide last:border-r-0 ${thText}`}
        >
          {children}
        </th>
      );
    },
    td({ children }) {
      return <td>{children}</td>;
    },
    p({ children }) {
      return (
        <p
          className={`mt-4 border-l-2 pl-3 text-xs leading-relaxed text-zinc-600 first:mt-0 dark:text-zinc-400 ${paraBorder}`}
        >
          {children}
        </p>
      );
    },
    strong({ children }) {
      return <strong className={`font-semibold ${strongText}`}>{children}</strong>;
    },
    ul({ children }) {
      return <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-zinc-600 dark:text-zinc-400">{children}</ul>;
    },
    li({ children }) {
      return <li className="leading-relaxed">{children}</li>;
    },
  };
}

const comparisonComponentsCache = {
  comparison: buildComponents("comparison"),
  claimMapping: buildComponents("claimMapping"),
} as const;

export function ComparisonTableMarkdown({
  markdown,
  variant = "comparison",
}: {
  markdown: string;
  variant?: ComparisonTableVariant;
}) {
  if (!markdown.trim()) {
    return <span className="text-slate-400 dark:text-slate-500">—</span>;
  }
  const components = comparisonComponentsCache[variant];
  return (
    <div className="comparison-table-markdown space-y-3 text-sm text-[#334155] dark:text-slate-100">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {markdown}
      </ReactMarkdown>
    </div>
  );
}
