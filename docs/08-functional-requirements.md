# Counsly — Functional Requirements

**Source:** PRD v2.0, Section 8
**Last updated:** 12 April 2026

---

## Auth & Identity

| ID | Requirement |
|---|---|
| FR-1 | Direct Google OAuth · `/auth/callback` · backend-created Counsly session |
| FR-2 | Backend verifies Google ID token and validates Counsly session directly |
| FR-3 | Profile persisted and editable · recs regenerate |
| FR-37 | Device fingerprint · SHA-256 · abuse prevention only |
| FR-38 | Roll number verification · triple-layer · TNEA Phase 4 |
| FR-39 | Auto-welcome · one-time · broad band context · no message consumed |

---

## Eligibility

| ID | Requirement |
|---|---|
| FR-57 | Students below 90/200 see a hard gate at onboarding Step 1 (TNEA Phase 2+). Empathetic copy. No shaming. No recommendations, no rank guidance, no choice filing accessible. |

---

## Trust-First Guidance System

The product does not claim to predict ranks. It provides honest rank guidance grounded in historical evidence.

| ID | Requirement |
|---|---|
| FR-22a | Rank guidance has two states via `RANK_RELEASED`: before release, show historical rank bands; after release, retire estimates and use official rank only. |
| FR-22b | **AI Rank Lookup (All Users):** Query `rank_lookup` by aggregate mark. Output a historical rank range (`rank_min–rank_max`) and confidence label (High/Medium/Low). This is range-only guidance, not an exact guaranteed rank. No precision language. CBSE/ICSE disclaimer required. |
| FR-22c | **Full Guidance (Paid):** Same range as broad band, plus historical evidence panel (last 3 years), community-wise context, and board context note. No confidence percentage — High/Medium/Low label only. |
| FR-22d | **Abstain rule:** If <3 data points in marks range across all years, show "Not enough historical data to estimate a reliable range." No band. |
| FR-22e | **Official-rank-first:** When `RANK_RELEASED=true`, all guidance paths retire. Official rank replaces them for all users. |
| FR-22f | **Disclaimer always shown:** "These bands are based on historical TNEA allotment data and are not a guarantee." |
| FR-22g | Previously shown band archived alongside official rank: "Earlier estimate: X–Y" |
| FR-22h | `rank_lookup` table: aggregate-mark rows · O(1) PK lookup · seeded from 2020–2025 historical rank-list data with abstain rules for sparse ranges |
| FR-22i | **No ML precision claims:** Paid path must not claim ML-model accuracy. No "AI-predicted" or "ML-powered rank" in UI copy. |

---

## Recommendations

| ID | Requirement |
|---|---|
| FR-4 | Free: top 10 + free columns + compare CTA · Paid: all + premium columns |
| FR-5 | Safety labels compare student rank against the relevant community cutoff rank. Lower rank number is better. Safe = student rank is at least 500 ranks better than cutoff. Moderate = student rank is within ±500 ranks of cutoff. Ambitious = student rank is worse than cutoff by more than 500 ranks. |
| FR-6 | Community-specific cutoffs |
| FR-7 | Filters and sorts server-side · free payload reduced |
| FR-7b | Compare CTA → `/compare?focus=[college_code]` — never chat |

---

## AI Chat

| ID | Requirement |
|---|---|
| FR-12 | Chat context must avoid filling the LLM context window: send last-N messages, compact conversation summary, and retrieved grounding snippets instead of full raw history. Personally identifying details must be anonymised before the LLM call. |
| FR-13 | Grounded in TNEA data including TFC procedures and `tfc_locations` |
| FR-14 | Probabilistic language only — never guarantee admission |
| FR-14b | Text-only — no voice, no mic |
| FR-30 | 3 free messages/season · server-side · fingerprint second layer |
| FR-30a | Paid tier AI chat is unlimited with abuse controls. Capacity planning target is ~1M tokens per paid user per season. |

---

## TFC Awareness

| ID | Requirement |
|---|---|
| FR-41a | AI chat answers TFC questions accurately — which option requires TFC, nearest location |
| FR-41b | Rounds Tracker shows TFC guidance for "Accept and Upward" and "Decline and Upward" |
| FR-41c | Each confirmation option card states whether TFC visit is required |
| FR-41d | `tfc_locations` must be seeded before TNEA Phase 4, including district, address, phone when available, latitude, and longitude. |
| FR-41e | AI chat never invents TFC locations |

| Option | TFC Required? |
|---|---|
| Accept and Join | No |
| Accept and Upward | **Yes** — nearest TFC, pay fees |
| Decline and Upward | **Yes** — nearest TFC, pay fees |
| Decline and Move to Next Round | No |
| Decline and Quit | No |
| Upward or Move to Next Round | Conditional |

