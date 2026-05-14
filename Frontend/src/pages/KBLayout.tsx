import { Link, Outlet, useLocation, useParams } from "react-router-dom";
import { Topbar } from "@/components/shell/Topbar";
import { FileText, Search, GitBranch, LockKeyhole } from "lucide-react";
import { cn } from "@/lib/utils";

export function KBLayout() {
  const { kbId = "" } = useParams();
  const { pathname } = useLocation();

  const tabs = [
    { label: "Documents", href: `/kb/${kbId}`, icon: FileText },
    { label: "Query", href: `/kb/${kbId}/query`, icon: Search },
    { label: "Graph", href: `/kb/${kbId}/graph`, icon: GitBranch },
  ];

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <Topbar title="Knowledge Base" />
      <div className="border-b border-white/10 px-6 py-4">
        <div className="mb-4 flex items-center justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-teal-300/75">
              Governed knowledge space
            </p>
            <p className="mt-1 font-mono text-xs text-white/32">{kbId}</p>
          </div>
          <div className="hidden items-center gap-2 rounded-lg border border-emerald-300/16 bg-emerald-300/8 px-3 py-2 text-xs text-emerald-100/72 sm:flex">
            <LockKeyhole className="h-3.5 w-3.5 text-emerald-300" />
            Role-based access
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {tabs.map((tab) => {
            const active = pathname === tab.href;
            return (
              <Link
                key={tab.href}
                to={tab.href}
                className={cn(
                  "flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-all",
                  active
                    ? "border-teal-300/35 bg-teal-300/10 text-teal-100"
                    : "border-white/9 bg-white/[0.02] text-white/45 hover:bg-white/6 hover:text-white/75"
                )}
              >
                <tab.icon className="h-3.5 w-3.5" />
                {tab.label}
              </Link>
            );
          })}
        </div>
      </div>
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
