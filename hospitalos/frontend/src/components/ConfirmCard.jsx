// ConfirmCard — shown when the AI wants to CHANGE data. Nothing happens until the user clicks Yes.
import { ShieldAlert } from "lucide-react";

export default function ConfirmCard({ action, onAnswer, disabled }) {
  return (
    <div className="mt-2 rounded-control border border-warning/40 bg-warning-soft p-3" role="group" aria-label="Confirm action">
      <div className="flex items-center gap-2 text-sm font-semibold text-warning">
        <ShieldAlert size={16} aria-hidden="true" /> Confirmation needed
      </div>
      <p className="mt-1 text-sm">
        Run <code className="num font-semibold">{action.server}.{action.tool}</code> with:
      </p>
      <ul className="mt-1 text-sm text-ink-muted">
        {Object.entries(action.arguments).map(([k, v]) => (
          <li key={k}><span className="num">{k}</span> = <span className="num font-semibold text-ink">{String(v)}</span></li>
        ))}
      </ul>
      <div className="mt-3 flex gap-2">
        <button className="btn-primary" disabled={disabled} onClick={() => onAnswer("yes")}>Yes, do it</button>
        <button className="btn-ghost" disabled={disabled} onClick={() => onAnswer("no")}>No, cancel</button>
      </div>
    </div>
  );
}
