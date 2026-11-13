# HospitalOS Frontend

React + Vite + Tailwind + Recharts + lucide-react.

```powershell
cd frontend
copy .env.example .env      # sets VITE_API_URL (backend address)
npm install                 # downloads the libraries into node_modules/
npm run dev                 # starts the app at http://localhost:5173
npm run build               # production build into dist/
```

## Where things are
| Path | What it is |
|------|-----------|
| `tailwind.config.js` | **Design tokens** — colours, fonts, radii, shadows. Change the look here. |
| `src/index.css` | Shared classes: `.card`, `.btn-primary`, `.input`, `.th`, `.num` |
| `src/api.js` | All backend calls + `useApi` hook (loading / error / reload) |
| `src/components/` | TopBar, Sidebar, VitalCard, StatusChip, BedTile, OccupancyRing, ChatPanel, ToolsUsed, ConfirmCard, AlertPanel, SkeletonCard, States |
| `src/pages/` | Dashboard, Chat, Beds, Patients, Calendar, Pharmacy, Billing, Reports, Settings |

Every page handles three states: **loading** (skeletons), **empty** (EmptyState) and **backend down** (ErrorState with Try again).

Note: `design.md` was not available, so tokens follow the existing HospitalOS style
(alabaster canvas, white cards, medical teal, Plus Jakarta Sans / Public Sans / JetBrains Mono).
Update `tailwind.config.js` when design.md is provided.
