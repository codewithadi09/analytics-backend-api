export interface FunnelStepDatum {
  label: string;
  users: number;
  dropoffPct: number;
  conversionFromTopPct: number;
}

/**
 * The single most important visualization in the project per the owner —
 * an actual narrowing funnel shape, not a table. Widths are proportional
 * to `conversionFromTopPct` so the visual taper reflects real drop-off,
 * not just relative step order.
 */
export function FunnelChart({ steps }: { steps: FunnelStepDatum[] }) {
  const MIN_WIDTH_PCT = 18; // even the smallest step stays visible/legible

  return (
    <div className="card flex flex-col items-center gap-3 !p-6">
      {steps.map((step, i) => {
        const widthPct = Math.max(step.conversionFromTopPct, MIN_WIDTH_PCT);
        // Each trapezoid's top matches the previous step's bottom width, so the
        // shape reads as one continuous funnel rather than disconnected bars.
        const prevWidthPct = i === 0 ? widthPct : Math.max(steps[i - 1].conversionFromTopPct, MIN_WIDTH_PCT);
        const topInset = (100 - prevWidthPct) / 2;
        const bottomInset = (100 - widthPct) / 2;

        return (
          <div key={step.label} className="w-full max-w-md">
            <div
              className="flex h-14 items-center justify-center bg-accent-600 text-center text-sm font-medium text-white"
              style={{
                clipPath: `polygon(${topInset}% 0%, ${100 - topInset}% 0%, ${100 - bottomInset}% 100%, ${bottomInset}% 100%)`,
                opacity: 1 - i * 0.08,
              }}
            >
              <div>
                <div>{step.label}</div>
                <div className="text-xs font-normal text-accent-50">{step.users.toLocaleString()} users</div>
              </div>
            </div>
            {i > 0 && (
              <div className="mt-1 text-center text-xs text-zinc-500">
                {step.dropoffPct > 0 ? (
                  <span className="text-red-600">−{step.dropoffPct}% drop-off</span>
                ) : (
                  <span>No drop-off</span>
                )}
                <span className="mx-1.5 text-zinc-300">·</span>
                <span>{step.conversionFromTopPct}% of top</span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
