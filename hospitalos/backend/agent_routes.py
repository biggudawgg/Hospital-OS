"""
backend/agent_routes.py — Chat endpoint + MCP server status for the frontend.

  POST /chat         {message, history, confirm_id?} -> {answer, tool_calls, pending_action, error}
  GET  /mcp/status   one row per MCP server (used by the Settings page dots)
  GET  /llm/info     which model is configured (never returns the API key)

The MCP hub (all servers) is started once when FastAPI starts (see `lifespan`)
and closed when FastAPI stops. Set HOSPITALOS_DISABLE_MCP=1 to skip it (API tests).
"""

import os
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import APIRouter, FastAPI, Request
from pydantic import BaseModel, Field

from agent.agent import HospitalAgent
from agent.mcp_hub import MCPHub
from agent.settings import llm_config_problem, llm_settings

router = APIRouter(tags=["AI Agent"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start all MCP servers when the API starts; stop them when it stops."""
    app.state.hub = None
    app.state.agent = None
    if os.getenv("HOSPITALOS_DISABLE_MCP") != "1":
        hub = MCPHub()
        await hub.start()
        app.state.hub = hub
        app.state.agent = HospitalAgent(hub)
        connected = sum(1 for s in hub.status() if s["status"] == "connected")
        print(f"[HospitalOS] MCP servers connected: {connected}/{len(hub.status())}")
    yield
    if app.state.hub is not None:
        await app.state.hub.close()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="The user's question")
    history: list[ChatMessage] = Field(default_factory=list, description="Earlier messages")
    confirm_id: str | None = Field(None, description="Send with 'yes'/'no' to answer a confirmation card")


@router.post("/chat")
async def chat(payload: ChatRequest, request: Request):
    """Ask the AI agent a question. It answers using the MCP tools."""
    agent: HospitalAgent | None = request.app.state.agent
    if agent is None:
        return {"answer": "The AI agent is not running (MCP servers are disabled on this server).",
                "tool_calls": [], "pending_action": None, "error": True}
    history = [m.model_dump() for m in payload.history]
    return await agent.chat(payload.message, history, payload.confirm_id)


@router.get("/mcp/status")
def mcp_status(request: Request):
    """Connection status and tool count of every MCP server."""
    hub: MCPHub | None = request.app.state.hub
    return {"servers": hub.status() if hub else [], "agent_running": hub is not None}


@router.get("/llm/info")
def llm_info():
    """Which LLM is configured (provider host + model). The key is never returned."""
    s = llm_settings()
    return {"provider_host": urlparse(s["base_url"]).hostname, "model": s["model"],
            "configured": llm_config_problem() is None, "problem": llm_config_problem()}
