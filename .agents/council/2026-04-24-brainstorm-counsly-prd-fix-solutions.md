---
id: council-2026-04-24-brainstorm-counsly-prd-fix-solutions
type: council
date: 2026-04-24
---

## Council Consensus: FIXABLE WITH P0 CONTRACT CHANGES

**Target:** Solutions to prior PRD warnings in `PRD-v2_1.md`, `DESIGN.md`, and the flaw report.  
**Mode:** brainstorm / recommendation  
**Judges:** Product Strategy, Data/Ops, Mobile UX

The prior `FAIL` does not mean the product idea is bad. It means the PRD needs stronger contracts around truth readiness, launch scope, plan limits, payment behavior, and recovery flows.

Sections 11 and 13 are now populated, so they are no longer treated as placeholder problems. The remaining work is to wire those contracts into the rest of the PRD.

---

## Core Decision

Every feature must answer one question before it can guide a student:

**Is the source data verified enough to make a decision today?**

If not, the product must show education, preview, or “data not ready” state. It must not show paywalls, personalized claims, nearest-location claims, countdowns, or AI-grounded certainty from unverified data.

---

## P0 Solutions

### 1. Add Truth Readiness Gates

**Problem fixed:** Rank, TFC, rounds, news, compare, and detail screens can look authoritative before their data is ready.

**Better solution:** Add a `data_readiness` contract backed by `data_freshness`.

Recommended statuses:

- `missing`
- `seeded_unverified`
- `verified`
- `stale`
- `disabled`

Decision-grade guidance is allowed only when the required dataset is `verified`.

**PRD impact:** Sections 3, 5, 8, 10, 11, and 16.

### 2. Make `rank_lookup` A Launch Blocker For Rank Guidance

**Problem fixed:** PRD promises rank bands while Section 3 says `rank_lookup` is not present.

**Better solution:** Rank guidance is available only when `RANK_LOOKUP_READY=true`.

If false:

- show process education
- allow Explore browsing
- do not show historical rank band
- do not run recommendations from estimated rank
- do not upsell paid rank evidence

**PRD impact:** Sections 3, 5, 6, 8, 11, 17, and 18.

### 3. Freeze Product Truth

**Problem fixed:** Navigation, community taxonomy, and college counts drift.

**Better solution:**

- Launch nav: `Home`, `Recs`, `Choices`, `Explore`, `Profile`
- Secondary modules: Chat, Rounds, News, Compare, Analytics from dashboard cards or contextual links
- Public college count: `430 active non-architecture colleges`
- Raw ingestion count: `466 raw colleges`
- App-facing communities: `OC`, `BC`, `BCM`, `MBC`, `SC`, `SCA`, `ST`
- Preserve raw `MBCDNC` and `MBCV`; render them under `MBC` only with source preservation

**PRD impact:** Sections 1, 3, 4, 8, 11, 13, and 18, plus `DESIGN.md`.

### 4. Replace Vague Trial Access With Exact Limits

**Problem fixed:** “Trial preview” creates ambiguity and a large QA matrix.

| Feature | Free | Paid |
| --- | --- | --- |
| Recommendations | Top 10 total per student profile, all safety labels visible, premium evidence hidden | All recommendations, filters, sorts, evidence |
| Chat | 3 user messages per season, full quality, no live/TFC claims unless data ready | Unlimited with abuse throttles and ~1M token planning budget |
| Choices | 20 active rows, notes on 5 rows, 1 preview PDF watermark | 200 rows, notes on all rows, unlimited snapshots, clean PDF |
| Compare | 1 pair, core rows only | Save sessions, multi-compare, premium metrics when data ready |
| Explore | Search, district filter, shortlist up to 30, overview pages | Fit ranking, premium fields, advanced filters |
| College Insight | Overview + cutoff summary | Full tabs when data ready |
| Analytics | 1 chart per college/branch, 3-year summary | Full 2020-2025 trends and community breakdown |
| Rounds | Active phase explanation and generic checklist | Countdown, saved checklist, TFC-aware consequence logic when data ready |
| News | Free for everyone | Free for everyone |

**PRD impact:** Section 5 and FR-32 family.

### 5. Rework Paywall To Preview-First

**Problem fixed:** No-dismiss paywall conflicts with trust-first and no-refund policy.

**Better solution:**

- Locked content shows an inline `Full Access` board first.
- `/subscribe?from=[feature]` opens only after the user taps `Unlock Full Access`.
- Paywall has `Back to [feature]` and `Back to Dashboard`.
- Back returns to the prior task and preserves user work.
- No auto-redirect to payment while editing.
- No-refund consent stays only inside payment step.

**PRD impact:** Section 4 Paywall, Section 5, FR-32, FR-40, Section 13 Unlock Boards.

### 6. Use One Restriction Explanation Model

**Problem fixed:** Users cannot tell whether a restriction comes from payment, phase, or missing data.

