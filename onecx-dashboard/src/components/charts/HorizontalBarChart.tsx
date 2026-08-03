import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export interface HorizontalBarDatum {
  label: string;
  value: number;
}

const ACCENT = "#4f46e5"; // indigo-600, per design tokens — the one accent, reserved for the primary series
const AXIS_COLOR = "#71717a"; // zinc-500

function truncate(label: string, max = 28): string {
  return label.length > max ? `${label.slice(0, max - 1)}…` : label;
}

/**
 * Ranked/categorical count data → horizontal bar chart, per design guide rule 2.
 * Caps to topN (default 8) with the rest summarized by the caller via a
 * "+N more" affordance — this component only ever renders what it's given,
 * so callers slice their data before passing it in.
 */
export function HorizontalBarChart({
  data,
  height,
  valueFormatter = (v: number) => v.toLocaleString(),
}: {
  data: HorizontalBarDatum[];
  height?: number;
  valueFormatter?: (value: number) => string;
}) {
  const chartHeight = height ?? Math.max(data.length * 36 + 24, 120);

  return (
    <div className="card !p-4">
      <ResponsiveContainer width="100%" height={chartHeight}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, bottom: 4, left: 4 }}>
          <CartesianGrid horizontal={false} stroke="#f4f4f5" />
          <XAxis type="number" tick={{ fontSize: 12, fill: AXIS_COLOR }} axisLine={false} tickLine={false} />
          <YAxis
            type="category"
            dataKey="label"
            width={150}
            tick={{ fontSize: 12, fill: "#18181b" }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v: string) => truncate(v)}
          />
          <Tooltip
            cursor={{ fill: "#fafafa" }}
            formatter={(value) => valueFormatter(typeof value === "number" ? value : Number(value))}
            contentStyle={{
              borderRadius: 8,
              border: "1px solid #e4e4e7",
              boxShadow: "none",
              fontSize: 12,
            }}
          />
          <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={20}>
            {data.map((_, i) => (
              <Cell key={i} fill={ACCENT} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
