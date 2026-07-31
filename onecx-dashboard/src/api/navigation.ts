import { apiFetch } from "@/api/client";
import type { NavigationOverviewResponse } from "@/types/api";
import type { DateRangeParams } from "@/types/params";

export function getNavigationOverview(
  params: DateRangeParams = {}
): Promise<NavigationOverviewResponse> {
  return apiFetch<NavigationOverviewResponse>("/navigation/overview", { params });
}
