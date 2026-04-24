# Counsly — Extracted Edits

These notes were moved out of the product specification files so the core docs stay clean. They are not applied decisions yet.

## docs/01-introduction-and-philosophy.md

| Location | Current spec text | Edit note |
| --- | --- | --- |
| Philosophy heading | `Philosophy: Trust First, Precision Never` | The whole part below this feels like AI slop. |
| Pricing / Tax | Inclusive of 30% GST — registration not required until ₹20L revenue (~1,342 paying users) | Changed 18% to 30% so the product does not end up in a VAT trap. This is not going to be registered for now, so keep it as normal income tax. |

## docs/02-goals.md

| ID | Current spec text | Edit note |
| --- | --- | --- |
| G-5 | Cutoff analytics 2020–2026, community-wise | 2020–2025. |
| G-6 | Production-grade rounds tracker with countdown, TFC flow, and consequence logic | Need more clarity; this is not understandable yet. |
| G-8 | Mild light-first UI on mobile | Not a goal. |
| G-12 | Paywall as a standalone dedicated page at the exact moment of feature-limit reach | Not a goal. |
| G-13 | Compare as a serious decision tool — not a directory feature | Need more clarification; this is not understandable yet. |
| G-14 | Explore and detail pages as decision pages — not directory pages | Need more clarification; this is not understandable yet. |
| G-16 | Choice persistence up to 300 rows, snapshots, import/export | 200 choices is enough. |
| G-17 | Supabase Auth + Vercel deployment path launchable | AI slop. |
| G-18 | Chat provider/model configurable by env variable — no hard-coded model strings | Not a goal. |
| G-19 | Runtime admin system that gives complete operational control without deployment | More explanation needed on what this really means. |
| G-20 | Data ingestion treated as a first-class subsystem with audit logs and validation | Explanation needed; this is not understandable yet. |
| G-21 | Observability layer in place before launch | Explanation needed; this is not understandable yet. |

## docs/04-screen-inventory.md

| Location | Current spec text | Edit note |
| --- | --- | --- |
| Document title | `Counsly — Screen Inventory` | We want trial on everything. |
| Recommendations free tier | Top 3 | Top 10. |

## docs/05-access-model.md

| Location | Current spec text | Edit note |
| --- | --- | --- |
| Document title | `Counsly — Access Model` | We can say our model's prediction is this much. That might be helpful. |
| Paid Tier / AI Chat | Unlimited · TFC-aware | Prediction: 1M tokens per person and 2K-4K tokens per conversation, giving roughly 250-500 conversations per person. Need ideas. |

## docs/06-tnea-timeline-and-phases.md

| Location | Current spec text | Edit note |
| --- | --- | --- |
| Phase 5 hero surface | Rounds tracker · TFC-aware AI chat | Rounds must be dynamic. If total rounds is set to 4, everything must adjust dynamically. |
| Rank System Fate / Broad Band | Broad Band | Need explanation of what broad band means. |
| Rank System Fate / Full Guidance | Full Guidance | Need explanation of what full guidance means. |

## docs/07-auth-and-identity.md

| Location | Current spec text | Edit note |
| --- | --- | --- |
| Document title | `Counsly — Auth & Identity` | Auth and premium subscription stay in a different table; user data stays in a different table. |
| Auth provider | Supabase Google Auth + Personal Data Environment | No Supabase Auth. Use direct Google OAuth because Supabase Auth shows its project URL, which is considered vulnerable and may reveal the database provider to competitors. |

## docs/08-functional-requirements.md

| ID | Current spec text | Edit note |
| --- | --- | --- |
| FR-22a | Two states via `RANK_RELEASED` | More clarity needed; this is not understandable yet. |
| FR-22b | **Broad Band (Free):** Query `rank_lookup` by (maths, physics, chemistry). Output: rank_min, rank_max, confidence label (High/Medium/Low). No precision language. CBSE/ICSE disclaimer required. | What is broad band? |
| FR-5 | Safe = rank better than cutoff by >500 · Moderate = within 500 · Ambitious = exceeds | Need more clarity on `>500`, `within 500`, and related cutoff logic. |
| FR-12 | Full history as context · anonymised before LLM call · TFC-aware grounding | Need a way to avoid context filling. |
| TFC Awareness heading | TFC Awareness | Want to get TFC geo locations as well. |
| FR-66 | Fast reorder — drag-and-drop desktop, long-press mobile, optimistic UI | Find a better mobile method: pressing the choice number should open a keyboard, and entering a number should move the college to that choice number. |

## docs/14-non-goals.md

| Location | Current spec text | Edit note |
| --- | --- | --- |
| Real-time tneaonline.org scraping | Never | We can add it now. |

## docs/17-open-questions.md

| ID | Current spec text | Edit note |
| --- | --- | --- |
| OQ-26 | Premium column split: `§3.3 + §11` | Need explanation of what the `§` symbol means. |
| OQ-30 | Classic rank band methodology — how rank_min/rank_max computed from historical data. Blocks seed script. | Everyone gets AI-based rank prediction, not only paid users. |
