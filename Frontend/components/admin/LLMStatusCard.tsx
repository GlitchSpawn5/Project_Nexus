import { CheckCircle2, Loader2, Route, XCircle } from "lucide-react";
import type { LLMStatus } from "@/lib/types/api";

export function LLMStatusCard({ status, isLoading }: { status?: LLMStatus; isLoading: boolean }) {
  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-white/40 text-sm">
        <Loader2 className="h-4 w-4 animate-spin" />
        Checking providers…
      </div>
    );
  }

  if (!status) return null;

  const providers = status.providers ?? [];

  return (
    <div className="space-y-4">
      <div className="section-panel rounded-lg p-4">
        <div className="flex items-center gap-2 text-sm font-medium text-white/80">
          <Route className="h-4 w-4 text-teal-300" />
          Provider fallback chain
        </div>
        <p className="mt-2 text-xs text-white/38">
          Primary provider: {status.primary_provider}. Auto fallback is{" "}
          {status.auto_fallback_enabled ? "enabled" : "disabled"}.
        </p>
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {providers.map((p) => (
          <div key={p.provider} className="section-panel rounded-lg p-4">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-medium capitalize text-white/80">{p.provider}</span>
              {p.available ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              ) : (
                <XCircle className="h-4 w-4 text-red-400" />
              )}
            </div>
            <p className={`text-xs ${p.available ? "text-emerald-400" : "text-red-400"}`}>
              {p.available ? "Reachable" : "Unreachable"}
            </p>
            {!p.configured && <p className="mt-1 font-mono text-[10px] text-white/25">not configured</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
