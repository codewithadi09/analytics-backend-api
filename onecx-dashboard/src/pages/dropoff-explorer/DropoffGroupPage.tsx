import { useState } from "react";
import { Link } from "react-router-dom";
import { getFormDropoffOverview } from "@/api/formDropoff";
import { getDropoffSummary, getDropoffVisitors } from "@/api/dropoffExplorer";
import { getFilterOptions } from "@/api/filters";
import { useApiData } from "@/hooks/useApiData";
import { DateRangeFilter } from "@/components/ui/DateRangeFilter";
import { Pagination } from "@/components/ui/Pagination";
import { StatCard, SectionHeading, DataTable, ErrorState, EmptyState } from "@/components/ui/DataDisplay";
import { SkeletonTable, SkeletonBlock } from "@/components/ui/Skeleton";
import { HorizontalBarChart } from "@/components/charts/HorizontalBarChart";
import type { DateRangeParams } from "@/types/params";
import { FUNNEL_STEPS, FUNNEL_STEP_LABELS, type FieldDropoff, type DropoffVisitor, type FunnelStep } from "@/types/api";

export function DropoffGroupPage() {
  const [range, setRange] = useState<DateRangeParams>({});
  const { data: filters } = useApiData(() => getFilterOptions(), []);

  return (
    <div className="page-container-wide">
      <div className="page-header">
        <h1 className="page-title">Drop-off Group</h1>
      </div>

      <div className="mb-8">
        <DateRangeFilter
          value={range}
          onChange={setRange}
          earliest={filters?.date_range.earliest_event}
          latest={filters?.date_range.latest_event}
        />
      </div>

      {/* 1. Form Field Drop-off — static table, no interaction needed */}
      <div className="mb-10">
        <SectionHeading>Form field drop-off</SectionHeading>
        <FormFieldDropoffTable range={range} />
      </div>

      {/* 2 & 3. Step-picker, then summary + visitor list once both steps are chosen */}
      <div>
        <SectionHeading>Drop-off explorer</SectionHeading>
        <DropoffExplorer range={range} />
      </div>
    </div>
  );
}

function FormFieldDropoffTable({ range }: { range: DateRangeParams }) {
  const { data, isLoading, error, refetch } = useApiData(
    () => getFormDropoffOverview(range),
    [range.start_date, range.end_date]
  );

  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (isLoading || !data) return <SkeletonBlock className="h-48 w-full" />;

  return (
    <div className="space-y-4">
      {data.most_common_dropoff_field && (
        <p className="text-sm text-zinc-500">
          Most visitors give up at{" "}
          <span className="font-medium text-zinc-900">{data.most_common_dropoff_field}</span>.
        </p>
      )}
      {data.fields.length > 0 && (
        <HorizontalBarChart
          data={data.fields.map((f) => ({ label: f.field_name, value: f.dropoff_pct }))}
          valueFormatter={(v) => `${v}%`}
        />
      )}
      <DataTable<FieldDropoff>
        rowKey={(r) => r.field_name}
        emptyMessage="No form field data found for this range."
        columns={[
          { key: "field", header: "Field", accessor: (r) => r.field_name },
          { key: "focus", header: "Focused", numeric: true, accessor: (r) => r.focus_count.toLocaleString() },
          { key: "complete", header: "Completed", numeric: true, accessor: (r) => r.complete_count.toLocaleString() },
          { key: "error", header: "Errors", numeric: true, accessor: (r) => r.error_count.toLocaleString() },
          { key: "dropoff", header: "Drop-off", numeric: true, accessor: (r) => `${r.dropoff_pct}%` },
          {
            key: "time",
            header: "Avg. fill time",
            numeric: true,
            accessor: (r) => (r.avg_time_seconds != null ? `${r.avg_time_seconds}s` : "—"),
          },
        ]}
        rows={data.fields}
      />
    </div>
  );
}

