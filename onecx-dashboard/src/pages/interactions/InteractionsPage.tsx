import { useState, type ReactNode } from "react";
import { getInteractionLeaderboard, getInteractionEvents } from "@/api/interactions";
import { getNavigationOverview } from "@/api/navigation";
import { getFilterOptions } from "@/api/filters";
import { useApiData } from "@/hooks/useApiData";
import { DateRangeFilter } from "@/components/ui/DateRangeFilter";
import { Pagination } from "@/components/ui/Pagination";
import { StatCard, SectionHeading, DataTable, ErrorState, EmptyState } from "@/components/ui/DataDisplay";
import { SkeletonBlock, SkeletonStatGrid } from "@/components/ui/Skeleton";
import { Disclosure } from "@/components/ui/Disclosure";
import { HorizontalBarChart } from "@/components/charts/HorizontalBarChart";
import type { DateRangeParams } from "@/types/params";
import { INTERACTION_TYPES, type InteractionEvent, type ExitRateByPage } from "@/types/api";

const TOP_N = 8;

type Tab = "interactions" | "navigation";

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

export function InteractionsPage() {
  const [tab, setTab] = useState<Tab>("interactions");
  const [range, setRange] = useState<DateRangeParams>({});
  const { data: filters } = useApiData(() => getFilterOptions(), []);

  return (
    <div className="page-container-wide">
      <div className="page-header">
        <h1 className="page-title">Interactions & Navigation</h1>
      </div>

      <div className="mb-4 flex gap-6 border-b border-zinc-200">
        <TabButton active={tab === "interactions"} onClick={() => setTab("interactions")}>
          Interactions
        </TabButton>
        <TabButton active={tab === "navigation"} onClick={() => setTab("navigation")}>
          Navigation
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

      {tab === "interactions" ? (
        <InteractionsSection range={range} />
      ) : (
        <NavigationSection range={range} />
      )}
    </div>
  );
}

function InteractionsSection({ range }: { range: DateRangeParams }) {
  const [selectedType, setSelectedType] = useState<string>("");
  const [page, setPage] = useState(1);

  const {
    data: leaderboard,
    isLoading: leaderboardLoading,
    error: leaderboardError,
    refetch: refetchLeaderboard,
  } = useApiData(() => getInteractionLeaderboard(range), [range.start_date, range.end_date]);

  const {
    data: events,
    isLoading: eventsLoading,
    error: eventsError,
    refetch: refetchEvents,
  } = useApiData(
    () =>
      getInteractionEvents({
        ...range,
        interaction_type: selectedType || undefined,
        page,
        page_size: 25,
      }),
    [range.start_date, range.end_date, selectedType, page]
  );

  return (
    <div className="space-y-8">
      {leaderboardError && <ErrorState message={leaderboardError} onRetry={refetchLeaderboard} />}
      {!leaderboardError && leaderboardLoading && (
        <div className="space-y-6">
          <SkeletonStatGrid count={1} />
          <SkeletonBlock className="h-64 w-full" />
        </div>
      )}
      {!leaderboardError && !leaderboardLoading && leaderboard && (
        <>
          <div className="grid grid-cols-2 gap-3 sm:max-w-xs">
            <StatCard label="Total interactions" value={leaderboard.total_interactions.toLocaleString()} />
          </div>

          <div>
            <SectionHeading>Leaderboard by type</SectionHeading>
            {leaderboard.by_type.length === 0 ? (
              <EmptyState message="No interactions found for this range." />
            ) : (
              <>
                <HorizontalBarChart
                  data={leaderboard.by_type
                    .slice(0, TOP_N)
                    .map((t) => ({ label: t.interaction_type, value: t.count }))}
                />
                {leaderboard.by_type.length > TOP_N && (
                  <p className="mt-2 text-xs text-zinc-400">
                    +{leaderboard.by_type.length - TOP_N} more types not shown.
                  </p>
                )}
              </>
            )}
          </div>
        </>
      )}

      {/* Raw event log — secondary content, collapsed by default per design guide rule 7 */}
      <div>
        <div className="mb-3 flex items-center justify-between">
          <span className="text-sm font-medium text-zinc-900">Events</span>
          <select
            className="input !w-auto"
            value={selectedType}
            onChange={(e) => {
              setSelectedType(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All types</option>
            {INTERACTION_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        <Disclosure label="View raw events">
          {eventsError && <ErrorState message={eventsError} onRetry={refetchEvents} />}
          {!eventsError && eventsLoading && <SkeletonBlock className="h-40 w-full" />}
          {!eventsError && !eventsLoading && events && (
            <>
              <DataTable<InteractionEvent>
                rowKey={(r, i) => `${r.timestamp}-${r.interaction_type}-${i}`}
                emptyMessage="No events found."
                columns={[
                  { key: "type", header: "Type", accessor: (r) => r.interaction_type },
                  { key: "label", header: "Label", accessor: (r) => r.label ?? <span className="text-zinc-400">—</span> },
                  { key: "path", header: "Page", accessor: (r) => r.page_path ?? <span className="text-zinc-400">—</span> },
                  { key: "timestamp", header: "Time", accessor: (r) => new Date(r.timestamp).toLocaleString() },
                ]}
                rows={events.items}
              />
              <Pagination meta={events.meta} onPageChange={setPage} />
            </>
          )}
        </Disclosure>
      </div>
    </div>
  );
}

function NavigationSection({ range }: { range: DateRangeParams }) {
  const { data, isLoading, error, refetch } = useApiData(
    () => getNavigationOverview(range),
    [range.start_date, range.end_date]
  );

  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (isLoading || !data) {
    return (
      <div className="space-y-6">
        <SkeletonStatGrid count={1} />
        <SkeletonBlock className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-2 gap-3 sm:max-w-xs">
        <StatCard label="Avg. pages per session" value={data.average_pages_per_session.toFixed(2)} />
      </div>

      <div>
        <SectionHeading>Top navigation paths</SectionHeading>
        {data.top_paths.length === 0 ? (
          <EmptyState message="No navigation paths found for this range." />
        ) : (
          <>
            <HorizontalBarChart
              data={data.top_paths
                .slice(0, TOP_N)
                .map((p) => ({ label: p.steps.join(" → "), value: p.visitor_count }))}
              valueFormatter={(v) => `${v.toLocaleString()} sessions`}
            />
            {data.top_paths.length > TOP_N && (
              <p className="mt-2 text-xs text-zinc-400">
                Showing top {TOP_N} of {data.top_paths.length} paths.
              </p>
            )}
          </>
        )}
      </div>

      <div>
        <SectionHeading>Exit rates by page</SectionHeading>
        {data.exit_rates.length === 0 ? (
          <EmptyState message="No exit-rate data found for this range." />
        ) : (
          <>
            <HorizontalBarChart
              data={data.exit_rates
                .slice(0, TOP_N)
                .map((r) => ({ label: r.path, value: r.exit_rate_pct }))}
              valueFormatter={(v) => `${v}%`}
            />
            <div className="mt-3">
              <Disclosure label="View full exit-rate table">
                <DataTable<ExitRateByPage>
                  rowKey={(r) => r.path}
                  columns={[
                    { key: "path", header: "Page", accessor: (r) => r.path },
                    { key: "exits", header: "Exits", numeric: true, accessor: (r) => r.exits.toLocaleString() },
                    { key: "pct", header: "Exit rate", numeric: true, accessor: (r) => `${r.exit_rate_pct}%` },
                  ]}
                  rows={data.exit_rates}
                />
              </Disclosure>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
