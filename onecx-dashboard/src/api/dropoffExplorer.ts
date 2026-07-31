import { apiFetch } from "@/api/client";
import type { DropoffSummary, DropoffVisitor, PaginatedResponse } from "@/types/api";
import type { DateRangeParams } from "@/types/params";

export type StepPickerParams = DateRangeParams & {
  from_step: string;
  to_step: string;
};

export function getDropoffSummary(params: StepPickerParams): Promise<DropoffSummary> {
  return apiFetch<DropoffSummary>("/dropoff-explorer/summary", { params });
}

export type GetDropoffVisitorsParams = StepPickerParams & {
  page?: number;
  page_size?: number;
};

export function getDropoffVisitors(
  params: GetDropoffVisitorsParams
): Promise<PaginatedResponse<DropoffVisitor>> {
  return apiFetch<PaginatedResponse<DropoffVisitor>>("/dropoff-explorer/visitors", { params });
}
