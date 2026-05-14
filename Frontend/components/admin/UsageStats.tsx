import { Users, Database, FileText, Layers, Search } from "lucide-react";
import type { UsageStats } from "@/lib/types/api";

const STATS = [
  { key: "total_users" as const, label: "Users", icon: Users, color: "teal" },
  { key: "total_knowledge_bases" as const, label: "Knowledge Spaces", icon: Database, color: "cyan" },
  { key: "total_documents" as const, label: "Documents", icon: FileText, color: "blue" },
  { key: "total_chunks" as const, label: "Chunks", icon: Layers, color: "emerald" },
  { key: "total_queries" as const, label: "Queries", icon: Search, color: "amber" },
] as const;

const COLOR_MAP: Record<string, string> = {
  teal: "bg-teal-300/12 text-teal-300",
  cyan: "bg-cyan-500/15 text-cyan-400",
  blue: "bg-blue-500/15 text-blue-400",
  emerald: "bg-emerald-500/15 text-emerald-400",
  amber: "bg-amber-500/15 text-amber-400",
};

export function UsageStatsPanel({ stats }: { stats: UsageStats }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
      {STATS.map(({ key, label, icon: Icon, color }) => (
        <div key={key} className="section-panel rounded-lg p-4">
          <div className={`inline-flex h-9 w-9 items-center justify-center rounded-lg mb-3 ${COLOR_MAP[color]}`}>
            <Icon className="h-4 w-4" />
          </div>
          <p className="text-2xl font-bold text-white">{(stats[key] ?? 0).toLocaleString()}</p>
          <p className="text-xs text-white/40 mt-0.5">{label}</p>
        </div>
      ))}
    </div>
  );
}
