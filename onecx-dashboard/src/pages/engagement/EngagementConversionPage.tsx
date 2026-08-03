import { useMemo, useState, type ReactNode } from "react";
import { getEngagementOverview } from "@/api/engagement";
import { getConversionFunnel } from "@/api/conversion";
import { getFilterOptions } from "@/api/filters";
import { useApiData } from "@/hooks/useApiData";
import { DateRangeFilter } from "@/components/ui/DateRangeFilter";
import { SectionHeading, DataTable, ErrorState, EmptyState } from "@/components/ui/DataDisplay";
import { SkeletonBlock } from "@/components/ui/Skeleton";
import { Disclosure } from "@/components/ui/Disclosure";
import { HorizontalBarChart } from "@/components/charts/HorizontalBarChart";
import { FunnelChart } from "@/components/charts/FunnelChart";
import type { DateRangeParams } from "@/types/params";
import type { PageEngagement, ContentEngagementItem, EngagementMilestoneBucket } from "@/types/api";

type Tab = "engagement" | "conversion";

function TabButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={
        active
          ? "border-b-2 border-zinc-900 px-1 pb-2 text-sm font-medium text-zinc-900"
          : "border-b-2 border-transparent px-1 pb-2 text-sm text-zinc-500 hover:text-zinc-700"
      }
    >
      {children}
    </button>
  );
}

export function EngagementConversionPage() {
  const [tab, setTab] = useState<Tab>("engagement");
  const [range, setRange] = useState<DateRangeParams>({});
  const { data: filters } = useApiData(() => getFilterOptions(), []);

  return (
    <div className="page-container-wide">
      <div className="page-header">
        <h1 className="page-title">Engagement & Conversion</h1>
      </div>

      <div className="mb-4 flex gap-6 border-b border-zinc-200">
        <TabButton active={tab === "engagement"} onClick={() => setTab("engagement")}>
          Engagement
        </TabButton>
        <TabButton active={tab === "conversion"} onClick={() => setTab("conversion")}>
          Conversion Funnel
        </TabButton>
      </div>

      <div className="mb-6">
        <DateRangeFilter
          value={range}
          onChange={setRange}
          earliest={filters?.date_range.earliest_event}
          latest={filters?.date_range.latest_event}
        />
      </div>

      {tab === "engagement" ? <EngagementSection range={range} /> : <ConversionSection range={range} />}
    </div>
  );
}

const KNOWN_MILESTONES = [30, 60, 120, 180];

/**
 * Buckets raw milestone_seconds values into the 4 originally-intended
 * RudderStack milestones (30/60/120/180) plus a single "180s+" overflow
 * bucket for anything beyond. The backend has been observed returning
 * many more distinct values than expected (possibly a genuine data/query
 * issue worth revisiting server-side) — this bucketing is a frontend-side
 * mitigation regardless of that root cause, since the chart should never
 * render more than a handful of bars for this metric.
 */
function bucketMilestones(rows: EngagementMilestoneBucket[]): { label: string; value: number }[] {
  const buckets = new Map<string, number>([
    ["30s", 0],
    ["60s", 0],
    ["2m", 0],
    ["3m", 0],
    ["3m+", 0],
  ]);
  const labelFor = (seconds: number): string => {
    if (seconds === 30) return "30s";
    if (seconds === 60) return "60s";
    if (seconds === 120) return "2m";
    if (seconds === 180) return "3m";
    return "3m+";
  };
  for (const row of rows) {
    const label = labelFor(row.milestone_seconds);
    buckets.set(label, (buckets.get(label) ?? 0) + row.visit_count);
  }
  return Array.from(buckets.entries()).map(([label, value]) => ({ label, value }));
}

