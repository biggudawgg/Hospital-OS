"""
agent/agent.py — The HospitalOS AI agent (the "brain" behind the chat).

How one question is answered (the tool-calling loop, max 6 steps):
  1. Send the system prompt + chat history + new question + list of all MCP tools to the LLM.
  2. If the LLM asks for tools, call them through the MCP hub and send the results back.
  3. Repeat until the LLM writes a final answer (or 6 steps are used up).

Safety rule enforced IN CODE (not just in the prompt):
  A WRITE tool (admit, discharge, book, cancel, restock, order test, mark paid ...)
  is never run straight away. The agent stops and returns a confirmation request.
  Only when the user replies "yes" with that confirmation id is the tool executed.
"""

import json
import time
import uuid

from agent.llm import LLMError, chat_completion
from agent.mcp_hub import MCPHub

MAX_STEPS = 6
MAX_HISTORY_MESSAGES = 20
PENDING_TTL_SECONDS = 600            # a confirmation request expires after 10 minutes
YES_WORDS = {"yes", "y", "yes please", "confirm", "ok", "okay", "go ahead", "proceed", "haan"}

SYSTEM_PROMPT = """You are HospitalOS Assistant, an AI helper for hospital staff.
All data in this system is synthetic (fake) and used for a college project.

Rules you must follow:
1. Use the tools for EVERY fact about patients, beds, doctors, appointments, medicines,
   lab tests and bills. Never answer such questions from memory.
2. Never invent patient data, IDs, names or numbers. Only report what tools return.
3. If a tool returns nothing, "not found", or an error, say so honestly and suggest a next step.
4. To find a patient or doctor by name, search first, then use the numeric ID.
5. WRITE tools (admitting, discharging, booking, cancelling, restocking, ordering tests,
   marking bills paid) change data. When the user clearly asks for such an action, call the
   tool directly with the right arguments: the system will automatically show the user a
   Yes/No confirmation card and run it only after they say yes. Do not ask for confirmation
   in text yourself, and never claim a write succeeded unless the tool result says so.
6. If a request is unclear (e.g. missing patient ID or date), ask a short question first.
7. Today's date is {today}. Dates use YYYY-MM-DD, times use 24h HH:MM.
8. Keep answers short and clear: use bullet points or a small table for lists.
9. Drug information from openFDA is general public information, not medical advice."""


def _is_yes(text: str) -> bool:
    return text.strip().lower().rstrip(".!") in YES_WORDS


def _clean_history(history) -> list[dict]:
    """Keep only plain user/assistant text messages from the client (last 20)."""
    cleaned = []
    for item in history or []:
        if isinstance(item, dict) and item.get("role") in ("user", "assistant") and isinstance(item.get("content"), str):
            cleaned.append({"role": item["role"], "content": item["content"][:4000]})
    return cleaned[-MAX_HISTORY_MESSAGES:]


