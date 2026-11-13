# HospitalOS — AI Hospital Management Platform with MCP

HospitalOS is a web app where hospital staff chat with an AI agent
("Which ICU beds are free?", "Book Dr. Menon for patient 3 next Monday at 10:00").
The agent answers by calling tools on **multiple MCP servers** (MCP = Model Context
Protocol, a standard way for an AI to call tools). Built for a college PBL project.

- 100% free and open-source. Only **synthetic (fake) data** — never real patients.
- Any OpenAI-compatible LLM: switch between **Gemini free tier** and **Groq** with 3 values in `.env`.
- Every data-changing action needs the user's **Yes** first — enforced in code, not just in the prompt.

| Part | Technology |
|------|-----------|
| Backend API | Python 3.11+, FastAPI, SQLAlchemy, SQLite (PostgreSQL via one setting) |
| MCP servers | Official Python MCP SDK (FastMCP), stdio transport |
| AI agent | MCP Python client SDK + any OpenAI-compatible chat API (httpx) |
| Frontend | React 18, Vite, Tailwind CSS, Recharts, lucide-react |
| Tests | pytest (46 tests) |

See also: [Architecture](docs/ARCHITECTURE.md) · [Demo script](docs/DEMO_SCRIPT.md) ·
[Slide text](docs/PPT_SLIDES.md) · [Teacher Q&A](docs/TEACHER_QA.md)

---

## 1. Folder structure

```text
hospitalos/
├── backend/                 FastAPI app
│   ├── database.py          the ONE place the database connection is made
│   ├── models.py            8 tables: patients, doctors, appointments, wards, beds, medicines, lab_tests, bills
│   ├── schemas.py           request/response shapes (Pydantic)
│   ├── main.py              CRUD endpoints for every table + admit/discharge
│   ├── agent_routes.py      POST /chat, GET /mcp/status, GET /llm/info (starts all MCP servers)
│   └── dashboard_routes.py  GET /stats, /reports
├── mcp_servers/
│   ├── common/db.py         shared database helper (no copy-paste between servers)
│   ├── beds/ patients/ appointments/ pharmacy/ lab/ billing/   6 hospital servers (server.py + manual test script)
│   └── openfda/             7th custom server: public FDA drug info (internet, no key)
├── agent/
│   ├── mcp_config.json      list of ALL MCP servers (command, args, env)
│   ├── mcp_hub.py           starts/connects every server, converts tools to OpenAI format
│   ├── llm.py               calls the LLM (retries on rate limit, friendly errors)
│   ├── agent.py             system prompt + tool-calling loop (max 6 steps) + confirmation logic
│   ├── check_servers.py     prints a status table of all servers
│   └── cli_chat.py          chat in the terminal
├── frontend/                React app (9 pages)
├── data/seed.py             fills the database with fake data (Faker, fixed seed)
├── reports/                 the ONLY folder the filesystem MCP may access
├── tests/                   pytest suite (MCP tools, API, 3 agent scenarios)
├── docs/                    architecture, demo script, slides, teacher Q&A
├── .env.example  requirements.txt  pytest.ini  .gitignore
```

## 2. MCP servers

| # | Server | Type | Tools (R = read, W = write, needs confirmation) |
|---|--------|------|------|
| 1 | beds | custom | get_free_beds R · admit_patient W · discharge_patient W |
| 2 | patients | custom | search_patients R · get_patient R · get_patient_history R |
| 3 | appointments | custom | list_doctor_availability R · list_appointments R · book_appointment W · cancel_appointment W |
| 4 | pharmacy | custom | check_stock R · list_low_stock R · restock_medicine W |
| 5 | lab | custom | list_pending_tests R · get_results R · order_test W |
| 6 | billing | custom | get_bill R · list_unpaid_bills R · mark_bill_paid W |
| 7 | openfda | custom | drug_label_info R · drug_adverse_events R |
| 8 | filesystem | ready-made | `@modelcontextprotocol/server-filesystem` (npm), restricted to `reports/` |
| 9 | hospital_db | ready-made | `mcp-server-sqlite` (PyPI), only read_query · list_tables · describe_table exposed |

**Ready-made servers are switched off until you approve installing them** (see section 5).

## 3. Setup (Windows, step by step)

> **Tip:** move the project to a simple path first, e.g. `C:\Users\you\Downloads\hospitalos`.
> The current folder name contains `&` and `—`, which confuse some Windows tools.
> (The npm scripts already work around the `&` problem.)

```powershell
cd hospitalos

# 1. Create a virtual environment (a private Python just for this project)
python -m venv .venv

# 2. Turn it on (your prompt then starts with (.venv))
.venv\Scripts\activate

# 3. Install the Python libraries listed in requirements.txt
pip install -r requirements.txt

# 4. Create your private settings file, then open it and paste your LLM key
copy .env.example .env

# 5. Fill the database with fake data (type y when asked)
python -m data.seed
```

