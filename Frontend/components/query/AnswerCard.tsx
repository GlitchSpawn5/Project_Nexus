"use client";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { AlertTriangle, GitBranch, Quote } from "lucide-react";
import type { AnswerCitation, GraphData } from "@/lib/types/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useState } from "react";
import * as Popover from "@radix-ui/react-popover";
import { getChain } from "@/lib/api/graph";

interface Props {
  answer: string; // annotated_text (contains [1], [2] numeric labels)
  citations: AnswerCitation[];
  confidenceScore?: number;
  insufficientEvidence?: boolean;
  onShowChain?: (data: GraphData) => void;
}

type Token =
  | { type: "text"; content: string }
  | { type: "citation"; label: string; citation: AnswerCitation };

function parseAnnotatedText(text: string, citations: AnswerCitation[]): Token[] {
  const citMap = Object.fromEntries(citations.map((c) => [c.citation_label, c]));
  const parts = text.split(/(\[\d+\])/g);
  const tokens: Token[] = [];
  for (const part of parts) {
    if (!part) continue;
    const match = part.match(/^(\[\d+\])$/);
    if (match && citMap[match[1]]) {
      tokens.push({ type: "citation", label: match[1], citation: citMap[match[1]] });
    } else {
      tokens.push({ type: "text", content: part });
    }
  }
  return tokens;
}

function CitationChip({
  citation,
  index,
  onShowChain,
}: {
  citation: AnswerCitation;
  index: number;
  onShowChain?: (data: GraphData) => void;
}) {
  const [loading, setLoading] = useState(false);

  const handleChain = async () => {
    setLoading(true);
    try {
      const data = await getChain(citation.chunk_id);
      onShowChain?.(data);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Popover.Root>
      <Popover.Trigger asChild>
        <button className="mx-0.5 inline-flex h-5 min-w-5 cursor-pointer items-center justify-center rounded border border-teal-300/35 bg-teal-300/14 px-1.5 align-middle text-[10px] font-bold text-teal-100 transition-colors hover:bg-teal-300/24">
          {index}
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          side="top"
          className="z-50 w-72 rounded-lg border border-white/10 bg-[#0b1017] p-4 shadow-2xl"
          sideOffset={5}
        >
          <p className="text-xs font-medium text-white/40 mb-2 uppercase tracking-wider">Source</p>
          <p className="text-sm text-white/80 font-medium truncate">{citation.filename}</p>
          <div className="mt-1 text-xs text-white/35 font-mono space-x-2">
            {citation.page_number && <span>p{citation.page_number}</span>}
            {citation.timestamp_start != null && (
              <span>{Math.floor(citation.timestamp_start)}s</span>
            )}
            <span className="capitalize text-white/25">{citation.modality}</span>
          </div>
          {onShowChain && (
            <button
              onClick={handleChain}
              disabled={loading}
              className="mt-3 flex items-center gap-1 text-xs text-teal-300 transition-colors hover:text-teal-200"
            >
              <GitBranch className="h-3 w-3" />
              {loading ? "Loading…" : "Show chain"}
            </button>
          )}
          <Popover.Arrow className="fill-white/10" />
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}

export function AnswerCard({
  answer,
  citations,
  confidenceScore,
  insufficientEvidence,
  onShowChain,
}: Props) {
  const tokens = parseAnnotatedText(answer, citations ?? []);

  return (
    <div className="section-panel rounded-lg p-5">
      {insufficientEvidence && (
        <div className="flex items-center gap-2 text-amber-400 bg-amber-500/10 border border-amber-500/25 rounded-lg px-3 py-2 mb-4 text-sm">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          Insufficient evidence in the knowledge base to fully answer this question.
        </div>
      )}

      {confidenceScore !== undefined && (
        <div className="mb-4 flex items-center justify-between gap-3 border-b border-white/8 pb-3">
          <div className="flex items-center gap-2 text-sm font-medium text-white/75">
            <Quote className="h-4 w-4 text-teal-300" />
            Grounded answer
          </div>
          <ConfidenceBadge score={confidenceScore} />
        </div>
      )}

      <div className="prose prose-sm prose-invert max-w-none">
        {tokens.map((token, i) => {
          if (token.type === "text") {
            return (
              <ReactMarkdown key={i} remarkPlugins={[remarkGfm]}>
                {token.content}
              </ReactMarkdown>
            );
          }
          const idx = citations.findIndex((c) => c.citation_label === token.label) + 1;
          return (
            <CitationChip
              key={i}
              citation={token.citation}
              index={idx}
              onShowChain={onShowChain}
            />
          );
        })}
      </div>
    </div>
  );
}
