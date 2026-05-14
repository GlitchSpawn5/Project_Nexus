import { apiClient } from "./client";
import { mockApi, useMockApi } from "./mock";
import type { KnowledgeBase, CreateKBRequest } from "../types/api";

export async function listKBs(): Promise<KnowledgeBase[]> {
  if (useMockApi) return mockApi.listKBs();

  const res = await apiClient.get<KnowledgeBase[]>("/kb/");
  return res.data;
}

export async function createKB(data: CreateKBRequest): Promise<KnowledgeBase> {
  if (useMockApi) return mockApi.createKB(data);

  const res = await apiClient.post<KnowledgeBase>("/kb/", data);
  return res.data;
}
