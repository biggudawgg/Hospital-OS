# HospitalOS — Slide Text

## Slide 1 — Title
**HospitalOS: AI-Powered Hospital Management using the Model Context Protocol**
Team members · Guide name · Department · College · Year

## Slide 2 — Problem
- Staff use separate systems for beds, appointments, pharmacy, lab and billing.
- Simple questions ("Is there a free ICU bed?") need several screens and clicks.
- Generic AI chatbots don't know live hospital data, and can invent answers.
- Letting an AI change records without human approval is unsafe.

## Slide 3 — Existing systems
| System | Strength | Limitation |
|--------|----------|-----------|
| Traditional HMS (e.g. OpenMRS, Bahmni) | Complete records, open-source | Form-based; no natural-language access |
| Commercial HMS with dashboards | Reports, analytics | Costly, closed, fixed screens |
| General AI chatbots | Natural language | No live data access; can hallucinate; no safety controls |

## Slide 4 — Proposed system
- Staff ask in plain English; an **AI agent** answers using **live data**.
- The agent reaches data only through **MCP servers** (standard tool interface).
- **Every data change needs a Yes from the user**, enforced in code.
- Modern dashboard: beds, patients, calendar, pharmacy, billing, reports.
- 100% free and open-source, synthetic data, LLM swappable (Gemini / Groq).

## Slide 5 — Architecture
*(Insert the Mermaid diagram from docs/ARCHITECTURE.md, exported as an image.)*
React frontend → FastAPI → AI agent → (LLM + MCP hub) → 9 MCP servers → SQLite database / reports folder / openFDA.

## Slide 6 — MCP servers
| Server | Type | Example tools |
|--------|------|---------------|
| beds | custom | get_free_beds, admit_patient, discharge_patient |
| patients | custom | search_patients, get_patient_history |
| appointments | custom | list_doctor_availability, book_appointment |
| pharmacy | custom | check_stock, list_low_stock, restock_medicine |
| lab | custom | list_pending_tests, order_test |
| billing | custom | list_unpaid_bills, mark_bill_paid |
| openfda | custom | drug_label_info, drug_adverse_events |
| filesystem | ready-made | read/write files in reports/ only |
| hospital_db | ready-made | read-only SQL queries |

## Slide 7 — Tech stack
Python 3.11+, FastAPI, SQLAlchemy, SQLite/PostgreSQL · Official MCP Python SDK (FastMCP + client) ·
OpenAI-compatible LLM API (Gemini free tier / Groq) · React, Vite, Tailwind, Recharts, lucide-react · pytest

## Slide 8 — Safety & reliability
- Tools marked READ or WRITE; WRITE needs confirmation (one-time id, expires in 10 min).
- Input validation and friendly error messages in every tool.
- A failing server doesn't stop the others; rate limits are retried automatically.
- 46 automated tests run on a temporary database copy.

## Slide 9 — Demo
1. "Which ICU beds are free?" 2. Patient history 3. Low-stock medicines 4. Pending lab tests
5. Restock with confirmation 6. Booking cancelled with "No" 7. Multi-server question 8. Missing patient → honest answer

## Slide 10 — Results
- 7 custom + 2 ready-made MCP servers, 21+ tools.
- Answers in a few seconds on free LLM tiers.
- No invented data in tests; every write confirmed.

## Slide 11 — Limitations
- Free LLM tiers are rate-limited and sometimes slow.
- Synthetic data only; not validated with real hospital workflows.
- No login / roles yet; anyone with the URL can use it.
- English only; LLM may still misread ambiguous requests (mitigated by confirmation).

## Slide 12 — Future scope
- Login with roles (doctor, nurse, admin) and per-role tool access.
- Audit log of every write action.
- Voice input and regional languages.
- FHIR export for interoperability; real calendar integration.
- Deploy with Docker and PostgreSQL.

## Slide 13 — Conclusion
MCP lets an AI agent use many hospital systems through one standard interface, safely,
with humans approving every change — built entirely with free, open-source tools.
