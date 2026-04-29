# Counsly — Product Requirements Document

**Version:** 2.1
**Date:** 24 April 2026
**Status:** CURRENT
**Author:** Mohamed Haarith, CEO & Co-Founder
**Domain:** counsly.in

---

## Changelog

| Version | Date | Summary |
|---|---|---|
| v2.0 | 12 Apr 2026 | Product surface expansion and PRD consolidation |
| **v2.1** | **24 Apr 2026** | **Applied edit decisions:** trial-first access on major paid features · Top 10 free recommendations · AI rank lookup for all users · chat policy clarified (3 free, paid unlimited with ~1M token planning) · real-time scraping set as post-launch requirement · wording cleanup and section-reference normalization |

---

## Table of Contents

1. Introduction & Philosophy
2. Goals
3. Data Requirements
4. Screen Inventory
5. Access Model
6. TNEA Timeline and Phases
7. Auth & Identity
8. Functional Requirements
9. Counselling Round Logic
10. Runtime Admin System
11. Database Schema
12. Tech Stack
13. Design Tokens
14. Non-Goals
15. Success Metrics
16. Gap Register
17. Open Questions
18. Glossary

---

## 1. Introduction & Philosophy


**Source:** PRD v2.0, Section 1
**Last updated:** 12 April 2026

---

## The Problem

TNEA serves over 1.5 lakh students navigating **430 colleges** (excluding architecture), **107 branch codes**, **6 app-facing community quotas** (OC/BC/BCM/MBC/SC/ST), **3 counselling rounds**, and **6 confirmation options per round** — with almost no structured guidance.

**Minimum eligibility:** 90/200 marks (Maths 0–100, Physics 0–100, Chemistry 0–100, whole integers). Hard gate applied at onboarding Step 1 in TNEA Phase 2 and above. The formula is:
`Maths + (Physics + Chemistry) / 2`

**Why this gate exists:** Students below 77.5/200 are statistically ineligible for any seat in the TNEA allotment system. But we choose 90 as a mark because showing them rank guidance or college recommendations would create false hope. The gate is empathetic — it acknowledges their effort, explains honestly why Counsly cannot help this cycle, and doesn't shame them.

---

## Philosophy: Evidence First

Counsly should not pretend counselling data is more certain than it is.

Before official 2026 ranks are released, Counsly shows historical ranges from real TNEA data and explains the basis clearly. After official ranks are released, Counsly stops showing estimated ranges and uses the official rank.

---

## The Solution

Counsly is an AI-powered TNEA counsellor structured around ten product surfaces, each designed to do one job excellently:

1. A **trust-first guidance system** — broad bands, abstains when uncertain, switches to official rank the moment it is available
2. A **dashboard command centre** — one next action, real status, no filler
3. A **choice filing surface** — the strongest tool — fast reorder, snapshots, import, export, strategy notes
4. A **compare tool** — a real decision instrument, not a directory feature
5. **Explore and detail pages** — help a student decide, not just browse
6. A **rounds tracker** — production-grade — countdown, TFC flow, consequences, logic
7. A **runtime admin system** — complete operational control over every live product variable
8. A **data ingestion subsystem** — treated as infrastructure, not a one-time task
9. A **mobile surface** — first-class app, not a scaled-down website
10. An **observability layer** — in place before scale, not after

Every authenticated student gets a **strictly private personal data environment** — one per user, no sharing, no members. It holds their onboarding state, shortlists, chat history, compare sessions, activity, and personalization.

---

## What is TFC?

**Tamil Nadu Engineering Admissions Facilitation Centre (TFC)** is a physical office network operated by DTE across Tamil Nadu. Students must visit a TFC when choosing "Accept and Upward" or "Decline and Upward" — the two options that involve paying fees to remain eligible for a better seat.

- **TFC data status:** Location data (address, phone, district, GPS) is collected and ready for ingestion.
- **TFC is not relevant for:** Accept and Join, Decline and Move to Next Round, Decline and Quit.

---

## Pricing

| Item | Detail |
| --- | --- |
| Price | **₹149 one-time** — no subscription, no auto-renewal |
| Validity | Until TNEA 2026 ends (~August 2026) |
| Tax | Price treated as normal business income unless registration becomes legally required. GST/VAT handling must be reviewed before registration threshold decisions. |
| Refunds | **No refunds** — all payments final, consent checkbox required before payment CTA |
| Chargeback risk | Logged as known flaw. Consent checkbox is the mitigation. |
---

## 2. Goals


**Source:** PRD v2.0, Section 2
**Last updated:** 12 April 2026

---

| ID  | Goal |
| ---- | --- |
| G-1 | Profile setup in under 3 minutes |
| G-2 | Safe / Moderate / Ambitious recommendations from real TNEA cutoff data |
| G-3 | Choice filing surface that is the most useful tool a student uses during TNEA |
| G-4 | AI chat grounded in TNEA data including TFC procedures — no hallucinations, no guarantees |
| G-5 | Cutoff analytics 2020–2025, community-wise |
| G-6 | Rounds tracker that shows the active counselling stage, remaining time, required student action, TFC requirement, and consequence of not acting |
| G-7 | Mobile-first — 360px minimum width — first-class app surface, not a scaled-down website |
| G-9 | Launch at counsly.in by 05 May 2026 |
| G-10 | College explorer — 430 colleges, map, compare, wishlist |
| G-11 | Trust-first guidance: broad bands, official-rank-first once available, abstain when uncertain |
| G-12 | Free users get meaningful trial access on every major feature before paywall limits apply |
| G-13 | Compare helps students choose between colleges using decision metrics such as fees, hostel, cutoff safety, travel, district fit, and facilities |
| G-14 | Explore and detail pages help students decide whether a college belongs in their choice list, not just browse names |
| G-15 | Private per-user personal data environment as the canonical boundary for all student data |
| G-16 | Choice persistence up to 200 rows, snapshots, import/export |
| G-17 | Runtime admin controls for changing live variables such as TNEA phase, round dates, broadcast message, free chat limit, and season end date without redeploying |
| G-18 | Direct Google OAuth identity flow with separate tables for auth identity, subscription/payment, and student data |
| G-19 | Real-time scraping pipeline activated after launch to update news cards and auto-download official PDFs for ingestion |
| G-20 | Data ingestion workflow with source validation, audit logs, idempotent re-runs, and safe failure handling when required references are missing |
| G-21 | Observability baseline before scale: uptime checks, payment auditability, chat failure visibility, and funnel telemetry from onboarding to payment |
---

## 3. Data Requirements


**Source of truth:** files currently present in this repo
**Populated on:** 23 April 2026

---

## Overview

This file replaces the older launch-planning notes with the **actual extracted data and schemas** currently available in `supabase_db/Data_Extractor`, with compact staged copies in `supabase_db/seed_data`.

This repo is **not** currently running on a Supabase-first schema. It is running on a **file-output pipeline** with CSV/JSON artifacts. If you want to ingest into Supabase, use the schemas below as the current source-of-truth inputs.

---

## 3.1 — Historical Allotment Data (actual data present)

**Status:** Present and populated for **2020–2025**

**Canonical training-ready file:**
- `Allotement/data/processed/merged/merged_records_all_years_rounds_training_ready.csv`

**Row count:** `554,166`

**Coverage by year:**
- 2020: `67,339`
- 2021: `77,756`
- 2022: `81,426`
- 2023: `92,288`
- 2024: `106,859`
- 2025: `128,498`

**Rounds present in merged data:**
- Round 1: `83,688`
- Round 2: `180,919`
- Round 3: `207,157`
- Round 4: `82,402`

**Actual CSV schema:**
- `YEAR`
- `ROUND`
- `S NO`
- `APPLICATION NUMBER`
- `NAME OF THE CANDIDATE`
- `AGGREGATE MARK`
- `RANK`
- `COMMUNITY`
- `COLLEGE CODE`
- `BRANCH CODE`
- `ALLOTTED CATEGORY`

**Community values currently present after cleanup:**
- `BC`, `BCM`, `MBC`, `OC`, `SC`, `ST`