---

## Dashboard — Command Centre

| ID | Requirement |
|---|---|
| FR-60 | One "next best action" per session based on student state |
| FR-61 | Progress resume — onboarding step if incomplete, last screen link |
| FR-62 | Shortlist status — count, last modified, quick link to /choices |
| FR-63 | Recent compares — last 2 sessions with resume link |
| FR-64 | Phase-aware alerts — current phase banner, active deadlines, active broadcast |
| FR-65 | No card without actionable information. No decorative filler. |

---

## Choice Filing — Primary Surface

| ID | Requirement |
|---|---|
| FR-66 | Fast reorder — desktop drag-and-drop; mobile primary interaction is tapping the priority number, entering a new position with numeric keyboard, and moving the college to that position with optimistic UI. |
| FR-67 | Manual position jump — input box per row |
| FR-68 | Strategy notes — optional free-text per row, visible inline, in PDF export |
| FR-69 | Category editing — manual override Safe/Moderate/Ambitious, labelled "Manually set" |
| FR-70 | Snapshot versions — named, immutable, restorable |
| FR-71 | CSV import — format `priority,college_code,branch_code,category,notes`, preview diff |
| FR-72 | PDF export — student name, marks, community, date, ordered table, disclaimer |
| FR-73 | Mobile-first editing — one active row at a time |

---

## College Compare — Decision Tool

| ID | Requirement |
|---|---|
| FR-74 | Side-by-side structured metric rows |
| FR-75 | Required metrics: fees, hostel, transport, cutoff (3yr community-specific), cutoff safety, district fit, college type, NBA, autonomous |
| FR-76 | "Why this differs" — top 2 significant differences, one-line AI reasoning |
| FR-77 | Save compare session — named, accessible from dashboard and compare page |
| FR-78 | Premium metrics (paid): railway station + distance, placement rate, avg package |
| FR-79 | Free tier: full structure visible, premium rows blurred with "Full Access" overlay |

---

## College Explore and Detail Pages — Decision Pages

| ID | Requirement |
|---|---|
| FR-80 | `/explore` — decision-starting surface, default ranked by student fit |
| FR-81 | `/explore/[code]` — Tabs: Overview · Cutoffs · Fees & Facilities · Placements · Nearby |
| FR-82 | Overview tab: name, type, district, autonomous/NBA, hostel/transport, shortlist/compare CTA |
| FR-83 | Cutoffs tab: branch-level 3yr community-specific with trend indicator (↑↓→) |
| FR-84 | Fees & Facilities: annual fees, hostel details, transport, establishment fees |
| FR-85 | Placements tab (paid): placement rate, avg package, recruiters. Free: blurred unlock board |
| FR-86 | Nearby tab: nearest TFC, nearest railway, distance from home district |
| FR-87 | Shortlist action — directly add any branch to choice list or wishlist |
| FR-88 | Branch-level insight — expandable: seat counts by community, year trend, last cutoff vs rank band |

---

## Rounds Tracker — Production Grade

| ID | Requirement |
|---|---|
| FR-89 | Round countdown timer — live countdown to confirm_end |
| FR-90 | Current seat panel — allotted college, branch, community. "No seat allotted" if none. |
| FR-91 | Upward movement logic — explanation for Accept/Decline and Upward |
| FR-92 | Consequence logic — "What happens if you don't act" per option (mandatory) |
| FR-93 | TFC-required action panel — nearest TFC from student's home district |
| FR-94 | Reporting flow — Accept and Join: download letter, documents, deadline |
| FR-95 | Per-round checklist — 4 items per round, persists server-side, green tick on complete |
| FR-96 | Round history — completed rounds collapsed, shows choice and outcome |

---

## Runtime Admin System

| ID | Requirement |
|---|---|
| FR-97 | All runtime variables controllable via Telegram bot without deployment |
| FR-98 | `/status` returns complete snapshot of all app_config, round_dates, news count, freshness |
| FR-99 | Every Telegram bot write produces audit log in `admin_audit_log` |
| FR-100 | Reject malformed input, confirm writes, never silently fail |
| FR-101 | `BROADCAST_ACTIVE` / `BROADCAST_MESSAGE` seeded in migrations, rendered on frontend |

---

## Data Ingestion Subsystem

| ID | Requirement |
|---|---|
| FR-102 | Every ingestion writes to `ingestion_audit_log` on start and completion/failure |
| FR-103 | `reference_validate.py` runs after every ingestion. Failures block `ROLL_DATA_READY=true` |
| FR-104 | `data_freshness` updated after every successful ingestion. `/status` includes freshness |
| FR-105 | Historical cutoff backfill (2020–2025) idempotent — safe to re-run |
| FR-106 | Rank PDF pipeline handles confirmed DTE PDF layout, produces validation report |
| FR-121 | Real-time scraping pipeline must be activated after launch to monitor official sources, update news cards, and auto-download official PDFs into the ingestion queue with failure alerts and manual override. |

