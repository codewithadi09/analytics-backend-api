import { apiFetch } from "@/api/client";
import type { ConversionFunnelResponse } from "@/types/api";
import type { DateRangeParams } from "@/types/params";

export function getConversionFunnel(
  params: DateRangeParams = {}
): Promise<ConversionFunnelResponse> {
  return apiFetch<ConversionFunnelResponse>("/conversion/funnel", { params });
}