**Notes:**
- This is the cleanest current source for historical allotment ingestion.
- `MBCDNC` and `MBCV` were normalized away in the training-ready file. Any raw `SCA` values are folded into app-facing `SC`.
- Architecture-only colleges and architecture/design branches were removed from the training-ready export.

**Suggested destination table:** `cutoff_data`

---

## 3.2 — 2026 Allotment Data

**Status:** Not present in this repo yet.

There is no 2026 per-round output under the current `Allotement/data/processed/` tree.

---

## 3.3 — College Information

**Status:** Present

**Raw file:**
- `College_Info_Done/output.json`

**Filtered non-architecture file used across the repo:**
- `College_Info_Done/output_present_non_architecture.json`

**Counts:**
- Raw colleges: `466`
- Filtered colleges: `430`

**Actual top-level JSON schema:**
- `College_Code`
- `PDF_Page_Number`
- `College_Name`
- `Dean_Principal`
- `Bank_A_c_No`
- `Address`
- `Bank_Name`
- `Taluk`
- `District`
- `Distance_in_KMS_from_Dist_HQ`
- `Pincode`
- `Nearest_Railway_Station`
- `Phone_Fax`
- `Email-ID`
- `Distance_in_KMS_from_Nearest_Railway_Station`
- `Website`
- `Anti_Ragging_Phone_No`
- `Autonomous_Status`
- `Placement_Record`
- `Hostel_Boys_Permanent_or_Rental`
- `Hostel_Girls_Permanent_or_Rental`
- `Type_of_Mess`
- `Room_Rent`
- `Electricity_Charges`
- `Caution_Deposit`
- `Establishment_Charges`
- `Admission_Fees`
- `Transport_Facilities`
- `Min_Transport_Charges`
- `Max_Transport_Charges`
- `Internal_Page_Number`
- `Minority_Status`
- `courses`

**Nested `courses` schema:**
- `Branch_Code`
- `Approved_Intake`
- `Year_Starting`
- `NBA_Accredited`
- `Valid_Upto`

**Notes:**
- This is the real source for the `colleges` table.
- Several premium-style fields already exist in raw form here, for example railway distance, placement text, hostel, transport, and fee-related values.
- The current repo stores these mostly as extracted text, not fully normalized numeric fields.

**Suggested destination table:** `colleges`

---

## 3.4 — Branch Codes

**Status:** Present and now filtered into a dedicated branch master output.

**Raw branch-code sources:**
- `Allotement/data/processed/merged/merged_records_all_years_rounds_training_ready.csv`
- `Seat_Matrix/output/seat_matrix_data.json`
- `College_Info_Done/output.json` inside `courses[].Branch_Code`

**Observed raw counts:**
- Distinct branch codes in training-ready allotment data: `115`
- Distinct branch codes in seat matrix data: `107`

**Canonical filtered branch master:**
- `Seat_Matrix/output/branch_codes_filtered.json`

**Removed-branch report:**
- `Seat_Matrix/output/branch_codes_removed.csv`

**Filter implementation:**
- `Seat_Matrix/filter_branch_codes.py`

**Current filtered result from seat-matrix branch codes:**
- Total branch codes discovered: `107`
- Kept branch codes: `73`
- Removed branch codes: `34`

**Removal rules currently implemented:**
- Remove self-financing branches when branch name contains `(SS)`
- Remove architecture-related branches using explicit architecture/interior-design branch codes
- Explicitly keep computing/design-science style branches such as `COMPUTER SCIENCE AND DESIGN`, `DATA SCIENCE`, `ARTIFICIAL INTELLIGENCE`, `MACHINE LEARNING`, and `CYBER SECURITY`

**All currently removed branch codes (`34`):**
- `AP` → `APPAREL TECHNOLOGY (SS)`
- `AS` → `AUTOMOBILE ENGINEERING (SS)`
- `AT` → `ARTIFICIAL INTELLIGENCE AND DATA SCIENCE (SS)`
- `BP` → `B.Plan`
- `BS` → `BIO TECHNOLOGY (SS)`
- `BY` → `BIO MEDICAL ENGINEERING (SS)`
- `CC` → `CHEMICAL AND ELECTRO CHEMICAL ENGINEERING (SS)`
- `CG` → `Computer Science and Engineering (Artificial Intelligence and Machine Learning) (SS)`
- `CL` → `CHEMICAL ENGINEERING (SS)`
- `CM` → `COMPUTER SCIENCE AND ENGINEERING (SS)`
- `CN` → `CIVIL ENGINEERING (SS)`
- `CR` → `CERAMIC TECHNOLOGY (SS)`
- `CW` → `Computer Science and Business System (SS)`
- `DA` → `Bachelor of Design`
- `EL` → `Electronics Engineering (VLSI Design and Technology) (SS)`
- `EM` → `ELECTRONICS AND COMMUNICATION ENGINEERING (SS)`
- `EY` → `ELECTRICAL AND ELECTRONICS ENGINEERING (SS)`
- `FS` → `FOOD TECHNOLOGY (SS)`
- `FY` → `FASHION TECHNOLOGY (SS)`
- `ID` → `Interior Design (SS)`
- `IF` → `Interior Design`
- `IM` → `INFORMATION TECHNOLOGY (SS)`
- `IS` → `INDUSTRIAL BIO TECHNOLOGY (SS)`
- `IY` → `INSTRUMENTATION AND CONTROL ENGINEERING (SS)`
- `MA` → `MATERIAL SCIENCE AND ENGINEERING (SS)`
- `MF` → `MECHANICAL ENGINEERING (SS)`
- `MG` → `MECHATRONICS (SS)`
- `MS` → `MECHANICAL ENGINEERING (SANDWICH) (SS)`
- `MY` → `METALLURGICAL ENGINEERING (SS)`
- `PM` → `PHARMACEUTICAL TECHNOLOGY (SS)`
- `PN` → `PRODUCTION ENGINEERING (SS)`
- `PP` → `PETROLEUM ENGINEERING AND TECHNOLOGY (SS)`
- `RA` → `ROBOTICS AND AUTOMATION (SS)`
- `TT` → `TEXTILE TECHNOLOGY (SS)`

**Explicit kept examples despite design/science wording:**
- `CD` → `COMPUTER SCIENCE AND DESIGN`
- `AD` → `Artificial Intelligence and Data Science`
- `CF` → `COMPUTER SCIENCE AND ENGINEERING (DATA SCIENCE)`
- `SC` → `Computer Science and Engineering (Cyber Security)`
- `AM` → `COMPUTER SCIENCE AND ENGINEERING (AI AND MACHINE LEARNING)`

**Filtered branch-master schema (`branch_codes_filtered.json`):**
- `branch_code`
- `branch_name`
- `observed_names`
- `row_count`
- `college_count`
- `total_seats`
- `is_self_financing`
- `is_architecture`
- `keep`
- `removal_reasons`

**Notes:**
- This filtered JSON is now the best source for a canonical `branches` table.
- The seat-matrix branch universe is the practical base here because it includes both `branch_code` and human-readable `branch_name` values.
- The allotment dataset still contains a wider raw branch-code universe (`115`) and is not yet automatically constrained to the filtered branch master.

**Suggested destination table:** `branches`

---

## 3.5 — College-Branch Mapping + Seat Matrix

**Status:** Present

**Canonical file:**
- `Seat_Matrix/output/seat_matrix_data.json`

**Row count:** `3,497`

**Coverage:**
- Colleges: `427`
- Distinct branch codes: `107`

**Actual JSON schema:**
- `s_no`
- `college_code`
- `college_name`
- `branch_code`
- `branch_name`
- `oc`
- `bc`
- `bcm`
- `mbc`
- `sc`
- `sca`
- `st`
- `total`
- `source_file`
- `extraction_date`

**Notes:**
- This file is the real source for both a `college_branches` mapping and a `community_seats` table.
- `SCA` still appears here in raw seat allocations, but app-facing guidance folds it into `SC`.

