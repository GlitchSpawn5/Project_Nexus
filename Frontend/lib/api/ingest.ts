import { apiClient } from "./client";
import { mockApi, useMockApi } from "./mock";
import type { UploadResponse, IngestionJob, Document, Transcript } from "../types/api";

export async function uploadFile(
  kbId: string,
  file: File,
  onProgress?: (pct: number) => void
): Promise<UploadResponse> {
  if (useMockApi) return mockApi.uploadFile(kbId, file, onProgress);

  const form = new FormData();
  form.append("file", file);
  // kb_id is a query param on the backend (Query(...)), not a form field
  const res = await apiClient.post<UploadResponse>(`/ingest/file?kb_id=${encodeURIComponent(kbId)}`, form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    },
  });
  return res.data;
}

export async function getJob(jobId: string): Promise<IngestionJob> {
  if (useMockApi) return mockApi.getJob(jobId);

  const res = await apiClient.get<IngestionJob>(`/ingest/jobs/${jobId}`);
  return res.data;
}

export async function getDocuments(kbId: string): Promise<Document[]> {
  if (useMockApi) return mockApi.getDocuments(kbId);

  const res = await apiClient.get<Document[]>(`/ingest/documents`, {
    params: { kb_id: kbId },
  });
  return res.data;
}

export async function deleteDocument(docId: string): Promise<void> {
  if (useMockApi) return mockApi.deleteDocument(docId);

  await apiClient.delete(`/ingest/${docId}`);
}

export async function getTranscript(docId: string): Promise<Transcript> {
  if (useMockApi) return mockApi.getTranscript(docId);

  const res = await apiClient.get<Transcript>(`/ingest/${docId}/transcript`);
  return res.data;
}
