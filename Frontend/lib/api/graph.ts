import { apiClient } from "./client";
import { mockApi, useMockApi } from "./mock";
import type { GraphData, GraphStats } from "../types/api";

interface ChainResponse {
  nodes?: GraphData["nodes"];
  edges?: GraphData["links"];
  links?: GraphData["links"];
}

export async function getGraph(kbId: string): Promise<GraphData> {
  if (useMockApi) return mockApi.getGraph();

  const res = await apiClient.get<GraphData>(`/graph/${kbId}`);
  return res.data;
}

export async function getChain(chunkId: string): Promise<GraphData> {
  if (useMockApi) return mockApi.getGraph();

  const res = await apiClient.get<ChainResponse>(`/graph/chain/${chunkId}`);
  const data = res.data;
  return {
    nodes: data.nodes ?? [],
    links: data.edges ?? data.links ?? [],
  };
}

export async function getGraphStats(kbId: string): Promise<GraphStats> {
  if (useMockApi) return mockApi.getGraphStats();

  const res = await apiClient.get<GraphStats>(`/graph/${kbId}/stats`);
  return res.data;
}
