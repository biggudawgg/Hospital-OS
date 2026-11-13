"""
tests/test_agent.py — Agent scenarios with REAL MCP servers (over stdio) and a FAKE LLM.

The fake LLM returns scripted replies, so the tests are free, fast and repeatable,
while everything else (MCP client, servers, database, confirmation logic) is real.

Scenarios:
  1. READ question  -> agent calls get_free_beds and answers with the real number.
  2. WRITE request  -> agent does NOT run admit_patient until the user says "yes";
                       saying "no" cancels it.
  3. Failures       -> tool "not found", LLM rate limit, and a server that cannot start.
"""

import asyncio
import json
import sqlite3

import agent.agent as agent_module
from agent.agent import HospitalAgent
from agent.llm import LLMError
from agent.mcp_hub import MCPHub
from tests.conftest import TEST_DB, TEST_DB_URL


def tool_call(name, args, call_id="call_1"):
    return {"role": "assistant", "content": None, "tool_calls": [
        {"id": call_id, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}]}


def scripted_llm(replies):
    """A fake chat_completion that returns the given replies in order and records what it saw."""
    seen = []

    async def fake(messages, tools=None):
        seen.append([dict(m) for m in messages])
        reply = replies[len(seen) - 1]
        return reply(messages) if callable(reply) else reply
    fake.seen = seen
    return fake


def patient_admitted(patient_id) -> bool:
    with sqlite3.connect(TEST_DB) as conn:
        return bool(conn.execute("SELECT is_admitted FROM patients WHERE id=?", (patient_id,)).fetchone()[0])


async def with_hub(servers, body):
    hub = MCPHub(only=servers, extra_env={"DATABASE_URL": TEST_DB_URL})
    await hub.start()
    try:
        return await body(hub)
    finally:
        await hub.close()


def test_scenario_read_question(monkeypatch):
    def final_answer(messages):
        free = json.loads(messages[-1]["content"])["free_count"]   # read the real tool result
        return {"role": "assistant", "content": f"There are {free} free ICU beds."}

    fake = scripted_llm([tool_call("beds__get_free_beds", {"ward": "ICU"}), final_answer])
    monkeypatch.setattr(agent_module, "chat_completion", fake)

    async def body(hub):
        assert {s["name"]: s["status"] for s in hub.status()} == {"beds": "connected", "patients": "connected"}
        return await HospitalAgent(hub).chat("Which ICU beds are free?", [])

    result = asyncio.run(with_hub(["beds", "patients"], body))
    assert result["answer"] == "There are 8 free ICU beds."
    call = result["tool_calls"][0]
    assert (call["server"], call["tool"], call["status"], call["kind"]) == ("beds", "get_free_beds", "ok", "READ")
    assert result["pending_action"] is None
    # The LLM received tools in OpenAI format with server-prefixed names
    assert fake.seen[0][0]["role"] == "system"


def test_scenario_write_needs_confirmation(monkeypatch):
    fake = scripted_llm([
        tool_call("beds__admit_patient", {"patient_id": 3, "ward": "ICU"}),
        {"role": "assistant", "content": "Done: Rohan Verma admitted to ICU."},
        tool_call("beds__admit_patient", {"patient_id": 5, "ward": "General"}, "call_2"),
        {"role": "assistant", "content": "OK, cancelled."},
    ])
    monkeypatch.setattr(agent_module, "chat_completion", fake)

    async def body(hub):
        agent = HospitalAgent(hub)
        first = await agent.chat("Admit patient 3 to ICU", [])
        assert first["pending_action"]["tool"] == "admit_patient"
        assert first["tool_calls"][-1]["status"] == "pending_confirmation"
        assert patient_admitted(3) is False                     # NOT executed yet

        second = await agent.chat("yes", [], confirm_id=first["pending_action"]["id"])
        assert patient_admitted(3) is True                      # executed after "yes"
        assert second["tool_calls"][-1]["status"] == "ok"
        assert second["answer"].startswith("Done")

        reused = await agent.chat("yes", [], confirm_id=first["pending_action"]["id"])
        assert "expired" in reused["answer"]                    # a confirmation works only once

        third = await agent.chat("Admit patient 5 to General", [])
        fourth = await agent.chat("no", [], confirm_id=third["pending_action"]["id"])
        assert fourth["tool_calls"][-1]["status"] == "cancelled"
        assert patient_admitted(5) is False                     # "no" means nothing changed

    asyncio.run(with_hub(["beds"], body))


def test_scenario_failures_are_handled(monkeypatch, tmp_path):
    # (a) Tool says "not found" -> the LLM sees the honest error text
    def honest(messages):
        assert "not found" in messages[-1]["content"]
        return {"role": "assistant", "content": "I could not find patient 9999."}
    monkeypatch.setattr(agent_module, "chat_completion",
                        scripted_llm([tool_call("patients__get_patient", {"patient_id": 9999}), honest]))

    async def body(hub):
        agent = HospitalAgent(hub)
        result = await agent.chat("Show patient 9999", [])
        assert result["tool_calls"][0]["status"] == "error"
        assert "could not find" in result["answer"]

        # (b) LLM rate limit -> friendly message, no crash
        async def rate_limited(messages, tools=None):
            raise LLMError("The AI model's free-tier rate limit was reached. Please wait a minute and try again.")
        monkeypatch.setattr(agent_module, "chat_completion", rate_limited)
        result = await agent.chat("Which ICU beds are free?", [])
        assert result["error"] is True and "rate limit" in result["answer"]

    asyncio.run(with_hub(["patients"], body))

    # (c) A server that cannot start is marked failed; the good one still works
    config = tmp_path / "mcp_config.json"
    config.write_text(json.dumps({"mcpServers": {
        "broken": {"command": "${PYTHON}", "args": ["-c", "import sys; sys.exit(1)"], "env": {}},
        "missing": {"command": "definitely-not-a-real-command-xyz", "args": []},
        "beds": {"command": "${PYTHON}", "args": ["${ROOT}/mcp_servers/beds/server.py"], "env": {}},
    }}), encoding="utf-8")

    async def check():
        hub = MCPHub(config_path=config, extra_env={"DATABASE_URL": TEST_DB_URL})
        await hub.start()
        status = {s["name"]: s["status"] for s in hub.status()}
        await hub.close()
        return status

    assert asyncio.run(check()) == {"broken": "failed", "missing": "not_installed", "beds": "connected"}
