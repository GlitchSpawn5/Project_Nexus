"use client";
import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getGraph, getGraphStats } from "@/lib/api/graph";
import { EvidenceGraph } from "@/components/graph/EvidenceGraph";
import type { GraphNode } from "@/lib/types/api";
import { Activity, GitBranch, Network, X } from "lucide-react";

export function GraphPage() {
  const { kbId = "" } = useParams();
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const { data: graphData, isLoading } = useQuery({
    queryKey: ["graph", kbId],
    queryFn: () => getGraph(kbId),
  });

  const { data: stats } = useQuery({
    queryKey: ["graph-stats", kbId],
    queryFn: () => getGraphStats(kbId),
  });

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-teal-300 border-t-transparent" />
      </div>
    );
  }

  if (!graphData || graphData.nodes.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-center">
        <div>
          <p className="text-lg font-medium text-white/50">No graph data yet</p>
          <p className="mt-1 text-sm text-white/30">
            Upload and ingest documents to build the evidence graph.
          </p>
        </div>
      </div>
    );
  }

  const avgDegree =
    stats && stats.total_nodes > 0
      ? ((2 * stats.total_edges) / stats.total_nodes).toFixed(1)
      : "-";

  return (
    <div className="relative h-full w-full">
      <EvidenceGraph data={graphData} onNodeClick={setSelectedNode} />

      {stats && (
        <div className="absolute right-4 top-4 grid w-72 gap-2 text-xs">
          <GraphStat icon={Network} label="Nodes" value={String(stats.total_nodes)} />
          <GraphStat icon={GitBranch} label="Edges" value={String(stats.total_edges)} />
          <GraphStat icon={Activity} label="Avg degree" value={avgDegree} />
        </div>
      )}

      {selectedNode && (
        <div className="absolute bottom-0 right-0 top-0 w-80 overflow-y-auto border-l border-white/10 bg-[#0b1017]/95 p-5 shadow-2xl">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-medium text-white/80">Chunk detail</h3>
            <button
              onClick={() => setSelectedNode(null)}
              className="p-1 text-white/30 transition-colors hover:text-white/70"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <div className="space-y-3 text-sm">
            <div>
              <p className="mb-1 text-[10px] uppercase tracking-wider text-white/30">Modality</p>
              <p className="capitalize text-white/70">{selectedNode.modality}</p>
            </div>
            {selectedNode.text_preview && (
              <div>
                <p className="mb-1 text-[10px] uppercase tracking-wider text-white/30">Content</p>
                <p className="text-xs leading-relaxed text-white/65">
                  {String(selectedNode.text_preview)}
                </p>
              </div>
            )}
            <div>
              <p className="mb-1 text-[10px] uppercase tracking-wider text-white/30">Chunk ID</p>
              <p className="break-all font-mono text-[10px] text-white/30">{selectedNode.id}</p>
            </div>
            {selectedNode.page_number && (
              <div>
                <p className="mb-1 text-[10px] uppercase tracking-wider text-white/30">Page</p>
                <p className="text-white/70">{String(selectedNode.page_number)}</p>
              </div>
            )}
            {selectedNode.timestamp_start != null && (
              <div>
                <p className="mb-1 text-[10px] uppercase tracking-wider text-white/30">Timestamp</p>
                <p className="font-mono text-white/70">{String(selectedNode.timestamp_start)}s</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function GraphStat({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-white/10 bg-[#0b1017]/88 px-3 py-2 backdrop-blur">
      <span className="flex items-center gap-2 text-white/45">
        <Icon className="h-3.5 w-3.5 text-teal-300" />
        {label}
      </span>
      <span className="font-mono text-white/76">{value}</span>
    </div>
  );
}
