# Architecture Refactoring Plan

## Background & Motivation
During the codebase review, two major architectural areas for improvement were identified:
1. **Frontend:** The pervasive use of `"use client"` in Next.js App Router pages and UI components nullifies the benefits of Server Components, bloating the client-side JavaScript bundle and degrading performance.
2. **Backend:** The `backend/app/services/` directory is empty. All business logic (e.g., eligibility gates, safety computations, and recommendation rules) is tightly coupled with database operations inside `backend/app/db/queries.py`.

## Scope & Impact
- **Frontend:** `frontend/src/app/**/*.tsx` and `frontend/src/components/**/*.tsx`
- **Backend:** `backend/app/db/queries.py`, `backend/app/services/**/*.py`, and `backend/app/routers/**/*.py`

## Proposed Solution

### Phase 1: Frontend Server Components Refactor
1. **Audit Components & Pages:** Identify which pages and components strictly require client-side interactivity (hooks like `useState`, `useEffect`, or event listeners).
2. **Push `"use client"` Down the Tree:** 
   - Remove `"use client"` from layout and page files where data fetching or static rendering can be done server-side.
   - Restrict `"use client"` to strictly interactive UI components (e.g., `Button`, `Input`, `Toast`, interactive forms).
3. **Data Fetching:** Transition data fetching currently happening in client components (via `useEffect` or React Query/SWR) to Server Components where applicable.

### Phase 2: Backend Services Extraction
1. **Create Service Modules:** Scaffold service files in `backend/app/services/` (e.g., `recommendation_service.py`, `onboarding_service.py`, `explore_service.py`).
2. **Decouple Business Logic:**
   - Move purely logical functions (like `compute_safety`, mark aggregation, eligibility rules) out of `queries.py`.
   - Update `queries.py` to only contain thin, parameterized data access functions.
3. **Update Routers:** Refactor endpoints in `backend/app/routers/` to call the new service modules, delegating the orchestration of database calls and business logic to the services layer.

## Verification & Testing
- **Frontend:** Verify the production build (`npm run build`) passes and inspect the build output to ensure pages are correctly classified as Server/Static where appropriate. Ensure no client-side runtime errors occur.
- **Backend:** Run backend compile checks, static typing (if configured), and `pytest` (e.g., `test_launch_readiness.py`) to confirm that extracting logic to services did not break existing functionality.
- **End-to-End:** Perform a manual smoke test of the core flows (Login, Onboarding, Recommendations, Choices) to verify end-to-end integration.

## Migration & Rollback
Since these are structural refactoring changes, they will be developed on a dedicated branch (`refactor-architecture`). If regressions are found during verification, the branch can simply be discarded or specific commits reverted. No database migrations are required for this track.