# Counsly — Tech Stack

**Source:** PRD v2.0, Section 12
**Last updated:** 12 April 2026

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14+ (App Router) · TailwindCSS |
| Auth | Direct Google OAuth · backend-created Counsly session · `/auth/callback` |
| State | React Context + useState |
| Charts | Recharts |
| Drag & Drop | @dnd-kit/core + @dnd-kit/sortable |
| PDF | jsPDF (client-side) |
| Maps | Leaflet.js + React-Leaflet + markercluster + OpenStreetMap |
| Payment | Razorpay SDK |
| Backend | FastAPI (Python) · async · httpx · sse-starlette |
| Rank Guidance | `rank_lookup` table query — O(1), ~5–10ms |
| Chat | OpenRouter · DeepSeek V3.2 · `OPENROUTER_MODEL` env var · streaming SSE |
| Database | Supabase PostgreSQL · RLS + service-role |
| Frontend Hosting | Vercel |
| Backend Hosting | Railway |
| Monitoring | UptimeRobot |
| Analytics | GA4 |
| Domain | counsly.in (GoDaddy → Vercel DNS) |
| Admin | Telegram bot (v1) |
| Build Executor | Codex |

---

## Runtime Environment Variables

### Web (Required)

- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_RAZORPAY_KEY_ID`

### API (Required)

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `SESSION_SECRET`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `CORS_ORIGINS`
- `TRUSTED_HOSTS`

### API (Optional — paid/chat/payments)

- `OPENROUTER_API_KEY`
- `OPENROUTER_API_URL`
- `OPENROUTER_MODEL`
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`

**Runtime rule:** Missing optional keys must degrade those features gracefully. They must not prevent app boot.
