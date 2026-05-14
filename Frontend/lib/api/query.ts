import { apiClient } from "./client";
import { mockApi, useMockApi } from "./mock";
import type { QueryRequest, QueryResponse, QuerySession } from "../types/api";

interface QueryHistoryResponse {
  sessions?: Array<Omit<QuerySession, "id">>;
}

export async function ask(data: QueryRequest): Promise<QueryResponse> {
  if (useMockApi) return mockApi.ask(data);

  const res = await apiClient.post<QueryResponse>("/query/", data);
  return res.data;
}

export async function getQueryHistory(kbId: string): Promise<QuerySession[]> {
  if (useMockApi) return mockApi.getQueryHistory();

  const res = await apiClient.get<QueryHistoryResponse>("/query/history", {
    params: { kb_id: kbId },
  });
  const sessions = res.data?.sessions ?? [];
  return sessions.map((s) => ({ ...s, id: s.session_id }));
}
