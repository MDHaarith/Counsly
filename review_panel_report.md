# Counsly — Final Consolidated Launch Readiness Report

**Date:** 2026-04-25
**Sources:** Code Review Panel (4 reviewers), Database Council (2 judges), 6 supplemental risks
**Verdict:** NOT LAUNCHABLE | **Overall Score:** 3.5/10

---

## Launch Verdict

**The product CANNOT launch.** There are **8 launch-blocking (P0)** issues that make the application either insecure, non-functional, or unable to load data. On top of that, **22 must-fix (P1)** issues would degrade the product to an unacceptable level for real users. Estimated remediation: **~5-7 days** of focused engineering work.

---

## P0 — Launch Blockers (Score: 0/10 — App is broken/insecure without these)

| # | Finding | Domain | Source | File(s) | Impact | Fix Effort |
|---|---------|--------|--------|---------|--------|------------|
| **P0-1** | Hardcoded JWT session secret enables full auth bypass | Security | Review Panel (consensus) | `backend/app/config.py:9` | Attacker forges valid JWTs for any user. Complete auth bypass. | 30 min |
| **P0-2** | No frontend auth middleware or route protection | Security | Review Panel (consensus) | `frontend/src/` | Unauthenticated users access all protected pages. | 2h |
| **P0-3** | No session invalidation mechanism | Security | Review Panel (consensus) | `backend/app/auth/session.py` | Stolen tokens valid for 14 days. No logout. | 3h |
| **P0-4** | No database connection pooling | Architecture | Review Panel + Council P1-4 | `backend/app/db/connection.py` | 503 cascading failures under TNEA concurrent load. | 1h |
| **P0-5** | College seed script produces all NULLs — key-name mismatch | Data | Council P0-1 | `backend/scripts/seed_colleges.py:12` | Explore, detail, recommendations, choice filing all return empty. | 1h |
| **P0-6** | Cutoff data (554K rows) cannot be loaded — CSV vs JSON-only parser | Data | Council P0-2 | `backend/scripts/seed_utils.py:26-41` | Recommendations engine completely non-functional. | 2-3h |
| **P0-7** | `aggregate_mark` is INT but 63% of data has decimal values | Data | Council P0-3 | `backend/migrations/001_initial_schema.sql:192,209` | 350K+ rows fail to insert or lose precision. Inaccurate recommendations. | 1h |
| **P0-8** | `rank_lookup` table has no build/aggregation pipeline | Data | Council P0-4 | `backend/scripts/seed_rank_lookup.py` | Rank estimation non-functional. `is_abstain: true` for all students. | 4-6h |
| **P0-9** | `useAuth` hook is a non-functional stub | Frontend | Review Panel (consensus) | `frontend/src/hooks/useAuth.ts` | Auth state never propagates. User always appears logged out. | 3h |

**P0 Subtotal: ~17-20 hours**

---

## P1 — Must Fix Before Launch (Score: 4/10 — App works but is dangerously incomplete)

| # | Finding | Domain | Source | File(s) | Impact | Fix Effort |
|---|---------|--------|--------|---------|--------|------------|
| **P1-1** | OAuth has no `state` parameter — CSRF exposure | Security | Review P2-21 + User risk #1 | `backend/app/routers/auth.py:36,44` | Session fixation / CSRF on Google login. | 1h |
| **P1-2** | Eligibility gate (cutoff >= 90) recorded but never enforced | Correctness | User risk #2 | `backend/app/db/queries.py:81,191,279` | Ineligible students get recommendations and file choices. | 1h |
| **P1-3** | Frontend cookie name hardcoded, backend configurable — silent breakage | Correctness | User risk #3 | `frontend/src/proxy.ts:26` | Production env override would break all route protection. | 30 min |
| **P1-4** | Payment verification is client-return only, no webhook reconciliation | Payments | User risk #4 + Review P1-10 | `backend/app/routers/payments.py:62` | Payment failures not caught. Revenue leakage. | 3h |
| **P1-5** | Bearer token fallback in auth middleware | Security | Review Panel | `backend/app/auth/middleware.py:12-16` | Cookie auth bypassed via header. | 30 min |
| **P1-6** | Subscription check doesn't filter by season_year | Correctness | Review Panel | `backend/app/db/queries.py:48-54` | Previous-season free users treated as "paid" for current year. | 30 min |
| **P1-7** | Choice priority collision on move | Correctness | Review Panel | `backend/app/db/queries.py:391-402` | Reordering produces duplicate priorities. | 2h |
| **P1-8** | Razorpay SDK blocks async event loop | Performance | Review Panel | `backend/app/routers/payments.py:34` | All concurrent requests freeze during payment. | 30 min |
| **P1-9** | No rate limiting on any endpoint | Security | Review Panel (consensus) | `backend/app/main.py` | Brute-force on auth, payment abuse. | 1h |
| **P1-10** | Dead "Unlock Full Access" button on choices | UX | Review Panel | `frontend/src/app/(auth)/choices/page.tsx:227` | Users hit paywall but button does nothing. | 15 min |
| **P1-11** | No logout button in the app | UX | Review Panel | `frontend/src/app/(auth)/profile/page.tsx` | Users cannot sign out. | 30 min |
| **P1-12** | No payment success feedback | UX | Review Panel | `frontend/src/app/(public)/subscribe/page.tsx:46-55` | Users pay but get no confirmation. Support burden. | 1h |
| **P1-13** | No loading skeletons on any page | UX | Review Panel (consensus) | All page files | Every page shows "Loading..." text. Feels broken. | 2h |
| **P1-14** | Missing marks validation on frontend | UX | Review Panel | `frontend/src/app/(auth)/onboarding/marks/page.tsx` | Users submit invalid marks, corrupt onboarding. | 1h |
| **P1-15** | `data_freshness` never updated by seed scripts | Data | Council P1-2 | Seed scripts | `dataset_is_verified()` always returns False. All feature gates locked. | 1h |
| **P1-16** | Geo data not merged into college seeding | Data | Council P1-3 | `backend/scripts/seed_colleges.py` | College detail pages show no map data. | 1-2h |
| **P1-17** | Migrations 001 + 002 must be applied atomically | Data | Council P0-5 | `backend/migrations/` | Seat matrix table missing if only 001 applied; endpoints crash. | Trivial |
| **P1-18** | Recommendation sorting breaks for users without official rank | Correctness | Review Panel (consensus) | `backend/app/db/queries.py` | All cutoff distances become 0 when rank is NULL. Bad ordering. | 1h |
| **P1-19** | No structured logging or observability | Architecture | Review Panel | `backend/app/main.py` | No way to debug production issues. | 1h |
| **P1-20** | Health check doesn't verify DB connectivity | Architecture | Review Panel | `backend/app/main.py:62-64` | App reports healthy even when DB is down. | 30 min |
| **P1-21** | Onboarding progress bar is static at 33% | UX | Review Panel | `frontend/src/app/(auth)/onboarding/layout.tsx:8` | No sense of progress during 3-step flow. | 30 min |
| **P1-22** | No back navigation in onboarding | UX | Review Panel | Onboarding pages | Mobile users trapped in forward-only flow. | 30 min |

