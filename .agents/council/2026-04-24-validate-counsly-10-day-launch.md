---
id: council-2026-04-24-validate-counsly-10-day-launch
type: council
date: 2026-04-24
---

## Council Consensus: WARN

**Target:** Counsly PRD docs 01-18, extracted edits, 10-day launch plan, and DESIGN.md visual direction.
**Mode:** validate, --debate
**Rounds:** 2
**Judges:** Product Scope, Engineering/Data, Mobile UX/Design

Full current PRD in 10 days: **FAIL**.
Strict mobile-first Phase-2 MVP in 10 days: **WARN / feasible if scope is frozen immediately**.

---

## Verdicts

| Judge | Round 1 | Round 2 | Shift |
| --- | --- | --- | --- |
| Product Scope | FAIL full PRD, WARN MVP | FAIL full PRD, WARN strict Phase-2 MVP | Slightly stronger on hiding chat and cutting 8-tab scope |
| Engineering/Data | FAIL full PRD, WARN MVP | FAIL full PRD, WARN narrow paid MVP | Cut chat harder; rank bands can ship with conservative method |
| Mobile UX/Design | FAIL full PRD, WARN MVP | WARN cut MVP, FAIL current PRD | Stronger on 5-tab mobile shell and no chat tab |

---

## Shared Decision

Ship a narrow mobile-first TNEA product, not the full counselling OS.

The launch product should help a student:

1. Enter marks and profile details.
2. See an honest historical rank band.
3. See safe/moderate/ambitious recommendations.
4. Save colleges into a choice list.
5. Reorder choices on mobile.
6. Export/share the list.
7. Upgrade for full results and premium evidence.

Everything else is either hidden, a locked preview, or a post-launch promise.

---

## Edit Decisions

### Accept Now

| Edit | Decision |
| --- | --- |
| Use 2020-2025, not 2020-2026 | Accept. 2026 data is not present. |
| Free recommendations Top 10 | Accept. Stronger trial and more trust. |
| Choice cap 200 | Accept. Enough for launch and simpler UX. |
| Tap choice number -> enter new position | Accept. Primary mobile reorder interaction. |
| Dynamic round count | Accept conceptually, but defer full rounds tracker. |
| Separate auth, subscription, profile, and student data tables | Accept. |
| Avoid full chat-history context stuffing | Accept. Use last-N plus summaries/retrieval if chat ships. |
| TFC geo locations | Accept later. Not a Day-10 blocker unless verified data exists. |

### Reject Or Defer

| Edit | Decision |
| --- | --- |
| Direct Google OAuth instead of Supabase Auth | Reject for 10-day launch. Supabase Auth is faster and safer to ship. |
| AI-based rank prediction copy | Reject. Use "historical rank band"; no AI accuracy claims. |
| Real-time tneaonline.org scraping | Defer. Too fragile for launch. |
| Unlimited AI chat as paid value | Reject for v1. Chat is optional capped beta only. |
| 30% GST/tax treatment as product copy | Defer to accountant/legal review. Product copy should say "₹149 one-time." |
| Full runtime admin, ingestion audit, observability | Defer to post-launch hardening. |
| Full rounds tracker/TFC live guidance | Defer until official dates and TFC data are verified. |

---

## V1 Scope

### Must Ship

- Landing
- Login with Supabase Auth
- Onboarding marks/details
- Eligibility gate with empathetic copy
- Rank guidance using historical rank bands
- Dashboard with one next action
- Recommendations with Top 10 free results
- Basic explore/search reachable from recommendations
- Choice filing with add, reorder, notes, save, and PDF export
- Subscribe/paywall and payment status
- Profile/settings

### Optional If Ready By Day 8

- Capped AI counsellor beta, not in primary nav
- Rule-based compare preview
- News/phase broadcast strip

### Cut From V1

- Full AI chat
- Rounds tracker
- TFC live guidance
- Analytics/trends
- 430/466-pin map
- Full compare history
- AI "why this differs"
- CSV import
- Full snapshot restore/versioning
- Telegram admin beyond minimal config/status
- 2026 ingestion automation

---

