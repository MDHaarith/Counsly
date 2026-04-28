# Task: Remove News/Broadcast/Telegram + Migrate app_config to Env Vars

## Context

The app has unused features designed around a Telegram bot admin system: `news_items` table, `admin_audit_log` table, broadcast config, and associated UI. The Telegram bot was never built. These add complexity with zero value. Migrate the remaining `app_config` keys to environment variables (set via Vercel/Railway env dashboard) so there's no need for a Telegram bot at all.

---

## Step 1: Backend Config — Add env vars to Settings class

**File:** `backend/app/config.py`

Add these fields to the `Settings` class (after `season_year: int = 2026` on line 18):

```python
# TNEA runtime config (replaces app_config table reads)
tnea_phase: int = 0
total_rounds: int = 0
rank_released: bool = False
free_chat_limit: int = 3
season_end_date: str | None = None
```

---

## Step 2: Backend Router — Rewrite config endpoint to use env vars

**File:** `backend/app/routers/config.py`

Rewrite `GET /api/config/status` to read admin-controlled values from `settings` (env vars) instead of `fetch_config()` from the `app_config` DB table. Keep reading `ROLL_DATA_READY`, `RANK_LOOKUP_READY` from DB (those are written by seed scripts).

The endpoint should:
1. Import `from app.config import settings`
2. Remove the `broadcast_active` and `broadcast_message` fields
3. Read `tnea_phase`, `total_rounds`, `rank_released`, `free_chat_limit`, `season_end_date` from `settings`
4. Read `roll_data_ready`, `rank_lookup_ready` from `fetch_config()` (DB, written by seed scripts)
5. Read `data_freshness` from `fetch_data_freshness()` (DB)
6. Keep the `_int()` and `_bool()` helper functions if still useful, or remove if no longer needed

---

## Step 3: Backend Models — Remove broadcast fields

**File:** `backend/app/models/__init__.py`

Remove these two lines from `AppConfigResponse` (lines 29-30):
```python
    broadcast_active: bool
    broadcast_message: str | None
```

---

## Step 4: Backend Seed Script — Remove broadcast entries

**File:** `backend/scripts/seed_app_config.py`

Remove these two entries from the `DEFAULTS` list (lines 12-13):
```python
    {"config_key": "BROADCAST_ACTIVE", "value_json": "false", "updated_by": "seed"},
    {"config_key": "BROADCAST_MESSAGE", "value_json": None, "updated_by": "seed"},
```

---

## Step 5: Migration 001 — Remove news_items and admin_audit_log tables

**File:** `backend/migrations/001_initial_schema.sql`

1. **Remove** the `news_items` table entirely (lines 376-390):
```sql
CREATE TABLE news_items (
    ...
);
ALTER TABLE news_items ENABLE ROW LEVEL SECURITY;
CREATE INDEX idx_news_items_status_published ON news_items (status, published_at DESC);
```

2. **Remove** the `admin_audit_log` table entirely (lines 420-431):
```sql
CREATE TABLE admin_audit_log (
    ...
);
ALTER TABLE admin_audit_log ENABLE ROW LEVEL SECURITY;
```

3. **Remove** `BROADCAST_ACTIVE` and `BROADCAST_MESSAGE` from the `app_config` seed INSERT (lines 441-442):
```sql
    ($$BROADCAST_ACTIVE$$, $$boolean$$, $$false$$),
    ($$BROADCAST_MESSAGE$$, $$string$$, $$null$$)
```

---

## Step 6: Migration 002 — Remove news_items from data_freshness

**File:** `backend/migrations/002_launch_schema_gaps.sql`

Remove this line from the `data_freshness` INSERT (line 171):
```sql
    ($$news_items$$, $$missing$$, $$Set from runtime admin or scraping pipeline$$)
```

---

## Step 7: Frontend Dashboard — Remove broadcast banner

**File:** `frontend/src/app/(auth)/dashboard/page.tsx`

1. Remove `broadcast_active: boolean;` and `broadcast_message: string | null;` from the `StatusPayload` interface (lines 14-15)
2. Remove the broadcast banner JSX block (lines 52-54):
```tsx
      {status?.broadcast_active && status.broadcast_message && (
        <Card variant="featured"><p className="text-sm leading-relaxed text-anthracite">{status.broadcast_message}</p></Card>
      )}
```

---

## Step 8: Frontend Types — Remove broadcast from AppConfig

**File:** `frontend/src/types/index.ts`

Remove these two lines from the `AppConfig` interface (lines 140-141):
```typescript
  broadcastActive: boolean;
  broadcastMessage: string | null;
```

---

## Step 9: Root .env.example — Add new env vars

**File:** `.env.example` (or `backend/.env.example`)

Add these entries with defaults:
```
TNEA_PHASE=0
TOTAL_ROUNDS=0
RANK_RELEASED=false
FREE_CHAT_LIMIT=3
SEASON_END_DATE=
```

---

## Files NOT Changed (do not modify these)
- `backend/app/db/queries.py` — `fetch_config()` stays (still used by data readiness)
- `backend/scripts/load_rank_lookup.py` — keeps writing `RANK_LOOKUP_READY` to DB
- Any files in `docs/` — documentation is not in scope
- `PRD-v2_1.md` — not in scope

---

## Verification

After all changes:
1. `cd backend && python -c "from app.config import settings; print(settings.tnea_phase, settings.rank_released)"`
2. `cd frontend && npx tsc --noEmit` — confirm no type errors
3. Check dashboard renders without broadcast banner
4. Confirm `GET /api/config/status` returns all fields except broadcast
