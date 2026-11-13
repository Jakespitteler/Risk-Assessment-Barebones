---
id: 0003
title: Rate a risk (spec F1)
status: todo
owner:
branch:
---

## Goal
Build the risk scoring as one pure module: the 5x5 matrix, the bands, the JHA threshold, and the rating of a hazard and of a whole Take 5. This is the part of the app that most has to be right, so it comes first and has no API or database code.

## Acceptance criteria
- [ ] `backend/src/take5/domain/` has the scales (including `ControlKind`), the matrix, `rate()`, and the `Control`, `Hazard` and `Take5` models needed for spec rules R1 to R6.
- [ ] Spec worked examples 1 to 17 each have a test, named by example number.
- [ ] A test checks all 25 matrix cells against the table in `docs/spec.md`.
- [ ] The domain package imports only the standard library and pydantic.
- [ ] All checks pass.

## Out of scope
- The API, the front end and storage.
- Verdict, thinking and challenge rules (tasks 0004 to 0008).

## Notes / assumptions
Don't start until the spec is approved (task 0001 is `done`). Depends on 0002. Task 0002 already adds the matrix with worked example 1; extend it rather than starting again.