## Navigation Decision

Use a focused v1 mobile shell.

Preferred v1 tabs:

- Home
- Recs
- Choices
- Explore
- Profile

Alternate if rank needs direct access:

- Home
- Rank
- Recs
- Choices
- Profile

Do not ship the 8-tab shell in v1. It makes the product look unfinished when Chat, Trends, and Rounds are not ready.

---

## Paid Offer

₹149 is credible if it unlocks:

- All recommendations
- Premium college columns
- Full rank evidence panel
- Full choice filing
- Strategy notes
- Saved list
- PDF export
- Basic compare/details
- Season access to future official-rank and rounds updates

Do not make AI chat the paid promise.

If Razorpay KYC is not ready, launch as a free beta/waitlist. Do not accept manual payments.

---

## Rank Guidance Method

Rank bands can ship without perfect OQ-30 only if the method is conservative and documented.

Minimum acceptable method:

- Use historical 2020-2025 rank-list data.
- Group by aggregate mark, optionally plus community context.
- Return rank_min and rank_max as a historical range.
- Use confidence labels only: High, Medium, Low.
- Abstain when data points are too sparse.
- Always show: "Based on historical TNEA data. Not a guarantee."
- Replace with official rank when available.

Do not use "AI-predicted rank," "ML accuracy," or a single exact predicted rank.

---

## 10-Day Build Plan

| Day | Work |
| --- | --- |
| 1 | Scaffold Next.js, FastAPI, Supabase, Supabase Auth, mobile shell, DESIGN.md tokens. |
| 2 | Define minimal schema: users, profiles, subscriptions, payments, colleges, branches, college_branches, community_seats, cutoffs, rank_bands, choices, app_config. |
| 3 | Seed mandatory data: colleges, branches, seat matrix, 2020-2025 cutoffs, rank bands, community mapping. |
| 4 | Build onboarding, eligibility gate, rank band API/UI, dashboard next action. |
| 5 | Build recommendations, safe/moderate/ambitious labels, shortlist/add-to-choice actions. |
| 6 | Build choices: list, add/remove, priority number jump, notes, save. |
| 7 | Build PDF export, paywall, access gates, Razorpay if KYC is ready. |
| 8 | Add locked previews, optional capped chat beta only if grounded/retrieval-safe, phase/news strip. |
| 9 | Mobile polish at 360px, empty/error states, trust copy, auth/payment/data smoke tests. |
| 10 | Production deploy, seed production, final QA, freeze and launch. |

---

## Design Contract

Use DESIGN.md as the implementation contract:

- 360px mobile-first layout.
- Parchment page background `#f5f4ed`.
- Ivory cards `#faf9f5`.
- Georgia headings at weight 500.
- Warm sans body text.
- JetBrains Mono for ranks, marks, cutoffs, countdowns.
- Terracotta `#c96442` only for primary CTAs.
- Full-width cards on mobile.
- 44px minimum touch targets.
- Sticky bottom actions where there is a primary action.
- Skeleton loaders, not spinners.
- Warm ring borders, not heavy shadows.
- No cool blue-gray SaaS theme, no dark mode, no generic AI dashboard.

Locked previews must look intentional: blurred data, warm ivory card, concise value explanation, one CTA.

---

## Primary Risks

| Risk | Mitigation |
| --- | --- |
| PRD scope too large | Freeze v1 scope immediately. |
| Schema missing | Build minimal schema before UI feature work. |
| Rank methodology unresolved | Use conservative historical bands with abstain rule. |
| Razorpay KYC delay | Launch free beta/waitlist fallback. |
| Data outside project | Create reproducible seed scripts and checks. |
| Chat hallucination | Cut or capped beta only; do not market as core value. |
| Product feels unfinished | Reduce nav; hide unfinished surfaces instead of empty pages. |
| Legal/tax/refund wording | Keep product copy simple and get review. |

---

## Final Recommendation

Build the Phase-2 acquisition MVP: marks, historical rank band, recommendations, and paid choice planning. That is the only credible 10-day launch path.

The current PRD should become the season roadmap, not the Day-10 launch scope.