**Suggested destination tables:**
- `college_branches`
- `community_seats`

---

## 3.6 — Official TNEA Rank List

**Status:** Present for **2020–2025**

**Processed bundle root:**
- `General_Rank_List/processed/bundles/`

**Total rows across all years:** `1,017,768`

**Coverage by year:**
- 2020: `110,873`
- 2021: `136,973`
- 2022: `156,278`
- 2023: `176,744`
- 2024: `197,601`
- 2025: `239,299`

**Actual CSV schema:**
- `S NO`
- `GENERAL RANK`
- `APPLICATION NUMBER`
- `NAME OF THE CANDIDATE`
- `DATE OF BIRTH`
- `AGGREGATE MARK`
- `COMMUNITY`
- `COMMUNITY RANK`

**Observed community values:**
- `BC`, `BCM`, `MBC`, `MBCDNC`, `MBCV`, `OC`, `SC`, `SCA`, `ST`

**Notes:**
- The old document said this would arrive in Phase 4, but the repo already contains processed rank-list data for 2020–2025.
- 2026 rank-list data is not present.

**Suggested destination table:** `tnea_roll_numbers`

---

## 3.7 — Pre-Computed Rank Lookup Table

**Status:** Not present as a populated dataset.

No concrete `rank_lookup` output or seeded table export was found in this repo.

---

## 3.8 — College GPS Coordinates

**Status:** Present, but in multiple snapshots with slightly different coverage

### Legacy/core alignment snapshot
- `geo_integration/core_colleges_college_info_allotement_430_algorithmic.json`
- Count: `430`

### Active v4-go resolved output
- `geo_integration/active/v4go_intermediate/college_names_only_core_430_allotement_clean_output.json`
- Resolved count: `427`

### Active unresolved output
- `geo_integration/active/v4go_intermediate/college_names_only_core_430_algorithmic_unresolved.json`
- Unresolved count: `2`

**Actual active resolved schema:**
- `index`
- `original`
- `query`
- `latitude`
- `longitude`
- `maps_url`
- `status`
- `place_id`
- `source`
- `note`

**Notes:**
- The old document mentioned `lat/lng` and `lon -> lng` renaming, but the active resolver output currently uses `latitude` and `longitude`.
- If loading into `colleges`, a normalization step is still needed.

---

## 3.9 — TFC Location Data

**Status:** Source PDF is present, but no structured extracted dataset was found.

**Source file present:**
- `TFC/7_List_of_TFCs.pdf`

**Notes:**
- The old SQL table definition exists only as a plan.
- There is no verified JSON/CSV seed file for TFC locations in the current repo.

---

## 3.10 — Round Dates

**Status:** Not present as data in this repo.

No structured `round_dates` dataset or seed file was found.

---

## 3.11 — News and Announcements

**Status:** Not present as data in this repo.

No structured `news_items` dataset or seed file was found.

---

## 3.12 — Ingestion / Audit Subsystem

**Status:** File-based workflow exists, but not the planned database-first ingestion subsystem.

**What actually exists today:**
- per-bundle `meta.json`
- per-bundle `manifest.csv`
- merged CSV outputs
- report CSVs under `Allotement/data/processed/reports/`
- QA summaries under `qa/reports/`

**What was planned but is not present as actual tables/files here:**
- `ingestion_audit_log`
- `data_freshness`
- Telegram-triggered ingestion status flow

---

## Practical Supabase Mapping From Current Repo

If you want to ingest what is real today, use this mapping:

| Dataset in repo | Real source file | Suggested table |
| --- | --- | --- |
| Historical allotment 2020–2025 | `Allotement/data/processed/merged/merged_records_all_years_rounds_training_ready.csv` | `cutoff_data` |
| College metadata | `College_Info_Done/output.json` | `colleges` |
| Filtered non-architecture colleges | `College_Info_Done/output_present_non_architecture.json` | `colleges` or staging |
| Seat matrix | `Seat_Matrix/output/seat_matrix_data.json` | `college_branches`, `community_seats` |
| General rank list 2020–2025 | `General_Rank_List/processed/bundles/*/records.csv` | `tnea_roll_numbers` |
| GPS resolved data | `geo_integration/active/v4go_intermediate/college_names_only_core_430_allotement_clean_output.json` | `colleges` geo columns or geo staging |

---

## Bottom Line

The repo currently has **real extracted data** for:
- historical allotments (`2020–2025`)
- college metadata (`466 raw`, `430 filtered`)
- seat matrix (`3,497` rows)
- general rank lists (`2020–2025`)
- GPS resolution snapshots

It does **not** yet have real structured data for:
- 2026 allotments
- TFC structured seed data
- round dates
- news items
- rank lookup
- the planned database ingestion audit subsystem
---

## 4. Screen Inventory


**Source:** PRD v2.0, Section 4
**Last updated:** 12 April 2026

---

## 16 Product Screens

Every major paid surface should expose a free preview or trial state. Free users should understand what the feature does before being asked to pay.

| # | Screen | Route | Free | Paid |
|---|---|---|---|---|
| 0 | Landing | `/` | Yes | Yes |
| A | Login | `/login` | Yes | Yes |
| B | Subscribe + Paywall | `/subscribe?from=[x]` | Yes | Yes |
| 1a | Onboarding — Marks | `/onboarding/marks` | Yes | Yes |
| 1b | Onboarding — Details | `/onboarding/details` | Yes | Yes |
| 1c | Onboarding — Rank | `/onboarding/rank` | AI rank lookup band | Full guidance + evidence |
| 2 | Dashboard | `/dashboard` | Command centre | Command centre |
| 3 | Recommendations | `/recommendations` | Top 10 | All |
| 4 | Choice Filing | `/choices` | Trial preview + limited edits | Primary surface |
| 5 | AI Chat | `/chat` | 3 msgs + welcome | Unlimited |
| 6 | Analytics | `/analytics` | Trial preview | Yes |
| 7 | Rounds Tracker | `/rounds` | Trial preview | Production-grade |
| 8 | College Explorer | `/explore` | Browse + map + shortlist | Full data |
| 9 | College Insight | `/explore/[code]` | Overview + AI preview | Decision page |
| 10 | College Compare | `/compare` | Preview only | Decision tool |
| 11 | Rank Guidance | `/rank` | Broad band | Full band + context |
| 12 | Profile Edit | `/profile/edit` | Yes | Yes |
| 13 | News & Alerts | `/news` | Yes | Yes |

**No `/workspace` route.** Personal data environment capabilities surface contextually inside existing screens.

---

## Mobile Navigation

**Mobile shell:** 5-tab bottom navigation for launch — Home · Recs · Chat · Explore · Profile.

Choices, Trends, Rounds, and News surface as dashboard cards or locked previews until they are ready enough to deserve primary navigation.

---

## Paywall Page — `/subscribe?from=[feature]`

Standalone. No dismiss. Back → dashboard (authenticated) or home (unauthenticated).

### Paywall Triggers

| Trigger | Heading |
|---|---|
| Past 10th rec card | "Showing 10 of X colleges. Unlock all for ₹149." |
| 4th chat message | "You've used your 3 free messages. Unlock Full Access for ₹149." |
| `/choices` trial limit reached | "Continue full choice filing with Full Access." |
| `/analytics` trial limit reached | "Unlock full Trend Analytics for ₹149." |
| `/rounds` trial limit reached | "Unlock full Rounds Tracker for ₹149." |
| `/compare` premium or `/explore/[code]` premium | "Full compare and college details require Full Access." |
| Full guidance on `/rank` | "Full Rank Guidance requires Full Access." |

### Paywall Page Content

Context heading · feature summary · ₹149 · "One-time. No subscription." · **consent checkbox (required — no refunds policy)** · CTA → Razorpay · context-aware back · already-paid redirect
---

## 5. Access Model


**Source:** PRD v2.0, Section 5
**Last updated:** 12 April 2026

---

## Free Tier — ₹0

Trial-first rule: every major paid feature provides a free preview or limited trial mode before full lock.

