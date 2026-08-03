import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

export interface DonutDatum {
  label: string;
  value: number;
}

// One accent + a small zinc ramp — never a rainbow palette, per design guide rule 8.
const SLICE_COLORS = ["#4f46e5", "#a5b4fc", "#d4d4d8", "#e4e4e7", "#f4f4f5"];

export function DonutChart({
  data,
  valueFormatter = (v: number) => v.toLocaleString(),
}: {
  data: DonutDatum[];
  valueFormatter?: (value: number) => string;
}) {
  const total = data.reduce((sum, d) => sum + d.value, 0);

  return (
    <div className="card flex flex-col items-center gap-4 !p-4 sm:flex-row">
      <div className="h-44 w-44 shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="label"
              innerRadius="62%"
              outerRadius="100%"
              paddingAngle={data.length > 1 ? 2 : 0}
              stroke="none"
            >
              {data.map((_, i) => (
                <Cell key={i} fill={SLICE_COLORS[i % SLICE_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value, name) => {
                const numeric = typeof value === "number" ? value : Number(value);
                return [
                  `${valueFormatter(numeric)} (${total > 0 ? ((numeric / total) * 100).toFixed(1) : 0}%)`,
                  String(name),
                ];
              }}
              contentStyle={{ borderRadius: 8, border: "1px solid #e4e4e7", boxShadow: "none", fontSize: 12 }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <ul className="flex-1 space-y-2 text-sm">
        {data.map((d, i) => (
          <li key={d.label} className="flex items-center justify-between gap-4">
            <span className="flex items-center gap-2 text-zinc-600">
              <span
                className="h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: SLICE_COLORS[i % SLICE_COLORS.length] }}
              />
              {d.label}
            </span>
            <span className="tabular-nums text-zinc-900">
              {valueFormatter(d.value)}
              <span className="ml-1.5 text-xs text-zinc-400">
                ({total > 0 ? ((d.value / total) * 100).toFixed(0) : 0}%)
              </span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
