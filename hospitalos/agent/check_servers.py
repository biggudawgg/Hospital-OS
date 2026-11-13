"""
agent/check_servers.py — Starts every MCP server in mcp_config.json and prints a status table.

Run from the hospitalos/ folder:
  python -m agent.check_servers

Example output:
  SERVER         STATUS          TOOLS  NOTE
  beds           connected           3  Custom: free beds, admit and discharge
  filesystem     disabled            0  disabled in mcp_config.json
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent.mcp_hub import MCPHub  # noqa: E402

GREEN, RED, GREY, RESET = "\033[32m", "\033[31m", "\033[90m", "\033[0m"


async def main():
    hub = MCPHub()
    print("Starting MCP servers... (first start can take a few seconds)\n")
    await hub.start()
    rows = hub.status()
    print(f"{'SERVER':<14} {'STATUS':<15} {'TOOLS':>5}  NOTE")
    print("-" * 78)
    for row in rows:
        color = GREEN if row["status"] == "connected" else RED if row["status"] == "failed" else GREY
        note = row["error"] or row["description"]
        print(f"{row['name']:<14} {color}{row['status']:<15}{RESET} {row['tool_count']:>5}  {note[:60]}")
    connected = [r for r in rows if r["status"] == "connected"]
    print("-" * 78)
    print(f"{len(connected)}/{len(rows)} servers connected, "
          f"{sum(r['tool_count'] for r in connected)} tools available to the agent.")
    await hub.close()


if __name__ == "__main__":
    asyncio.run(main())
