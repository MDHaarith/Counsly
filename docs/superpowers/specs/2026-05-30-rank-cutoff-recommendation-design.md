# Rank And Cutoff Recommendation Design

## Objective

Build an advanced deterministic recommendation algorithm for TNEA college suggestions that ranks `college + branch` pairs using actual historical evidence. The system must not expose a fake fit score, must not depend on seat matrix data, and must explain recommendations with structured facts rather than narrative confidence.

## Current Context

The current recommendation flow calls `searchColleges()` and receives college cards sorted by a simple `fit_score`. That score is based on broad college properties such as district, autonomous status, NBA, placement rate, and average package. It does not sufficiently use the strongest evidence already in the project: community-wise historical `CutoffData` with both `cutoff_rank` and `cutoff_mark` for 2020-2025.

The profile and onboarding flows store useful student inputs in browser storage:

- aggregate from maths, physics, and chemistry
- community category
- general rank, if available
- community rank, if available
- preferred branches
- default district

The backend has:

- colleges
- college branches
- branches
- cutoff history with rank and mark evidence
- college quality and practicality metadata

## Non-Goals

- Do not use seat matrix data in the recommendation algorithm.
- Do not show a numerical `fitScore` or any synthetic AI-style score in the UI.
- Do not invent admission certainty when rank or cutoff history is missing.
- Do not train a machine learning model unless future labelled admission outcomes are available.
- Do not replace official counselling rules or present recommendations as guaranteed allotments.

## Inputs

The recommendation request should support:

- `community`: required or resolved from verified roll number; fallback `OC` only when no student context is present.
- `aggregate`: optional student aggregate out of 200; required only for mark evidence and the eligibility gate.
- `general_rank`: optional.
- `community_rank`: optional.
- `preferred_branches`: ordered branch codes.
- `district`: optional hard filter.
- `branch_code`: optional hard filter.
- `search`: optional text filter.
- `limit` and `offset`.
- `include_unlikely`: optional boolean, default false.

Rank selection rule:

- If `community_rank` exists, use it for community-specific cutoff rank comparisons.
- Else if `general_rank` exists, use it as a weaker rank signal.
- Else rank evidence is unavailable and mark evidence becomes primary.

## Candidate Generation

Generate candidates from `CollegeBranch` joined to `College` and `Branch`. Load community-specific `CutoffData` separately for each candidate so candidates with missing history can still appear as `Insufficient Data`.

Each candidate is one `college_code + branch_code` pair. This matters because the same college can be likely for one branch and aspirational for another.

Hard filters run before ranking:

- district filter
- branch filter
- search text over college code, college name, district, and branch name
- community-specific cutoff lookup after candidate generation

No seat matrix join is required.

## Historical Evidence Model

For each candidate, load cutoff rows for the selected community and branch, ordered by year descending. Use 2020-2025 data where available.

Use recent years more strongly:

- latest year: weight `1.00`
- previous year: weight `0.85`
- third year: weight `0.70`
- older rows: weight `0.55`

For every candidate compute:

- `latest_cutoff_rank`
- `latest_cutoff_mark`
- `rank_margin`: `latest_cutoff_rank - student_rank`, where positive means the student rank clears the historical closing rank
- `mark_margin`: `student_aggregate - latest_cutoff_mark`, where positive means the student aggregate clears the historical cutoff mark
- `rank_cleared_years`
- `mark_cleared_years`
- `weighted_rank_margin`
- `weighted_mark_margin`
- `rank_trend`
- `mark_trend`
- `data_years`
- `data_confidence`

Trend labels:

- `Loosening`: historical cutoff is becoming easier.
- `Stable`: movement is small.
- `Tightening`: historical cutoff is becoming harder.
- `Insufficient`: too little history.

## Decision Bands

The algorithm returns bands instead of a visible score:

- `Likely`: rank clears recent history and marks also clear or are close.
- `Competitive`: one of rank or marks clearly clears, or both are close.
- `Aspirational`: evidence is historically tight but not impossible.
- `Unlikely`: rank and marks are clearly outside history.
- `Insufficient Data`: fewer than two useful cutoff rows, or neither rank nor mark evidence can be compared.

Default results exclude `Unlikely`; users can enable broader search to include it.

Banding must be deterministic. It should use thresholds such as:

- rank margin greater than or equal to `0`: clears rank evidence.
- mark margin greater than or equal to `0`: clears mark evidence.
- mark margin between `-5` and `0`: close mark evidence.
- rank miss within `10%` of latest cutoff rank: close rank evidence.
- rank miss beyond `25%` of latest cutoff rank and mark miss below `-10`: unlikely.

## Conflict Resolution

When rank and mark evidence disagree, rank wins because allocation behavior is rank-driven.

Examples:

- Rank clears but marks are close: `Competitive`, with evidence showing rank as the stronger signal.
- Marks clear but rank misses badly: `Aspirational` or `Unlikely`, depending on rank miss size.
- No rank but marks clear: `Competitive`, not `Likely`, because rank evidence is absent.

