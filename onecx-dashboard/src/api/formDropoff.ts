import { apiFetch } from "@/api/client";
import type { FormFieldDropoffResponse } from "@/types/api";
import type { DateRangeParams } from "@/types/params";

export function getFormDropoffOverview(
  params: DateRangeParams = {}
): Promise<FormFieldDropoffResponse> {
  return apiFetch<FormFieldDropoffResponse>("/form-dropoff/overview", { params });
}
