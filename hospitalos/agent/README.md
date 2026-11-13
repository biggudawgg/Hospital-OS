# HospitalOS AI Agent

| File | What it does |
|------|-------------|
| `mcp_config.json` | Lists every MCP server: command, args, env (values like `${DATABASE_URL}` come from `.env`) |
| `settings.py` | Reads `.env`; the three LLM values `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` |
| `mcp_hub.py` | Starts all servers over stdio, lists their tools, converts them to OpenAI format, calls tools safely |
| `llm.py` | Sends the chat to the LLM; retries on rate limits; friendly error messages |
| `agent.py` | System prompt, tool-calling loop (max 6 steps), write confirmation |
| `check_servers.py` | `python -m agent.check_servers` → table of server, status, tool count |
| `cli_chat.py` | `python -m agent.cli_chat` → chat in the terminal |
| `logs/` | Error output of each server (look here when a server shows `failed`) |

Run commands from the `hospitalos/` folder.
