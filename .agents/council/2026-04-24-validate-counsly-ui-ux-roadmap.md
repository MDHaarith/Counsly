---
id: council-2026-04-24-validate-counsly-ui-ux-roadmap
type: council
date: 2026-04-24
---

## Council Consensus: FAIL

**Target:** Counsly `PRD-v2_1.md`, `DESIGN.md`, and the ordered 10-day execution push.  
**Mode:** validate, --debate  
**Rounds:** 2  
**Judges:** Product Scope, Mobile UX/Design, Engineering Delivery

**Bottom line:** the **UI direction is right for the product**, but the **current full PRD is not a credible 10-day build**.  
If leadership insists on a 10-day push, the only defensible path is a **narrow mobile-first launch slice** with locked previews and post-launch expansion.

---

## Verdict Table

| Judge | Round 1 | Round 2 | Shift |
| --- | --- | --- | --- |
| Product Scope | WARN | FAIL | Moved harder after weighing missing data systems and trust friction conflicts |
| Mobile UX/Design | WARN | WARN | Held position: aesthetic is right, IA is too wide |
| Engineering Delivery | FAIL | FAIL | Held position: design is buildable, full scope is not |

Consensus rule: **Any FAIL => FAIL**.

---

## What Is Okay

- `DESIGN.md` is directionally correct for this audience: warm, calm, trust-first, mobile-first, and distinct from generic SaaS.
- The core value loop is strong: onboarding -> rank guidance -> recommendations -> choices -> payment.
- The launch shell in `PRD-v2_1.md` Section 4 is already pointing the right way: `Home`, `Recs`, `Choices`, `Explore`, `Profile`.
- The strongest product surface is still **Choice Filing**, especially with numeric position jump as the primary mobile interaction.

---

## What Is Not Okay

- The product shape is too broad for 10 days: chat, analytics, rounds, compare, map, insight tabs, runtime admin, ingestion automation, observability, payment, and direct OAuth are all in scope at once.
- The IA is internally inconsistent: `PRD-v2_1.md` Section 4 says **5 tabs**, while `DESIGN.md` Section 4 still specifies **8 tabs**.
- Several “UI” surfaces depend on systems the PRD says are not ready yet:
  - `rank_lookup` for rank guidance
  - TFC structured data
  - round dates
  - news ingestion
  - compare/detail APIs
- The current no-dismiss paywall pattern in Section 4 fights the trust-first positioning in Section 1 if used too aggressively.
- The design system is emotionally correct but too card-heavy for dense decision screens unless launch uses list-first, high-density layouts for recommendations, compare, and choices.

---

## Forced UI/UX Decision

Use `DESIGN.md` as the **visual contract**, but not as a literal screen-count contract.

Required changes before build:

- Freeze launch nav to **5 tabs only**: `Home`, `Recs`, `Choices`, `Explore`, `Profile`.
- Remove the `8-tab` bottom-bar spec from `DESIGN.md`.
- Keep `Chat`, `Rounds`, `Analytics`, `News`, `Compare`, and `Map` out of primary navigation.
- Use **Georgia** for titles only; dense rows and metric-heavy screens should be **sans + mono**.
- Use **one lock pattern** across the product: preview first, explicit unlock action, then checkout.
- Make decision-heavy screens **list-first**, not editorial-card-first.
- Keep **numeric position jump** as the default mobile reorder path; drag should be optional, not primary.

---

## Launch Scope For A 10-Day Push

### Must Be Real

- Landing
- Login
- Onboarding: marks, details, eligibility gate
- Rank guidance using historical band logic
- Dashboard with one next action
- Recommendations with Top 10 free
- Basic choice filing: add, reorder, notes, save
- PDF export
- Paywall/payment
- Profile/settings
- Basic explore list
- College overview-lite

### Can Exist Only As Locked Preview Or Dashboard Module

- AI chat
- Compare
- Analytics
- Rounds tracker
- Map / Near Me
- Premium college insight tabs
- News beyond a simple feed

### Must Be Deferred

- Real-time scraping automation
- Full TFC-aware flows unless data is seeded and verified
- Full runtime admin breadth
- Full compare reasoning
- CSV import
- Advanced snapshot restore/versioning

---

## 10-Day Roadmap

| Day | Focus |
| --- | --- |
| 1 | Freeze scope, freeze 5-tab IA, resolve `5-tab vs 8-tab`, decide auth approach, scaffold app shell and mobile design tokens |
| 2 | Build core schema, sessions/auth, access gates, health/error logging, and the minimal backend contract for onboarding/recs/choices/payments |
| 3 | Seed critical data: colleges, branches, cutoff data, and `rank_lookup`; if `rank_lookup` slips, cut more scope immediately |
| 4 | Ship onboarding, eligibility gate, rank guidance, and dashboard next action |
| 5 | Ship recommendations, Top 10 free gating, safety labels, shortlist/add-to-choice, and unlock path |
| 6 | Ship choice filing core: numeric move, notes, save, category override, PDF export |
| 7 | Ship explore list + college overview-lite + payment verification + server-side access enforcement |
| 8 | Add narrow chat beta or simple news only if core flows are stable; otherwise use locked previews instead |
| 9 | Full 360px QA pass: density, sticky areas, keyboard, empty/error/loading states, trust copy, paywall consistency |
| 10 | Seed production, smoke test onboarding -> recs -> choices -> payment -> export, deploy, freeze, launch |

---

## Non-Negotiables

- Do not ship the 8-tab shell.
- Do not let direct Google OAuth consume launch capacity without cutting other surfaces.
- Do not market AI chat, rounds, or live scraping as core if the underlying systems are not ready.
- Do not make the UI calm but hollow; every visible primary surface needs real data and real value.
- Do not use hard paywall interruption as the default unlock pattern after promising trial-first trust.

---

## Final Recommendation

`DESIGN.md` is **okay for the product**.  
The **current full PRD is not okay for a 10-day full build**.

If the order is to move in 10 days, ship a **narrow mobile-first counselling core**:

1. onboarding
2. rank guidance
3. recommendations
4. choice filing
5. payment

Everything else should either be:

- a dashboard-linked preview,
- a locked surface,
- or a post-launch milestone.
