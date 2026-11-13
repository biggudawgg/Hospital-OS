// StatusChip — small pill showing a state. Always icon + text (never colour alone).
import { AlertTriangle, CheckCircle2, Circle, Info, XCircle } from "lucide-react";

const TONES = {
  ok: { cls: "bg-ok-soft text-ok", Icon: CheckCircle2 },
  warning: { cls: "bg-warning-soft text-warning", Icon: AlertTriangle },
  critical: { cls: "bg-critical-soft text-critical", Icon: XCircle },
  info: { cls: "bg-info-soft text-info", Icon: Info },
  neutral: { cls: "bg-canvas text-ink-muted border border-line", Icon: Circle },
};

export default function StatusChip({ tone = "neutral", children }) {
  const { cls, Icon } = TONES[tone] || TONES.neutral;
  return (
    <span className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-semibold ${cls}`}>
      <Icon size={12} aria-hidden="true" />
      {children}
    </span>
  );
}

/** Map common status words from the database to a chip tone. */
export function toneFor(status = "") {
  const s = status.toLowerCase();
  if (["paid", "completed", "free", "connected", "in stock"].includes(s)) return "ok";
  if (["partial", "pending", "low stock", "scheduled"].includes(s)) return s === "scheduled" ? "info" : "warning";
  if (["unpaid", "cancelled", "failed", "critical", "out of stock"].includes(s)) return "critical";
  return "neutral";
}
