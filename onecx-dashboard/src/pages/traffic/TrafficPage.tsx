import { useState } from "react";
import { getTrafficOverview } from "@/api/traffic";
import { getFilterOptions } from "@/api/filters";
import { useApiData } from "@/hooks/useApiData";
import { DateRangeFilter } from "@/components/ui/DateRangeFilter";
import { StatCard, SectionHeading, DataTable, ErrorState } from "@/components/ui/DataDisplay";
import { SkeletonBlock, SkeletonStatGrid } from "@/components/ui/Skeleton";
import { Disclosure } from "@/components/ui/Disclosure";
import { HorizontalBarChart } from "@/components/charts/HorizontalBarChart";
import { DonutChart } from "@/components/charts/DonutChart";
import type { DateRangeParams } from "@/types/params";
import type { TopPage } from "@/types/api";

const TOP_N = 8;

export function TrafficPage() {
  const [range, setRange] = useState<DateRangeParams>({});

  const { data: filters } = useApiData(() => getFilterOptions(), []);
  const {
    data: overview,
    isLoading,
    error,
    refetch,
  } = useApiData(() => getTrafficOverview(range), [range.start_date, range.end_date]);

  return (
    <div className="page-container-wide">
      <div className="page-header">
        <h1 className="page-title">Traffic & Overview</h1>
      </div>

      <div className="mb-6">
        <DateRangeFilter
          value={range}
          onChange={setRange}
          earliest={filters?.date_range.earliest_event}
          latest={filters?.date_range.latest_event}
        />
      </div>

      {error && <ErrorState message={error} onRetry={refetch} />}

      {!error && isLoading && (
        <div className="space-y-6">
          <SkeletonStatGrid count={2} />
          <SkeletonBlock className="h-64 w-full" />
        </div>
      )}

      {!error && !isLoading && overview && (
        <div className="space-y-8">
          {/* Only the two non-redundant top-line KPIs — mobile/desktop live in the device chart below. */}
          <div className="grid grid-cols-2 gap-3 sm:max-w-sm">
            <StatCard label="Total page views" value={overview.total_page_views.toLocaleString()} />
            <StatCard label="Unique visitors" value={overview.unique_visitors.toLocaleString()} />
          </div>

          <div>
            <SectionHeading>Top pages</SectionHeading>
            {overview.top_pages.length === 0 ? (
              <ErrorState message="No page views found for this range." />
            ) : (
              <>
                <HorizontalBarChart
                  data={overview.top_pages.slice(0, TOP_N).map((p) => ({ label: p.path, value: p.views }))}
                />
                {overview.top_pages.length > TOP_N && (
                  <p className="mt-2 text-xs text-zinc-400">
                    Showing top {TOP_N} of {overview.top_pages.length} pages.
                  </p>
                )}
                <div className="mt-3">
                  <Disclosure label="View full page list">
                    <DataTable<TopPage>
                      rowKey={(r) => r.path}
                      columns={[
                        { key: "path", header: "Page", accessor: (r) => r.path },
                        {
                          key: "views",
                          header: "Views",
                          numeric: true,
                          accessor: (r) => r.views.toLocaleString(),
                        },
                      ]}
                      rows={overview.top_pages}
                    />
                  </Disclosure>
                </div>
              </>
            )}
          </div>

          <div>
            <SectionHeading>Device breakdown</SectionHeading>
            <DonutChart
              data={[
                { label: "Mobile", value: overview.device_breakdown.mobile },
                { label: "Desktop", value: overview.device_breakdown.desktop },
                { label: "Unknown", value: overview.device_breakdown.unknown },
              ]}
            />
          </div>

          <div>
            <SectionHeading>Platform breakdown</SectionHeading>
            {overview.platform_breakdown.length === 0 ? (
              <ErrorState message="No platform data found for this range." />
            ) : (
              <HorizontalBarChart
                data={overview.platform_breakdown.map((p) => ({ label: p.platform, value: p.views }))}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
