"use client";
import React, { useState } from "react";
import {
  FileText, Image, Music, Video, File, Trash2, FileAudio, ChevronDown,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDuration } from "@/lib/utils/format";
import { deleteDocument, getTranscript } from "@/lib/api/ingest";
import { toast } from "sonner";
import type { Document, Transcript } from "@/lib/types/api";

const MODALITY_ICON: Record<string, React.ElementType> = {
  pdf: FileText,
  docx: FileText,
  doc: FileText,
  image: Image,
  audio: Music,
  video: Video,
};

function DocIcon({ type }: { type: string }) {
  const Icon = MODALITY_ICON[type] ?? File;
  return <Icon className="h-4 w-4 shrink-0" />;
}

interface Props {
  documents: Document[];
  onDeleted: (docId: string) => void;
}

export function DocumentTable({ documents, onDeleted }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const [transcripts, setTranscripts] = useState<Record<string, Transcript>>({});

  const handleDelete = async (docId: string) => {
    try {
      await deleteDocument(docId);
      onDeleted(docId);
      toast.success("Document deleted");
    } catch {
      toast.error("Failed to delete document");
    }
  };

  const handleTranscript = async (docId: string) => {
    if (transcripts[docId]) {
      setExpanded(expanded === docId ? null : docId);
      return;
    }
    try {
      const t = await getTranscript(docId);
      setTranscripts((prev) => ({ ...prev, [docId]: t }));
      setExpanded(docId);
    } catch {
      toast.error("Transcript not available");
    }
  };

  if (!documents.length) {
    return (
      <p className="py-8 text-center text-sm text-white/30">No documents yet. Upload files to build the evidence layer.</p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/6 text-left text-xs text-white/35 font-medium">
            <th className="pb-2 pr-4">File</th>
            <th className="pb-2 pr-4">Type</th>
            <th className="pb-2 pr-4">Details</th>
            <th className="pb-2 pr-4">Status</th>
            <th className="pb-2 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/4">
          {documents.map((doc) => (
            <React.Fragment key={doc.id}>
              <tr className="group">
                <td className="py-3 pr-4">
                  <div className="flex items-center gap-2">
                    <span className="text-white/40"><DocIcon type={doc.file_type} /></span>
                    <span className="text-white/80 truncate max-w-[200px]">{doc.filename}</span>
                  </div>
                </td>
                <td className="py-3 pr-4">
                  <Badge variant={doc.file_type as "text" | "image" | "audio"}>
                    {doc.file_type}
                  </Badge>
                </td>
                <td className="py-3 pr-4 text-white/40 font-mono text-xs">
                  {doc.page_count ? `${doc.page_count}p` : ""}
                  {doc.duration_seconds ? formatDuration(doc.duration_seconds) : ""}
                  {!doc.page_count && !doc.duration_seconds ? "—" : ""}
                </td>
                <td className="py-3 pr-4">
                  <Badge
                    variant={
                      doc.status === "ready"
                        || doc.status === "complete"
                        ? "success"
                        : doc.status === "error"
                        || doc.status === "failed"
                        ? "error"
                        : doc.status === "processing"
                        ? "info"
                        : "default"
                    }
                  >
                    {doc.status}
                  </Badge>
                </td>
                <td className="py-3 text-right">
                  <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {(doc.file_type === "audio" || doc.file_type === "video") &&
                      doc.status === "ready" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleTranscript(doc.id)}
                          className="gap-1"
                        >
                          <FileAudio className="h-3.5 w-3.5" />
                          Transcript
                          <ChevronDown
                            className={`h-3 w-3 transition-transform ${
                              expanded === doc.id ? "rotate-180" : ""
                            }`}
                          />
                        </Button>
                      )}
                    <Button
                      variant="destructive"
                      size="icon"
                      onClick={() => handleDelete(doc.id)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </td>
              </tr>
              {expanded === doc.id && transcripts[doc.id] && (
                <tr key={`${doc.id}-transcript`}>
                  <td colSpan={5} className="pb-4">
                    <div className="glass rounded-lg p-4 mt-1 max-h-60 overflow-y-auto">
                      <p className="text-xs font-medium text-white/40 mb-2 uppercase tracking-wider">Transcript</p>
                      <div className="space-y-2">
                        {transcripts[doc.id].chunks.map((chunk, i) => (
                          <div key={i} className="flex gap-3 text-sm">
                            <span className="font-mono text-xs text-white/30 shrink-0 pt-0.5">
                              {Math.floor(chunk.timestamp_start ?? 0)}s
                            </span>
                            <p className="text-white/70">{chunk.text}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </td>
                </tr>
              )}
            </React.Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