| Feature | Detail |
|---|---|
| Eligibility gate | Students below 90/200 see empathetic hard gate. No recs, no guidance, no choice filing. Never shame. |
| Rank guidance | AI rank lookup table for everyone (historical rank band) — no confidence percentage and no false precision language |
| Recommendations | Top 10 per tab · limited columns · compare CTA available |
| AI Chat | 3 messages/season · full quality · server-side enforced · fingerprint second layer |
| Auto-welcome | One-time · broad band rank · does not consume free messages |
| College explorer | Browse + search + district filter + map + shortlist |
| College insight | Overview + AI preview + unlock board |
| College compare | One pair + summary preview + unlock board |
| Choice filing | Trial preview with limited edits and save count |
| Analytics | Trial preview with limited charts/data rows |
| Rounds tracker | Trial preview with active stage and explanation cards |
| Wishlist | Save up to 30 colleges |
| Personal data continuity | Onboarding resume · pinned colleges · saved filters · activity timeline |
| Dashboard | Command centre — phase-aware, full access |
| /news | Always free |

---

## Paid Tier — ₹149 One-Time

| Feature | Detail |
|---|---|
| Rank guidance | Full band + historical evidence panel + community context + board note |
| Recommendations | All colleges · all columns including premium · all filters · all sort |
| AI Chat | Unlimited · TFC-aware when verified TFC data is available · expected budget target: ~1M tokens per paid user per season |
| Choice Filing | Primary surface — fast reorder · snapshots · CSV import · PDF export · strategy notes |
| Analytics | Cutoff trends 2020–2025 · community breakdown |
| Rounds Tracker | Production-grade — countdown · TFC flow · consequence logic |
| College Map | 430 pins · Near Me filter |
| College Compare | Full decision tool — fees, hostel, travel, cutoff safety, district fit, reasoning |
| College Details | Full decision page — branch insight, year trends, placement, facilities, shortlist actions |
| Shortlist snapshots | Full version history + restore |
---

## 6. TNEA Timeline and Phases


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
---

## 7. Auth & Identity


**Source:** PRD v2.0, Section 7
**Last updated:** 12 April 2026

---

## Direct Google OAuth + Personal Data Environment

```
Student opens counsly.in
  → Direct Google OAuth
  → /auth/callback exchanges Google code for identity
  → Backend verifies Google ID token
  → Backend creates Counsly session
  → Upsert app user row using auth_user_id
  → Create personal data environment (workspace) if missing
  → New user → /onboarding/marks?entry=1
  → Returning incomplete → resume exact onboarding step
  → Returning complete → /dashboard
  → If TNEA_PHASE=4 AND ROLL_DATA_READY=true AND roll_number_verified=false
      → Roll number interstitial
```

Auth identity, premium subscription, and student product data are stored in separate tables.

One personal data environment per user. Strictly private. No members. No sharing. `auth_user_id` is canonical. `google_id` is stored only as an external identity reference and must not be used as the product ownership boundary.

---

## Device Fingerprinting (FR-37)

Silent SHA-256. Abuse prevention only — not model training (DPDP). `chat_messages_used` does NOT reset on new account.

---

## Auto-Welcome (FR-39)

First chat open. Broad band rank context. Does NOT consume free messages. One-time via `welcome_message_sent BOOLEAN DEFAULT false`. Ends with 3 suggested follow-up chips.

---

## Roll Number Verification (FR-38)

TNEA Phase 4. Triple-layer:
1. Roll number in `tnea_roll_numbers` → Hard block
2. Random number matches DTE record → Hard block
3. Marks ±5 → Soft flag only

One per account. First claim locks it. Conflicts → support@counsly.in. Official rank auto-populated.
---

## 8. Functional Requirements


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
| FR-22i | **Labeled ML predictions:** ML predictions are clearly labeled as predictions with confidence labels (High/Medium/Low). No exact precision claims or accuracy percentages in UI copy. Display confidence intervals, not point estimates. Historical data is shown alongside predictions for transparency. Users can always see which data source (ML prediction vs historical) informs their guidance. |

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
| FR-28 | 430 map pins within 3s on 4G |
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
---

## 9. Counselling Round Logic


**Source:** PRD v2.0, Section 9
**Last updated:** 12 April 2026

---

## Round Structure

4 stages per round:

1. **Choice Filling** — 3 days. Order matters. Fill any number of choices.
2. **Allotment** — DTE generates based on rank, community, availability.
3. **Confirmation** — 2 days. Confirm or lose the seat.
4. **Reporting** — Report to college or TFC. Non-reporting = seat cancelled.

---

## 6 Confirmation Options

| Option | Plain English | TFC? | What if you don't act? |
|---|---|---|---|
| Accept and Join | Satisfied. Will join. | No | Seat cancelled. No more rounds. |
| Accept and Upward | Want this seat, but hoping for better. | **Yes** | Seat cancelled. No TFC report = no upward consideration. |
| Decline and Upward | Don't want this seat, waiting for better. | **Yes** | Seat released. No TFC report = moved to next round without upward. |
| Decline and Move Next Round | Don't want this seat. Try next round. | No | Seat released. Automatically in next round. |
| Decline and Quit | Exiting counselling. | No | Seat released. Cannot rejoin. |
| Upward or Move Next Round | No seat allotted this round. | Conditional | Automatically considered for upward; if none, moves to next round. |

---

## Critical Rules

- 2 days to confirm — non-confirmation = automatic seat loss + next round
- Non-reporting to college (Accept and Join) = seat cancelled, no more rounds
- Non-payment at TFC (upward options) = seat cancelled, no more rounds
- Unoccupied seats pooled for upward movement
- 7.5% Govt School and PMSS holders: must report but need not pay fees
---

## 10. Runtime Admin System


**Source:** PRD v2.0, Section 10
**Last updated:** 12 April 2026

---

## Overview

All commands require input validation. Invalid input rejected. Never corrupts `app_config`. Every write logged in `admin_audit_log`.

---

## Telegram Bot Commands

| Command | Effect |
|---|---|
| `/setphase [1-5]` | Set TNEA_PHASE — instant |
| `/rankrelease` | Set RANK_RELEASED=true AND ROLL_DATA_READY=true |
| `/freechat [n]` | Change free chat limit (default 3) |
| `/endseason` | Set SEASON_END_DATE=today |
| `/setdate [key] [YYYY-MM-DD]` | Set any round deadline (validated format) |
| `/setrounds [n]` | Set `TOTAL_ROUNDS` (validated integer, default 3). Round tracker, checklists, deadline views, and history must adapt to this value dynamically. |
| `/listdates` | Show all round dates |
| `/addnews [msg] | [url]` | Push news item (max 10 active) |
| `/listnews` | Show active news with IDs |
| `/deletenews [id]` | Remove news item |
| `/broadcast [msg]` | Set BROADCAST_ACTIVE=true, BROADCAST_MESSAGE=[msg] |
| `/status` | All app_config · all round_dates · active news count · data freshness · last ingestion results |

---

## Audit Log

Every Telegram bot write must insert a row in `admin_audit_log` with:

- command
- previous value
- new value
- admin identifier
- timestamp
- success or failure status
- validation error when rejected
---

## 11. Database Schema

**Source:** Populated from Sections 3, 5, 7, 8, 10, 16, and 17  
**Last updated:** 24 April 2026

---

## Schema Rules

- Supabase PostgreSQL is the system of record for all product state.
- Student-owned product data is scoped by `workspace_id`. `auth_user_id` binds identity only; it is not the personal data ownership boundary.
- Use `uuid` primary keys by default. Keep stable natural keys only where they already exist and are truly canonical, such as `college_code`, `branch_code`, and `app_config.config_key`.
- Every mutable table must include `created_at timestamptz` and `updated_at timestamptz`.
- Every audit table is append-only. Audit rows are never updated in place.
- Preserve source-truth values in `source_*` columns when the app-facing normalized value differs from the raw source.
- App-facing community taxonomy is fixed to `OC`, `BC`, `BCM`, `MBC`, `SC`, `ST`. Raw values such as `MBCDNC`, `MBCV`, and `SCA` must be preserved, then normalized for app use; `SCA` maps to `SC`.
- `rank_lookup` is a curated derived table, not a raw-ingestion table.
- No automatic data deletion in v2.0. Archival states are explicit.

