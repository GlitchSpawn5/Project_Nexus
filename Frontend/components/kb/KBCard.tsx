"use client";
import { Link } from "react-router-dom";
import { ArrowRight, Database, FileText, GitBranch, LockKeyhole } from "lucide-react";
import { formatDate } from "@/lib/utils/format";
import type { KnowledgeBase } from "@/lib/types/api";

export function KBCard({ kb }: { kb: KnowledgeBase }) {
  return (
    <Link
      to={`/kb/${kb.id}`}
      className="group section-panel flex min-h-56 flex-col gap-4 rounded-lg p-5 transition-all duration-200 hover:bg-white/6 hover:glow-border"
    >
      <div className="flex items-start justify-between">
        <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-teal-300/10 text-teal-300 ring-1 ring-teal-300/20">
          <Database className="h-5 w-5" />
        </div>
        <ArrowRight className="h-4 w-4 text-white/24 transition-colors group-hover:text-white/70" />
      </div>
      <div>
        <h3 className="font-semibold text-white group-hover:text-white transition-colors">{kb.name}</h3>
        {kb.description && (
          <p className="mt-1 line-clamp-2 text-sm leading-relaxed text-white/42">{kb.description}</p>
        )}
      </div>
      <div className="mt-auto grid grid-cols-3 gap-2 text-[10px] text-white/36">
        <span className="flex items-center gap-1 rounded-md bg-white/[0.03] px-2 py-1">
          <LockKeyhole className="h-3 w-3 text-emerald-300" />
          Access
        </span>
        <span className="flex items-center gap-1 rounded-md bg-white/[0.03] px-2 py-1">
          <FileText className="h-3 w-3 text-blue-300" />
          Files
        </span>
        <span className="flex items-center gap-1 rounded-md bg-white/[0.03] px-2 py-1">
          <GitBranch className="h-3 w-3 text-amber-300" />
          Graph
        </span>
      </div>
      <p className="text-xs text-white/28">{formatDate(kb.created_at)}</p>
    </Link>
  );
}
