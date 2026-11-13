// ChatPanel — the AI chat: message list, input box, "Tools used" and Yes/No confirmation cards.
import { useEffect, useRef, useState } from "react";
import { Bot, SendHorizontal, User } from "lucide-react";
import { api } from "../api";
import ConfirmCard from "./ConfirmCard";
import ToolsUsed from "./ToolsUsed";

const STORAGE_KEY = "hospitalos-chat";

const SUGGESTIONS = [
  "Which ICU beds are free?",
  "List medicines with stock below 30",
  "Show unpaid bills",
  "What lab tests are pending?",
  "Show the history of patient 1",
  "When is doctor 1 free next Monday?",
];

function loadSaved() {
  try { return JSON.parse(sessionStorage.getItem(STORAGE_KEY)) || []; } catch { return []; }
}

export default function ChatPanel({ initialQuestion }) {
  const [messages, setMessages] = useState(loadSaved);   // {role, content, tool_calls?, pending_action?, error?}
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);
  const askedInitial = useRef(false);

  useEffect(() => {
    try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-40))); } catch { /* storage blocked */ }
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (initialQuestion && !askedInitial.current) { askedInitial.current = true; send(initialQuestion); }
  }, [initialQuestion]); // eslint-disable-line react-hooks/exhaustive-deps

  async function send(text, confirmId = null) {
    const question = text.trim();
    if (!question || busy) return;
    // history = earlier plain text messages (the backend only needs role + content)
    const history = messages.map(({ role, content }) => ({ role, content }));
    setMessages((m) => [
      // once answered, a confirmation card can't be clicked again
      ...m.map((msg) => (msg.pending_action ? { ...msg, pending_action: null, answered: true } : msg)),
      { role: "user", content: question },
    ]);
    setInput("");
    setBusy(true);
    try {
      const res = await api("/chat", { method: "POST", body: { message: question, history, confirm_id: confirmId } });
      setMessages((m) => [...m, { role: "assistant", ...res, content: res.answer }]);
    } catch (err) {
      setMessages((m) => [...m, { role: "assistant", content: err.message, error: true, tool_calls: [] }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card flex h-full min-h-0 flex-col">
      <div className="flex-1 space-y-4 overflow-y-auto p-5" aria-live="polite">
        {messages.length === 0 && (
          <div className="py-8 text-center">
            <Bot size={32} className="mx-auto text-primary" aria-hidden="true" />
            <p className="mt-2 font-display font-semibold">Ask HospitalOS anything</p>
            <p className="text-sm text-ink-muted">Answers come from live MCP tools. Data changes always ask you first.</p>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s) => (
                <button key={s} className="rounded-full border border-line px-3 py-1.5 text-sm hover:border-primary hover:text-primary"
                        onClick={() => send(s)}>{s}</button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`flex gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
            <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-full ${
              m.role === "user" ? "bg-ink text-white" : "bg-primary-soft text-primary"}`} aria-hidden="true">
              {m.role === "user" ? <User size={15} /> : <Bot size={15} />}
            </span>
            <div className={`max-w-[85%] ${m.role === "user" ? "text-right" : ""}`}>
              <div className={`inline-block whitespace-pre-wrap rounded-card px-4 py-2.5 text-left text-sm ${
                m.role === "user" ? "bg-primary text-white"
                  : m.error ? "border border-critical/30 bg-critical-soft text-critical" : "bg-canvas"}`}>
                {m.content}
              </div>
              {m.role === "assistant" && <ToolsUsed calls={m.tool_calls} />}
              {m.pending_action && (
                <ConfirmCard action={m.pending_action} disabled={busy}
                             onAnswer={(answer) => send(answer, m.pending_action.id)} />
              )}
            </div>
          </div>
        ))}
        {busy && <p className="text-sm text-ink-muted" role="status">HospitalOS is thinking and calling tools…</p>}
        <div ref={endRef} />
      </div>

      <form className="flex gap-2 border-t border-line p-3" onSubmit={(e) => { e.preventDefault(); send(input); }}>
        <input className="input" value={input} onChange={(e) => setInput(e.target.value)} maxLength={2000}
               placeholder="e.g. Book Dr. Rao for patient 12 tomorrow at 10:00" aria-label="Message" disabled={busy} />
        <button className="btn-primary" disabled={busy || !input.trim()} aria-label="Send">
          <SendHorizontal size={16} aria-hidden="true" />
        </button>
        {messages.length > 0 && (
          <button type="button" className="btn-ghost" onClick={() => setMessages([])} disabled={busy}>Clear</button>
        )}
      </form>
    </div>
  );
}
