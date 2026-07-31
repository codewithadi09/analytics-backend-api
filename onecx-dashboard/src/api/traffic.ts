import { apiFetch } from "@/api/client";
import type { TrafficOverviewResponse } from "@/types/api";
import type { DateRangeParams } from "@/types/params";

export function getTrafficOverview(params: DateRangeParams = {}): Promise<TrafficOverviewResponse> {
  return apiFetch<TrafficOverviewResponse>("/traffic/overview", { params });
}
