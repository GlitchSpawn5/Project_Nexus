"use client";
import { Topbar } from "@/components/shell/Topbar";
import { KBCard } from "@/components/kb/KBCard";
import { CreateKBDialog } from "@/components/kb/CreateKBDialog";
import { useKBs } from "@/lib/hooks/useKBs";
import { Database, FileAudio, FileText, GitBranch, ShieldCheck } from "lucide-react";

export function DashboardPage() {
  const { data: kbs, isLoading } = useKBs();
  const count = kbs?.length ?? 0;

  return (
    <>
      <Topbar title="Knowledge Spaces" />
      <div className="page-shell space-y-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-teal-300/75">
              Global knowledge operations
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Knowledge spaces</h1>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-white/45">
              Organize trusted content by team, region, function, or client. Ingest multimodal
              files and answer questions with vector retrieval plus evidence graph expansion.
            </p>
          </div>
          <CreateKBDialog />
        </div>

        <div className="grid gap-3 md:grid-cols-4">
          <Metric label="Active spaces" value={String(count)} icon={Database} tone="text-teal-300" />
          <Metric label="Governance" value="RBAC" icon={ShieldCheck} tone="text-emerald-300" />
          <Metric label="Modalities" value="Text/Image/Audio" icon={FileAudio} tone="text-blue-300" />
          <Metric label="Evidence layer" value="Graph" icon={GitBranch} tone="text-amber-300" />
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="glass h-36 animate-pulse rounded-xl" />
            ))}
          </div>
        ) : kbs && kbs.length > 0 ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {kbs.map((kb) => (
              <KBCard key={kb.id} kb={kb} />
            ))}
          </div>
        ) : (
          <div className="section-panel flex flex-col items-center justify-center rounded-lg py-20 text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-lg bg-teal-300/10 text-teal-300">
              <FileText className="h-8 w-8" />
            </div>
            <h3 className="text-base font-medium text-white/75">No knowledge spaces yet</h3>
            <p className="mt-1 mb-5 max-w-xs text-sm text-white/38">
              Create your first space to upload trusted content and query it with cited AI.
            </p>
            <CreateKBDialog />
          </div>
        )}
      </div>
    </>
  );
}

function Metric({
  label,
  value,
  icon: Icon,
  tone,
}: {
  label: string;
  value: string;
  icon: React.ElementType;
  tone: string;
}) {
  return (
    <div className="section-panel rounded-lg p-4">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-[0.18em] text-white/32">{label}</p>
        <Icon className={`h-4 w-4 ${tone}`} />
      </div>
      <p className="mt-3 truncate text-xl font-semibold text-white">{value}</p>
    </div>
  );
}