function EngagementSection({ range }: { range: DateRangeParams }) {
  const { data, isLoading, error, refetch } = useApiData(
    () => getEngagementOverview(range),
    [range.start_date, range.end_date]
  );

  const milestoneChartData = useMemo(
    () => (data ? bucketMilestones(data.milestone_breakdown) : []),
    [data]
  );

  const topPagesByEngagement = useMemo(() => {
    if (!data) return [];
    return [...data.page_engagement]
      .sort((a, b) => b.engaged_visit_count - a.engaged_visit_count)
      .slice(0, 5)
      .map((p) => ({ label: p.path, value: p.engaged_visit_count }));
  }, [data]);

  const hasUnexpectedMilestones = data?.milestone_breakdown.some(
    (b) => !KNOWN_MILESTONES.includes(b.milestone_seconds)
  );

  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (isLoading || !data) {
    return (
      <div className="space-y-6">
        <SkeletonBlock className="h-48 w-full" />
        <SkeletonBlock className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <SectionHeading>Engagement milestones</SectionHeading>
        {data.milestone_breakdown.length === 0 ? (
          <EmptyState message="No engagement milestones recorded for this range." />
        ) : (
          <>
            <HorizontalBarChart data={milestoneChartData} valueFormatter={(v) => `${v.toLocaleString()} visits`} />
            {hasUnexpectedMilestones && (
              <p className="mt-2 text-xs text-zinc-400">
                Bucketed from raw milestone values — the API is returning additional distinct values beyond the
                expected 30/60/120/180s, worth a backend check.
              </p>
            )}
          </>
        )}
      </div>

      {topPagesByEngagement.length > 0 && (
        <div>
          <SectionHeading>Top pages by engaged visits</SectionHeading>
          <HorizontalBarChart data={topPagesByEngagement} valueFormatter={(v) => `${v.toLocaleString()} visits`} />
        </div>
      )}

      <div>
        <SectionHeading>Page engagement</SectionHeading>
        <DataTable<PageEngagement>
          rowKey={(r) => r.path}
          emptyMessage="No page engagement data found for this range."
          columns={[
            { key: "path", header: "Page", accessor: (r) => r.path },
            { key: "views", header: "Views", numeric: true, accessor: (r) => r.views.toLocaleString() },
            { key: "avg", header: "Avg. scroll depth", numeric: true, accessor: (r) => `${r.avg_scroll_depth_pct}%` },
            {
              key: "median",
              header: "Median scroll depth",
              numeric: true,
              accessor: (r) => `${r.median_scroll_depth_pct}%`,
            },
            {
              key: "engaged",
              header: "Engaged visits",
              numeric: true,
              accessor: (r) => r.engaged_visit_count.toLocaleString(),
            },
          ]}
          rows={data.page_engagement}
        />
      </div>

      <div>
        <SectionHeading>Content engagement</SectionHeading>
        <DataTable<ContentEngagementItem>
          rowKey={(r, i) => `${r.content_type}-${r.label}-${i}`}
          emptyMessage="No blog or case study clicks found for this range."
          columns={[
            {
              key: "type",
              header: "Type",
              accessor: (r) => (
                <span className="badge-neutral capitalize">{r.content_type.replace("_", " ")}</span>
              ),
            },
            { key: "label", header: "Title", accessor: (r) => r.label },
            { key: "clicks", header: "Clicks", numeric: true, accessor: (r) => r.clicks.toLocaleString() },
          ]}
          rows={data.content_engagement}
        />
      </div>
    </div>
  );
}

function ConversionSection({ range }: { range: DateRangeParams }) {
  const { data, isLoading, error, refetch } = useApiData(
    () => getConversionFunnel(range),
    [range.start_date, range.end_date]
  );

  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (isLoading || !data) return <SkeletonBlock className="h-96 w-full" />;
  if (data.steps.length === 0) return <EmptyState message="No funnel data found for this range." />;

  return (
    <div>
      <SectionHeading>Conversion funnel</SectionHeading>
      <FunnelChart
        steps={data.steps.map((s) => ({
          label: s.step_name.replace(/_/g, " "),
          users: s.users,
          dropoffPct: s.dropoff_pct,
          conversionFromTopPct: s.conversion_from_top,
        }))}
      />
      <div className="mt-3">
        <Disclosure label="View step data as a table">
          <DataTable
            rowKey={(r) => r.step_name}
            columns={[
              { key: "step", header: "Step", accessor: (r) => r.step_name.replace(/_/g, " ") },
              { key: "users", header: "Users", numeric: true, accessor: (r) => r.users.toLocaleString() },
              { key: "dropoff", header: "Drop-off", numeric: true, accessor: (r) => `${r.dropoff_pct}%` },
              { key: "conv", header: "% of top", numeric: true, accessor: (r) => `${r.conversion_from_top}%` },
            ]}
            rows={data.steps}
          />
        </Disclosure>
      </div>
    </div>
  );
}
