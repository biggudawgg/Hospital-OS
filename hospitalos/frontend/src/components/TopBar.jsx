// TopBar — page title on the left; backend connection indicator and page actions on the right.
import { useEffect, useState } from "react";
import { api } from "../api";

export default function TopBar({ title, subtitle, actions }) {
  const [online, setOnline] = useState(null);

  useEffect(() => {
    let alive = true;
    const check = () => api("/").then(() => alive && setOnline(true)).catch(() => alive && setOnline(false));
    check();
    const timer = setInterval(check, 15000);   // re-check every 15 seconds
    return () => { alive = false; clearInterval(timer); };
  }, []);

  return (
    <header className="flex flex-wrap items-center justify-between gap-3 border-b border-line bg-surface px-6 py-4">
      <div>
        <h1 className="text-xl font-bold">{title}</h1>
        {subtitle && <p className="text-sm text-ink-muted">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-3">
        {actions}
        <span className="flex items-center gap-2 text-xs font-medium text-ink-muted" aria-live="polite">
          <span className={`h-2 w-2 rounded-full ${online === null ? "bg-ink-subtle" : online ? "bg-ok" : "bg-critical"}`} />
          {online === null ? "Checking…" : online ? "Backend online" : "Backend offline"}
        </span>
      </div>
    </header>
  );
}
