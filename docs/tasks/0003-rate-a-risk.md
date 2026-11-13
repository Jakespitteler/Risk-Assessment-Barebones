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

Implementation plan: extend the existing matrix scoring, add the six control kinds and frozen scoring models,
and test worked examples 1 to 17, all booklet cells and a second matrix. Only the template name/matrix and the
hazards/template fields needed for R1 to R6 are added now; later tasks add questions, worker/job details,
storage and verdicts. No new dependencies or changes to the existing API are needed.

Implementation notes for the next task:

- `ControlKind` uses the card's exact labels; remove, isolate and barricade report `is_strong` as true.
- `Take5Template` currently has `name` and `matrix`. The booklet template wraps the existing `BOOKLET_MATRIX`.
- `Hazard` has `description`, `before`, `controls` and `after`. Obtain ratings from `rate()`; if there are no
  controls, pass the before rating as after without asking the worker to rate it again. Validation refuses
  any changed rating without controls, or an increased score with controls.
- `Take5` has the scoring fields `template` and non-empty `hazards`. Its validator checks every before and
  after score/band against its template. `rating` is the highest after rating and `needs_jha` uses that
  template's threshold. Later tasks extend these models with their own fields.
- Tests name examples 1 to 17, independently check all 25 booklet cells, and rate a hazard on a second
  two-by-two matrix with different scales, bands and JHA threshold. Import tests enforce the domain boundary.

Validation: `uv run scripts/check.py` passed (53 Python tests, Ruff lint/format, strict Pyright, markdown,
ESLint, Prettier, TypeScript, three front-end tests, unchanged generated API types and one browser test).
The browser test used installed system Chromium 156 via the existing temporary cache link outside the repo,
because the environment blocks the Playwright download. No UI, API, dependency or storage files changed.

Unrelated documentation issue: task 0002 is already merged into main, but its task file still says review.
This task leaves that file unchanged.

Review follow-up: Jake's VS Code Python 2026.10 log shows the Python Environments discovery launcher
exiting immediately with null code/signal and no pytest traceback. Direct discovery and all 53 tests pass
here. Apply the supported workspace opt-out from that launcher, preserve the backend interpreter/settings,
and document the required reload and local verification.

Workaround added: `.vscode/settings.json` explicitly sets `python.useEnvironmentsExtension` to false.
The published Python extension setting and its pytest discovery source confirm that this selects the
execution-factory path using the selected interpreter instead of the Environments launcher. README explains
reloading and refreshing tests. All checks still pass here; Windows editor discovery needs Jake's confirmation.

Root-cause investigation requested by Jake: the Windows Environments log now shows an attempted spawn of
`backend/.venv` itself followed by ENOENT, although the locator also resolves `Scripts/python.exe`.
The extension's interpreter-selection source wraps a configured directory using that original directory
as its run executable. Correct the launch target without disabling Environments or introducing a shared
Windows-only default; preserve the user's selection of the actual project interpreter. Record evidence,
the reversible correction and Windows verification still required.