function DropoffExplorer({ range }: { range: DateRangeParams }) {
  const [fromStep, setFromStep] = useState<FunnelStep | "">("");
  const [toStep, setToStep] = useState<FunnelStep | "">("");
  const [page, setPage] = useState(1);

  const fromIndex = fromStep ? FUNNEL_STEPS.indexOf(fromStep) : -1;
  const toIndex = toStep ? FUNNEL_STEPS.indexOf(toStep) : -1;
  const stepsChosen = fromStep !== "" && toStep !== "";
  const stepsValid = stepsChosen && fromIndex < toIndex;

  const eligibleToSteps = fromStep ? FUNNEL_STEPS.filter((_, i) => i > fromIndex) : FUNNEL_STEPS;

  const {
    data: summary,
    isLoading: summaryLoading,
    error: summaryError,
    refetch: refetchSummary,
  } = useApiData(
    () =>
      stepsValid
        ? getDropoffSummary({ from_step: fromStep, to_step: toStep, ...range })
        : Promise.resolve(null),
    [fromStep, toStep, stepsValid, range.start_date, range.end_date]
  );

  const {
    data: visitors,
    isLoading: visitorsLoading,
    error: visitorsError,
    refetch: refetchVisitors,
  } = useApiData(
    () =>
      stepsValid
        ? getDropoffVisitors({ from_step: fromStep, to_step: toStep, page, page_size: 25, ...range })
        : Promise.resolve(null),
    [fromStep, toStep, stepsValid, page, range.start_date, range.end_date]
  );

  return (
    <div className="space-y-6">
      <div className="card flex flex-wrap items-end gap-4 !p-4">
        <div>
          <label className="field-label" htmlFor="from_step">
            From step
          </label>
          <select
            id="from_step"
            className="input !w-56"
            value={fromStep}
            onChange={(e) => {
              const next = e.target.value as FunnelStep | "";
              setFromStep(next);
              // Reset an invalid to_step (one that no longer comes after from_step).
              if (toStep && next && FUNNEL_STEPS.indexOf(toStep) <= FUNNEL_STEPS.indexOf(next)) {
                setToStep("");
              }
              setPage(1);
            }}
          >
            <option value="">Select a step…</option>
            {FUNNEL_STEPS.map((step) => (
              <option key={step} value={step}>
                {FUNNEL_STEP_LABELS[step]}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="field-label" htmlFor="to_step">
            To step
          </label>
          <select
            id="to_step"
            className="input !w-56"
            value={toStep}
            disabled={!fromStep}
            onChange={(e) => {
              setToStep(e.target.value as FunnelStep | "");
              setPage(1);
            }}
          >
            <option value="">Select a step…</option>
            {eligibleToSteps.map((step) => (
              <option key={step} value={step}>
                {FUNNEL_STEP_LABELS[step]}
              </option>
            ))}
          </select>
        </div>
      </div>

      {!stepsChosen && (
        <EmptyState message="Choose a from-step and to-step to see who dropped off between them." />
      )}

      {stepsChosen && !stepsValid && (
        <p className="text-sm text-red-600">
          "From" step must come before "to" step in the funnel — choose an earlier from-step or a later to-step.
        </p>
      )}

      {stepsValid && (
        <div className="space-y-6">
          {summaryError && <ErrorState message={summaryError} onRetry={refetchSummary} />}
          {!summaryError && summaryLoading && (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <StatCard label="Total drop-off" value="…" />
            </div>
          )}
          {!summaryError && !summaryLoading && summary && (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <StatCard
                label="Total drop-off"
                value={summary.total_dropoff.toLocaleString()}
                hint={`${FUNNEL_STEP_LABELS[fromStep as FunnelStep]} → ${FUNNEL_STEP_LABELS[toStep as FunnelStep]}`}
              />
            </div>
          )}

          <div>
            {visitorsError && <ErrorState message={visitorsError} onRetry={refetchVisitors} />}
            {!visitorsError && visitorsLoading && <SkeletonTable rows={6} />}
            {!visitorsError && !visitorsLoading && visitors && (
              <>
                <DataTable<DropoffVisitor>
                  rowKey={(r) => r.anonymous_id}
                  emptyMessage="No visitors dropped off between these steps for this range."
                  columns={[
                    {
                      key: "id",
                      header: "Visitor",
                      accessor: (r) => (
                        <Link to={`/journey/${encodeURIComponent(r.anonymous_id)}`} className="text-accent-700 hover:underline">
                          {r.anonymous_id}
                        </Link>
                      ),
                    },
                    { key: "action", header: "Last known action", accessor: (r) => r.last_known_action },
                    {
                      key: "seen",
                      header: "Last seen",
                      accessor: (r) => new Date(r.last_seen).toLocaleString(),
                    },
                  ]}
                  rows={visitors.items}
                />
                <Pagination meta={visitors.meta} onPageChange={setPage} />
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
