import type { DateRangeParams } from "@/types/params";

export function DateRangeFilter({
  value,
  onChange,
  earliest,
  latest,
}: {
  value: DateRangeParams;
  onChange: (next: DateRangeParams) => void;
  /** From GET /filters — bounds the date pickers to the range real data actually exists in. */
  earliest?: string;
  latest?: string;
}) {
  const hasFilter = Boolean(value.start_date || value.end_date);

  return (
    <div className="flex flex-wrap items-end gap-3">
      <div>
        <label className="field-label" htmlFor="start_date">
          From
        </label>
        <input
          id="start_date"
          type="date"
          className="input"
          min={earliest}
          max={value.end_date ?? latest}
          value={value.start_date ?? ""}
          onChange={(e) => onChange({ ...value, start_date: e.target.value || undefined })}
        />
      </div>
      <div>
        <label className="field-label" htmlFor="end_date">
          To
        </label>
        <input
          id="end_date"
          type="date"
          className="input"
          min={value.start_date ?? earliest}
          max={latest}
          value={value.end_date ?? ""}
          onChange={(e) => onChange({ ...value, end_date: e.target.value || undefined })}
        />
      </div>
      {hasFilter && (
        <button className="btn-text mb-2" onClick={() => onChange({})}>
          Clear
        </button>
      )}
    </div>
  );
}
