import { apiClient } from "./client";
import { mockApi, useMockApi } from "./mock";
import type {
  TokenResponse, User, LoginRequest, RegisterRequest, ChangePasswordRequest,
} from "../types/api";

type ApiUser = Omit<User, "id">;

export async function login(data: LoginRequest): Promise<TokenResponse> {
  if (useMockApi) return mockApi.login(data);

  const form = new URLSearchParams();
  form.append("username", data.username);
  form.append("password", data.password);
  const res = await apiClient.post<TokenResponse>("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return res.data;
}

export async function register(data: RegisterRequest): Promise<User> {
  if (useMockApi) return mockApi.register();

  const res = await apiClient.post<User>("/auth/register", data);
  return res.data;
}

export async function getMe(): Promise<User> {
  if (useMockApi) return mockApi.getMe();

  const res = await apiClient.get<ApiUser>("/auth/me");
  return { ...res.data, id: res.data.user_id };
}

export async function changePassword(data: ChangePasswordRequest): Promise<void> {
  if (useMockApi) return mockApi.changePassword();

  await apiClient.post("/auth/change-password", data);
}
