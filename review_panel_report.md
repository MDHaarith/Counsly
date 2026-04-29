# Counsly Launch Readiness — Review Panel Report

**Date:** 29 April 2026 | **Target Launch:** 05 May 2026
**Panel:** 4 reviewers (Completeness Checker, Security Auditor, ML Specialist, Devil's Advocate)
**Confidence:** High — all findings verified against source code
**Review mode:** Exhaustive (architecture + code + ML pipeline + product completeness)
**Previous review:** 28 April (5.5/10, "Launch with conditions")

---

## Executive Summary

Since the 28 April review, significant fixes have been applied: duplicate functions removed, Google ID token verification added, input validation completed, security logging deployed, dead code cleaned, and RLS policies migration written. The security posture is now strong.

The app is **product-complete for MVP**. All 7 core features work end-to-end with real data flows, not stubs. The ML pipeline is correctly isolated from production — the rank lookup table (not ML models) powers the actual rank guidance.

Two items need fixing before launch:

1. **Frontend middleware.ts** — The route guard logic exists in `proxy.ts` but is dead code because Next.js requires the file to be named `middleware.ts`. A 5-minute rename fixes this.
2. **`compute_safety()` asymmetric band** — Students whose rank is worse than a college's cutoff are incorrectly labeled "moderate" instead of "ambitious." The symmetric 500-rank band treats "500 ranks better" and "500 ranks worse" identically. A 30-min fix.

**Verdict: LAUNCH on 05 May. Fix the two items above first.**

---

## Score Summary

| Reviewer | Score | Recommendation |
|---|---|---|
| Completeness Checker | 7.5/10 | Launch ready |
| Security Auditor | 7.0/10 | Launch with 1 fix (middleware.ts) |
| ML Specialist | 8.0/10 | Launch ready — ML not in production path |
| Devil's Advocate | 4.0/10 | Fix P0s first, then launch |
| **Weighted Average** | **6.5/10** | **Launch with 2 fixes** |

---

## Previous P0/P1 Status Tracker

| # | Finding (28 April) | Status | Verified By |
|---|---------------------|--------|-------------|
| P0-1 | Duplicate functions in `queries.py` | **FIXED** | Completeness Checker |
| P0-2 | No frontend auth middleware | **NOT FIXED** | All 4 reviewers |
| P0-3 | RLS enabled but no policies | **FIXED** (migration exists) | Security Auditor |
| P1-4 | No Google ID token verification | **FIXED** | Security Auditor |
| P1-5 | Input validation gaps on marks | **FIXED** | Completeness Checker |
| P1-6 | No security event logging | **FIXED** | Security Auditor |
| P1-7 | `access.ts` dead code | **FIXED** (deleted) | Completeness Checker |
| P1-8 | `useAuth` hook is a stub | **FIXED** (43-line implementation) | Completeness Checker |

**Progress: 6 of 7 previous items fixed. 1 remaining (middleware.ts).**

---

## New Findings (29 April)

### P0 — Fix Before Launch

| # | Finding | Source | Effort | Verified |
|---|---------|--------|--------|----------|
| 1 | **Frontend middleware.ts missing** — `proxy.ts` has correct logic but is dead code. Next.js only runs `middleware.ts` at project root or `src/` root. All protected routes show error cards to unauthenticated users instead of redirecting to login. | All 4 reviewers | 5 min | YES — no `middleware.ts` exists anywhere |

### P1 — Should Fix Before Launch

| # | Finding | Source | Effort | Verified |
|---|---------|--------|--------|----------|
| 2 | **`compute_safety()` symmetric band** — Uses `abs(student_rank - cutoff_rank) <= 500` which treats "500 ranks worse" the same as "500 ranks better." A student ranked 5000 with cutoff 4500 gets "moderate" when they should get "ambitious." | Devil's Advocate, verified | 30 min | YES — code read at `queries.py:189-196` |
| 3 | **CORS defaults to localhost** — `CORS_ORIGINS` must be set to production domain before deploy. | Security Auditor | 5 min (env config) | YES — `config.py:15` |

### P2 — Post-Launch

| # | Finding | Source | Detail |
|---|---------|--------|--------|
| 4 | Rate limiter is per-process | Devil's Advocate | In-memory `defaultdict(deque)` — fine for single-worker, needs Redis for multi-worker |
| 5 | Subscription has no `ends_at` | Devil's Advocate | `NULL` in INSERT — logically scoped by season, but no automated cleanup |
| 6 | Quick-add choices requires raw codes | Devil's Advocate | No autocomplete/search — power-user only, acceptable for MVP |
| 7 | Webhook audit log has no event dedup | Security Auditor | Duplicate entries on Razorpay retries, data is correct |
| 8 | Explore page lacks district filter UI | Completeness Checker | Backend supports it, frontend only has text search |

---

## ML Pipeline Assessment

### Model Status

| Model | Status | Production Use |
|-------|--------|---------------|
| Rank prediction (`rank_model.json`) | **FAILED** — 0.0% MAPE accuracy | NOT used. Production uses `rank_lookup` table |
| Total students (`total_students_model.json`) | **PASSED** — 95.31% test accuracy | NOT used. Experimental only |

### Why the rank model failed

The custom `TinyMLP` (single hidden layer, 12 nodes, tanh) is too simple for the mark-to-rank relationship, which is a steep S-curve. The MAPE loss function amplifies errors on high-mark predictions (where actual rank is small). The model saturates at `rank_fraction = 1.0` (worst rank) for 60% of the mark range. Root causes: no momentum, no LR scheduling, no gradient clipping, destructive loss function.

### Why this doesn't matter for launch

The production system uses `backend/scripts/build_rank_lookup.py` which performs direct statistical aggregation over 1M+ rows of historical GRL data (2020-2025). No ML inference at runtime. The lookup table provides:
- O(1) lookup by aggregate mark
- Historical rank range with sample sizes and source years
- Confidence labels (High/Medium/Low)
- Honest, verifiable guidance — not predictions

This aligns with the PRD: "No ML precision claims — No 'AI-predicted' or 'ML-powered rank' in UI copy."

### ML Recommendations

| Priority | Action |
|---|---|
| P0 | Verify `rank_lookup` table is seeded in production DB |
| P1 | Archive or delete the failed `rank_model.json` (0% accuracy is misleading) |
| P2 | If rank prediction is ever desired, rebuild with proper framework (PyTorch/sklearn), MSE loss, 2+ hidden layers |
| P2 | Replace total-students TinyMLP with simple linear regression — same accuracy, zero complexity |

---

## Security Posture

### What's Strong

| Area | Detail |
|------|--------|
| Connection pooling | `AsyncConnectionPool(min_size=5, max_size=20)` |
| Session management | JWT + DB-backed with revocation check |
| OAuth CSRF protection | HMAC `compare_digest` on state parameter |
| Google ID token verification | `verify_oauth2_token()` with audience constraint |
| Payment signatures | HMAC-SHA256 with timing-safe comparison |
| SQL injection protection | 100% parameterized queries |
| Security headers | X-Frame-Options, HSTS, CSP, X-Content-Type-Options |
| Security logging | Structured logging across auth, session, payment paths |
| Input validation | Pydantic `Field` constraints on all models |
| Cookie security | httpOnly, Secure (on HTTPS), SameSite=Lax |
| RLS policies | Public reference data readable, private data service_role only |
| Startup validation | Rejects SESSION_SECRET < 32 chars |

### What Needs Attention

| Area | Detail |
|------|--------|
| Frontend middleware | Dead code — `proxy.ts` never executes |
| CORS configuration | Defaults to localhost, must set for production |
| Rate limiting | In-memory only, per-process |

---

## What the Honest MVP Looks Like

Ships on 05 May:

1. Google OAuth login
2. 3-step onboarding with rank band from historical data (6 years, 1M+ students)
3. Safe/Moderate/Ambitious recommendations (10 free, 200 paid)
4. Choice filing with reorder, delete, PDF export (20 free, 200 paid)
5. Searchable college explorer with 430 colleges
6. Dashboard with TNEA round schedule
7. Razorpay payment (₹149 one-time)

**Not in MVP (deferred, documented):** AI Chat, Compare tool, Analytics, Mobile app, ML rank prediction, TFC location finder

---

## 48-Hour Fix Plan (03–04 May)

| Day | Task | Time |
|-----|------|------|
| Day 1 AM | Rename `proxy.ts` → `middleware.ts`, fix export name | 5 min |
| Day 1 AM | Fix `compute_safety()` asymmetric band | 30 min |
| Day 1 PM | Set production `CORS_ORIGINS` env var | 5 min |
| Day 1 PM | Verify `rank_lookup` table seeded in production | 15 min |
| Day 1 PM | Verify RLS migration 004 applied to production | 10 min |
| Day 2 AM | Smoke test: login → onboarding → recommendations → choices → payment | 2h |
| Day 2 PM | Deploy from clean tagged SHA | 1h |

**Total: ~5 hours of focused work.**

---

## Bottom Line

The codebase is in significantly better shape than 28 April. 6 of 7 previous issues are fixed. Security is solid. ML models failing doesn't matter — the production system never uses them. The remaining P0 (middleware rename) is a 5-minute fix. The P1 (compute_safety asymmetric band) is a real but contained issue.

**Recommendation: LAUNCH on 05 May.** Complete the 48-hour fix plan. The ML workspace stays as-is — it's correctly isolated experimental code that doesn't affect the app.