class HospitalAgent:
    """Runs conversations against the LLM using the tools from an MCPHub."""

    def __init__(self, hub: MCPHub):
        self.hub = hub
        self.pending: dict[str, dict] = {}   # confirmation_id -> saved state of a paused conversation

    # ---------------- public entry point ----------------
    async def chat(self, message: str, history=None, confirm_id: str | None = None) -> dict:
        """
        Answer one user message.
        Returns {"answer": str, "tool_calls": [...], "pending_action": {...} or None}.
        """
        self._drop_expired()
        tool_log: list[dict] = []
        try:
            if confirm_id:
                messages = await self._resume_after_confirmation(confirm_id, message, tool_log)
                if messages is None:
                    return self._reply("That confirmation has expired or was already used. "
                                       "Please ask again.", tool_log)
            else:
                today = time.strftime("%Y-%m-%d")
                messages = [{"role": "system", "content": SYSTEM_PROMPT.format(today=today)}]
                messages += _clean_history(history)
                messages.append({"role": "user", "content": message})
            return await self._loop(messages, tool_log)
        except LLMError as exc:
            return self._reply(exc.user_message, tool_log, error=True)

    # ---------------- the tool-calling loop ----------------
    async def _loop(self, messages: list[dict], tool_log: list[dict]) -> dict:
        tools = self.hub.openai_tools()
        if not tools:
            return self._reply("No MCP tool servers are connected, so I can't look anything up right now. "
                               "Run `python -m agent.check_servers` to see what's wrong.", tool_log, error=True)

        for _step in range(MAX_STEPS):
            reply = await chat_completion(messages, tools)
            tool_calls = reply.get("tool_calls") or []
            if not tool_calls:
                return self._reply(reply.get("content") or "(The model returned an empty answer.)", tool_log)

            # Give every tool call an id (some providers leave it empty)
            for tc in tool_calls:
                tc["id"] = tc.get("id") or f"call_{uuid.uuid4().hex[:8]}"
            messages.append({"role": "assistant", "content": reply.get("content") or "",
                             "tool_calls": [{"id": tc["id"], "type": "function", "function": tc["function"]}
                                            for tc in tool_calls]})

            # Run READ tools now; hold back the first WRITE tool for confirmation
            write_call = None
            for tc in tool_calls:
                name = tc["function"]["name"]
                args, arg_error = self._parse_args(tc["function"].get("arguments"))
                if arg_error:
                    self._add_tool_result(messages, tc["id"], arg_error)
                    tool_log.append(self._log_entry(name, {}, arg_error, "error"))
                elif self.hub.is_write_tool(name):
                    if write_call is None:
                        write_call = (tc, name, args)
                    else:
                        note = "Not run: only one data-changing action can be confirmed at a time. Ask again after this one."
                        self._add_tool_result(messages, tc["id"], note)
                        tool_log.append(self._log_entry(name, args, note, "skipped"))
                else:
                    ok, output = await self.hub.call_tool(name, args)
                    self._add_tool_result(messages, tc["id"], output)
                    tool_log.append(self._log_entry(name, args, output, "ok" if ok else "error"))

            if write_call:
                return self._ask_confirmation(messages, write_call, tool_log, reply.get("content"))

        return self._reply("I couldn't finish this within 6 steps. Please ask a simpler or more specific question.",
                           tool_log, error=True)

    # ---------------- confirmation handling ----------------
    def _ask_confirmation(self, messages, write_call, tool_log, model_text) -> dict:
        tc, name, args = write_call
        server, tool = self.hub.split_name(name)
        confirm_id = uuid.uuid4().hex
        self.pending[confirm_id] = {"messages": messages, "tool_call_id": tc["id"], "name": name,
                                    "args": args, "created": time.time(), "tool_log": list(tool_log)}
        arg_text = ", ".join(f"{k}={v!r}" for k, v in args.items()) or "no arguments"
        question = f"Please confirm: run **{tool}** ({server}) with {arg_text}? This will change hospital data."
        pending_action = {"id": confirm_id, "server": server, "tool": tool, "arguments": args, "message": question}
        tool_log.append({**self._log_entry(name, args, None, "pending_confirmation"), "confirmation": pending_action})
        answer = (model_text.strip() + "\n\n" if model_text and model_text.strip() else "") + question
        return self._reply(answer, tool_log, pending_action=pending_action)

    async def _resume_after_confirmation(self, confirm_id: str, message: str, tool_log: list) -> list | None:
        """Run (on 'yes') or cancel (otherwise) the paused WRITE tool, then continue the conversation."""
        saved = self.pending.pop(confirm_id, None)
        if saved is None:
            return None
        tool_log.extend(saved["tool_log"])
        messages = saved["messages"]
        if _is_yes(message):
            ok, output = await self.hub.call_tool(saved["name"], saved["args"])
            tool_log.append(self._log_entry(saved["name"], saved["args"], output, "ok" if ok else "error"))
        else:
            output = "The user declined. The action was NOT performed. Tell them it was cancelled."
            tool_log.append(self._log_entry(saved["name"], saved["args"], "Cancelled by user", "cancelled"))
        self._add_tool_result(messages, saved["tool_call_id"], output)
        return messages

    def _drop_expired(self):
        now = time.time()
        for key in [k for k, v in self.pending.items() if now - v["created"] > PENDING_TTL_SECONDS]:
            del self.pending[key]

    # ---------------- small helpers ----------------
    @staticmethod
    def _parse_args(raw) -> tuple[dict, str | None]:
        if isinstance(raw, dict):
            return raw, None
        try:
            args = json.loads(raw or "{}")
            return (args, None) if isinstance(args, dict) else ({}, "Tool error: arguments must be a JSON object.")
        except json.JSONDecodeError:
            return {}, "Tool error: the arguments were not valid JSON."

    @staticmethod
    def _add_tool_result(messages, tool_call_id, content):
        messages.append({"role": "tool", "tool_call_id": tool_call_id, "content": content})

    def _log_entry(self, name, args, output, status) -> dict:
        server, tool = self.hub.split_name(name)
        return {"server": server, "tool": tool, "arguments": args, "output": output,
                "status": status, "kind": "WRITE" if self.hub.is_write_tool(name) else "READ"}

    @staticmethod
    def _reply(answer, tool_log, pending_action=None, error=False) -> dict:
        return {"answer": answer, "tool_calls": tool_log, "pending_action": pending_action, "error": error}
