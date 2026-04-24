# Counsly — Real Data Inventory and Current Schema

**Source of truth:** files currently present in this repo
**Populated on:** 23 April 2026

---

## Overview

This file replaces the older launch-planning notes with the **actual extracted data and schemas** currently available in `/home/mdhaarith/Desktop/Data_Extractor (Copy)`.

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
- `MBCDNC`, `MBCV`, and `SCA` were normalized away in the training-ready file.
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
- `SCA` still appears here in seat allocations, even though the training-ready allotment dataset normalizes communities differently.

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
