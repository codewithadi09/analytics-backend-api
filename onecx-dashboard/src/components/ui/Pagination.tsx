import type { PaginationMeta } from "@/types/api";

export function Pagination({
  meta,
  onPageChange,
}: {
  meta: PaginationMeta;
  onPageChange: (page: number) => void;
}) {
  if (meta.total_pages <= 1) return null;

  return (
    <div className="mt-4 flex items-center justify-between text-sm text-zinc-500">
      <span>
        Page {meta.page} of {meta.total_pages} · {meta.total_items} total
      </span>
      <div className="flex gap-2">
        <button
          className="btn-secondary"
          disabled={meta.page <= 1}
          onClick={() => onPageChange(meta.page - 1)}
        >
          Previous
        </button>
        <button
          className="btn-secondary"
          disabled={meta.page >= meta.total_pages}
          onClick={() => onPageChange(meta.page + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
