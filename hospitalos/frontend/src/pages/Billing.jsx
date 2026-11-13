// Billing page — all bills with totals and a status filter.
import { useState } from "react";
import { money, useApiMany } from "../api";
import TopBar from "../components/TopBar";
import VitalCard from "../components/VitalCard";
import StatusChip, { toneFor } from "../components/StatusChip";
import SkeletonCard from "../components/SkeletonCard";
import { EmptyState, ErrorState } from "../components/States";
import { CircleDollarSign, Clock, Wallet } from "lucide-react";

const FILTERS = ["All", "Unpaid", "Partial", "Paid"];

export default function Billing() {
  const { data, loading, error, reload } = useApiMany({ bills: "/bills", patients: "/patients" });
  const [filter, setFilter] = useState("All");

  const patientById = Object.fromEntries((data?.patients || []).map((p) => [p.id, p]));
  const bills = (data?.bills || []).slice().sort((a, b) => b.created_at.localeCompare(a.created_at));
  const rows = bills.filter((b) => filter === "All" || b.paid_status === filter);
  const sum = (list) => list.reduce((t, b) => t + b.total_amount, 0);
  const unpaid = bills.filter((b) => b.paid_status !== "Paid");

  return (
    <>
      <TopBar title="Billing" subtitle={data ? `${bills.length} invoices` : "Loading…"} />
      <main className="space-y-4 p-6">
        {data && (
          <div className="grid gap-4 sm:grid-cols-3">
            <VitalCard label="Total billed" value={money(sum(bills))} icon={CircleDollarSign} />
            <VitalCard label="Outstanding" value={money(sum(unpaid))} icon={Wallet} tone="warning" hint={`${unpaid.length} bills not fully paid`} />
            <VitalCard label="Collected" value={money(sum(bills.filter((b) => b.paid_status === "Paid")))} icon={Clock} tone="info" />
          </div>
        )}
        <div className="flex gap-2" role="tablist">
          {FILTERS.map((f) => (
            <button key={f} role="tab" aria-selected={filter === f} onClick={() => setFilter(f)}
                    className={`rounded-full px-3 py-1.5 text-sm font-medium ${filter === f ? "bg-primary text-white" : "border border-line bg-surface text-ink-muted"}`}>
              {f}
            </button>
          ))}
        </div>
        {error && <ErrorState message={error} onRetry={reload} />}
        {loading && <SkeletonCard lines={8} />}
        {data && rows.length === 0 && <EmptyState title={`No ${filter.toLowerCase()} bills`} />}
        {rows.length > 0 && (
          <div className="card overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-line"><tr>
                <th className="th">Bill</th><th className="th">Patient</th><th className="th">Items</th>
                <th className="th text-right">Amount</th><th className="th">Date</th><th className="th">Status</th>
              </tr></thead>
              <tbody className="divide-y divide-line">
                {rows.map((b) => (
                  <tr key={b.id} className="hover:bg-canvas">
                    <td className="td num text-ink-muted">#{b.id}</td>
                    <td className="td font-medium">{patientById[b.patient_id]?.full_name || `Patient #${b.patient_id}`}</td>
                    <td className="td max-w-xs truncate text-ink-muted" title={b.description}>{b.description}</td>
                    <td className="td num text-right font-semibold">{money(b.total_amount)}</td>
                    <td className="td num text-ink-muted">{new Date(b.created_at).toLocaleDateString("en-IN")}</td>
                    <td className="td"><StatusChip tone={toneFor(b.paid_status)}>{b.paid_status}</StatusChip></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </>
  );
}