## Canonical Enums

| Domain | Allowed values | Notes |
| --- | --- | --- |
| `community_quota` | `OC`, `BC`, `BCM`, `MBC`, `SC`, `ST` | App-facing taxonomy |
| `workspace_kind` | `personal` | One PDE per user in v2.0 |
| `preference_group` | `wishlist`, `primary`, `pinned` | `primary` is the actual ordered choice list |
| `safety_category` | `safe`, `moderate`, `ambitious` | Stored in lowercase even if rendered as title case |
| `subscription_status` | `pending`, `active`, `expired`, `payment_failed`, `cancelled` | No refund flow in-app |
| `chat_role` | `system`, `assistant`, `user` | Transcript roles |
| `news_status` | `draft`, `active`, `archived` | Runtime admin controlled |
| `audit_status` | `started`, `success`, `failed`, `rejected` | Used in ingestion and admin audit logs |

## Identity And Access Tables

| Table | Purpose | PK / uniqueness | Required columns |
| --- | --- | --- | --- |
| `auth_identities` | External identity bridge for direct Google OAuth | `id uuid pk`, unique `auth_user_id`, unique `google_id`, unique `email` | `auth_user_id`, `provider`, `google_id`, `email`, `email_verified`, `display_name`, `avatar_url`, `last_login_at` |
| `app_users` | Internal app principal row | `id uuid pk`, unique `auth_identity_id`, unique `auth_user_id` | `auth_identity_id`, `auth_user_id`, `role`, `status`, `current_season_year` |
| `workspaces` | Personal Data Environment boundary | `id uuid pk`, unique `app_user_id` | `app_user_id`, `workspace_kind`, `display_name`, `season_year`, `archived_at` |
| `student_profiles` | Onboarding + canonical student facts | `id uuid pk`, unique `workspace_id` | `workspace_id`, `full_name`, `board`, `district`, `home_district`, `community_quota`, `maths_mark`, `physics_mark`, `chemistry_mark`, `cutoff_mark`, `expected_cutoff_mark`, `official_rank`, `official_community_rank`, `roll_number`, `roll_number_verified_at` |
| `onboarding_state` | Resume-exact-step state | `id uuid pk`, unique `workspace_id` | `workspace_id`, `current_step`, `is_complete`, `eligible`, `eligibility_reason`, `last_route`, `entered_phase`, `completed_at` |
| `user_sessions` | Server-side allowlist/revocation store for JWT cookies | `id uuid pk`, unique `jti` | `app_user_id`, `jti`, `token_hash`, `issued_at`, `expires_at`, `revoked_at` |
| `roll_number_claims` | One-account-per-roll enforcement | `id uuid pk`, unique `(season_year, roll_number)` | `workspace_id`, `season_year`, `roll_number`, `claim_status`, `verified_at`, `conflict_note` |

## Subscription And Payment Tables

| Table | Purpose | PK / uniqueness | Required columns |
| --- | --- | --- | --- |
| `subscriptions` | Paid entitlement for a season | `id uuid pk`, unique `(workspace_id, season_year)` | `workspace_id`, `season_year`, `plan_code`, `status`, `amount_paise`, `starts_at`, `ends_at`, `activated_at`, `source_payment_order_id` |
| `payment_orders` | Razorpay order/payment linkage | `id uuid pk`, unique `razorpay_order_id`, nullable unique `razorpay_payment_id` | `workspace_id`, `season_year`, `razorpay_order_id`, `razorpay_payment_id`, `razorpay_signature`, `amount_paise`, `currency`, `status`, `verified_at`, `failure_reason` |
| `payment_audit_log` | Append-only payment event log | `id uuid pk` | `workspace_id`, `payment_order_id`, `event_type`, `event_payload jsonb`, `created_at` |

## Workspace Product Tables

| Table | Purpose | PK / uniqueness | Required columns |
| --- | --- | --- | --- |
| `user_college_preferences` | Canonical preference store from FR-44 | `id uuid pk`, unique `(workspace_id, preference_group, college_code, branch_code)` | `workspace_id`, `preference_group`, `priority`, `college_code`, `branch_code`, `system_category`, `manual_category`, `notes`, `added_from`, `active` |
| `shortlist_snapshots` | Snapshot header rows | `id uuid pk` | `workspace_id`, `title`, `item_count`, `created_by`, `created_at` |
| `shortlist_snapshot_items` | Immutable rows captured per snapshot | `id uuid pk` | `snapshot_id`, `priority`, `college_code`, `branch_code`, `category`, `notes` |
| `college_compare_history` | Saved compare session metadata | `id uuid pk` | `workspace_id`, `title`, `created_from`, `created_at` |
| `college_compare_history_items` | Colleges/branches inside one compare session | `id uuid pk` | `compare_history_id`, `sort_order`, `college_code`, `branch_code` |
| `user_saved_filters` | Persisted recommendation/explore filters | `id uuid pk`, unique `(workspace_id, screen_name)` | `workspace_id`, `screen_name`, `filter_payload jsonb` |
| `user_activity_log` | Timeline/events inside a workspace | `id uuid pk` | `workspace_id`, `event_type`, `entity_type`, `entity_id`, `event_payload jsonb`, `created_at` |
| `chat_threads` | Per-workspace chat containers | `id uuid pk` | `workspace_id`, `title`, `archived`, `last_message_at` |
| `chat_messages` | Stored chat transcript | `id uuid pk` | `thread_id`, `role`, `content`, `token_estimate`, `grounding_payload jsonb`, `source_count`, `created_at` |
| `chat_usage_counters` | Free/paid usage meter per season | `id uuid pk`, unique `(workspace_id, season_year)` | `workspace_id`, `season_year`, `free_messages_used`, `paid_messages_used`, `welcome_message_sent`, `fingerprint_hash`, `last_message_at` |

## Reference Data Tables

| Table | Purpose | PK / uniqueness | Required columns |
| --- | --- | --- | --- |
| `colleges` | Canonical college master | natural PK `college_code` | `college_code`, `college_name`, `address`, `district`, `taluk`, `pincode`, `phone_fax`, `email`, `website`, `autonomous_status`, `minority_status`, `placement_record`, `hostel_boys`, `hostel_girls`, `transport_facilities`, `min_transport_charges`, `max_transport_charges`, `latitude`, `longitude`, `maps_url`, `is_architecture`, `raw_payload jsonb` |
| `branches` | Canonical branch master | natural PK `branch_code` | `branch_code`, `branch_name`, `is_architecture`, `keep`, `removal_reasons jsonb` |
| `college_branches` | College-to-branch mapping | `id uuid pk`, unique `(college_code, branch_code)` | `college_code`, `branch_code`, `branch_name`, `active`, `source_file`, `extraction_date` |
| `community_seats` | Per-college per-branch seat totals | `id uuid pk`, unique `(college_code, branch_code)` | `college_code`, `branch_code`, `oc`, `bc`, `bcm`, `mbc`, `sc`, `sca`, `st`, `total`, `source_file`, `extraction_date` |
| `cutoff_data` | Historical allotment rows for recommendations and analytics | `id uuid pk` | `season_year`, `round_number`, `aggregate_mark`, `general_rank`, `community_quota`, `source_community_raw`, `college_code`, `branch_code`, `allotted_category`, `application_number`, `source_file` |
| `rank_lookup` | Pre-computed historical rank band lookup | PK `(aggregate_mark)` | `aggregate_mark`, `rank_min`, `rank_max`, `confidence_label`, `sample_size`, `source_years jsonb`, `method_version`, `is_abstain` |
| `tnea_roll_numbers` | Official rank-list rows and claim lookup | `id uuid pk`, unique `(season_year, application_number)`, nullable unique `(season_year, roll_number)` | `season_year`, `roll_number`, `application_number`, `general_rank`, `aggregate_mark`, `community_quota`, `source_community_raw`, `community_rank`, `candidate_name`, `date_of_birth`, `random_number`, `source_file` |
| `tfc_locations` | Facilitation centre master | `id uuid pk` | `name`, `district`, `address`, `phone`, `latitude`, `longitude`, `maps_url`, `verified_at`, `source_file` |

