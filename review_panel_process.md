# Review Panel Process History

**Date:** 29 April 2026 | **Target:** Counsly launch readiness + ML model assessment
**Mode:** Exhaustive | **Runs:** 1

---

## Phase 1: Setup

### Context Brief

**Codebase State:** main branch, 5 commits since last review (28 April). Working tree has untracked ML training artifacts.

**Previous Review:** 28 April, 5.5/10 "Launch with conditions". P0 items: duplicate functions, frontend middleware, RLS policies.

**ML Pipeline:** Two TinyMLP models trained from scratch (no numpy/pytorch). Rank model failed (0% accuracy). Total-students model passed (95.3%). Neither integrated into production — backend uses `rank_lookup` table.

**Content Signals:** FastAPI (Python), Next.js 16 (TypeScript), PostgreSQL, Razorpay payments, Google OAuth, ML/neural network training.

### Persona Selection

| Persona | Role | Intensity | Reasoning Strategy |
|---------|------|-----------|-------------------|
| Completeness Checker | Product/MVP completeness | 40% | Backward reasoning |
| Security Auditor | Security + operations | 30% | Adversarial simulation |
| ML Specialist | ML model quality + integration | 50% | Systematic enumeration |
| Devil's Advocate | Challenge everything | 20% | Analogical reasoning |

---

## Phase 3: Independent Reviews

### [Completeness Checker] — Score: 7.5/10

**Key findings:**
- All 7 MVP features fully implemented
- P0-1 (duplicate functions): FIXED
- P0-2 (middleware): NOT FIXED, downgraded to P1 (backend auth is strong)
- P0-3 (RLS): EXISTS, appears correct
- All P1 items fixed
- useAuth hook is now a working 43-line implementation
- Product polish sufficient for launch
- Minor UX gaps: no district filter on explore, quick-add needs raw codes

### [Security Auditor] — Score: 7.0/10

**Key findings:**
- Only P0: frontend middleware.ts missing (proxy.ts is dead code)
- Google ID token verification: VERIFIED FIXED (verify_oauth2_token with audience)
- RLS policies: VERIFIED (004_rls_policies.sql with service_role pattern)
- Security logging: VERIFIED (structured logging across all paths)
- Security headers: VERIFIED (HSTS, CSP, X-Frame-Options, etc.)
- CORS defaults to localhost — P1 ops concern
- All payment security strong (HMAC signatures, audit log, webhook)
- Rate limiter in-memory, acceptable for launch

### [ML Specialist] — Score: 8.0/10 (for launch readiness, not ML quality)

**Key findings:**
- Rank model FAILED: 0.0% MAPE accuracy, saturates at rank_fraction=1.0
- Root cause: single hidden layer too simple, MAPE loss destructive, no optimization fundamentals
- Total-students model PASSED: 95.31% test accuracy, but unnecessary complexity (5-point curve fit)
- Production system uses rank_lookup table (direct statistical aggregation over 1M+ rows)
- ML models NOT integrated into app (intentional)
- Launch readiness NOT affected by ML status
- Recommend: verify rank_lookup seeded, archive failed model

### [Devil's Advocate] — Score: 4.0/10

**Key findings:**
- P0: middleware dead code
- P0→P1: compute_safety() symmetric 500-rank band (verified: student ranked 5000 with cutoff 4500 = "moderate")
- P1: single-year cutoff data (verified but assessed as reasonable design)
- P1: in-memory rate limiter per-process
- P1: RLS migration unverified in production
- P1: Quick-add UX
- MITIGATED: connection pooling, session verification, PDF export, security headers, payment flow
- Worst-case: student pays ₹149, gets misleading safety labels, tells friends

---

## Phase 10-11: Claim Verification

### Claim: compute_safety() symmetric band

**Verdict: [VERIFIED]**
- Code at `queries.py:189-196`
- `abs(student_rank - cutoff_rank) <= 500` treats direction identically
- student_rank=500, cutoff_rank=1 → "moderate" (wrong)
- student_rank=5000, cutoff_rank=4500 → "moderate" (wrong)
- Fix: when student_rank > cutoff_rank, always return "ambitious"

### Claim: Single-year cutoff data

**Verdict: [VERIFIED] but NOT a bug**
- SQL uses `max(season_year)` with no multi-year averaging
- Assessed as reasonable: most recent year's cutoffs are standard reference for TNEA
- Single-year approach matches how counsellors use the data

---

## Phase 14: Supreme Judge Synthesis

**Synthesis by orchestrator (no separate agent):**

1. **Middleware P0** — Confirmed by all 4 reviewers. The fix is trivial (rename file). Must fix before launch.

2. **compute_safety P1** — Verified by claim verification agent. The symmetric band is a real bug that provides misleading guidance. The specific extreme case (rank 500, cutoff 1) is rare, but the pattern (any student_rank > cutoff_rank within 500) is common. Should fix before launch.

3. **ML Pipeline** — Rank model failed but production doesn't use it. Total-students model works but isn't used either. The `rank_lookup` table is the correct production system. No launch impact.

4. **Security** — Significantly improved since 28 April. All previous P1 items fixed. Strong posture remaining.

5. **Previous false claims** — Connection pooling and DB-backed sessions were falsely claimed missing in the 28 April Devil's Advocate review. This round's Devil's Advocate correctly verified these as MITIGATED.

**Final verdict: 6.5/10, LAUNCH with 2 fixes.**
