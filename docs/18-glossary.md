# Counsly — Glossary

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
