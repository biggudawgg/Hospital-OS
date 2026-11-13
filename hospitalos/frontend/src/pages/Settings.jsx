// Settings page — which MCP servers are connected (row of dots), which LLM is configured, API URL.
import { RefreshCw } from "lucide-react";
import { API_URL, useApiMany } from "../api";
import TopBar from "../components/TopBar";
import StatusChip from "../components/StatusChip";
import SkeletonCard from "../components/SkeletonCard";
import { ErrorState } from "../components/States";

const DOT = { connected: "bg-ok", failed: "bg-critical", not_installed: "bg-warning", disabled: "bg-ink-subtle" };
const CHIP = { connected: "ok", failed: "critical", not_installed: "warning", disabled: "neutral" };

export default function Settings() {
  const { data, loading, error, reload } = useApiMany({ mcp: "/mcp/status", llm: "/llm/info" });
  const servers = data?.mcp.servers || [];
  const connected = servers.filter((s) => s.status === "connected");

  return (
    <>
      <TopBar title="Settings" subtitle="System status"
              actions={<button className="btn-ghost" onClick={reload}><RefreshCw size={15} /> Refresh</button>} />
      <main className="space-y-5 p-6">
        {error && <ErrorState message={error} onRetry={reload} />}
        {loading && <SkeletonCard lines={6} />}
        {data && (
          <>
            <section className="card p-5" aria-labelledby="mcp-title">
              <h2 id="mcp-title" className="text-base font-semibold">MCP servers</h2>
              <p className="text-sm text-ink-muted">
                {data.mcp.agent_running
                  ? `${connected.length} of ${servers.length} connected · ${connected.reduce((t, s) => t + s.tool_count, 0)} tools available`
                  : "The agent is not running on the backend."}
              </p>
              {/* The row of dots: one per server */}
              <div className="mt-4 flex flex-wrap gap-4" aria-label="Server status dots">
                {servers.map((s) => (
                  <span key={s.name} className="flex items-center gap-1.5 text-sm" title={`${s.name}: ${s.status}`}>
                    <span className={`h-3 w-3 rounded-full ${DOT[s.status] || "bg-ink-subtle"}`} aria-hidden="true" />
                    {s.name}
                  </span>
                ))}
              </div>
              <div className="mt-5 overflow-x-auto">
                <table className="w-full">
                  <thead className="border-b border-line"><tr>
                    <th className="th">Server</th><th className="th">Status</th><th className="th text-right">Tools</th><th className="th">Details</th>
                  </tr></thead>
                  <tbody className="divide-y divide-line">
                    {servers.map((s) => (
                      <tr key={s.name}>
                        <td className="td num font-semibold">{s.name}</td>
                        <td className="td"><StatusChip tone={CHIP[s.status]}>{s.status.replace("_", " ")}</StatusChip></td>
                        <td className="td num text-right">{s.tool_count}</td>
                        <td className="td text-ink-muted">
                          {s.error || s.description}
                          {s.tools.length > 0 && <p className="num mt-1 text-xs text-ink-subtle">{s.tools.join(", ")}</p>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="card grid gap-4 p-5 sm:grid-cols-3" aria-label="Configuration">
              <div><p className="text-xs text-ink-subtle">LLM provider</p><p className="num font-medium">{data.llm.provider_host || "not set"}</p></div>
              <div><p className="text-xs text-ink-subtle">LLM model</p><p className="num font-medium">{data.llm.model || "not set"}</p></div>
              <div><p className="text-xs text-ink-subtle">Backend API</p><p className="num font-medium">{API_URL}</p></div>
              {!data.llm.configured && <p className="text-sm text-warning sm:col-span-3" role="alert">{data.llm.problem}</p>}
            </section>
          </>
        )}
      </main>
    </>
  );
}
