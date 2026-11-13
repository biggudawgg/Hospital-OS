// Pharmacy page — medicine stock table with low-stock highlighting.
import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { money, useApi } from "../api";
import TopBar from "../components/TopBar";
import StatusChip from "../components/StatusChip";
import SkeletonCard from "../components/SkeletonCard";
import { EmptyState, ErrorState } from "../components/States";

const LOW = 50;
const stockTone = (q) => (q === 0 ? ["critical", "Out of stock"] : q < 20 ? ["critical", "Critical"] : q < LOW ? ["warning", "Low stock"] : ["ok", "In stock"]);

export default function Pharmacy() {
  const { data, loading, error, reload } = useApi("/medicines");
  const [query, setQuery] = useState("");
  const [onlyLow, setOnlyLow] = useState(false);

  const rows = useMemo(() => (data || [])
    .filter((m) => (!onlyLow || m.stock_quantity < LOW) && `${m.name} ${m.category}`.toLowerCase().includes(query.toLowerCase()))
    .sort((a, b) => a.stock_quantity - b.stock_quantity), [data, query, onlyLow]);
  const lowCount = (data || []).filter((m) => m.stock_quantity < LOW).length;

  return (
    <>
      <TopBar title="Pharmacy" subtitle={data ? `${data.length} medicines · ${lowCount} below ${LOW} units` : "Loading…"} />
      <main className="space-y-4 p-6">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative min-w-[220px] flex-1">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-subtle" aria-hidden="true" />
            <input className="input pl-9" placeholder="Search medicine or category" value={query}
                   onChange={(e) => setQuery(e.target.value)} aria-label="Search medicines" />
          </div>
          <label className="flex items-center gap-2 text-sm text-ink-muted">
            <input type="checkbox" className="accent-primary" checked={onlyLow} onChange={(e) => setOnlyLow(e.target.checked)} />
            Low stock only
          </label>
        </div>
        {error && <ErrorState message={error} onRetry={reload} />}
        {loading && <SkeletonCard lines={8} />}
        {data && rows.length === 0 && <EmptyState title="No medicines found" />}
        {rows.length > 0 && (
          <div className="card overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-line"><tr>
                <th className="th">Medicine</th><th className="th">Category</th><th className="th text-right">Stock</th>
                <th className="th text-right">Unit price</th><th className="th">Expiry</th><th className="th">Status</th>
              </tr></thead>
              <tbody className="divide-y divide-line">
                {rows.map((m) => {
                  const [tone, label] = stockTone(m.stock_quantity);
                  return (
                    <tr key={m.id} className="hover:bg-canvas">
                      <td className="td font-medium">{m.name}</td>
                      <td className="td text-ink-muted">{m.category}</td>
                      <td className="td num text-right font-semibold">{m.stock_quantity}</td>
                      <td className="td num text-right">{money(m.unit_price)}</td>
                      <td className="td num text-ink-muted">{m.expiry_date}</td>
                      <td className="td"><StatusChip tone={tone}>{label}</StatusChip></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        <p className="text-xs text-ink-subtle">Tip: ask the AI "Restock Insulin Glargine by 100" — it will ask you to confirm first.</p>
      </main>
    </>
  );
}
