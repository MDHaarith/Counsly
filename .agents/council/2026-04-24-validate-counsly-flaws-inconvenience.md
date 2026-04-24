---
id: council-2026-04-24-validate-counsly-flaws-inconvenience
type: council
date: 2026-04-24
---

## Council Consensus: FAIL

**Target:** Counsly application concept, `PRD-v2_1.md`, and `DESIGN.md`  
**Mode:** validate, --debate  
**Rounds:** 2  
**Judges:** Student UX, Product/PRD, Implementation/Ops

**Bottom line:** there are real flaws and user inconveniences in the current product definition.  
The core idea is strong, but the current PRD is **not yet a stable, build-ready source of truth**.

This repo still appears to be primarily a documentation/spec repository, not a runnable app surface. The council therefore reviewed the **current application concept and PRD**, not a working shipped interface.

---

## Verdict Table

| Judge | Round 1 | Round 2 | Shift |
| --- | --- | --- | --- |
| Student UX | WARN | FAIL | Hardened after weighing missing truth sources behind trust-sensitive screens |
| Product / PRD | WARN | FAIL | Hardened after weighing missing datasets and live procedural promises |
| Implementation / Ops | FAIL | FAIL | Held position |

Consensus rule: **Any FAIL => FAIL**.

---

## What Is Good

- The emotional and visual direction is right: calm, trust-first, evidence-first, mobile-first.
- The core workflow is strong: onboarding -> rank guidance -> recommendations -> choices -> payment.
- The design system is constrained enough to ship if scope is narrowed.

---

## Most Serious Flaws

### 1. Trust-Sensitive Features Depend On Missing Or Unstable Truth Sources

This is the biggest flaw.

The PRD promises:

- rank guidance via `rank_lookup`
- TFC-aware chat and nearest TFC guidance
- round countdowns and round logic
- news freshness and live procedural awareness
- compare/detail decision quality

But the PRD also says several of those inputs are not ready yet:

- `rank_lookup` missing
- `tfc_locations` not seeded
- `round_dates` not present
- `news_items` not present
- compare/detail APIs still blocked

Result: the app can look authoritative while giving incomplete, stale, or inconsistent guidance.

---

### 2. The PRD Does Not Maintain One Stable Product Truth

The spec contradicts itself in multiple places:

- `PRD-v2_1.md` says launch with **5 tabs**
- `DESIGN.md` still specifies **8 tabs**
- sections assume **7 community groups**, while training-ready data says `SCA` was normalized away and other sections still carry `SCA`, `MBCDNC`, `MBCV`
- map/data counts drift between **430** and **466**

This means engineering could build different “correct” versions and still violate the product.

---

### 3. The Free/Paid Model Creates Too Many Ambiguous States

The product currently mixes:

- Top 10 free recommendations
- 3 free chat messages
- preview-only compare
- blurred premium rows
- trial-limited choices
- trial-limited rounds
- AI preview on details
- phase-based retirement of some features
- standalone paywall redirects

For the student, this creates a repeated question:

“Is this limited because I am free, because the phase changed, or because the underlying data is not ready?”

That is a trust problem, not just a monetization problem.

---

### 4. The Paywall Model Is Too Harsh For A Trust-First Product

The PRD says:

- trial-first access on major features
- no refunds
- standalone paywall
- no dismiss

That combination is risky for this audience.  
Students can invest effort through multiple previews and then hit a hard transactional wall in the middle of a decision flow.

The council viewed this as a major user inconvenience and a likely source of support complaints.

---

### 5. Choice Filing Is Too Interaction-Heavy For The Highest-Stakes Screen

The product’s strongest screen is also overloaded.  
Choices currently combine:

- numeric move
- swipe actions
- long-press drag
- notes
- manual category editing
- snapshots
- CSV import
- PDF export
- sticky action area

On a 360px screen, that is too much interaction density for a ranked list students are anxious about getting wrong.

---

### 6. Identity And Claim Flows Create High Support Risk

Direct Google OAuth plus:

- backend-created sessions
- fingerprint usage limits
- roll-number claim locking
- one-time claim ownership

creates a high-friction failure mode during peak season.

The worst operational inconvenience identified by the council:

students signing in with the wrong Google account, colliding on a roll-number claim, or getting blocked from official-rank mode and falling into manual support.

This is especially dangerous because `support@counsly.in` is itself still listed as a business gap.

---

### 7. Foundational Spec Sections Are Still Placeholders

Two sections are not really specifications yet:

- **Section 11** database schema
- **Section 13** design tokens

But many other sections depend on them as if they were settled.

This guarantees rework in:

- schema ownership
- table boundaries
- access checks
- audit logs
- UI token implementation
- mobile component consistency

---

## Main User Inconveniences

- Too many surfaces and mental models introduced too early.
- Too many overlapping “limited” states.
- Phase changes can make the app feel like it changed the rules.
- Rounds/TFC guidance could become misleading if data is incomplete.
- Choices screen risks becoming precise but stressful instead of fast and calming.
- The paywall can interrupt the user in the middle of a high-stakes decision path.

---

## Main Operator Inconveniences

- Manual support burden around auth, entitlement, and roll-number claims.
- QA state explosion across free/paid/phase/preview/expired combinations.
- Telegram-only runtime admin is too fragile for seasonal production control.
- Decision-heavy premium surfaces are promised before the truth layer is stable.
- Refund/access disputes are likely if users feel interrupted or misled.

---

## Fixes The Council Would Force First

1. Freeze one product truth:
   - 5-tab launch shell only
   - one community taxonomy
   - one canonical map/data count

2. Turn missing dependencies into staged requirements:
   - `rank_lookup`
   - `tfc_locations`
   - `round_dates`
   - `news_items`
   - compare/detail APIs

3. Replace placeholder sections:
   - make Section 11 a real schema contract
   - make Section 13 a real design-token/mobile-component contract

4. Simplify choice filing for launch:
   - numeric move first
   - fewer simultaneous actions
   - import and advanced extras later

5. Rework monetization UX:
   - preview-first
   - less coercive lock behavior
   - exact free limits defined per feature

6. Simplify identity and recovery:
   - either reduce auth complexity
   - or specify recovery, claim conflict, and support flows before launch

7. Remove live procedural promises until the underlying data is truly present and validated.

---

## Final Judgment

There **are** flaws and inconveniences in the current application concept and PRD.

The biggest one is this:

**the product wants users to trust decision-grade counselling guidance before the underlying truth model is fully stable.**

That flaw then cascades into:

- navigation inconsistency
- monetization friction
- support burden
- QA complexity
- user confusion

The concept is still strong.  
But the PRD needs another tightening pass before it becomes a reliable build contract.
