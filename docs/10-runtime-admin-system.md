# Counsly — Runtime Admin System

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
