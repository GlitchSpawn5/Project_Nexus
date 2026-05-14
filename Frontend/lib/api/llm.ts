import { apiClient } from "./client";
import { mockApi, useMockApi } from "./mock";
import type { LLMStatus, ProviderStatus } from "../types/api";

interface RawProviderStatus {
  configured?: boolean;
  status?: string;
}

interface RawLLMStatus extends Omit<LLMStatus, "providers"> {
  providers?: Record<string, RawProviderStatus>;
}

export async function getLLMStatus(): Promise<LLMStatus> {
  if (useMockApi) return mockApi.getLLMStatus();

  const res = await apiClient.get<RawLLMStatus>("/llm/status");
  const raw = res.data;
  const providers: ProviderStatus[] = Object.entries(raw.providers ?? {}).map(
    ([name, cfg]) => ({
      provider: name,
      available: cfg.status === "ok",
      configured: cfg.configured ?? false,
      status: cfg.status ?? "not_tested",
    })
  );
  return { ...raw, providers };
}