**P1 Subtotal: ~22-24 hours**

---

## P2 — Should Fix (Score: 6/10 — Important but not launch-blocking)

| # | Finding | Domain | Source | Fix Effort |
|---|---------|--------|--------|------------|
| **P2-1** | Design-system drift: ghost buttons and focus rings use terracotta instead of specified colors | Design | User risk #5 | 1h |
| **P2-2** | Choice "Export PDF" is browser print from popup, not real PDF | UX | User risk #6 | 4-6h |
| **P2-3** | No API version prefix (`/api/v1/`) | Architecture | Review Panel | 2h |
| **P2-4** | CORS allows wildcard methods/headers | Security | Review Panel | 30 min |
| **P2-5** | Error handler may leak internal details | Security | Review Panel | 30 min |
| **P2-6** | Razorpay signature stored in plaintext | Security | Review Panel | 1h |
| **P2-7** | Zero test files in project | Quality | Review Panel | Ongoing |
| **P2-8** | No CI/CD pipeline | DevOps | Review Panel | 1 day |
| **P2-9** | `save_details` doesn't verify marks exist first | Correctness | Review Panel | 30 min |
| **P2-10** | LIKE wildcards in search input not escaped | Correctness | Review Panel | 30 min |
| **P2-11** | Choice deletion doesn't recompact priorities | Correctness | Review Panel | 1h |
| **P2-12** | Profile page has no edit capability | UX | Review Panel | 3h |
| **P2-13** | "Quick add" uses raw college/branch codes | UX | Review Panel | 2h |
| **P2-14** | Subscribe page has no free vs paid comparison | UX | Review Panel | 2h |
| **P2-15** | Dashboard shows raw API keys for data freshness | UX | Review Panel | 30 min |
| **P2-16** | SCA community missing from historical cutoff data | Data | Council P1-1 | 2-3h |
| **P2-17** | No `seed_tfc_locations.py` script | Data | Council P2-4 | 30 min |
| **P2-18** | No DDL template for per-round seat matrix tables | Data | Council P2-3 | 1h |
| **P2-19** | No graceful degradation for missing 2026 data | Data | Council P2-5 | 1h |

**P2 Subtotal: ~22-28 hours**

---

## P3 — Nice to Have (Score: 8/10 — Polish, not blocking)

| # | Finding | Domain |
|---|---------|--------|
| P3-1 | No CSP headers | Security |
| P3-2 | No HSTS, X-Frame-Options headers | Security |
| P3-3 | Frontend API client has no runtime response validation | Security |
| P3-4 | TabBar active indicator is subtle | UX |
| P3-5 | Landing page has no trust signals or social proof | UX |
| P3-6 | Safety labels are English-only (no Tamil) | UX |
| P3-7 | No pull-to-refresh on list pages | UX |
| P3-8 | Banker's rounding in cutoff calculation | Correctness |
| P3-9 | Small checkbox touch target (20px) on subscribe page | UX |

---

## What Works (Positive Findings)

