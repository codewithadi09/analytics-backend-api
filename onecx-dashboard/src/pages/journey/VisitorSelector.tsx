import { useState } from "react";
import { Link } from "react-router-dom";
import { getVisitors } from "@/api/journey";
import { useApiData } from "@/hooks/useApiData";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { DataTable, ErrorState } from "@/components/ui/DataDisplay";
import { Pagination } from "@/components/ui/Pagination";
import { SkeletonTable } from "@/components/ui/Skeleton";
import type { VisitorSummary } from "@/types/api";

export function VisitorSelector() {
  const [searchInput, setSearchInput] = useState("");
  const [page, setPage] = useState(1);
  const search = useDebouncedValue(searchInput);

  const { data, isLoading, error, refetch } = useApiData(
    () => getVisitors({ search: search || undefined, page, page_size: 25 }),
    [search, page]
  );

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">User Journey</h1>
      </div>

      <div className="mb-6">
        <label className="field-label" htmlFor="visitor_search">
          Search visitors
        </label>
        <input
          id="visitor_search"
          className="input"
          placeholder="Search by anonymous ID, email, or name…"
          value={searchInput}
          onChange={(e) => {
            setSearchInput(e.target.value);
            setPage(1);
          }}
        />
      </div>

      {error && <ErrorState message={error} onRetry={refetch} />}
      {!error && isLoading && <SkeletonTable rows={8} />}
      {!error && !isLoading && data && (
        <>
          <DataTable<VisitorSummary>
            rowKey={(r) => r.anonymous_id}
            emptyMessage="No visitors found. Try a different search."
            columns={[
              {
                key: "visitor",
                header: "Visitor",
                accessor: (r) => {
                  const identity = r.name ?? r.email;
                  return (
                    <Link
                      to={`/journey/${encodeURIComponent(r.anonymous_id)}`}
                      className="hover:underline"
                    >
                      {identity ? (
                        <span className="text-zinc-900">{identity}</span>
                      ) : (
                        <span className="font-mono text-xs text-zinc-400">{r.anonymous_id}</span>
                      )}
                    </Link>
                  );
                },
              },
              { key: "first_seen", header: "First seen", accessor: (r) => new Date(r.first_seen).toLocaleDateString() },
              { key: "last_seen", header: "Last seen", accessor: (r) => new Date(r.last_seen).toLocaleDateString() },
            ]}
            rows={data.items}
          />
          <Pagination meta={data.meta} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}
