import type { ReactNode } from "react";

export function StatCard({ label, value, hint }: { label: string; value: ReactNode; hint?: string }) {
  return (
    <div className="card-compact">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="mt-1 text-xl font-medium tabular-nums text-zinc-900">{value}</div>
      {hint && <div className="mt-0.5 text-xs text-zinc-400">{hint}</div>}
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="card flex items-center justify-center py-10">
      <p className="empty-state">{message}</p>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="card flex flex-col items-center justify-center gap-3 py-10 text-center">
      <p className="text-sm text-red-600">{message}</p>
      {onRetry && (
        <button className="btn-secondary" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

export function SectionHeading({ children }: { children: ReactNode }) {
  return <h2 className="mb-3 text-sm font-medium text-zinc-900">{children}</h2>;
}

export function BooleanBadge({ value, trueLabel = "Yes", falseLabel = "No" }: { value: boolean; trueLabel?: string; falseLabel?: string }) {
  return (
    <span className={value ? "badge-positive" : "badge-neutral"}>
      {value ? trueLabel : falseLabel}
    </span>
  );
}

interface TableColumn<T> {
  header: string;
  accessor: (row: T) => ReactNode;
  numeric?: boolean;
  key: string;
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  emptyMessage = "No data found.",
}: {
  columns: TableColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  emptyMessage?: string;
}) {
  if (rows.length === 0) return <EmptyState message={emptyMessage} />;

  return (
    <div className="card overflow-x-auto !p-0">
      <table className="w-full text-sm">
        <thead>
          <tr className="table-head-row">
            {columns.map((col) => (
              <th
                key={col.key}
                className={`table-head-cell ${col.numeric ? "text-right" : ""}`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={rowKey(row)} className="table-body-row">
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={`table-body-cell ${col.numeric ? "table-numeric" : ""}`}
                >
                  {col.accessor(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