Get a free key: Gemini → https://aistudio.google.com/apikey · Groq → https://console.groq.com/keys.
Put it in `.env` as `LLM_API_KEY`. To switch provider, change only `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`.

## 4. Run it

```powershell
# Check every MCP server starts (prints name, status, tool count)
python -m agent.check_servers

# Terminal 1: backend API + all MCP servers   -> http://127.0.0.1:8000/docs
uvicorn backend.main:app --reload

# Terminal 2: frontend                         -> http://localhost:5173
cd frontend
copy .env.example .env
npm install
npm run dev

# Or chat in the terminal without the web app
python -m agent.cli_chat

# Run all tests (uses a temporary copy of the database; your data is safe)
python -m pytest
```

Stop servers with **Ctrl+C** in their terminal (closing the window may leave `--reload` workers running).

## 5. Enabling the ready-made MCP servers (needs your approval)

| Package | Publisher | Version checked | Notes |
|---------|-----------|-----------------|-------|
| `@modelcontextprotocol/server-filesystem` | Model Context Protocol org (official reference servers, maintainers incl. Anthropic staff) | 2.3.0, published 2026-11-11 | Tools: read_file, write_file, edit_file, list_directory, search_files, … Only `reports/` is allowed. Write tools need confirmation. |
| `mcp-server-sqlite` (PyPI) | Model Context Protocol reference servers (now archived) | 2025.4.25 | Tools: read_query, write_query, create_table, list_tables, describe_table, append_insight. We expose only the 3 read tools. |

To enable after you approve:
```powershell
pip install mcp-server-sqlite          # for hospital_db
# filesystem uses npx and downloads the package the first time it starts
```
Then set `"enabled": true` for those entries in `agent/mcp_config.json` and re-run `python -m agent.check_servers`.

Google Calendar MCP was **not** added: no maintained, verifiable free package was confirmed, and it needs
an OAuth setup with a Google account. The Calendar page uses the hospital's own appointments instead.

## 6. API endpoints (full list at /docs)

| Endpoint | What it does |
|----------|--------------|
| `GET/POST/PUT /patients, /doctors, /wards, /beds, /appointments, /medicines, /lab_tests, /bills` | list, get by id, create, update |
| `POST /beds/admit`, `POST /beds/discharge` | the only way to change bed occupancy (keeps beds and patients in sync) |
| `POST /chat` | `{message, history, confirm_id?}` → `{answer, tool_calls, pending_action, error}` |
| `GET /mcp/status` | status + tool count of every MCP server |
| `GET /stats` | dashboard numbers, chart data and alerts |
| `GET /reports`, `GET /reports/{name}`, `POST /reports/occupancy` | report files in `reports/` |

### How write confirmation works
1. You ask "Admit patient 8 to ICU". The LLM calls `beds__admit_patient`.
2. The agent does **not** run it. It returns `pending_action` (with an `id`) and the UI shows Yes/No.
3. Clicking **Yes** sends `{message: "yes", confirm_id: id}`; only then is the tool executed.
   **No** cancels. Each confirmation works once and expires after 10 minutes.

## 7. Eight sample questions to try

1. Which ICU beds are free?
2. Find patient Meera and show her full history.
3. List medicines with stock below 30.
4. What lab tests are pending?
5. Show all unpaid bills and the total outstanding.
6. Is Dr. Rajesh Menon (doctor 1) free next Monday? Book patient 3 at the first open slot. *(write → confirm)*
7. Restock Insulin Glargine by 100 units. *(write → confirm)*
8. Patient 1's lab results — and what does openFDA say about the warnings for atorvastatin? *(uses several servers)*

## 8. Troubleshooting

| Problem | Fix |
|---------|-----|
| `pip install` tries to build Rust / fails | Use Python 3.11–3.13 if possible; `requirements.txt` uses version ranges so wheels are found |
| `No module named 'mcp.server.fastmcp'` | You have mcp 2.x. Run `pip install "mcp[cli]>=1.9,<2"` |
| Chat says "AI model is not configured" | Create `.env` from `.env.example` and fill the 3 LLM values, then restart uvicorn |
| "rate limit reached" | Free tiers allow a few requests per minute; wait and retry, or switch to Groq |
| A server shows `failed` in Settings | Read `agent/logs/<server>.log` |
| Dashboard says "database is empty" | `python -m data.seed` |
| Frontend says "Cannot reach the backend" | Start uvicorn; check `VITE_API_URL` in `frontend/.env` |
| `npm run dev` fails with a weird path | Folder path contains `&`; move the project to a simple path |

## 9. Rules this project follows
- Secrets only in `.env` (git-ignored). `.env.example` is the committed template.
- Only fake data from `data/seed.py`; phone numbers use the fake `555-` prefix.
- Only the drug name (never patient data) is sent to openFDA.
