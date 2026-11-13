---
id: 0003
title: Rate a risk (spec F1)
status: in-progress
owner: chatgpt
branch: chatgpt/0003-rate-a-risk
---

## Goal

Build the risk scoring as one pure module: the 5x5 matrix, the bands, the JHA threshold, and the rating of a hazard
and of a whole Take 5. This is the part of the app that most has to be right, so it comes first and has no API or
database code.

## Acceptance criteria

- [ ] `backend/src/risk_assessment/domain/` has `risk.py` (`RiskMatrix` as data, `RiskRating`, `rate()`),
  `controls.py` (`ControlKind`, `Control`), and in `take5/` the booklet's template with its matrix and the `Hazard`
  and `Take5` models needed for spec rules R1 to R6.
- [ ] Spec worked examples 1 to 17 each have a test, named by example number.
- [ ] A test checks all 25 matrix cells against the table in `docs/spec.md`.
- [ ] A test rates a hazard on a second, made-up matrix, to prove nothing about the booklet's matrix is built into
  the code.
- [ ] `risk.py` and `controls.py` import nothing from `domain/take5/`.
- [ ] The domain package imports only the standard library and pydantic.
- [ ] All checks pass.

## Out of scope

- The API, the front end and storage.
- Verdict, thinking and challenge rules (tasks 0004 to 0008).

## Notes / assumptions

Don't start until the spec is approved (task 0001 is `done`). Depends on 0002. Task 0002 already adds the matrix
with worked example 1; extend it rather than starting again.

Implementation plan: extend the existing matrix scoring, add the six control kinds and frozen scoring models,
and test worked examples 1 to 17, all booklet cells and a second matrix. Only the template name/matrix and the
hazards/template fields needed for R1 to R6 are added now; later tasks add questions, worker/job details,
storage and verdicts. No new dependencies or changes to the existing API are needed.

Unrelated documentation issue: task 0002 is already merged into main, but its task file still says review.
This task leaves that file unchanged.
