import { apiFetch } from "@/api/client";
import type { InteractionEvent, InteractionLeaderboardResponse, PaginatedResponse } from "@/types/api";
import type { DateRangeParams } from "@/types/params";

export function getInteractionLeaderboard(
  params: DateRangeParams = {}
): Promise<InteractionLeaderboardResponse> {
  return apiFetch<InteractionLeaderboardResponse>("/interactions/leaderboard", { params });
}

export type GetInteractionEventsParams = DateRangeParams & {
  interaction_type?: string;
  page?: number;
  page_size?: number;
};

export function getInteractionEvents(
  params: GetInteractionEventsParams = {}
): Promise<PaginatedResponse<InteractionEvent>> {
  return apiFetch<PaginatedResponse<InteractionEvent>>("/interactions/events", { params });
}