## Runtime And Audit Tables

| Table | Purpose | PK / uniqueness | Required columns |
| --- | --- | --- | --- |
| `app_config` | Runtime key-value store | natural PK `config_key` | `config_key`, `value_type`, `value_json`, `updated_by`, `updated_at` |
| `round_dates` | Counselling round schedule | `id uuid pk`, unique `(season_year, round_number)` | `season_year`, `round_number`, `choice_fill_start_at`, `choice_fill_end_at`, `allotment_at`, `confirm_end_at`, `report_end_at`, `is_active` |
| `news_items` | Runtime-managed news strip and links | `id uuid pk` | `title`, `summary`, `source_url`, `published_at`, `status`, `sort_order`, `created_by` |
| `admin_audit_log` | Telegram/admin write log | `id uuid pk` | `admin_identifier`, `command`, `target_key`, `previous_value jsonb`, `new_value jsonb`, `success`, `validation_error`, `created_at` |
| `ingestion_audit_log` | Ingestion lifecycle tracking | `id uuid pk` | `dataset_name`, `run_type`, `status`, `started_at`, `finished_at`, `source_reference`, `rows_seen`, `rows_loaded`, `report_path`, `error_message` |
| `data_freshness` | Last-known freshness per dataset | natural PK `dataset_name` | `dataset_name`, `last_success_at`, `last_source_at`, `freshness_status`, `source_reference`, `notes` |

## Required `app_config` Keys

- `TNEA_PHASE`
- `TOTAL_ROUNDS`
- `RANK_RELEASED`
- `ROLL_DATA_READY`
- `FREE_CHAT_LIMIT`
- `SEASON_END_DATE`
- `BROADCAST_ACTIVE`
- `BROADCAST_MESSAGE`

## Normalization Rules

- Keep raw source community values in `source_community_raw`.
- Normalize `MBCDNC` and `MBCV` into app-facing `MBC`, but do not overwrite raw-ingestion truth.
- Keep raw `sca` seat columns for traceability, but merge those seats into app-facing `SC` guidance and do not expose `SCA` as a separate student quota.
- Normalize geo columns to `latitude` and `longitude` in final tables even if source files differ.
- `college_code` and `branch_code` remain the only accepted natural foreign keys across reference tables.

## Minimum Indexes And Constraints

- `auth_identities(auth_user_id)`
- `auth_identities(google_id)`
- `workspaces(app_user_id)`
- `student_profiles(workspace_id)`
- `user_college_preferences(workspace_id, preference_group, priority)`
- `cutoff_data(season_year, round_number, community_quota, college_code, branch_code)`
- `rank_lookup(aggregate_mark)`
- `tnea_roll_numbers(season_year, roll_number)`
- `tnea_roll_numbers(season_year, application_number)`
- `news_items(status, published_at desc)`
- `round_dates(season_year, round_number)`

## Ownership And Access Rules

- Reference tables are read-only to the app client and writable only through backend/admin ingestion paths.
- Workspace tables are scoped by `workspace_id`; any direct client access must enforce that boundary with RLS.
- Payment, admin, and ingestion audit tables are backend/admin only.
- Chat grounding payloads, roll-number verification fields, and payment signatures must never be exposed to the client unfiltered.
- `workspace_id` is the canonical product boundary. `auth_user_id` remains an identity binding key only.
---

## 12. Tech Stack


**Source:** PRD v2.0, Section 12
**Last updated:** 12 April 2026

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14+ (App Router) · TailwindCSS |
| Auth | Direct Google OAuth · backend-created Counsly session · `/auth/callback` |
| State | React Context + useState |
| Charts | Recharts |
| Drag & Drop | @dnd-kit/core + @dnd-kit/sortable |
| PDF | jsPDF (client-side) |
| Maps | Leaflet.js + React-Leaflet + markercluster + OpenStreetMap |
| Payment | Razorpay SDK |
| Backend | FastAPI (Python) · async · httpx · sse-starlette |
| Rank Guidance | `rank_lookup` table query — O(1), ~5–10ms |
| Chat | OpenRouter · DeepSeek V3.2 · `OPENROUTER_MODEL` env var · streaming SSE |
| Database | Supabase PostgreSQL · RLS + service-role |
| Frontend Hosting | Vercel |
| Backend Hosting | Railway |
| Monitoring | UptimeRobot |
| Analytics | GA4 |
| Domain | counsly.in (GoDaddy → Vercel DNS) |
| Admin | Telegram bot (v1) |
| Build Executor | Codex |

---

## Runtime Environment Variables

### Web (Required)

- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_RAZORPAY_KEY_ID`

### API (Required)

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `SESSION_SECRET`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `CORS_ORIGINS`
- `TRUSTED_HOSTS`

### API (Optional — paid/chat/payments)

- `OPENROUTER_API_KEY`
- `OPENROUTER_API_URL`
- `OPENROUTER_MODEL`
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`

**Runtime rule:** Missing optional keys must degrade those features gracefully. They must not prevent app boot.
---

## 13. Design Tokens

**Source:** Populated from `DESIGN.md` and launch mobile rules  
**Last updated:** 24 April 2026

---

## Launch UI Rules

- Mobile only for v1.0. Baseline viewport is `360px`.
- This section is the implementation contract for launch UI. If `DESIGN.md` and this section differ, this section wins for launch build decisions.
- Launch authenticated navigation is `Home`, `Recs`, `Choices`, `Explore`, `Profile`.
- `Chat`, `Rounds`, `Analytics`, `News`, `Compare`, and `Map` are secondary entry points, not primary bottom-nav items in launch.
- One primary CTA per screen. Secondary actions belong in ghost actions, inline links, or an overflow bottom sheet.
- Decision-heavy surfaces use list-first density. Cards are containers, not an excuse for extra scroll.
- No dark mode in v2.0 mobile launch.

## Color Tokens

| Token | Value | Use |
| --- | --- | --- |
| `color.bg.page` | `#f5f4ed` | Main page background |
| `color.bg.card` | `#faf9f5` | Standard card background |
| `color.bg.surface_alt` | `#EEE7DC` | Section divider / alternate surface |
| `color.bg.button_secondary` | `#e8e6dc` | Secondary button and skeleton base |
| `color.bg.white` | `#ffffff` | Inputs and maximum-contrast surfaces |
| `color.text.primary` | `#141413` | Primary text |
| `color.text.secondary` | `#5e5d59` | Body/supporting copy |
| `color.text.tertiary` | `#87867f` | Metadata, footnotes, inactive nav |
| `color.text.emphasis` | `#3d3d3a` | Secondary emphasized text and links |
| `color.brand.primary` | `#c96442` | Only primary CTA background |
| `color.brand.secondary` | `#d97757` | Secondary accent moments only |
| `color.semantic.safe` | `#4E8A62` | Safe label |
| `color.semantic.moderate` | `#C17B4A` | Moderate label |
| `color.semantic.ambitious` | `#B45A52` | Ambitious label |
| `color.semantic.error` | `#b53333` | Error state |
| `color.focus` | `#3898ec` | Input focus ring only |
| `color.border.default` | `#f0eee6` | Default card/input border |
| `color.border.strong` | `#e8e6dc` | Stronger section or card border |
| `color.shadow.ring` | `#d1cfc5` | Ring shadow color |
| `color.shadow.ring_active` | `#c2c0b6` | Active/pressed ring color |

## Typography Tokens

