import { apiFetch } from "@/api/client";
import type { FilterOptionsResponse } from "@/types/api";

export function getFilterOptions(): Promise<FilterOptionsResponse> {
  return apiFetch<FilterOptionsResponse>("/filters");
}
