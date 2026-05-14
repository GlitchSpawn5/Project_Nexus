"use client";
import { useState } from "react";
import { ChevronDown, GitBranch, Search, Send, Settings2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import type { ModalityFilter, QueryRequest } from "@/lib/types/api";
import { cn } from "@/lib/utils";

interface Props {
  kbId: string;
  onSubmit: (req: QueryRequest) => void;
  isLoading: boolean;
}

export function QueryBox({ kbId, onSubmit, isLoading }: Props) {
  const [query, setQuery] = useState("");
  const [showOptions, setShowOptions] = useState(false);
  const [topK, setTopK] = useState(10);
  const [modalityFilter, setModalityFilter] = useState<ModalityFilter>("all");
  const [expandChains, setExpandChains] = useState(true);
  const [generateAnswer, setGenerateAnswer] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    onSubmit({
      kb_id: kbId,
      query: query.trim(),
      top_k: topK,
      modality_filter: modalityFilter,
      expand_evidence_chains: expandChains,
      generate_answer: generateAnswer,
    });
  };

  return (
    <div className="section-panel rounded-lg p-4">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-white">Ask across this knowledge space</h2>
          <p className="mt-1 text-sm text-white/40">
            Retrieval pulls nearest vectors, expands graph neighbors, then assembles cited evidence.
          </p>
        </div>
        <div className="flex gap-2 text-xs text-white/42">
          <span className="flex items-center gap-1 rounded-md bg-blue-400/10 px-2 py-1 text-blue-200/80">
            <Search className="h-3 w-3" />
            Vector
          </span>
          <span className="flex items-center gap-1 rounded-md bg-amber-400/10 px-2 py-1 text-amber-200/80">
            <GitBranch className="h-3 w-3" />
            Graph
          </span>
          <span className="flex items-center gap-1 rounded-md bg-teal-300/10 px-2 py-1 text-teal-100/80">
            <Sparkles className="h-3 w-3" />
            Answer
          </span>
        </div>
      </div>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question about your documents…"
          className="h-12 flex-1 text-base"
          disabled={isLoading}
        />
        <Button type="submit" size="lg" disabled={isLoading || !query.trim()} className="h-12 px-5">
          {isLoading ? (
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
        <Button
          type="button"
          variant="outline"
          size="lg"
          className="h-12 px-3"
          onClick={() => setShowOptions((s) => !s)}
        >
          <Settings2 className="h-4 w-4" />
          <ChevronDown className={cn("h-3 w-3 transition-transform", showOptions && "rotate-180")} />
        </Button>
      </form>

      {showOptions && (
        <div className="mt-4 grid grid-cols-2 gap-4 border-t border-white/8 pt-4 sm:grid-cols-4">
          <div className="space-y-1.5">
            <label className="text-xs text-white/40">Top-K results</label>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min={1}
                max={20}
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="flex-1 accent-teal-300"
              />
              <span className="text-xs font-mono text-white/60 w-5">{topK}</span>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs text-white/40">Modality</label>
            <Select
              value={modalityFilter}
              onValueChange={(v) => setModalityFilter(v as ModalityFilter)}
            >
              <SelectTrigger className="h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="text">Text only</SelectItem>
                <SelectItem value="image">Image only</SelectItem>
                <SelectItem value="audio">Audio only</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2 mt-auto">
            <input
              type="checkbox"
              id="expand"
              checked={expandChains}
              onChange={(e) => setExpandChains(e.target.checked)}
              className="accent-teal-300 h-4 w-4"
            />
            <label htmlFor="expand" className="text-xs text-white/60 cursor-pointer">
              Evidence chains
            </label>
          </div>

          <div className="flex items-center gap-2 mt-auto">
            <input
              type="checkbox"
              id="generate"
              checked={generateAnswer}
              onChange={(e) => setGenerateAnswer(e.target.checked)}
              className="accent-teal-300 h-4 w-4"
            />
            <label htmlFor="generate" className="text-xs text-white/60 cursor-pointer">
              Generate answer
            </label>
          </div>
        </div>
      )}
    </div>
  );
}