| Token | Font | Mobile size | Weight | Line height | Use |
| --- | --- | --- | --- | --- | --- |
| `font.heading` | `Georgia, 'Times New Roman', serif` | - | `500` max | - | Screen and section titles |
| `font.body` | `Inter, system-ui, -apple-system, sans-serif` | - | `400-500` | - | UI and body copy |
| `font.mono` | `'JetBrains Mono', 'Fira Code', monospace` | - | `500` | - | Ranks, marks, countdowns, tabular values |
| `text.screen_title` | heading | `22px` | `500` | `1.20` | Page title |
| `text.section_header` | heading | `18px` | `500` | `1.20` | Section heading |
| `text.card_title` | heading | `16px` | `500` | `1.20` | College or feature title |
| `text.feature_title` | heading | `14px` | `500` | `1.20` | Small heading |
| `text.body_lg` | body | `16px` | `400` | `1.50` | Intro copy |
| `text.body` | body | `14px` | `400-500` | `1.50` | Standard body |
| `text.body_sm` | body | `13px` | `400-500` | `1.40` | Dense lists |
| `text.caption` | body | `12px` | `400` | `1.40` | Metadata |
| `text.badge` | body | `11px` | `500` | `1.25` | Badges and tags |
| `text.overline` | body | `10px` | `500` | `1.50` | Uppercase helper labels |
| `text.data` | mono | `14px` | `500` | `1.40` | Numeric data |
| `text.cta` | body | `15px` | `500` | `1.00` | Button labels |

## Layout And Spacing Tokens

| Token | Value | Use |
| --- | --- | --- |
| `viewport.base` | `360px` | Primary layout target |
| `layout.page_padding_x` | `16px` | Screen horizontal padding |
| `layout.page_padding_y` | `16px` | Standard vertical inset |
| `layout.app_bar_h` | `56px` | Mobile app bar |
| `layout.tab_bar_h` | `56px` | Bottom nav bar |
| `layout.sticky_action_min_h` | `72px` | Sticky CTA zone including padding |
| `layout.touch_min` | `44px` | Minimum tappable area |
| `layout.button_h` | `48px` | Standard CTA height |
| `layout.input_h` | `48px` | Standard input height |
| `layout.card_gap` | `12px` | Gap between cards |
| `layout.max_scrolls_to_primary` | `3` | Max scroll-depth rule |
| `space.xs` | `4px` | Tight gap |
| `space.sm` | `8px` | Compact gap |
| `space.md` | `12px` | Card internal half-padding / compact section gap |
| `space.lg` | `16px` | Standard padding |
| `space.xl` | `20px` | Featured card padding |
| `space.2xl` | `24px` | Section spacing |
| `space.3xl` | `32px` | Major break |
| `space.4xl` | `48px` | Screen-level rhythm |

## Shape And Elevation Tokens

| Token | Value | Use |
| --- | --- | --- |
| `radius.sm` | `8px` | Small elements |
| `radius.md` | `12px` | Inputs, buttons, cards |
| `radius.lg` | `16px` | Featured cards and modals |
| `border.default` | `1px solid #f0eee6` | Standard card/input border |
| `border.strong` | `1px solid #e8e6dc` | Stronger divider |
| `shadow.ring` | `0 0 0 1px #d1cfc5` | Interactive state |
| `shadow.ring_active` | `0 0 0 1px #c2c0b6` | Pressed state |
| `shadow.whisper` | `rgba(0,0,0,0.05) 0 4px 24px` | Featured cards / modals |
| `overlay.blur` | `8px` | Unlock overlays and bottom sheet backdrop |

## Component Contracts

### Buttons

- Primary button: `48px` high, full width on mobile, `color.brand.primary` background, `color.bg.card` text, `radius.md`.
- Secondary button: `48px` high, `color.bg.button_secondary` background, `color.text.primary` text.
- Ghost button: `44px` high, transparent background, `color.text.emphasis`.
- Do not place two primary buttons in the same sticky action area.

### Cards

- Standard card: `color.bg.card`, `border.default`, `radius.md`, `16px` padding.
- Featured card: `color.bg.card`, `border.strong`, `radius.lg`, `20px` padding, `shadow.whisper`.
- Interactive cards use `shadow.ring` for hover/press feedback instead of heavy drop shadows.

### Inputs

- Text and select inputs: `48px` high, `16px` body text, white background, `border.strong`, `radius.md`.
- Numeric inputs use `font.mono` and must keep `16px` font size to avoid iOS zoom.
- Focus state uses only `color.focus` plus a soft focus ring.

### Unlock Boards

- Locked preview uses blurred content plus one clear value statement and one CTA.
- Use the same unlock pattern across recommendations, compare, insight, analytics, and rounds.
- Do not switch between inline blur, modal trap, and full-page interruption for the same type of entitlement event.

### Bottom Navigation

- Launch nav is 5 tabs only.
- Each tab gets a minimum `44px x 44px` tap target inside a `56px` high bar.
- Active state is color only; no extra underline or dot.

### Sticky Action Areas

- Sticky areas sit above the tab bar.
- They carry one primary CTA.
- If a screen needs more than one secondary action, those actions move into a ghost-action row or overflow bottom sheet.

## Screen Rules For Launch

- Dashboard: topmost full-width next-action card, no filler cards, no more than one horizontal content strip.
- Recommendations: vertical result list first, filters in a sheet, safety labels always visible.
- Choices: one active row at a time, numeric move is the default reorder interaction, `Add College` is the primary sticky CTA, `Save Snapshot` and `Export PDF` move to secondary actions.
- Compare: stacked metric rows only, no side-by-side desktop-style columns on mobile.
- Explore: sticky search, vertical results, map only as a secondary full-screen mode.
- College Insight: shortlist CTA sticky at bottom, premium sections lock inline, not as a route jump.
- Chat: text only, composer max 4 lines, send button `44px`.
- Onboarding: one step at a time, large numeric inputs, resume exactly where the user left off.

## Do Not Break These Rules

- Do not introduce desktop-first layout decisions into mobile launch screens.
- Do not add dark mode in v2.0.
- Do not use cool blue-gray UI chrome outside focus states.
- Do not use heavy shadows when ring borders are enough.
- Do not use more than one primary CTA per screen.
- Do not ship an 8-tab authenticated nav in launch.
- Do not use spinners where a skeleton or optimistic state is possible.
---

## 14. Non-Goals


**Source:** PRD v2.0, Section 14
**Last updated:** 12 April 2026

---

| Non-Goal | Target Version |
|---|---|
| Voice input | v2 |
| Push notifications | v2 |
| Tamil language | v2 |
| 7.5% Govt School reservation tracking | v2 |
| DA category | v2 |
| Multi-year access | Never |
| In-app refunds | Never |
| Shared personal data environments | Never |
| College photos for all 430 (category placeholder used) | v2 |
| Round-wise cutoff analytics (R1/R2/R3/R4...) | v2 |
| `/admin` Next.js page | v2 (Telegram bot is v1 admin) |
---

## 15. Success Metrics


**Source:** PRD v2.0, Section 15
**Last updated:** 12 April 2026

---

| Metric | Target |
|---|---|
| Onboarding completion | > 70% |
| Time to first rec | < 5 min |
| Choice list created | > 40% of onboarded |
| AI chat engagement | > 30% send >= 1 msg |
| PDF export | > 20% of choice builders |
| Explorer usage | > 50% first session |
| Wishlist saves | > 25% bookmark >= 1 |
| Rank guidance used | > 60% submit |
| Mobile bounce | < 40% at 360px |
| Lighthouse | >= 85 mobile |
| Map load | < 3s for 430 pins on 4G |
| Paywall → CTA | > 30% |
| Subscription conversion | > 10% of registered |
| Payment success | > 90% initiated |
| Roll verification | > 80% TNEA Phase 4 first session |
| Onboarding resume | > 50% of returning incomplete users finish |
| Shortlist snapshots | > 25% of choice builders save >= 1 |
| Choice PDF export | > 95% valid completion |
| Compare session saved | > 15% of compare users save a session |
| Dashboard next action used | > 60% of dashboard visits result in the action being taken |
---

## 16. Gap Register


**Source:** PRD v2.0, Section 16
**Last updated:** 12 April 2026

