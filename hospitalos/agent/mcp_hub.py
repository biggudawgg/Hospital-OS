"""
agent/mcp_hub.py — Connects to EVERY MCP server listed in agent/mcp_config.json.

What it does, step by step:
  1. Reads mcp_config.json and fills in placeholders (${PYTHON}, ${ROOT}, values from .env).
  2. Starts each enabled server as a child process and talks to it over stdio
     using the official MCP Python client SDK.
  3. Collects every tool and converts it to the OpenAI "function tool" format
     that Gemini / Groq understand. Tool names become "server__tool",
     e.g. "beds__get_free_beds", so we always know which server to call.
  4. Calls tools on request and turns any failure into a friendly text message.

A server that fails to start never breaks the others: it is just marked "failed"
and its error is shown in the status table / Settings page.

Technical note: each server runs inside its own asyncio task, which opens the
connection, waits until shutdown, then closes it. The MCP SDK requires the
connection to be opened and closed in the same task.
"""

import asyncio
import json
import os
import re
import shutil
import sys
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from datetime import timedelta

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agent.settings import CONFIG_PATH, LOG_DIR, PROJECT_ROOT

START_TIMEOUT_SECONDS = 40       # time allowed for one server to start and list its tools
TOOL_TIMEOUT_SECONDS = 60        # time allowed for one tool call
MAX_TOOL_OUTPUT_CHARS = 6000     # long outputs are cut so they fit in the LLM prompt
NAME_SEPARATOR = "__"

# JSON-schema keys every OpenAI-compatible provider accepts (Gemini is the strictest)
ALLOWED_SCHEMA_KEYS = {"type", "properties", "required", "description", "items", "enum",
                       "anyOf", "minimum", "maximum", "format"}


@dataclass
class ServerConnection:
    """Everything we know about one MCP server."""
    name: str
    description: str = ""
    enabled: bool = True
    status: str = "pending"            # pending | connected | failed | disabled | not_installed
    error: str | None = None
    session: ClientSession | None = None
    tools: list = field(default_factory=list)   # MCP Tool objects (after allowed_tools filter)
    write_tools: set = field(default_factory=set)
    allowed_tools: list | None = None   # None = expose every tool of this server
    params: StdioServerParameters | None = None
    ready: asyncio.Event = field(default_factory=asyncio.Event)


def _fill_placeholders(text: str) -> str:
    """Replace ${PYTHON}, ${ROOT}, ${SCRIPTS} and ${ANY_ENV_VAR} inside a config string."""
    special = {
        "PYTHON": sys.executable,
        "ROOT": PROJECT_ROOT.as_posix(),
        "SCRIPTS": os.path.dirname(sys.executable).replace("\\", "/"),
    }
    return re.sub(r"\$\{([A-Z0-9_]+)\}",
                  lambda m: special.get(m.group(1), os.getenv(m.group(1), "")), text)


def _clean_schema(schema):
    """Keep only JSON-schema keys all providers accept (Gemini rejects e.g. 'title', '$schema')."""
    if isinstance(schema, list):
        return [_clean_schema(s) for s in schema]
    if not isinstance(schema, dict):
        return schema
    cleaned = {}
    for key, value in schema.items():
        if key == "properties" and isinstance(value, dict):
            cleaned[key] = {prop: _clean_schema(sub) for prop, sub in value.items()}
        elif key in ALLOWED_SCHEMA_KEYS:
            cleaned[key] = _clean_schema(value)
    return cleaned


def _friendly_start_error(exc: BaseException, name: str) -> str:
    """Turn a low-level startup exception into a short message a beginner can act on."""
    # anyio wraps errors from child tasks in an ExceptionGroup; show the first real one
    while isinstance(exc, BaseExceptionGroup) and exc.exceptions:
        exc = exc.exceptions[0]
    if isinstance(exc, TimeoutError):
        return f"did not start within {START_TIMEOUT_SECONDS}s"
    if isinstance(exc, FileNotFoundError):
        return "command not found (is it installed?)"
    text = str(exc) or type(exc).__name__
    return f"{text[:160]} (details: agent/logs/{name}.log)"


