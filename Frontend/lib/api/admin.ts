import { apiClient } from "./client";
import { mockApi, useMockApi } from "./mock";
import type { AdminUser, UsageStats, UserRole } from "../types/api";

type ApiAdminUser = Omit<AdminUser, "id">;

export async function listUsers(): Promise<AdminUser[]> {
  if (useMockApi) return mockApi.listUsers();

  const res = await apiClient.get<ApiAdminUser[]>("/admin/users");
  return res.data.map((u) => ({ ...u, id: u.user_id }));
}

export async function setUserRole(userId: string, role: UserRole): Promise<void> {
  if (useMockApi) return;

  await apiClient.patch(`/admin/users/${userId}/role`, { role });
}

export async function deactivateUser(userId: string): Promise<void> {
  if (useMockApi) return;

  await apiClient.patch(`/admin/users/${userId}/deactivate`);
}

export async function getUsageStats(): Promise<UsageStats> {
  if (useMockApi) return mockApi.getUsageStats();

  const res = await apiClient.get<UsageStats>("/admin/usage");
  return res.data;
}