---

## Blockers (Pre-Launch)

| # | Gap | Action |
|---|---|---|
| B-1 | Razorpay KYC not confirmed | Start immediately — 3–7 day government processing window |
| B-2 | PDF rank-list ingestion needs live-file verification | Run parser against actual DTE PDF when published |
| B-3 | TFC seed script not built | Data is available — build seed script and load |
| B-4 | Direct Google OAuth and identity schema not built | Verify Google ID token server-side, store `google_id` only as an external identity reference, and use `auth_user_id` as the product ownership boundary |
| B-5 | Compare and college-detail APIs need real data | Replace demo-only paths before launch |
| B-6 | `BROADCAST_ACTIVE` / `BROADCAST_MESSAGE` not rendering on frontend | Wire DB keys to frontend banner component |
| B-7 | Workspace endpoint contract misaligned with current code | Align routes, settings, snapshot, import paths to this PRD |
| B-8 | Choice export PDF not built | Build jsPDF export with strategy notes and disclaimer |
| B-9 | Git not initialised | Init Git, first commit, set remote — before any Codex build work |
| B-10 | `ingestion_audit_log`, `data_freshness`, `admin_audit_log`, `payment_audit_log`, `college_compare_history` tables not in migrations | Add migrations before Codex begins schema work |
| B-11 | Observability not in place | GA4, UptimeRobot, error logging, payment audit log must be live before launch |

---

## Product Gaps (Pre-Launch)

- Eligibility gate empathetic copy written
- Empty states on all screens
- Error states for all API failures
- Phase-content matrix UX copy for all 5 phases
- `/news` navigation placement (6th tab vs replace existing)
- Session expiry re-login flow
- 404 and maintenance pages
- "What happens if you don't act" copy for all 6 confirmation options
- Compare "why this differs" reasoning prompt design
- Mobile editing mode for choices: priority number tap → numeric position jump

---

## Technical Gaps (Pre-Launch)

- `rank_lookup` seed script from 2020–2025 historical rank-list data
- Cutoff backfill workflow (idempotent)
- Cutoff refresh workflow (per-round)
- TFC seed script
- Real-time scraping pipeline for post-launch news/PDF automation (with legal and reliability review)
- `reference_validate.py`
- OpenRouter SSE validation
- Workspace endpoint alignment
- Compare session save/restore
- College insight tabs (all 5)
- Rounds tracker countdown timer
- Mobile-specific layouts for 4 key screens
- GA4 event schema
- UptimeRobot setup
- Payment audit log integration

---

## Business Gaps

- GST threshold monitoring
- support@counsly.in setup
- DPDP review
- Marketing plan
---

## 17. Open Questions


**Source:** PRD v2.0, Section 17
**Last updated:** 12 April 2026

---

## Resolved

| ID | Question | Resolution |
|---|---|---|
| OQ-1 | Official TNEA 2026 schedule | Runtime-managed via Telegram |
| OQ-2 | Choice list storage | Supabase DB |
| OQ-3 | Chat model | DeepSeek V3.2 or v4 via OpenRouter |
| OQ-4 | Low-mark UX | 90/200 hard gate · empathetic copy · no shaming |
| OQ-5 | 2026 allotment data | 2025 at launch · ingest 2026 per round |
| OQ-8 | TN state privacy | Deferred |
| OQ-10 | Round-wise data | Not available · FR-17c v2 |
| OQ-11 | Paid rank outputs | Full guidance = broad band + historical evidence panel · no ML precision claims |
| OQ-12 | RANK_RELEASED control | Telegram `/rankrelease` |
| OQ-13 | Wishlist login | Login required |
| OQ-14 | OTP provider | Google OAuth only |
| OQ-15 | Subscription schema | Separate `subscriptions` table |
| OQ-16 | Tax/GST | ₹149 one-time user-facing price. GST/VAT handling needs accountant/legal review before registration threshold decisions. |
| OQ-17 | Refund | No refunds · consent checkbox |
| OQ-18 | 3-msg reset | Does not reset |
| OQ-19 | TNEA phase dates | In Section 6 |
| OQ-20 | Roll number ingestion | Automated PDF parser · live file pending |
| OQ-21 | 5-phase TNEA system | INTACT |
| OQ-22 | Classic rank | `rank_lookup` table · all users get historical rank band guidance; paid users get added evidence/context |
| OQ-23 | DTE rank list format | PDF table |
| OQ-24 | Supabase RLS | Service role key for sensitive writes |
| OQ-25 | Free vs paid boundary | Defined in Section 5 |
| OQ-26 | Premium column split | Sections 3.3 and 11 |
| OQ-27 | Auth identity column | `auth_user_id` canonical |
| OQ-28 | Choice import format | CSV: `priority,college_code,branch_code,category,notes` |
| OQ-29 | Chat memory retention | No auto-deletion · clear option in settings |
| OQ-33 | Chat usage policy | Free tier: 3 messages/season. Paid tier: unlimited messages with planning target of ~1M tokens per paid user per season. |
| OQ-31 | Phase transition mid-session | Non-dismissible banner → user reload |
| OQ-30 | Classic rank band methodology | Build historical rank-band lookup from 2020–2025 rank-list data. Everyone gets the band; paid users get evidence/context. No exact AI-predicted rank copy. |

---

## Open (Must Resolve Before Build)

| ID | Question | Status |
|---|---|---|
| OQ-32 | "Why this differs" in compare — AI generated or rule-based? If AI: prompt design needed. If rule-based: logic for top-2 significant difference detection needed. | Must decide before compare build begins. |
---

## 18. Glossary


**Source:** PRD v2.0, Appendix
**Last updated:** 12 April 2026

---

| Term | Definition |
|---|---|
| TNEA | Tamil Nadu Engineering Admissions |
| DTE | Directorate of Technical Education — runs TNEA |
| TFC | Tamil Nadu Engineering Admissions Facilitation Centre — physical offices for fee payment and certificate verification |
| TNEA Phase | One of 5 operational stages (Pre-Marks / Marks Released / TNEA Announced / Rank Assigned / Counselling Active). Controlled by `TNEA_PHASE` in `app_config`. Not a project phase. |
| Personal Data Environment | Each student's strictly private isolated data space. Internally a `workspace`. One per user. No sharing. Contains onboarding state, preferences, chat history, shortlist snapshots, compare sessions, activity. |
| Trust-First Guidance | The product's rank guidance philosophy: broad bands only, abstain when uncertain, historical evidence over precision claims, official rank replaces all estimates immediately when available. |
| Broad Band | Historical rank range (`rank_min–rank_max`) with a High/Medium/Low confidence label. It is range-only guidance, not an exact predicted rank. No percentile, no decimal, no precision language. |
| Full Guidance | Paid rank guidance: broad band plus historical evidence panel showing recent real data for the student's marks range, with community and board context. |
| Eligibility Gate | Hard gate at onboarding Step 1 (TNEA Phase 2+). Students below 90/200 are blocked. Empathetic copy. No shaming. |
| Shortlist Snapshot | Immutable saved version of an ordered choice list. Titled, timestamped, restorable. |
| Compare Session | A named saved compare pair/triple. Includes college codes and branch codes. Accessible from dashboard and compare page. |
| rank_lookup | Planned lookup table · aggregate mark → (rank_min, rank_max, confidence). Built from 2020–2025 historical rank-list data with abstain rules for sparse data. |
| Upward Movement | TFC fee-paid students considered for higher-ranked choices if seats become available in upward movement processing. |
| Roll number | Official DTE identifier — TNEA Phase 4 identity gate |
| ROLL_DATA_READY | app_config flag — true only after rank list ingestion completes successfully |
| BROADCAST_ACTIVE | app_config flag — true when an active broadcast banner should be shown on all authenticated screens |
| Community quota | OC · BC · BCM · MBC · SC · ST |
| Codex | Build executor for all implementation work |
| 402 | HTTP status returned for paid features accessed by free users |
| DPDP | Digital Personal Data Protection Act 2023 |