class MCPHub:
    """Starts, tracks and calls all MCP servers from mcp_config.json."""

    def __init__(self, config_path=CONFIG_PATH, only: list[str] | None = None, extra_env: dict | None = None):
        self.config_path = config_path
        self.only = only                    # optional list of server names (used by tests)
        self.extra_env = extra_env or {}    # extra env vars for every server (used by tests)
        self.servers: dict[str, ServerConnection] = {}
        self._stop = asyncio.Event()
        self._tasks: list[asyncio.Task] = []
        self._log_files = []

    # ---------- configuration ----------
    def _load_config(self):
        with open(self.config_path, encoding="utf-8") as f:
            config = json.load(f)
        for name, spec in config.get("mcpServers", {}).items():
            if self.only is not None and name not in self.only:
                continue
            conn = ServerConnection(name=name, description=spec.get("description", ""),
                                    enabled=spec.get("enabled", True))
            conn.write_tools = set(spec.get("write_tools", []))
            conn.allowed_tools = spec.get("allowed_tools")  # None = all tools
            if not conn.enabled:
                conn.status = "disabled"
                conn.error = "disabled in mcp_config.json"
                conn.ready.set()
            else:
                command = _fill_placeholders(spec["command"])
                resolved = shutil.which(command)
                if resolved is None:
                    conn.status = "not_installed"
                    conn.error = f"command '{command}' not found"
                    conn.ready.set()
                else:
                    env = {k: _fill_placeholders(v) for k, v in spec.get("env", {}).items()}
                    env = {k: v for k, v in env.items() if v}          # drop empty values
                    env.update(self.extra_env)
                    env.setdefault("PYTHONIOENCODING", "utf-8")
                    conn.params = StdioServerParameters(
                        command=resolved,
                        args=[_fill_placeholders(a) for a in spec.get("args", [])],
                        env=env,
                        cwd=str(PROJECT_ROOT),
                    )
            self.servers[name] = conn

    # ---------- lifecycle ----------
    async def start(self):
        """Start every enabled server (in parallel) and wait until each is connected or failed."""
        self._load_config()
        LOG_DIR.mkdir(exist_ok=True)
        for conn in self.servers.values():
            if conn.params is not None:
                self._tasks.append(asyncio.create_task(self._run_server(conn)))
        await asyncio.gather(*(c.ready.wait() for c in self.servers.values()))

    async def _run_server(self, conn: ServerConnection):
        """Own one server connection for its whole life (open -> wait for stop -> close)."""
        log_file = open(LOG_DIR / f"{conn.name}.log", "w", encoding="utf-8")
        self._log_files.append(log_file)
        try:
            async with AsyncExitStack() as stack:
                read, write = await stack.enter_async_context(stdio_client(conn.params, errlog=log_file))
                session = await stack.enter_async_context(ClientSession(read, write))
                with anyio.fail_after(START_TIMEOUT_SECONDS):
                    await session.initialize()
                    tools = (await session.list_tools()).tools
                if conn.allowed_tools is not None:
                    tools = [t for t in tools if t.name in conn.allowed_tools]
                conn.tools, conn.session, conn.status, conn.error = tools, session, "connected", None
                conn.ready.set()
                await self._stop.wait()
        except BaseException as exc:  # noqa: BLE001 - we must never let one server crash the app
            if isinstance(exc, asyncio.CancelledError) and self._stop.is_set():
                return
            conn.status, conn.error = "failed", _friendly_start_error(exc, conn.name)
        finally:
            conn.session = None
            conn.ready.set()

    async def close(self):
        """Ask every server task to close its connection, then wait for them."""
        self._stop.set()
        if self._tasks:
            await asyncio.wait(self._tasks, timeout=10)
        for f in self._log_files:
            f.close()

    # ---------- tools ----------
    def openai_tools(self) -> list[dict]:
        """All tools of connected servers, in OpenAI function-tool format."""
        result = []
        for conn in self.servers.values():
            if conn.status != "connected":
                continue
            for tool in conn.tools:
                schema = _clean_schema(tool.inputSchema or {})
                schema.setdefault("type", "object")
                schema.setdefault("properties", {})
                result.append({
                    "type": "function",
                    "function": {
                        "name": f"{conn.name}{NAME_SEPARATOR}{tool.name}"[:64],
                        "description": (tool.description or "").strip()[:1024],
                        "parameters": schema,
                    },
                })
        return result

    def split_name(self, qualified: str) -> tuple[str, str]:
        """'beds__get_free_beds' -> ('beds', 'get_free_beds')."""
        server, _, tool = qualified.partition(NAME_SEPARATOR)
        return server, tool

    def is_write_tool(self, qualified: str) -> bool:
        """True if a tool changes data (marked WRITE in its docstring or in write_tools)."""
        server, tool_name = self.split_name(qualified)
        conn = self.servers.get(server)
        if conn is None:
            return False
        if tool_name in conn.write_tools:
            return True
        for tool in conn.tools:
            if tool.name == tool_name:
                return "OPERATION: WRITE" in (tool.description or "").upper()
        return False

    async def call_tool(self, qualified: str, arguments: dict) -> tuple[bool, str]:
        """Call a tool. Returns (ok, text). Never raises."""
        server, tool_name = self.split_name(qualified)
        conn = self.servers.get(server)
        if conn is None or conn.session is None:
            return False, f"Tool error: the '{server}' MCP server is not connected."
        if tool_name not in {t.name for t in conn.tools}:
            return False, f"Tool error: '{tool_name}' is not an available tool on '{server}'."
        try:
            result = await conn.session.call_tool(
                tool_name, arguments, read_timeout_seconds=timedelta(seconds=TOOL_TIMEOUT_SECONDS))
        except Exception as exc:  # noqa: BLE001
            return False, f"Tool error: calling {qualified} failed ({str(exc)[:200] or type(exc).__name__})."
        text = "\n".join(getattr(part, "text", "") for part in result.content).strip() or "(empty result)"
        if len(text) > MAX_TOOL_OUTPUT_CHARS:
            text = text[:MAX_TOOL_OUTPUT_CHARS] + "\n...(output shortened)"
        ok = not result.isError and not text.startswith("Friendly Error")
        return ok, text

    # ---------- status ----------
    def status(self) -> list[dict]:
        """One row per server for the status table and the Settings page."""
        return [{
            "name": c.name,
            "description": c.description,
            "status": c.status,
            "tool_count": len(c.tools) if c.status == "connected" else 0,
            "tools": [t.name for t in c.tools] if c.status == "connected" else [],
            "error": c.error,
        } for c in self.servers.values()]
