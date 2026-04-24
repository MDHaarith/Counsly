# Counsly — Project Framework

> Every AI agent working in this repo MUST read this file before writing code.
> Coordinate via TIMELINE.md. One agent writes code at a time.

---

## Directory Structure

```
counsly/
├── frontend/                        # Next.js 16 App Router
│   ├── src/
│   │   ├── app/                     # App Router pages
│   │   │   ├── (public)/            # Unauthenticated: landing, login, subscribe
│   │   │   │   ├── page.tsx         # Landing
│   │   │   │   ├── login/page.tsx
│   │   │   │   └── subscribe/page.tsx
│   │   │   ├── (auth)/              # Authenticated: main app
│   │   │   │   ├── layout.tsx       # TabBar wrapper
│   │   │   │   ├── dashboard/page.tsx
│   │   │   │   ├── recommendations/page.tsx
│   │   │   │   ├── choices/page.tsx
│   │   │   │   ├── explore/
│   │   │   │   │   ├── page.tsx
│   │   │   │   │   └── [code]/page.tsx
│   │   │   │   ├── profile/page.tsx
│   │   │   │   └── onboarding/
│   │   │   │       ├── layout.tsx   # Step indicator
│   │   │   │       ├── marks/page.tsx
│   │   │   │       ├── details/page.tsx
│   │   │   │       └── rank/page.tsx
│   │   │   ├── layout.tsx           # Root layout
│   │   │   ├── globals.css          # Design tokens + base styles
│   │   │   └── middleware.ts        # Auth route protection
│   │   ├── components/
│   │   │   └── ui/                  # 11 design system components (no external libs)
│   │   │       ├── Button.tsx
│   │   │       ├── Card.tsx
│   │   │       ├── Input.tsx
│   │   │       ├── Badge.tsx
│   │   │       ├── ProgressBar.tsx
│   │   │       ├── TabBar.tsx
│   │   │       ├── PageHeader.tsx
│   │   │       ├── Skeleton.tsx
│   │   │       ├── Toast.tsx
│   │   │       ├── UnlockOverlay.tsx
│   │   │       └── Sheet.tsx
│   │   ├── lib/
│   │   │   ├── api.ts               # Backend API client (fetch wrapper)
│   │   │   ├── auth.ts              # Auth utilities
│   │   │   ├── access.ts            # Free/paid access control
│   │   │   └── safety.ts            # Safe/Moderate/Ambitious computation
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   ├── useSubscription.ts
│   │   │   ├── usePhase.ts          # TNEA phase polling
│   │   │   └── useStudent.ts
│   │   ├── contexts/
│   │   │   └── AppContext.tsx        # Global state provider
│   │   └── types/
│   │       └── index.ts             # Shared TypeScript types
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   └── .env.local.example
│
├── backend/                         # FastAPI (Python 3.12+)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── config.py                # Settings from env vars
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── google.py            # Google OAuth flow
│   │   │   ├── session.py           # JWT session management
│   │   │   └── middleware.py        # Auth dependency
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # /api/auth/*
│   │   │   ├── onboarding.py        # /api/onboarding/*
│   │   │   ├── recommendations.py
│   │   │   ├── choices.py
│   │   │   ├── explore.py
│   │   │   ├── payments.py
│   │   │   ├── profile.py
│   │   │   └── config.py            # /api/config/* (phase, news)
│   │   ├── models/                  # Pydantic schemas
│   │   │   └── __init__.py
│   │   ├── services/                # Business logic
│   │   │   └── __init__.py
│   │   └── db/
│   │       ├── __init__.py
│   │       ├── connection.py        # Supabase connection pool
│   │       └── queries.py           # SQL query functions
│   ├── scripts/
│   │   ├── seed_colleges.py
│   │   ├── seed_branches.py
│   │   ├── seed_college_branches.py
│   │   ├── seed_community_seats.py
│   │   ├── seed_cutoffs.py
│   │   ├── seed_rank_lookup.py
│   │   └── seed_app_config.py
│   ├── migrations/
│   │   └── 001_initial_schema.sql
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── .env.example
│
├── docs/                            # PRD sections 01-18
├── .agents/council/                 # Council debate reports
├── DESIGN.md                        # Visual design specification
├── PRD-v2_1.md                      # Master product requirements
├── FRAMEWORK.md                     # THIS FILE
├── TIMELINE.md                      # Shared agent work registry
├── AGENTS.md                        # Agent instructions
├── CLAUDE.md
├── .gitignore
└── .env.example                     # Root env template
```

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | Next.js (App Router) | 16+ |
| UI Framework | React | 19+ |
| Language (FE) | TypeScript | 5+ |
| Styling | TailwindCSS | v4 |
| Backend | FastAPI | 0.115+ |
| Language (BE) | Python | 3.12+ |
| Database | Supabase PostgreSQL | Existing project |
| Auth | Direct Google OAuth | — |
| Payment | Razorpay SDK | Test → Production |
| PDF | jsPDF (client-side) | — |
| Hosting (FE) | Vercel | — |
| Hosting (BE) | Railway | — |
| Domain | counsly.in | — |

---

## Design System Rules

**Authority:** `docs/13-design-tokens.md` overrides `DESIGN.md` for any conflict.

