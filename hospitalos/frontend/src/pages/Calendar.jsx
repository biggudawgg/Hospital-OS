// Calendar page — one week of appointments, one column per day, filterable by doctor.
import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useApiMany } from "../api";
import TopBar from "../components/TopBar";
import StatusChip, { toneFor } from "../components/StatusChip";
import SkeletonCard from "../components/SkeletonCard";
import { ErrorState } from "../components/States";

const dayKey = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

function startOfWeek(date) {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7));   // Monday
  return d;
}

export default function Calendar() {
  const { data, loading, error, reload } = useApiMany({ appts: "/appointments", doctors: "/doctors", patients: "/patients" });
  const [weekStart, setWeekStart] = useState(() => startOfWeek(new Date()));
  const [doctorId, setDoctorId] = useState("all");

  const days = Array.from({ length: 7 }, (_, i) => { const d = new Date(weekStart); d.setDate(d.getDate() + i); return d; });
  const shiftWeek = (n) => setWeekStart((w) => { const d = new Date(w); d.setDate(d.getDate() + 7 * n); return d; });

  const doctorById = Object.fromEntries((data?.doctors || []).map((d) => [d.id, d]));
  const patientById = Object.fromEntries((data?.patients || []).map((p) => [p.id, p]));
  const byDay = {};
  for (const a of data?.appts || []) {
    if (doctorId !== "all" && String(a.doctor_id) !== doctorId) continue;
    const key = a.appointment_time.slice(0, 10);   // times are stored as hospital-local time
    (byDay[key] ||= []).push(a);
  }
  Object.values(byDay).forEach((list) => list.sort((x, y) => x.appointment_time.localeCompare(y.appointment_time)));
  const todayKey = dayKey(new Date());

  return (
    <>
      <TopBar title="Calendar" subtitle={`Week of ${weekStart.toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}`}
        actions={
          <div className="flex items-center gap-2">
            <select className="input w-auto" value={doctorId} onChange={(e) => setDoctorId(e.target.value)} aria-label="Filter by doctor">
              <option value="all">All doctors</option>
              {(data?.doctors || []).map((d) => <option key={d.id} value={d.id}>{d.full_name}</option>)}
            </select>
            <button className="btn-ghost" onClick={() => shiftWeek(-1)} aria-label="Previous week"><ChevronLeft size={16} /></button>
            <button className="btn-ghost" onClick={() => setWeekStart(startOfWeek(new Date()))}>Today</button>
            <button className="btn-ghost" onClick={() => shiftWeek(1)} aria-label="Next week"><ChevronRight size={16} /></button>
          </div>
        } />
      <main className="p-6">
        {error && <ErrorState message={error} onRetry={reload} />}
        {loading && <SkeletonCard lines={10} />}
        {data && (
          <div className="grid gap-3 md:grid-cols-7">
            {days.map((d) => {
              const key = dayKey(d);
              const list = byDay[key] || [];
              return (
                <section key={key} className={`card min-h-[160px] p-3 ${key === todayKey ? "ring-2 ring-primary-ring" : ""}`}>
                  <h2 className="flex items-baseline justify-between text-sm font-semibold">
                    {d.toLocaleDateString("en-IN", { weekday: "short" })}
                    <span className="num text-xs text-ink-muted">{d.getDate()}</span>
                  </h2>
                  <ul className="mt-2 space-y-2">
                    {list.length === 0 && <li className="text-xs text-ink-subtle">No appointments</li>}
                    {list.map((a) => (
                      <li key={a.id} className="rounded-control border border-line bg-canvas p-2 text-xs">
                        <div className="flex items-center justify-between gap-1">
                          <span className="num font-semibold">{a.appointment_time.slice(11, 16)}</span>
                          <StatusChip tone={toneFor(a.status)}>{a.status}</StatusChip>
                        </div>
                        <p className="mt-1 truncate font-medium">{patientById[a.patient_id]?.full_name || `Patient #${a.patient_id}`}</p>
                        <p className="truncate text-ink-muted">{doctorById[a.doctor_id]?.full_name}</p>
                      </li>
                    ))}
                  </ul>
                </section>
              );
            })}
          </div>
        )}
      </main>
    </>
  );
}
