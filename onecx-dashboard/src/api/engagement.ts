import { apiFetch } from "@/api/client";
import type { ServicesContentEngagementResponse } from "@/types/api";
import type { DateRangeParams } from "@/types/params";

export function getEngagementOverview(
  params: DateRangeParams = {}
): Promise<ServicesContentEngagementResponse> {
  return apiFetch<ServicesContentEngagementResponse>("/engagement/overview", { params });
}
