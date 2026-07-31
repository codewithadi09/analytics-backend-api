import { apiFetch } from "@/api/client";
import type { LoginResponse } from "@/types/api";

export function login(username: string, password: string): Promise<LoginResponse> {
  return apiFetch<LoginResponse>("/auth/login", {
    method: "POST",
    body: { username, password },
    skipAuth: true,
  });
}

export function changeOwnPassword(
  current_password: string,
  new_password: string
): Promise<{ message: string }> {
  return apiFetch("/auth/me/password", {
    method: "PATCH",
    body: { current_password, new_password },
  });
}
