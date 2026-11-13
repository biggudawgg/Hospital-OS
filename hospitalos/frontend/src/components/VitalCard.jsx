// VitalCard — one headline number on the dashboard (like a vital sign on a monitor).
export default function VitalCard({ label, value, icon: Icon, hint, tone = "primary" }) {
  const iconTone = {
    primary: "bg-primary-soft text-primary",
    warning: "bg-warning-soft text-warning",
    critical: "bg-critical-soft text-critical",
    info: "bg-info-soft text-info",
  }[tone];
  return (
    <div className="card flex items-start justify-between p-5">
      <div>
        <p className="text-sm font-medium text-ink-muted">{label}</p>
        <p className="num mt-2 text-3xl font-semibold text-ink">{value}</p>
        {hint && <p className="mt-1 text-xs text-ink-subtle">{hint}</p>}
      </div>
      {Icon && (
        <span className={`rounded-control p-2.5 ${iconTone}`}>
          <Icon size={20} aria-hidden="true" />
        </span>
      )}
    </div>
  );
}
