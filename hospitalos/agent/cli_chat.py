"""
agent/cli_chat.py — Chat with the HospitalOS agent in the terminal (no web server needed).

Run from the hospitalos/ folder:
  python -m agent.cli_chat

Type your question and press Enter. Type "exit" to quit.
When the agent wants to change data it asks for confirmation: answer yes or no.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent.agent import HospitalAgent  # noqa: E402
from agent.mcp_hub import MCPHub  # noqa: E402
from agent.settings import llm_config_problem  # noqa: E402


def print_tools(tool_calls):
    """Show which tools were used (short version)."""
    for tc in tool_calls:
        args = ", ".join(f"{k}={v!r}" for k, v in tc["arguments"].items())
        print(f"   [tool] {tc['server']}.{tc['tool']}({args}) -> {tc['status']} ({tc['kind']})")


async def main():
    problem = llm_config_problem()
    if problem:
        print("WARNING:", problem)
    hub = MCPHub()
    print("Starting MCP servers...")
    await hub.start()
    connected = [s["name"] for s in hub.status() if s["status"] == "connected"]
    print(f"Connected: {', '.join(connected) or 'none'}\n")
    agent = HospitalAgent(hub)
    history, pending_id = [], None

    try:
        while True:
            try:
                text = await asyncio.to_thread(input, "You: ")
            except (EOFError, KeyboardInterrupt):
                break
            text = text.strip()
            if not text:
                continue
            if text.lower() in ("exit", "quit"):
                break
            # Only treat the reply as an answer to the confirmation if it is yes/no
            is_answer = text.lower().rstrip(".!") in {"yes", "y", "no", "n", "ok", "confirm", "cancel"}
            result = await agent.chat(text, history, confirm_id=pending_id if is_answer else None)
            print_tools(result["tool_calls"])
            print(f"\nHospitalOS: {result['answer']}\n")
            pending_id = result["pending_action"]["id"] if result["pending_action"] else None
            if pending_id:
                print("   (Reply 'yes' to confirm or 'no' to cancel.)\n")
            history += [{"role": "user", "content": text}, {"role": "assistant", "content": result["answer"]}]
    finally:
        await hub.close()
        print("Bye!")


if __name__ == "__main__":
    asyncio.run(main())
