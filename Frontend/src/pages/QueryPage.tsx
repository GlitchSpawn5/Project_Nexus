"use client";
import { useState } from "react";
import { useParams } from "react-router-dom";
import { QueryBox } from "@/components/query/QueryBox";
import { AnswerCard } from "@/components/query/AnswerCard";
import { ChunkList } from "@/components/query/ChunkList";
import { useQueryAsk } from "@/lib/hooks/useQueryAsk";
import { useQuery } from "@tanstack/react-query";
import { getQueryHistory } from "@/lib/api/query";
import type { QueryRequest, QueryResponse, GraphData } from "@/lib/types/api";
import { Clock, GitBranch, Route, ShieldCheck, X } from "lucide-react";
import { formatDate } from "@/lib/utils/format";

export function QueryPage() {
  const { kbId = "" } = useParams();
  const { mutate, data: result, isPending, reset } = useQueryAsk();
  const [chainData, setChainData] = useState<GraphData | null>(null);

  const { data: history } = useQuery({
    queryKey: ["query-history", kbId],
    queryFn: () => getQueryHistory(kbId),
  });

  const handleSubmit = (req: QueryRequest) => {
    reset();
    setChainData(null);
    mutate(req);
  };

  return (
    <div className="flex h-full overflow-hidden">
      {history && history.length > 0 && (
        <div className="w-64 shrink-0 overflow-y-auto border-r border-white/10 bg-white/[0.018] p-3">
          <p className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-[0.22em] text-white/28">
            History
          </p>
          {history.map((session) => (
            <button
              key={session.id}
              className="w-full rounded-lg px-3 py-2 text-left text-xs text-white/52 transition-all hover:bg-white/5 hover:text-white/82"
            >
              <p className="truncate">{session.query_text}</p>
              <p className="mt-0.5 flex items-center gap-1 text-[10px] text-white/25">
                <Clock className="h-2.5 w-2.5" />
                {formatDate(session.created_at)}
              </p>
            </button>
          ))}
        </div>
      )}

      <div className="flex-1 overflow-y-auto">
        <div className="page-shell space-y-5">
          <div className="grid gap-3 md:grid-cols-3">
            <WorkflowStep icon={ShieldCheck} label="Governed access" text="Role and ownership policies protect evidence." />
            <WorkflowStep icon={GitBranch} label="Graph expansion" text="Neighbor chunks reveal cross-modal context." />
            <WorkflowStep icon={Route} label="Fallback chain" text="Provider health rolls answers to the next LLM." />
          </div>

          <QueryBox kbId={kbId} onSubmit={handleSubmit} isLoading={isPending} />

          {isPending && (
            <div className="flex items-center gap-3 text-sm text-white/40">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-teal-300 border-t-transparent" />
              Searching knowledge base...
            </div>
          )}

          {result && <QueryResult result={result} onShowChain={setChainData} />}

          {chainData && (
            <div className="section-panel rounded-lg p-5">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="flex items-center gap-1.5 text-sm font-medium text-white/70">
                  <GitBranch className="h-4 w-4 text-teal-300" />
                  Evidence chain ({chainData.nodes.length} nodes)
                </h3>
                <button
                  onClick={() => setChainData(null)}
                  className="p-1 text-white/30 transition-colors hover:text-white/70"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
              <div className="space-y-2">
                {chainData.nodes.map((node) => (
                  <div key={node.id} className="flex items-start gap-2 text-sm">
                    <span className="shrink-0 pt-0.5 font-mono text-xs text-white/25">
                      {node.modality}
                    </span>
                    <p className="line-clamp-2 text-white/60">{String(node.text_preview ?? "")}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function WorkflowStep({
  icon: Icon,
  label,
  text,
}: {
  icon: React.ElementType;
  label: string;
  text: string;
}) {
  return (
    <div className="section-panel rounded-lg p-4">
      <Icon className="h-4 w-4 text-teal-300" />
      <p className="mt-3 text-sm font-medium text-white/80">{label}</p>
      <p className="mt-1 text-xs leading-relaxed text-white/36">{text}</p>
    </div>
  );
}

function QueryResult({
  result,
  onShowChain,
}: {
  result: QueryResponse;
  onShowChain: (d: GraphData) => void;
}) {
  return (
    <div className="space-y-4">
      {result.answer && (
        <div>
          <AnswerCard
            answer={result.answer.annotated_text || result.answer.text}
            citations={result.answer.citations}
            confidenceScore={result.answer.confidence_score}
            insufficientEvidence={result.answer.insufficient_evidence}
            onShowChain={onShowChain}
          />
          {result.answer.llm_provider && (
            <p className="mt-1.5 text-right font-mono text-[10px] text-white/24">
              via {result.answer.llm_provider}
            </p>
          )}
        </div>
      )}

      {result.results.length > 0 && <ChunkList chunks={result.results} />}
    </div>
  );
}
