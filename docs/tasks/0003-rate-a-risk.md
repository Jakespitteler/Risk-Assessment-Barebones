---
id: 0003
title: Rate a risk (spec F1)
status: done
owner: chatgpt
branch: chatgpt/0003-rate-a-risk
---

## Goal

Build the risk scoring as one pure module: the 5x5 matrix, the bands, the JHA threshold, and the rating of a hazard
and of a whole Take 5. This is the part of the app that most has to be right, so it comes first and has no API or
database code.

## Acceptance criteria

- [x] `backend/src/risk_assessment/domain/` has `risk.py` (`RiskMatrix` as data, `RiskRating`, `rate()`),
  `controls.py` (`ControlKind`, `Control`), and in `take5/` the booklet's template with its matrix and the `Hazard`
  and `Take5` models needed for spec rules R1 to R6.
- [x] Spec worked examples 1 to 17 each have a test, named by example number.
- [x] A test checks all 25 matrix cells against the table in `docs/spec.md`.
- [x] A test rates a hazard on a second, made-up matrix, to prove nothing about the booklet's matrix is built into
  the code.
- [x] `risk.py` and `controls.py` import nothing from `domain/take5/`.
- [x] The domain package imports only the standard library and pydantic.
- [x] All checks pass.

## Out of scope

- The API, the front end and storage.
- Verdict, thinking and challenge rules (tasks 0004 to 0008).

## Notes / assumptions

Don't start until the spec is approved (task 0001 is `done`). Depends on 0002. Task 0002 already adds the matrix
with worked example 1; extend it rather than starting again.

Notes for the next task:

- `ControlKind` uses the card's exact labels; remove, isolate and barricade report `is_strong` as true.
- `Take5Template` has `name` and `matrix`. `BOOKLET_TEMPLATE` wraps `BOOKLET_MATRIX`.
- `Hazard` has `description`, `before`, `controls` and `after`. Ratings come from `rate()`. With no controls, pass
  the before rating as the after rating; validation refuses a changed rating without controls, and a higher score
  with them.
- `Take5` has `template` and at least one hazard. It checks every rating against its template's matrix. `rating`
  is the highest after rating, and `needs_jha` uses the template's threshold.
- A test enforces the domain's import rules.

VS Code test discovery problems met during review are covered in `docs/dev-setup.md`.
