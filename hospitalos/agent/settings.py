"""
agent/settings.py — Reads settings from hospitalos/.env (one place for all agent settings).

The LLM is swappable with exactly three values (OpenAI-compatible format):
  LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
A missing .env does not crash anything: the agent just reports "LLM not configured".
"""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]   # hospitalos/
AGENT_DIR = PROJECT_ROOT / "agent"
CONFIG_PATH = AGENT_DIR / "mcp_config.json"
LOG_DIR = AGENT_DIR / "logs"                          # MCP server error output goes here

load_dotenv(PROJECT_ROOT / ".env")

PLACEHOLDER_KEYS = {"", "PASTE_YOUR_KEY_HERE", "YOUR_GEMINI_API_KEY"}


def llm_settings() -> dict:
    """Return the three LLM values (read fresh each time so .env edits apply on restart)."""
    return {
        "base_url": os.getenv("LLM_BASE_URL", "").strip(),
        "api_key": os.getenv("LLM_API_KEY", "").strip(),
        "model": os.getenv("LLM_MODEL", "").strip(),
    }


def llm_config_problem() -> str | None:
    """Explain what is missing from the LLM config, or None if it looks complete."""
    s = llm_settings()
    missing = [name for name, key in [("LLM_BASE_URL", "base_url"), ("LLM_MODEL", "model")] if not s[key]]
    if s["api_key"] in PLACEHOLDER_KEYS:
        missing.append("LLM_API_KEY")
    if missing:
        return (f"The AI model is not configured yet (missing: {', '.join(missing)}). "
                "Copy .env.example to .env and fill in these values, then restart.")
    return None
