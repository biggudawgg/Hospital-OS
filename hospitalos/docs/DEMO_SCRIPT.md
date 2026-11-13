# HospitalOS — 5-Minute Demo Script

**Before the demo (5 minutes earlier)**
```powershell
cd hospitalos
.venv\Scripts\activate
python -m data.seed --force          # fresh, identical data every time
python -m agent.check_servers        # all custom servers "connected"?
uvicorn backend.main:app             # terminal 1
cd frontend; npm run dev             # terminal 2 -> open http://localhost:5173
```
Have the **Chat** page and the **Settings** page open in two tabs. Free tiers are rate-limited:
leave ~10 seconds between questions.

---

### 0:00 – 0:40 · The problem and the dashboard
- "Hospital staff jump between many systems to answer simple questions. HospitalOS lets them just ask."
- Show **Dashboard**: vital cards, ward occupancy rings, appointments chart, alerts.
- Show **Settings**: the row of green dots = MCP servers connected, with tool counts.

### 0:40 – 2:00 · Reading data (one server each)
1. **"Which ICU beds are free?"** → open *Tools used*: `beds.get_free_beds` with input `{"ward": "ICU"}` and its JSON output.
2. **"Find patient Meera and show her full history."** → `patients.search_patients` then `patients.get_patient_history` (two steps).
3. **"List medicines with stock below 30."** → `pharmacy.list_low_stock`.
4. **"What lab tests are pending?"** → `lab.list_pending_tests`.

Say: "The AI never answers from memory — every fact comes from a tool, and you can see exactly which one."

### 2:00 – 3:30 · Writing data with confirmation
5. **"Restock Insulin Glargine by 100 units."**
   → A yellow **Confirmation needed** card appears. Point out: *nothing has changed yet*.
   → Click **Yes** → success. Open **Pharmacy** page: stock went from 12 to 112.
6. **"Is doctor 1 free next Monday? Book patient 3 at the first open slot."**
   → `appointments.list_doctor_availability` runs, then a confirmation card for `book_appointment`.
   → Click **No** → "cancelled". Say: "Safety is enforced in code, not just by asking the AI nicely."

### 3:30 – 4:20 · One question, several servers
7. **"Give me patient 1's lab results and unpaid bills, and what openFDA lists as warnings for atorvastatin."**
   → *Tools used* shows `lab.get_results`, `billing.get_bill`, `openfda.drug_label_info` — three servers in one answer.

### 4:20 – 4:45 · Honest when data is missing
8. **"Show patient 9999."** → "I could not find patient 9999." The AI does not invent data.

### 4:45 – 5:00 · Wrap-up
- 7 custom MCP servers + 2 ready-made connectors, 21+ tools, 46 automated tests.
- Free, open-source, synthetic data only; LLM swappable between Gemini and Groq with three settings.

---

**If something goes wrong live**
| Symptom | Say / do |
|---------|---------|
| "rate limit reached" | "Free tier limit — this is the friendly error handling." Wait 30 s, retry. |
| Backend offline banner | Restart uvicorn; the UI shows a clear error instead of crashing. |
| openFDA slow (no Wi-Fi) | Skip question 7's openFDA part; the hospital servers work offline. |
