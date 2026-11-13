// Dashboard — hospital at a glance: vital cards, ward occupancy rings, appointments chart, alerts.
import { useNavigate } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { BedDouble, FlaskConical, Pill, RefreshCw, Sparkles, Users, Wallet } from "lucide-react";
import { money, useApi } from "../api";
import TopBar from "../components/TopBar";
import VitalCard from "../components/VitalCard";
import OccupancyRing from "../components/OccupancyRing";
import AlertPanel from "../components/AlertPanel";
import SkeletonCard, { SkeletonGrid } from "../components/SkeletonCard";
import { EmptyState, ErrorState } from "../components/States";

const QUICK_QUESTIONS = ["Which ICU beds are free?", "Show unpaid bills", "List low stock medicines"];

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-control border border-line bg-surface px-3 py-2 text-xs shadow-pop">
      <p className="font-semibold">{label}</p>
      <p className="text-ink-muted"><span className="num font-semibold text-ink">{payload[0].value}</span> scheduled</p>
    </div>
  );
}

export default function Dashboard() {
  const { data, loading, error, reload } = useApi("/stats");
  const navigate = useNavigate();

  const chartData = (data?.appointments_next_7_days || []).map((d) => ({
    day: new Date(d.date + "T00:00").toLocaleDateString("en-IN", { weekday: "short", day: "numeric" }),
    count: d.count,
  }));

  return (
    <>
      <TopBar title="Dashboard" subtitle="Live overview of the hospital (synthetic data)"
              actions={<button className="btn-ghost" onClick={reload}><RefreshCw size={15} /> Refresh</button>} />
      <main className="space-y-6 p-6">
        {error && <ErrorState message={error} onRetry={reload} />}
        {loading && !data && (
          <>
            <SkeletonGrid />
            <div className="grid gap-4 lg:grid-cols-3"><SkeletonCard lines={6} className="lg:col-span-2" /><SkeletonCard lines={6} /></div>
          </>
        )}
        {data && data.patients_total === 0 && (
          <EmptyState title="The database is empty" message="Run `python -m data.seed` in the hospitalos folder to create synthetic data." />
        )}
        {data && data.patients_total > 0 && (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <VitalCard label="Patients admitted" value={data.patients_admitted} icon={Users}
                         hint={`${data.patients_total} registered`} />
              <VitalCard label="Free beds" value={`${data.beds_free}/${data.beds_total}`} icon={BedDouble}
                         tone={data.beds_free < 5 ? "critical" : "primary"} hint={`${data.beds_occupied} occupied`} />
              <VitalCard label="Low-stock medicines" value={data.low_stock_count} icon={Pill}
                         tone={data.low_stock_count ? "warning" : "primary"} hint="below 50 units" />
              <VitalCard label="Unpaid bills" value={data.unpaid_bills_count} icon={Wallet} tone="info"
                         hint={`${money(data.unpaid_amount)} outstanding`} />
            </div>

            <div className="grid gap-4 lg:grid-cols-3">
              <section className="card p-5 lg:col-span-2" aria-labelledby="occ-title">
                <h2 id="occ-title" className="text-base font-semibold">Ward occupancy</h2>
                <div className="mt-4 grid grid-cols-2 gap-6 sm:grid-cols-3 lg:grid-cols-5">
                  {data.wards.map((w) => <OccupancyRing key={w.ward} label={w.ward} occupied={w.occupied} total={w.total} />)}
                </div>
              </section>
              <AlertPanel alerts={data.alerts} />
            </div>

            <div className="grid gap-4 lg:grid-cols-3">
              <section className="card p-5 lg:col-span-2" aria-labelledby="appt-title">
                <h2 id="appt-title" className="text-base font-semibold">Scheduled appointments · next 7 days</h2>
                <div className="mt-4 h-60">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                      <CartesianGrid vertical={false} stroke="#E2E8F0" />
                      <XAxis dataKey="day" tickLine={false} axisLine={false} tick={{ fontSize: 12, fill: "#475569" }} />
                      <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={{ fontSize: 12, fill: "#475569" }} />
                      <Tooltip content={<ChartTooltip />} cursor={{ fill: "#F0FDFA" }} />
                      <Bar dataKey="count" fill="#0D9488" radius={[4, 4, 0, 0]} maxBarSize={36} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </section>
              <section className="card flex flex-col p-5" aria-labelledby="ask-title">
                <h2 id="ask-title" className="flex items-center gap-2 text-base font-semibold">
                  <Sparkles size={16} className="text-primary" /> Ask the AI
                </h2>
                <p className="mt-1 text-sm text-ink-muted">One click sends the question to the agent.</p>
                <div className="mt-3 flex flex-col gap-2">
                  {QUICK_QUESTIONS.map((q) => (
                    <button key={q} className="btn-ghost justify-start" onClick={() => navigate(`/chat?q=${encodeURIComponent(q)}`)}>{q}</button>
                  ))}
                </div>
                <p className="mt-auto flex items-center gap-2 pt-4 text-xs text-ink-subtle">
                  <FlaskConical size={13} /> {data.pending_labs} lab tests pending · {data.doctors_available} doctors on duty
                </p>
              </section>
            </div>
          </>
        )}
      </main>
    </>
  );
}