### Colors
| Token | Hex | Use |
|-------|-----|-----|
| Parchment | `#f5f4ed` | Page background |
| Ivory | `#faf9f5` | Card background |
| Surface Alt | `#EEE7DC` | Section dividers |
| Warm Sand | `#e8e6dc` | Secondary buttons, skeleton base |
| Anthracite | `#141413` | Primary text |
| Olive Gray | `#5e5d59` | Body text |
| Stone Gray | `#87867f` | Metadata, inactive |
| Terracotta | `#c96442` | Primary CTA background ONLY |
| Coral Accent | `#d97757` | Secondary accent moments |
| Safe | `#4E8A62` | Rank safely above cutoff |
| Moderate | `#C17B4A` | Rank within range |
| Ambitious | `#B45A52` | Rank below cutoff |
| Error | `#b53333` | Error states |
| Focus Blue | `#3898ec` | Input focus rings ONLY |

### Typography
| Role | Font | Constraint |
|------|------|-----------|
| Headings | Georgia, 'Times New Roman', serif | Weight 500 max, never 700+ |
| Body | Inter, system-ui, sans-serif | 400-500 |
| Numeric Data | 'JetBrains Mono', monospace | Ranks, marks, cutoffs, countdowns |

### Rules
- No external UI libraries (no shadcn, Radix, Headless UI)
- No dark mode
- Terracotta ONLY on primary CTAs — never on text, badges, or secondary elements
- Focus Blue ONLY on input focus rings — never as a design accent
- 48px minimum touch targets on mobile
- 360px mobile-first baseline, test at 390px
- Skeleton loaders (warm-sand shimmer), never spinners
- Warm ring borders (`0 0 0 1px`), not heavy drop shadows
- Cards: 12px radius (standard), 16px radius (featured), ivory bg, cream border

---

## Coding Conventions

### TypeScript
- Strict mode enabled, no `any` types
- One component per file, named exports
- Props interface defined above the component
- Use `interface` for props, `type` for unions/intersections

### Python
- Type hints on all functions and method signatures
- async/await throughout the backend
- Pydantic v2 models for request/response schemas
- `asyncpg` or `psycopg[binary]` for database (async)

### API Design
- RESTful endpoints under `/api/`
- Consistent error shape: `{ "error": "string", "code": "string" }`
- Auth via httpOnly cookie (JWT), not localStorage tokens
- CORS configured for frontend origin only

### Git
- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`
- Keep commits atomic and descriptive
- Reference issue/PR number when applicable

---

## Agent Coordination

### Rules
1. **One agent writes code at a time.** No parallel edits to the same files.
2. **Read TIMELINE.md** before starting work. See what others have done.
3. **Read FRAMEWORK.md** before writing code. Follow the conventions.
4. **Append to TIMELINE.md** after completing work. Use the table format.
5. **Register edits** via `register_edit` if using jCodemunch, or update TIMELINE.md manually.
6. **Disagreements** defer to: `PRD-v2_1.md` → `docs/13-design-tokens.md` → `DESIGN.md`.
7. **No scope changes** without explicit user approval.
8. **P0 scope is frozen.** Any non-P0 request gets tagged "P1" and deferred.

### Handoff
When passing work to another agent:
- Update TIMELINE.md with current state
- Note any in-progress work or partial commits
- List any blockers or decisions needed

---

## Environment Variables

### Frontend (`.env.local`)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_RAZORPAY_KEY_ID=
```

### Backend (`.env`)
```
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
SESSION_SECRET=
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
CORS_ORIGINS=http://localhost:3000
TRUSTED_HOSTS=localhost,127.0.0.1
```

### Optional Backend (graceful degradation if missing)
```
OPENROUTER_API_KEY=
OPENROUTER_API_URL=
OPENROUTER_MODEL=deepseek/deepseek-chat-v3-0324
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
```

---

## Free/Paid Access Matrix

| Feature | Free | Paid (₹149 one-time) |
|---------|------|---------------------|
| Recommendations | Top 10 per profile | All, all filters/sorts |
| Rank guidance | Historical band (all users) | Evidence panel + community context |
| Choices | 20 rows, notes on 5 | 200 rows, notes on all |
| Chat | 3 messages/season (P1) | Unlimited (P1) |
| Explore | Browse + search + district | Full data + advanced filters |
| PDF export | Watermark | Clean |
| News | Free | Free |
| Analytics | Trial preview (P1) | Full trends (P1) |

### Restriction Label Model
Every restriction uses exactly one label:
- **Plan limit** — user has reached free tier cap
- **TNEA phase** — feature retired due to counselling phase
- **Data not ready** — underlying data not yet verified

Rules: never show a paywall for phase or data restrictions. Only show payment when the feature is ready and the user hit a plan limit.

---

## P0 Launch Scope

### Must Ship
Landing, Login (Google OAuth), Onboarding (marks/details/rank), Eligibility gate, Historical rank band, Dashboard, Recommendations (Top 10 free), Choice filing (add/reorder/notes/PDF), Explore + College detail, Subscribe/Paywall, Profile

### Cut from v1
AI chat, Rounds tracker, Analytics, Map, Compare, TFC guidance, Admin panel, Real-time scraping, Roll number verification, CSV import, Choice snapshots, Push notifications, Tamil language

---

## Key Reference Files

| File | Purpose |
|------|---------|
| `docs/13-design-tokens.md` | Design token contract (CSS implementation spec) |
| `docs/11-database-schema.md` | Database schema contract (28 tables) |
| `docs/05-access-model.md` | Free/paid access rules |
| `PRD-v2_1.md` | Master product requirements |
| `DESIGN.md` | Visual design specification |
| `TIMELINE.md` | Agent work registry |
| `FRAMEWORK.md` | This file — project conventions |
