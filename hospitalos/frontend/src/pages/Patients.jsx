// Patients page — searchable patient list with a details panel.
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { MessageSquare, Search, X } from "lucide-react";
import { initials, useApi } from "../api";
import TopBar from "../components/TopBar";
import StatusChip from "../components/StatusChip";
import SkeletonCard from "../components/SkeletonCard";
import { EmptyState, ErrorState } from "../components/States";

export default function Patients() {
  const { data, loading, error, reload } = useApi("/patients");
  const [query, setQuery] = useState("");
  const [onlyAdmitted, setOnlyAdmitted] = useState(false);
  const [selected, setSelected] = useState(null);
  const navigate = useNavigate();

  const rows = useMemo(() => (data || []).filter((p) =>
    (!onlyAdmitted || p.is_admitted) &&
    (`${p.id} ${p.full_name} ${p.diagnosis || ""}`.toLowerCase().includes(query.toLowerCase()))), [data, query, onlyAdmitted]);

  return (
    <>
      <TopBar title="Patients" subtitle={data ? `${data.length} registered patients` : "Loading…"} />
      <main className="flex flex-col gap-4 p-6 lg:flex-row">
        <div className="min-w-0 flex-1 space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative min-w-[220px] flex-1">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-subtle" aria-hidden="true" />
              <input className="input pl-9" placeholder="Search by name, ID or diagnosis" value={query}
                     onChange={(e) => setQuery(e.target.value)} aria-label="Search patients" />
            </div>
            <label className="flex items-center gap-2 text-sm text-ink-muted">
              <input type="checkbox" checked={onlyAdmitted} onChange={(e) => setOnlyAdmitted(e.target.checked)} className="accent-primary" />
              Admitted only
            </label>
          </div>

          {error && <ErrorState message={error} onRetry={reload} />}
          {loading && <SkeletonCard lines={8} />}
          {data && rows.length === 0 && <EmptyState title="No patients found" message="Try a different search." />}
          {rows.length > 0 && (
            <div className="card overflow-x-auto">
              <table className="w-full">
                <thead className="border-b border-line"><tr>
                  <th className="th">Patient</th><th className="th">Age / Sex</th><th className="th">Blood</th>
                  <th className="th">Diagnosis</th><th className="th">Status</th>
                </tr></thead>
                <tbody className="divide-y divide-line">
                  {rows.map((p) => (
                    <tr key={p.id} onClick={() => setSelected(p)} tabIndex={0}
                        onKeyDown={(e) => e.key === "Enter" && setSelected(p)}
                        className={`cursor-pointer hover:bg-canvas ${selected?.id === p.id ? "bg-primary-soft" : ""}`}>
                      <td className="td">
                        <div className="flex items-center gap-3">
                          <span className="grid h-8 w-8 place-items-center rounded-full bg-primary-soft text-xs font-bold text-primary">{initials(p.full_name)}</span>
                          <div><p className="font-medium">{p.full_name}</p><p className="num text-xs text-ink-subtle">#{p.id}</p></div>
                        </div>
                      </td>
                      <td className="td num">{p.age} / {p.gender[0]}</td>
                      <td className="td num">{p.blood_group}</td>
                      <td className="td text-ink-muted">{p.diagnosis || "—"}</td>
                      <td className="td">{p.is_admitted ? <StatusChip tone="info">Admitted</StatusChip> : <StatusChip>Outpatient</StatusChip>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {selected && (
          <aside className="card h-fit w-full shrink-0 p-5 lg:sticky lg:top-6 lg:w-80" aria-label="Patient details">
            <div className="flex items-start justify-between">
              <span className="grid h-12 w-12 place-items-center rounded-full bg-primary text-base font-bold text-white">{initials(selected.full_name)}</span>
              <button className="text-ink-subtle hover:text-ink" onClick={() => setSelected(null)} aria-label="Close"><X size={18} /></button>
            </div>
            <h2 className="mt-3 text-lg font-semibold">{selected.full_name}</h2>
            <p className="num text-xs text-ink-subtle">Patient #{selected.id}</p>
            <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
              {[["Age", selected.age], ["Gender", selected.gender], ["Blood group", selected.blood_group], ["Phone", selected.phone],
                ["Registered", new Date(selected.created_at).toLocaleDateString("en-IN")]].map(([k, v]) => (
                <div key={k}><dt className="text-xs text-ink-subtle">{k}</dt><dd className="num font-medium">{v}</dd></div>
              ))}
              <div className="col-span-2"><dt className="text-xs text-ink-subtle">Diagnosis</dt><dd className="font-medium">{selected.diagnosis || "—"}</dd></div>
            </dl>
            <button className="btn-primary mt-5 w-full justify-center"
                    onClick={() => navigate(`/chat?q=${encodeURIComponent(`Show the full history of patient ${selected.id}`)}`)}>
              <MessageSquare size={15} /> Ask AI for full history
            </button>
          </aside>
        )}
      </main>
    </>
  );
}
