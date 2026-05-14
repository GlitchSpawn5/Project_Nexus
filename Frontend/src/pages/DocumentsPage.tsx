"use client";
import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { toast } from "sonner";
import { Dropzone } from "@/components/ingest/Dropzone";
import { JobProgressList } from "@/components/ingest/JobProgressList";
import { DocumentTable } from "@/components/ingest/DocumentTable";
import { uploadFile, getDocuments } from "@/lib/api/ingest";
import { extractErrorMessage } from "@/lib/utils/errors";
import type { Document } from "@/lib/types/api";
import { useQueryClient } from "@tanstack/react-query";
import { DatabaseZap, FileAudio, FileImage, FileText, GitBranch } from "lucide-react";

interface ActiveJob {
  jobId: string;
  filename: string;
}

export function DocumentsPage() {
  const { kbId = "" } = useParams();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [activeJobs, setActiveJobs] = useState<ActiveJob[]>([]);
  const [uploading, setUploading] = useState(false);
  const qc = useQueryClient();

  useEffect(() => {
    getDocuments(kbId)
      .then(setDocuments)
      .catch(() => {});
  }, [kbId]);

  const handleFiles = async (files: File[]) => {
    setUploading(true);
    try {
      const results = await Promise.all(
        files.map(async (file) => {
          const res = await uploadFile(kbId, file);
          return { jobId: res.job_id, filename: file.name, docId: res.document_id };
        })
      );
      setActiveJobs((prev) => [
        ...prev,
        ...results.map((r) => ({ jobId: r.jobId, filename: r.filename })),
      ]);
      toast.success(`${files.length} file${files.length > 1 ? "s" : ""} queued for ingestion`);
      setTimeout(() => {
        getDocuments(kbId).then(setDocuments).catch(() => {});
        qc.invalidateQueries({ queryKey: ["kbs"] });
      }, 3000);
    } catch (e: unknown) {
      toast.error(extractErrorMessage(e, "Upload failed"));
    } finally {
      setUploading(false);
    }
  };

  const handleDeleted = (docId: string) => {
    setDocuments((prev) => prev.filter((d) => d.id !== docId));
  };

  return (
    <div className="page-shell space-y-6">
      <div className="grid gap-3 md:grid-cols-4">
        <Signal label="Text/PDF" value="PyMuPDF + DOCX" icon={FileText} />
        <Signal label="Images" value="OCR + CLIP" icon={FileImage} />
        <Signal label="Audio" value="Whisper timestamps" icon={FileAudio} />
        <Signal label="Linking" value="Semantic graph" icon={GitBranch} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-white">Ingestion pipeline</h2>
            <p className="mt-1 text-sm text-white/42">
              Upload once; NEXUS extracts modality-specific evidence, chunks it, embeds it, and
              connects related content in a searchable evidence network.
            </p>
          </div>
          <Dropzone onFiles={handleFiles} disabled={uploading} />
        </div>

        <div className="section-panel rounded-lg p-5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-white/82">Document registry</h3>
              <p className="text-xs text-white/34">Ready files become available for governed search.</p>
            </div>
            <DatabaseZap className="h-5 w-5 text-teal-300" />
          </div>
          <DocumentTable documents={documents} onDeleted={handleDeleted} />
        </div>
      </div>

      {activeJobs.length > 0 && (
        <div className="section-panel rounded-lg p-5">
          <h3 className="mb-3 text-sm font-medium text-white/50">Ingestion progress</h3>
          <JobProgressList jobs={activeJobs} />
        </div>
      )}
    </div>
  );
}

function Signal({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string;
  icon: React.ElementType;
}) {
  return (
    <div className="section-panel rounded-lg p-4">
      <Icon className="h-4 w-4 text-teal-300" />
      <p className="mt-3 text-sm font-medium text-white/80">{label}</p>
      <p className="mt-1 text-xs text-white/36">{value}</p>
    </div>
  );
}
