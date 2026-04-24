# Counsly — Screen Inventory

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

**Mobile shell:** 5-tab bottom navigation for launch — Home · Recs · Choices · Explore · Profile.

Chat, Trends, Rounds, and News surface as dashboard cards or locked previews until they are ready enough to deserve primary navigation.

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