---

## Payment & Access

| ID | Requirement |
|---|---|
| FR-29 | Razorpay · 14900 paise · order → modal → verify → active |
| FR-31 | ₹149 one-time · season expiry on `SEASON_END_DATE` |
| FR-32 | Trial-first gates → `/subscribe?from=[feature]` only after preview/trial limit is reached |
| FR-32a | Recommendations — top 10 free, rest → paywall |
| FR-32b | Explorer/compare/insight → soft gate with `PartialUnlockBoard` |
| FR-32c | Choices, analytics, and rounds must expose trial previews in free tier before full unlock prompt |
| FR-33 | Subscription server-side · re-validated every route |
| FR-34 | `SEASON_END_DATE` · 7-day notification · no auto-renewal |
| FR-40 | No refunds · consent checkbox before payment CTA |

---

## Phase System & Admin

| ID | Requirement |
|---|---|
| FR-35 | TNEA_PHASE 1–5 · all screens conditional · `/setphase` · `usePhase` polls every 5 min |
| FR-36 | Telegram bot · all commands require input validation · never corrupt `app_config` |

---

## Analytics & Explorer

| ID | Requirement |
|---|---|
| FR-15 | Cutoff trends 2020–2025 |
| FR-16 | Rank safety gauges top-5 |
| FR-17 | Community seat distribution |
| FR-17b | Community-wise cutoff (7 communities) · student's highlighted |
| FR-17c | Round-wise — DEFERRED TO V2 |
| FR-21a–g | Explorer — directory · detail · map · compare · wishlist · 18 approx coords |

---

## Personal Data Environment

| ID | Requirement |
|---|---|
| FR-42 | One private PDE per student. Auto-created on first login. |
| FR-43 | `workspace_id` is the canonical ownership boundary |
| FR-44 | `user_college_preferences` is the canonical preference store |
| FR-45 | Groups: `wishlist`, `primary`, `pinned` · priorities 1–200 |
| FR-46 | Onboarding resumes at exact last step |
| FR-47 | Shortlist snapshots — immutable, titled, timestamped |
| FR-48 | Chat history private. Clear option from settings |
| FR-49 | Defaults: district, branches, saved filters, phase preferences |
| FR-50 | Activity timeline: onboarding, shortlist, compare, import, export, payment, rank update |
| FR-51 | Choice import: CSV `priority,college_code,branch_code,category,notes` |
| FR-52 | Choice export: polished PDF with student details, table, notes, disclaimer |
| FR-53 | Compare history stored per student — accessible from dashboard and compare page |
| FR-54 | Personalization: pinned colleges, saved filters, compact view, display density |
| FR-55 | No automatic data expiry or deletion in v2.0 |
| FR-56 | `OPENROUTER_MODEL` env var — no hard-coded model strings |

---

## Mobile as First-Class App Surface

| ID | Requirement |
|---|---|
| FR-107 | Dedicated mobile layouts — dashboard, choices, compare, rounds tracker |
| FR-108 | Dashboard mobile: next action full-width top, stacked below |
| FR-109 | Choices mobile: full-screen list, sticky bottom action area, swipe row actions |
| FR-110 | Rounds mobile: full-screen active round, tappable confirmation rows, prominent countdown |
| FR-111 | All key action areas sticky on mobile |
| FR-112 | Low-scroll — max 3 scrolls to reach primary action |
| FR-113 | Onboarding resume one-tap from dashboard |
| FR-23 | 360px minimum viewport width |
| FR-24 | Mild light-first theme on mobile |
| FR-25 | 44x44px minimum touch targets |
| FR-26 | WCAG AA contrast |
| FR-27 | Lighthouse >= 85 mobile simulation |
| FR-28 | 466 map pins within 3s on 4G |
| FR-58 | Optimised for mid-range Android (₹10k–₹20k) |

---

## Observability

| ID | Requirement |
|---|---|
| FR-114 | Funnel analytics via GA4: onboarding → completion → first rec → college added → paywall → payment |
| FR-115 | Error logging: all 5xx with endpoint, error type, hashed user_id, timestamp. Client JS errors captured. |
| FR-116 | Payment auditability: every Razorpay event logged in `payment_audit_log` |
| FR-117 | Chat failures logged. If message failed, counter must not increment. |
| FR-118 | Data freshness daily poll. Core dataset staleness → Telegram alert. |
| FR-119 | UptimeRobot: `/health`, Vercel frontend, Supabase URL. Alerts to admin Telegram. |
| FR-120 | Every ingestion result in `/status` and queryable from `ingestion_audit_log`. |
