import { apiFetch } from "@/api/client";
import type { UserListResponse } from "@/types/api";

export function createMember(
  username: string,
  password: string
): Promise<{ message: string; username: string }> {
  return apiFetch("/admin/users", { method: "POST", body: { username, password } });
}

export function resetMemberPassword(
  username: string,
  new_password: string
): Promise<{ message: string }> {
  return apiFetch(`/admin/users/${encodeURIComponent(username)}/password`, {
    method: "PATCH",
    body: { new_password },
  });
}

export function listUsers(): Promise<UserListResponse> {
  return apiFetch<UserListResponse>("/admin/users");
}
