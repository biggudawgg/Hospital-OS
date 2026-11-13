// OccupancyRing — a donut showing occupied / total beds, drawn with plain SVG.
// The ring turns warning/critical colour when a ward is nearly full; the number is always printed too.
export default function OccupancyRing({ occupied = 0, total = 0, label, size = 96 }) {
  const pct = total ? occupied / total : 0;
  const stroke = 9;
  const r = (size - stroke) / 2;
  const circumference = 2 * Math.PI * r;
  const color = pct >= 0.9 ? "#B91C1C" : pct >= 0.75 ? "#B45309" : "#0D9488";

  return (
    <figure className="flex flex-col items-center gap-2" title={`${label}: ${occupied} of ${total} beds occupied`}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img"
           aria-label={`${label}: ${occupied} of ${total} beds occupied`}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#E2E8F0" strokeWidth={stroke} />
        <circle
          cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={stroke}
          strokeLinecap="round" strokeDasharray={`${circumference * pct} ${circumference}`}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: "stroke-dasharray 0.6s ease" }}
        />
        <text x="50%" y="48%" textAnchor="middle" className="fill-ink font-mono" fontSize={size * 0.2} fontWeight="600">
          {Math.round(pct * 100)}%
        </text>
        <text x="50%" y="66%" textAnchor="middle" className="fill-ink-muted font-mono" fontSize={size * 0.11}>
          {occupied}/{total}
        </text>
      </svg>
      {label && <figcaption className="text-sm font-medium text-ink-muted">{label}</figcaption>}
    </figure>
  );
}
