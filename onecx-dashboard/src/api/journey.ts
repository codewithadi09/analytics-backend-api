import { apiFetch } from "@/api/client";
import type { PaginatedResponse, UserJourneyResponse, VisitorSummary } from "@/types/api";

export type GetVisitorsParams = {
  search?: string;
  page?: number;
  page_size?: number;
};

export function getVisitors(
  params: GetVisitorsParams = {}
): Promise<PaginatedResponse<VisitorSummary>> {
  return apiFetch<PaginatedResponse<VisitorSummary>>("/journey/visitors", { params });
}

/**
 * No start_date/end_date here — this is the one confirmed, deliberate
 * exception in the whole API: the journey detail view only supports
 * sort_order (oldest/newest), never a date range. Do not "fix" this.
 */
export function getUserJourney(
  anonymousId: string,
  sortOrder: "asc" | "desc" = "asc"
): Promise<UserJourneyResponse> {
  return apiFetch<UserJourneyResponse>(`/journey/${encodeURIComponent(anonymousId)}`, {
    params: { sort_order: sortOrder },
  });
}
