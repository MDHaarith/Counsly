# Counsly — 5-Phase TNEA Timeline

**Source:** PRD v2.0, Section 6
**Last updated:** 12 April 2026

---

## Overview

**STATUS: INTACT.** `TNEA_PHASE = 1|2|3|4|5` in `app_config`. Set via Telegram `/setphase [n]`. Instant. No deployment. Frontend polls every 5 minutes via `usePhase` hook.

Counselling round count must be dynamic through `TOTAL_ROUNDS`. If the admin sets total rounds to 4, round tracker, checklists, deadlines, and history must render 4 rounds without code changes.

| Phase | Name | Approx | Hero Surface |
|---|---|---|---|
| 1 | Pre-Marks | Jan–Apr 2026 | Onboarding · process education |
| 2 | Marks Released | Apr–May 2026 | Rank guidance · Recommendations · **launch window** |
| 3 | TNEA Announced | May–Jun 2026 | Choice filing · AI chat strategy |
| 4 | Rank Assigned | Jun–Jul 2026 | Roll number gate · official recs · PDF export |
| 5 | Counselling Active | Jul–Aug 2026 | Dynamic rounds tracker · TFC-aware AI chat |

---

## Phase 4 Dual-Gate Rule

Roll number interstitial fires only when BOTH:
- `TNEA_PHASE = 4`
- `ROLL_DATA_READY = true` (set by ingestion automation after rank list loads)

---

## Rank System Fate

| Phase | Broad Band | Full Guidance | Official Rank |
|---|---|---|---|
| 1–3 | Active | Active (paid) | — |
| 4–5 | **Retired** | **Retired** | All users |

**Broad Band:** free rank guidance range, shown as `rank_min–rank_max` with High/Medium/Low confidence, based on historical rank-list data. It is not an exact prediction.

**Full Guidance:** paid rank guidance that includes the same range plus historical evidence, community context, and board/disclaimer notes.

---

## Phase-Content Matrix

### Phase 1 — Pre-Marks
- Dashboard: "Board exams are coming. Start planning your TNEA strategy now." + process education cards
- Rank guidance: accepts expected marks with prominent disclaimer — no precision language
- Recommendations: visible, labelled as based on expected marks
- Choice filing: accessible, marked as preliminary
- Rounds tracker: locked — no round dates set yet
- AI chat: process-education focused

### Phase 2 — Marks Released (Launch Window)
- Dashboard: "Board results are out. Enter your marks to see your colleges." + next action: complete profile
- Eligibility gate: fires at onboarding Step 1 for students below 90/200
- Rank guidance: full system active — primary acquisition phase
- Recommendations: fully functional with 2025 cutoff data
- Choice filing: active — students start building lists
- AI chat: strategy focused

### Phase 3 — TNEA Announced
- Dashboard: "TNEA 2026 counselling announced. Finalise your choices now." + urgency prompt
- Round dates: visible in Rounds Tracker
- Recommendations: banner — "Using historical rank band. Update once official ranks release."
- Choice filing: becomes the primary screen
- AI chat: deadline and strategy focused

### Phase 4 — Rank Assigned
- Dashboard: "Official TNEA ranks are out. Enter your DTE roll number to continue."
- Roll number interstitial before dashboard (when `ROLL_DATA_READY=true`)
- Rank guidance: retired — official rank input replaces it for all users
- Recommendations: recalculate with official rank — PDF export is primary CTA
- AI chat: TFC procedures and confirmation strategy

### Phase 5 — Counselling Active
- Dashboard: active round + confirmation deadline + countdown timer prominently
- Rounds Tracker: primary screen
- 6 confirmation options: all active with TFC guidance
- AI chat: real-time decision support
- Choice filing: read-only reference

---

## Phase Transition Mid-Session

`usePhase` detects update within 5 minutes. Non-dismissible banner: "Counsly has been updated with important TNEA information. Tap to refresh." Page reloads on user tap. No forced reload.
