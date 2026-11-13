// ToolsUsed — collapsible list under each AI answer: which MCP tool ran, with what inputs, and what it returned.
import { useState } from "react";
import { ChevronDown, Wrench } from "lucide-react";
import StatusChip from "./StatusChip";

const STATUS = {
  ok: ["ok", "Success"],
  error: ["critical", "Error"],
  pending_confirmation: ["warning", "Awaiting confirmation"],
  cancelled: ["neutral", "Cancelled"],
  skipped: ["neutral", "Skipped"],
};

export default function ToolsUsed({ calls = [] }) {
  const [open, setOpen] = useState(false);
  if (!calls.length) return null;

  return (
    <div className="mt-2 rounded-control border border-line bg-canvas">
      <button
        className="flex w-full items-center gap-2 px-3 py-2 text-xs font-semibold text-ink-muted"
        onClick={() => setOpen(!open)} aria-expanded={open}
      >
        <Wrench size={13} aria-hidden="true" />
        Tools used ({calls.length})
        <ChevronDown size={14} className={`ml-auto transition-transform ${open ? "rotate-180" : ""}`} aria-hidden="true" />
      </button>
      {open && (
        <ol className="space-y-2 border-t border-line p-3">
          {calls.map((c, i) => {
            const [tone, label] = STATUS[c.status] || ["neutral", c.status];
            return (
              <li key={i} className="rounded-control border border-line bg-surface p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <code className="num text-xs font-semibold">{c.server}.{c.tool}</code>
                  <StatusChip tone={c.kind === "WRITE" ? "warning" : "info"}>{c.kind}</StatusChip>
                  <StatusChip tone={tone}>{label}</StatusChip>
                </div>
                <p className="mt-2 text-[11px] font-semibold uppercase tracking-wide text-ink-subtle">Input</p>
                <pre className="num mt-1 overflow-x-auto whitespace-pre-wrap text-xs text-ink-muted">
                  {JSON.stringify(c.arguments, null, 2)}
                </pre>
                {c.output && (
                  <>
                    <p className="mt-2 text-[11px] font-semibold uppercase tracking-wide text-ink-subtle">Output</p>
                    <pre className="num mt-1 max-h-48 overflow-auto whitespace-pre-wrap text-xs text-ink-muted">{c.output}</pre>
                  </>
                )}
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );
}
