export function SkeletonBlock({ className = "" }: { className?: string }) {
  return <div className={`skeleton ${className}`} />;
}

export function SkeletonCard() {
  return (
    <div className="card-compact">
      <SkeletonBlock className="mb-2 h-3 w-20" />
      <SkeletonBlock className="h-6 w-16" />
    </div>
  );
}

export function SkeletonStatGrid({ count = 4 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}

export function SkeletonTable({ rows = 6 }: { rows?: number }) {
  return (
    <div className="card overflow-hidden !p-0">
      <div className="border-b border-zinc-200 bg-zinc-50 p-3">
        <SkeletonBlock className="h-3 w-32" />
      </div>
      <div className="divide-y divide-zinc-100">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex items-center gap-4 p-3">
            <SkeletonBlock className="h-3 w-1/3" />
            <SkeletonBlock className="h-3 w-1/4" />
            <SkeletonBlock className="ml-auto h-3 w-12" />
          </div>
        ))}
      </div>
    </div>
  );
}
