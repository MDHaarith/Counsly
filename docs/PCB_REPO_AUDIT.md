# Counsly PCB Repo Audit

Checked against commit `9b60e7d` after the PCB dataflow/API manifest commit.

## Current Health Snapshot

| Area | Status | Evidence |
| --- | --- | --- |
| Frontend unit tests | Pass | `cd frontend && npm test` -> 31 passing tests. |
| Backend tests | Pass | `APP_ENV=test PYTHONPATH=. pytest -q backend/tests` -> 17 passing tests. |
| TypeScript | Pass | `cd frontend && npx tsc --noEmit` exits successfully. |
| Production build | Pass with warning | `cd frontend && npm run build` succeeds; Google Fonts optimization is skipped when the stylesheet cannot be downloaded. |
| Lint | Blocked | `cd frontend && npm run lint` opens the interactive Next.js ESLint setup prompt because ESLint is not configured. |

## High-Priority Problems

| Priority | Location | Problem | Impact | Fix Plan |
| --- | --- | --- | --- | --- |
| P0 | `backend/routes/choices.py` | Choice add/reorder validates college and branch existence independently, but not whether the selected branch is offered by that college. | Impossible choice rows can be saved. This is a data-integrity bug in the filing lane. | Batch-validate `(college_code, branch_code)` pairs against `CollegeBranch` in add, reorder, restore, and CSV paths; add backend tests for invalid pairs. |
| P0 | `backend/routes/choices.py`, `backend/models.py` | Duplicate college-branch choices are not blocked. The only unique preference constraint protects priority, not duplicate selections. | Users can add the same college/branch multiple times and corrupt their filing order. | Add an API duplicate check and a DB uniqueness constraint for `(workspace_id, preference_group, college_code, branch_code)`; surface a friendly duplicate message in the UI. |
| P0 | `backend/routes/compare.py` | Compare validates college existence and branch existence but does not validate college-branch mappings; it also loads `Branch` without using it. | Compare can show misleading results for branches a college does not offer. | Validate every selected pair against `CollegeBranch` before building columns; reject invalid pairs with HTTP 400. |
| P1 | `backend/routes/explore.py` | Explore applies DB `offset/limit` before computing and sorting fit score in Python. | Ranking is only correct within a limited page; better-fit colleges can be hidden on later pages. | Compute or preload ranking inputs for all candidates, sort by fit score, then paginate; batch-load cutoff/seat/branch data to avoid N+1 queries. |
| P1 | `frontend/lib/api.mjs`, `backend/routes/choices.py` | Choice note updates are sent as URL query parameters. | Long notes can exceed URL limits and may leak into logs/history. | Replace query-string metadata updates with a JSON request body and a typed Pydantic schema. |
| P1 | `frontend/lib/api-routes.mjs`, `frontend/lib/error-logging.mjs`, `frontend/tests/integration_flow.spec.mjs` | Endpoint centralization is incomplete: logging and integration tests still use raw API strings, and dynamic builders still embed path fragments. | The manifest is not yet a true single source of truth. | Add logging and dynamic route builders to the manifest, refactor integration tests to public helpers, and add a route-contract test. |
| P1 | `frontend/package.json` | `npm run lint` is interactive because ESLint is not configured. | CI/non-interactive QA cannot rely on lint. | Add a deterministic ESLint config and dependencies, then make `npm run lint` exit with a normal pass/fail result. |
| P2 | `frontend/app/maps/page.tsx`, `frontend/app/choices/page.tsx`, `frontend/app/explore/[code]/page.tsx`, `frontend/lib/api.mjs` | Large mixed-responsibility files remain. | Maintenance cost is high; future changes risk regressions. | Split pages into lane-specific hooks/components and split API transport, mappers, and public feature connectors. |
| P2 | `frontend/tsconfig.tsbuildinfo`, `.gitignore` | TypeScript build info is tracked. | Typecheck/build can create noisy diffs. | Ignore `*.tsbuildinfo` and remove the tracked file from the index. |

## Implementation Sequence

1. **Filing integrity first:** validate college-branch pairs and block duplicate choices.
2. **Compare integrity next:** validate branch availability per selected college and reject invalid compare pairs.
3. **Contract cleanup:** finish endpoint manifest centralization and add backend/frontend route-contract tests.
4. **Explore correctness:** fix global fit-score sorting and remove N+1 query loops.
5. **Safety/UX cleanup:** move choice notes to JSON bodies, make error logging non-blocking, and sync verified roll-number community/rank into canonical student context.
6. **PCB refactor:** split the largest frontend files into feature hooks/components and split API transport/mappers/connectors.
7. **Tooling hygiene:** configure lint and stop tracking `tsconfig.tsbuildinfo`.

## Files To Start With

- `backend/routes/choices.py`
- `backend/routes/compare.py`
- `backend/routes/explore.py`
- `backend/schemas.py`
- `backend/models.py`
- `supabase_db/schema.sql`
- `frontend/lib/api-routes.mjs`
- `frontend/lib/api.mjs`
- `frontend/tests/api.test.mjs`
- `frontend/tests/integration_flow.spec.mjs`
- `frontend/package.json`
