// AlertPanel — list of alerts from /stats (ward nearly full, low stock, pending labs).
import StatusChip from "./StatusChip";

const LABEL = { critical: "Critical", warning: "Warning", info: "Info" };

export default function AlertPanel({ alerts = [] }) {
  return (
    <section className="card p-5" aria-labelledby="alerts-title">
      <h2 id="alerts-title" className="text-base font-semibold">Alerts</h2>
      {alerts.length === 0 ? (
        <p className="mt-3 text-sm text-ink-muted">No alerts right now.</p>
      ) : (
        <ul className="mt-3 divide-y divide-line">
          {alerts.map((a, i) => (
            <li key={i} className="flex items-start justify-between gap-3 py-2.5">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{a.title}</p>
                <p className="text-xs text-ink-muted">{a.detail}</p>
              </div>
              <StatusChip tone={a.level}>{LABEL[a.level] || a.level}</StatusChip>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
