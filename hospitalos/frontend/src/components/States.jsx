// EmptyState and ErrorState — what to show when there is no data, or the backend is down.
import { Inbox, WifiOff } from "lucide-react";

export function EmptyState({ title = "Nothing here yet", message, action }) {
  return (
    <div className="card flex flex-col items-center gap-2 p-10 text-center">
      <Inbox size={28} className="text-ink-subtle" aria-hidden="true" />
      <p className="font-display font-semibold">{title}</p>
      {message && <p className="max-w-sm text-sm text-ink-muted">{message}</p>}
      {action}
    </div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="card flex flex-col items-center gap-3 border-critical/30 bg-critical-soft p-8 text-center" role="alert">
      <WifiOff size={28} className="text-critical" aria-hidden="true" />
      <p className="font-display font-semibold text-critical">Could not load data</p>
      <p className="max-w-md text-sm text-ink-muted">{message}</p>
      {onRetry && <button className="btn-ghost" onClick={onRetry}>Try again</button>}
    </div>
  );
}
