# Counsly — Auth & Identity

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
