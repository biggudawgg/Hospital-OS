// SkeletonCard — grey pulsing placeholder shown while data is loading.
export default function SkeletonCard({ lines = 3, className = "" }) {
  return (
    <div className={`card animate-pulse p-5 ${className}`} aria-hidden="true">
      <div className="h-3 w-1/3 rounded bg-line" />
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="mt-3 h-3 rounded bg-line/70" style={{ width: `${90 - i * 15}%` }} />
      ))}
    </div>
  );
}

/** A grid of skeleton cards (used for whole-page loading). */
export function SkeletonGrid({ count = 4, className = "grid gap-4 sm:grid-cols-2 lg:grid-cols-4" }) {
  return (
    <div className={className} role="status" aria-label="Loading">
      {Array.from({ length: count }).map((_, i) => <SkeletonCard key={i} />)}
    </div>
  );
}
