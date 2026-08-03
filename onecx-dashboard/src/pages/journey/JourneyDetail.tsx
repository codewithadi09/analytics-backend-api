import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getUserJourney } from "@/api/journey";
import { useApiData } from "@/hooks/useApiData";
import { StatCard, BooleanBadge, ErrorState } from "@/components/ui/DataDisplay";
import { SkeletonBlock, SkeletonTable } from "@/components/ui/Skeleton";
import type { JourneyEvent, JourneyEventCategory } from "@/types/api";

const CATEGORY_LABELS: Record<JourneyEventCategory, string> = {
  page_view: "Page view",
  click: "Click",
  form_activity: "Form activity",
};

function CategoryBadge({ category }: { category: JourneyEventCategory }) {
  const className = category === "form_activity" ? "badge-positive" : "badge-neutral";
  return <span className={className}>{CATEGORY_LABELS[category]}</span>;
}

export function JourneyDetail() {
  const { anonymousId = "" } = useParams();
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");

  const { data, isLoading, error, refetch } = useApiData(
    () => getUserJourney(anonymousId, sortOrder),
    [anonymousId, sortOrder]
  );

  const notFound = error === "No journey found for this visitor";

  return (
    <div className="page-container-wide">
      <div className="page-header">
        <div>
          <Link to="/journey" className="btn-text mb-1">
            ← Back to visitors
          </Link>
          <h1 className="page-title">Visitor journey</h1>
        </div>
        {data && (
          <select
            className="input !w-auto"
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value as "asc" | "desc")}
          >
            <option value="asc">Oldest first</option>
            <option value="desc">Newest first</option>
          </select>
        )}
      </div>

      {error && (
        <ErrorState
          message={notFound ? "No journey found for this visitor." : error}
          onRetry={notFound ? undefined : refetch}
        />
      )}

      {!error && isLoading && (
        <div className="space-y-6">
          <SkeletonBlock className="h-20 w-full" />
          <SkeletonTable rows={8} />
        </div>
      )}

      {!error && !isLoading && data && (
        <div className="space-y-6">
          <div className="card">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <div>
                <div className="text-sm font-medium text-zinc-900">
                  {data.resolved_identity?.name ?? data.resolved_identity?.email ?? data.anonymous_id}
                </div>
                <div className="text-xs text-zinc-400">{data.anonymous_id}</div>
              </div>
              <BooleanBadge value={data.has_converted} trueLabel="Converted" falseLabel="Not converted" />
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <StatCard label="Total events" value={data.total_events.toLocaleString()} />
              <StatCard label="Sessions" value={data.session_count.toLocaleString()} />
              <StatCard label="First seen" value={new Date(data.first_seen).toLocaleDateString()} />
              <StatCard label="Last seen" value={new Date(data.last_seen).toLocaleDateString()} />
            </div>
          </div>

          <div>
            <h2 className="mb-3 text-sm font-medium text-zinc-900">Timeline</h2>
            {data.events.length === 0 ? (
              <div className="card flex items-center justify-center py-10">
                <p className="empty-state">No events recorded.</p>
              </div>
            ) : (
              <ol className="card divide-y divide-zinc-100 !p-0">
                {data.events.map((event: JourneyEvent, i: number) => (
                  <li key={`${event.timestamp}-${i}`} className="flex items-start gap-3 p-3">
                    <CategoryBadge category={event.event_category} />
                    <div className="min-w-0 flex-1">
                      <div className="text-sm text-zinc-900">
                        {event.label ?? event.event_type}
                        {event.page_path && (
                          <span className="ml-2 text-xs text-zinc-400">{event.page_path}</span>
                        )}
                      </div>
                      <div className="text-xs text-zinc-400">{event.event_type}</div>
                    </div>
                    <div className="shrink-0 text-xs text-zinc-400 tabular-nums">
                      {new Date(event.timestamp).toLocaleString()}
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
