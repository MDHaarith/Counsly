# Counsly — Open Questions

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