## Ordering Without Fit Score

The backend may use internal sortable tuples, but the UI must not show a synthetic number.

Sort order:

1. Band priority: `Likely`, `Competitive`, `Aspirational`, `Insufficient Data`, then `Unlikely` only if enabled.
2. Preferred branch priority.
3. Rank margin strength, if rank exists.
4. Mark margin strength.
5. Trend stability, preferring stable or loosening trends over tightening trends.
6. College quality tie-breakers: autonomous, NBA, placement rate, average package.
7. Practical tie-breakers: district match, lower travel distance, hostel/transport availability, annual fee.

The internal tuple is acceptable because it is only an ordering mechanism. It must not be returned as `fit_score`.

## Recommendation Evidence Output

Each result should expose structured fields:

- `college_code`
- `college_name`
- `branch_code`
- `branch_name`
- `district`
- `community`
- `band`
- `data_confidence`
- `latest_cutoff_rank`
- `latest_cutoff_mark`
- `student_rank_used`
- `student_aggregate`
- `rank_margin`
- `mark_margin`
- `rank_cleared_years`
- `mark_cleared_years`
- `rank_trend`
- `mark_trend`
- `evidence_points`
- quality/practicality fields already used by cards

`evidence_points` should be short factual strings:

- `Rank clears 4 of 6 historical years`
- `Latest BC closing rank: 18520`
- `Your community rank: 16200`
- `Mark margin: +7.50`
- `Trend: tightening`

No AI-style prose and no fake counselling certainty.

## API Design

Add a backend recommendation endpoint:

`POST /recommendations/`

Request schema:

```json
{
  "aggregate": 184.5,
  "community": "BC",
  "general_rank": 18500,
  "community_rank": 6200,
  "preferred_branches": ["CS", "IT", "EC"],
  "district": "Chennai",
  "branch_code": "CS",
  "search": "Anna",
  "include_unlikely": false,
  "limit": 50,
  "offset": 0
}
```

Response schema:

```json
[
  {
    "college_code": "1",
    "college_name": "University Departments of Anna University, Chennai - CEG Campus",
    "branch_code": "CS",
    "branch_name": "Computer Science and Engineering",
    "district": "Chennai",
    "community": "BC",
    "band": "Competitive",
    "data_confidence": "High",
    "latest_cutoff_rank": 18520,
    "latest_cutoff_mark": 178.5,
    "student_rank_used": 16200,
    "student_aggregate": 184.5,
    "rank_margin": 2320,
    "mark_margin": 6.0,
    "rank_cleared_years": 4,
    "mark_cleared_years": 5,
    "rank_trend": "Stable",
    "mark_trend": "Tightening",
    "evidence_points": [
      "Rank clears 4 of 6 historical years",
      "Latest BC closing rank: 18520",
      "Your community rank: 16200",
      "Mark margin: +6.00",
      "Trend: stable rank, tightening marks"
    ]
  }
]
```

## Frontend Design

The recommendations page should call the new endpoint instead of the generic explore search for primary results.

Cards should show:

- band badge
- branch and college
- latest closing rank and cutoff mark
- student rank used
- rank margin
- mark margin
- data confidence
- evidence bullet list

Remove visible `Fit N` from recommendation cards. Keep add-to-choice and compare actions.

Explore search may keep a lightweight ordering for browsing, but the dedicated recommendations page should use the recommendation endpoint.

## Missing Data Handling

If rank is missing:

- use aggregate and cutoff marks as primary evidence.
- never label as `Likely`; cap at `Competitive`.

If mark is missing:

- use rank evidence if available.
- show `student_aggregate` as null.

If cutoff rank is missing but cutoff mark exists:

- mark evidence drives the band.
- data confidence becomes `Medium`.

If fewer than two historical rows are available:

- band becomes `Insufficient Data` unless both the latest rank and mark clearly clear the cutoff.
- data confidence is `Limited`.

If there is no cutoff history for the community and branch:

- show `Insufficient Data`.
- sort below evidence-backed recommendations.

## Testing Requirements

Backend unit tests must cover:

- rank-first behavior when rank and mark disagree.
- mark fallback when rank is absent.
- no seat matrix dependency.
- preferred branch ordering inside the same band.
- missing-data banding.
- `Unlikely` hidden by default.

Frontend tests must cover:

- recommendation API request includes aggregate, ranks, community, and preferred branches.
- recommendation card does not show `Fit`.
- recommendation card renders evidence points and band.

Integration test should confirm:

- student lifecycle can request recommendations after onboarding.
- response returns `college + branch` rows with no `fit_score`.

## Risks And Constraints

Historical cutoffs are not guarantees. The UI must keep the language factual.

Ranks and marks can conflict if student input is stale or unofficial. Rank wins, but the evidence should show both values.

Community rank may not be available for every student. The algorithm must still work with general rank or aggregate only.

The first implementation should be deterministic and testable. More advanced calibration can come later only if validated outcome labels are available.
