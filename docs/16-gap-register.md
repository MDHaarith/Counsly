# Counsly — Gap Register

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
