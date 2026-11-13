# HospitalOS — Architecture

```mermaid
flowchart LR
    U["Hospital staff<br/>(browser)"] --> FE["React frontend<br/>Vite + Tailwind + Recharts"]
    CLI["cli_chat.py<br/>(terminal)"] --> AG
    FE -- "REST: /patients, /beds, /stats ..." --> API["FastAPI backend"]
    FE -- "POST /chat" --> API
    API --> AG["HospitalAgent<br/>tool loop, max 6 steps<br/>write confirmation"]
    AG -- "OpenAI-compatible HTTPS<br/>LLM_BASE_URL / KEY / MODEL" --> LLM["LLM<br/>Gemini free tier or Groq"]
    AG --> HUB["MCP Hub<br/>(official MCP client, stdio)"]
    HUB --> S1["beds"]
    HUB --> S2["patients"]
    HUB --> S3["appointments"]
    HUB --> S4["pharmacy"]
    HUB --> S5["lab"]
    HUB --> S6["billing"]
    HUB --> S7["openfda"]
    HUB -.-> S8["filesystem<br/>(ready-made)"]
    HUB -.-> S9["hospital_db<br/>(ready-made, read-only)"]
    S1 & S2 & S3 & S4 & S5 & S6 --> C["common/db.py"]
    C --> DB[("SQLite<br/>hospitalos.db")]
    API --> DB
    S9 -.-> DB
    S8 -.-> R[/"reports/ folder"/]
    S7 --> FDA["api.fda.gov<br/>(public)"]
```

Dotted lines = ready-made servers, enabled after you approve installing them.

## One chat question, step by step

```mermaid
sequenceDiagram
    participant User
    participant UI as Frontend
    participant API as FastAPI /chat
    participant Agent
    participant LLM
    participant MCP as MCP server

    User->>UI: "Admit patient 8 to ICU"
    UI->>API: {message, history}
    API->>Agent: chat()
    Agent->>LLM: system prompt + history + 21 tools
    LLM-->>Agent: call beds__admit_patient(8, "ICU")
    Note over Agent: WRITE tool → do NOT run yet
    Agent-->>UI: answer + pending_action {id}
    UI->>User: Yes / No card
    User->>UI: Yes
    UI->>API: {message: "yes", confirm_id}
    API->>Agent: resume saved conversation
    Agent->>MCP: admit_patient(8, "ICU")
    MCP-->>Agent: success JSON
    Agent->>LLM: tool result
    LLM-->>Agent: "Sanya Kapoor admitted to ICU-03"
    Agent-->>UI: answer + tool_calls (shown under "Tools used")
```

## Key design decisions
- **One database connection module** (`backend/database.py`), reused by the API, the seed script and every MCP server.
- **Each MCP server is its own process.** If one crashes, the others keep working; the hub marks it `failed`.
- **Tool names are prefixed** with the server name (`beds__get_free_beds`), so the agent always knows where to route a call.
- **READ/WRITE is declared in each tool's docstring**; the agent reads that marker to decide when confirmation is required.
- **The LLM is replaceable**: plain HTTP to `/chat/completions`, no vendor SDK.