| Area | Detail |
|-------|--------|
| Schema completeness | All 36 contract tables exist across 2 migration files |
| RLS coverage | ROW LEVEL SECURITY enabled on every table |
| Index coverage | All 11 contract-required indexes present |
| CHECK constraints | All canonical enums match (community, subscription, preference_group, etc.) |
| Query-schema consistency | Every backend query references columns that exist in schema |
| Pydantic model alignment | All models map correctly to schema columns |
| Recommendation gating | Proper `dataset_is_verified()` gate prevents misleading results |
| Empty-table resilience | Queries gracefully handle NULL/missing reference data |
| Onboarding rank endpoint | Returns `is_abstain: true` with disclaimer when no data exists |
| Seed data quality | 430 colleges, 73 branches, 554K cutoffs, 1M+ GRL rows, 110 TFC locations extracted |
| Seat matrix pipeline | `ingest_seat_matrix.py` is well-built and ready for 2026 data |
| data_freshness tracking | 11 datasets tracked with freshness status |
| Razorpay HMAC | Signature verification exists using `hmac.compare_digest` |
| Design system | Cohesive visual tokens (terra cotta, cream, charcoal, sage) |
| Core flow structure | Onboarding -> Rank Band -> Recommendations -> Choices is complete |

---

## Domain Scores

| Domain | Score | Assessment |
|--------|-------|------------|
| **Security** | 3/10 | Hardcoded secret, no session invalidation, no CSRF state, no rate limiting. Auth is bypassable. |
| **Data Pipeline** | 3/10 | Schema is sound (8/10) but seed infrastructure is broken. Zero reference data can be loaded. |
| **Correctness** | 4/10 | Eligibility not enforced, sort broken for NULL ranks, priority collisions, season_year gap. |
| **Architecture** | 5/10 | Clean router separation, good Pydantic alignment. No pooling, no logging, no CI/CD. |
| **Frontend/UX** | 4/10 | Design system solid but auth hooks are stubs, no skeletons, dead buttons, no back nav. |
| **Payments** | 5/10 | HMAC verification works. No webhooks, no idempotency, sync SDK blocks event loop. |

---

## What Must Be Done Before Launch

### Phase 1 — Critical Security & Auth (~1 day)
1. Remove hardcoded JWT secret, add startup validation
2. Build frontend auth middleware (session cookie check, redirect to `/login`)
3. Implement `useAuth` hook (call `getSession`, provide user context)
4. Implement server-side session store + invalidation on logout
5. Remove Bearer token fallback (cookie-only auth)
6. Add OAuth `state` parameter for CSRF protection
7. Fix frontend cookie name mismatch

### Phase 2 — Data Pipeline (~2 days)
8. Fix college seed script key-name mapping
9. Write CSV bulk loader for cutoff data
10. Change `aggregate_mark` to `NUMERIC(8,4)` in both tables
11. Write `build_rank_lookup.py` aggregation script from GRL data
12. Apply migrations 001+002 atomically
13. Add `data_freshness` UPDATE to all seed scripts
14. Merge geo data into college seeding

### Phase 3 — Correctness & Reliability (~1 day)
15. Add connection pooling (AsyncConnectionPool)
16. Enforce eligibility gate in recommendation and choice queries
17. Fix subscription season_year filter
18. Fix recommendation sort for NULL ranks
19. Fix choice priority collision on move
20. Add rate limiting
21. Wrap Razorpay SDK in `asyncio.to_thread()`
22. Add health check with DB connectivity
23. Add structured logging

### Phase 4 — UX Polish (~1 day)
24. Build loading skeletons for all pages
25. Add marks validation on frontend
26. Wire up "Unlock Full Access" button
27. Add logout button
28. Add payment success feedback
29. Wire up onboarding progress bar
30. Add back navigation in onboarding
31. Fix design-system drift (Button colors)

### Phase 5 — Payment Hardening (~0.5 day)
32. Add Razorpay webhook endpoint
33. Add idempotency key on payment verification

---

## Estimated Total

| Phase | Effort | Dependencies |
|-------|--------|-------------|
| Phase 1: Security & Auth | ~1 day | None |
| Phase 2: Data Pipeline | ~2 days | None (can parallel with Phase 1) |
| Phase 3: Correctness | ~1 day | Phase 2 (data must load first) |
| Phase 4: UX Polish | ~1 day | Phase 1 (auth must work) |
| Phase 5: Payments | ~0.5 day | None |
| **Total** | **~5-6 days** | |

---

## Final Verdict

**The product is NOT launchable.** The schema and core architecture are sound, but 8 P0 issues render the application both insecure and non-functional. The data pipeline is completely broken — zero reference data can be loaded into Supabase. Authentication is bypassable via a hardcoded secret. The frontend has no auth protection.

**With 5-6 days of focused engineering work addressing Phases 1-5 above, the product can launch as a limited beta** covering the core flow: onboarding -> rank estimation -> recommendations -> choice filing. The remaining P2/P3 items (real PDF export, CI/CD, test coverage, missing PRD screens like Chat and Analytics) can be deferred to post-launch.
