// Reports page — files in hospitalos/reports/ (the folder the filesystem MCP may access).
import { useState } from "react";
import { FilePlus2, FileText } from "lucide-react";
import { api, useApi } from "../api";
import TopBar from "../components/TopBar";
import SkeletonCard from "../components/SkeletonCard";
import { EmptyState, ErrorState } from "../components/States";

export default function Reports() {
  const { data, loading, error, reload } = useApi("/reports");
  const [open, setOpen] = useState(null);          // {name, content}
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState(null);

  async function view(name) {
    setActionError(null);
    try { setOpen(await api(`/reports/${encodeURIComponent(name)}`)); } catch (e) { setActionError(e.message); }
  }

  async function generate() {
    setBusy(true); setActionError(null);
    try {
      const { name } = await api("/reports/occupancy", { method: "POST" });
      await reload();
      await view(name);
    } catch (e) { setActionError(e.message); } finally { setBusy(false); }
  }

  return (
    <>
      <TopBar title="Reports" subtitle="Saved in hospitalos/reports/ — the only folder the filesystem MCP can open"
              actions={<button className="btn-primary" onClick={generate} disabled={busy}><FilePlus2 size={15} /> {busy ? "Generating…" : "Generate occupancy report"}</button>} />
      <main className="flex flex-col gap-4 p-6 lg:flex-row">
        <div className="space-y-2 lg:w-80">
          {error && <ErrorState message={error} onRetry={reload} />}
          {loading && <SkeletonCard lines={4} />}
          {data && data.length === 0 && <EmptyState title="No reports yet" message="Click “Generate occupancy report”." />}
          {data?.map((r) => (
            <button key={r.name} onClick={() => view(r.name)}
                    className={`card flex w-full items-center gap-3 p-3 text-left hover:border-primary ${open?.name === r.name ? "border-primary" : ""}`}>
              <FileText size={18} className="shrink-0 text-primary" aria-hidden="true" />
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{r.name}</p>
                <p className="text-xs text-ink-subtle">{new Date(r.modified).toLocaleString("en-IN")} · {r.size_bytes} bytes</p>
              </div>
            </button>
          ))}
        </div>
        <section className="card min-h-[300px] flex-1 p-5" aria-label="Report content">
          {actionError && <p className="mb-3 text-sm text-critical" role="alert">{actionError}</p>}
          {open ? (
            <>
              <h2 className="text-base font-semibold">{open.name}</h2>
              <pre className="num mt-3 whitespace-pre-wrap text-sm leading-relaxed text-ink-muted">{open.content}</pre>
            </>
          ) : (
            <p className="text-sm text-ink-muted">Select a report to read it. Tip: once the filesystem MCP is enabled, ask the AI “Summarise the latest report”.</p>
          )}
        </section>
      </main>
    </>
  );
}