**Better solution:** Every restriction must use one label:

- `Plan limit`
- `TNEA phase`
- `Data not ready`

Rules:

- If data is missing, do not show a paywall.
- If phase retired a feature, do not show a paywall.
- Show payment only when the feature is ready and the user has reached a plan limit.

**PRD impact:** Sections 5, 6, 8, and 13.

### 7. Simplify Choice Filing

**Problem fixed:** Choices is overloaded for 360px.

**Better solution for mobile launch:**

- Primary reorder: tap priority number -> enter new number -> confirm
- One overflow menu per row for notes, category override, remove
- Auto-save every edit with “Saved [time]”
- Sticky bottom has one primary CTA: `Add College`
- `Save Version` and `Export PDF` move to app-bar or overflow
- Long-press drag, swipe actions, CSV import, and restore UI move post-launch

**PRD impact:** FR-66 to FR-73, Section 13, `DESIGN.md` Choices.

### 8. Rename Rank Guidance

**Problem fixed:** “Broad Band” and “Full Guidance” are less clear and can sound like prediction.

**Better solution:**

- Free: `Historical Rank Band`
- Paid: `Evidence View`

Free includes:

- rank range
- confidence label
- sample size bucket
- disclaimer

Paid additionally includes:

- last 3 year evidence
- community note
- board disclaimer
- explanation of why the range may move

Never use “AI prediction” or “ML rank”.

**PRD impact:** Sections 4, 5, 6, 8, 17, and 18.

### 9. Add Phase Change Explanation

**Problem fixed:** Phase changes can feel like the app changed rules mid-flow.

**Better solution:** Add a `PhaseChangeNotice` pattern:

- what changed
- why it changed
- what the student should do next
- what previous data was archived

Example: “Official TNEA ranks are available. Counsly now uses your official rank instead of historical bands. Your earlier band is saved for reference.”

**PRD impact:** Section 6, FR-35, Section 13.

### 10. Add Roll-Number Claim Recovery

**Problem fixed:** Direct Google OAuth plus one-time roll-number locking creates support risk.

**Better solution:** Add in-app dispute flow.

Claim statuses:

- `active`
- `disputed`
- `released`
- `rejected`

Dispute form fields:

- roll number
- application number
- random number
- marks
- optional DOB
- Google email
- optional phone
- reason

Until resolved, user can use non-official-rank features but cannot access official-rank recommendations.

**PRD impact:** Section 7, FR-38, Section 11 `roll_number_claims`, Section 16.

### 11. Confirm Critical Telegram Admin Writes

**Problem fixed:** Telegram-only runtime controls can mutate production state too easily.

**Better solution:** Critical commands use two-step confirmation.

Critical commands:

- `/setphase`
- `/rankrelease`
- `/setdate`
- `/setrounds`
- scraper publish
- claim transfer

The first command returns old value, new value, affected features, and a short token. Mutation happens only after `/confirm [token]`. Token expires in 5 minutes.

**PRD impact:** Section 10 and `admin_audit_log`.

### 12. Define Launch Contract In The PRD

**Problem fixed:** PRD mixes vision and launch scope.

P0 launch:

- auth/session
- onboarding
- eligibility gate
- historical rank band
- recommendations
- choice filing
- PDF export
- payment/access
- dashboard
- explore list + college overview
- manual news
- basic observability

P1 after launch:

- monitored PDF/news ingestion
- limited chat
- official-rank claim recovery
- round dates
- TFC locations
- simple compare

P2:

- advanced compare
- full analytics
- full rounds tracker
- map performance target
- placements/nearby
- Telegram admin breadth

**PRD impact:** Add to Section 1 or immediately before Goals, then tag FRs as `P0`, `P1`, or `P2`.

---

## Feature Readiness Gates

| Feature | Required readiness | If not ready |
| --- | --- | --- |
| Rank guidance | `RANK_LOOKUP_READY=true` and `rank_lookup` verified | Education only; no rank band, no rank upsell |
| TFC rules | `TFC_RULES_READY=true` | No TFC procedural answers |
| Nearest TFC | `TFC_LOCATIONS_READY=true` | Show official-source link only |
| Rounds countdown | verified `round_dates` and `TNEA_PHASE>=5` | Education or schedule preview only |
| News | manual verified `news_items` | Hide strip; no stale placeholder |
| Scraping | validation passed and admin published | Draft only; no auto-publish |
| Compare/details | field-level readiness map | Show only verified/source-backed fields |

---

## Final Recommendation

The better product direction is:

- 5-tab shell
- dashboard as phase router
- truth-readiness gates
- exact free limits
- preview-first paywall
- simplified Choices
- phase-change explanations
- recoverable roll-number claims
- manual-verified news before scraping
- launch scope separated from season roadmap

Apply these as PRD edits before implementation. Once applied, the earlier `FAIL` should move to `WARN` or `PASS` as a build contract.
