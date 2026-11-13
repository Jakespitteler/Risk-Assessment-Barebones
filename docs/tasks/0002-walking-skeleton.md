---
id: 0002
title: Walking skeleton with CI
status: review
owner: chatgpt
branch: chatgpt/0002-review-fixes
---

## Goal

Build the thinnest end-to-end version of the app on the chosen stack, with CI enforcing lint, typecheck and tests,
before any real features.

## Acceptance criteria

- [x] App runs locally with one command.
- [x] One real end-to-end path works (e.g. create and view a trivial assessment).
- [x] Risk scoring module exists with tests for spec worked example #1.
- [x] .github/workflows/ci.yml runs lint, typecheck and tests on every PR and push to main.
- [x] AGENTS.md Commands and Conventions sections filled in.
- [x] README explains how to run and test.

## Notes / assumptions

Depends on 0001. The stack chosen there has two halves, `backend/` and `frontend/` (see `docs/architecture.md`);
the skeleton, the one-command run and CI need to cover both.

What was built, and the assumptions made (each is in `docs/decisions.md`):

- The end-to-end path is "rate a risk": the screen gets the booklet's matrix from `GET /api/take5/template` and
  shows the score and band as soon as a likelihood and a consequence are picked. Nothing is saved yet; storage
  comes with the first saved Take 5 in task 0004.
- `GET /api/take5/template` only returns the matrix for now. Task 0004 adds the control kinds and task 0005 the questions.
- `domain/risk.py` has `RiskMatrix`, `RiskCell`, `RiskRating` and `rate()`. The booklet's matrix is
  `BOOKLET_MATRIX` in `domain/take5/template.py`. Each cell carries its band, so the front end only looks
  things up. Task 0003 adds worked examples 2 to 17, the 25-cell check and the made-up matrix test.
- httpx2 replaced httpx, TypeScript is 5.9, and markdownlint-cli2 checks every markdown file.
- Branch: cloud agents can only push to `claude/project-thread-k14nwr`, not the `<owner>/<task-id>-<name>`
  pattern in AGENTS.md.

Unrelated problems found:

- `npm audit` reports a moderate advisory in `minimatch`, used only by the ESLint tooling. It does not reach the
  app. The fix needs a newer typescript-eslint; revisit when one is released.

## Review corrections (ChatGPT)

Jake requested corrections on top of Claude's completed branch `claude/project-thread-k14nwr`.
This branch will target that branch, so Jake can merge the corrections into his existing review.

- Fix first-run dependency preparation and wait for the API before exposing the front end.
- Resolve Pylance imports when opening the repository root in VS Code.
- Add explicit Python variable annotations throughout the application, scripts and tests.
- Keep the existing product behaviour, dependencies and risk scoring rules.

Completed corrections:

- `scripts/dev.py` syncs the back end before launch, detects a missing Vite package or command shim even in
  an existing `node_modules`, and waits for the API before starting Vite. Startup failures clean up the back end.
- The root `pyproject.toml` supplies strict checking, the source path and the back-end environment to both
  Pylance and the command-line checks. VS Code defaults to `backend/.venv`.
- Python assignments in app code, scripts and tests have explicit annotations, except direct constructor
  calls whose class is already clear. `AGENTS.md` records Jake's clarified convention.
- `frontend/.npmrc` selects the HTTPS registry. README explains interpreter selection and the stale
  `VIRTUAL_ENV` warning that uv can emit before the launcher itself runs.

Validation: `uv run scripts/check.py` passed: markdown, Ruff, strict Pyright, 14 Python tests (nine launcher
regression cases), ESLint, Prettier, TypeScript, three front-end tests, unchanged generated API types and the
browser test. The real launcher served the API before starting Vite; the browser test used those servers.
Phone-width screenshots were inspected; no screen code changed. The initial AST audit found no unannotated
named assignments; the follow-up review allows direct constructors to use inference. Windows Vite shims are
covered by tests; native Windows execution still needs Jake's check.

Environment limitation: Playwright's browser download was denied by this cloud environment's network policy.
The browser test passed using installed system Chromium 156 through a temporary browser-cache link outside
the repo. The application's Playwright configuration was unchanged.

Follow-up review from Jake: cover test imports and VS Code tool discovery, replace JSON Pyright
configuration with TOML, associate ignore files correctly, and allow inferred types for constructor calls.
Fetching the review branch on 2026-11-13 found no commits beyond `88ba9e8`; any additional local edits
on Jake's computer were not visible on GitHub at that point.

Follow-up completed: root Pyright JSON replaced by `[tool.pyright]` in the root `pyproject.toml`.
`check.py` and the documented typecheck command explicitly select the repository as the project root,
avoiding ambiguity between `backend/scripts` and the root launch scripts. Direct constructor assignments
use inferred types; computed values and collections retain annotations. VS Code test discovery runs in
`backend/`, Ruff uses its bundled executable with the project's rules, and ignore files have the correct
language association. The README explains the HTTPS-only `.npmrc`, selecting the actual back-end interpreter,
reloading VS Code, and disabling the redundant isort extension for this workspace.

Follow-up validation: all checks passed again, including 14 Python tests, three front-end tests and the browser
test using system Chromium. A direct check of `backend/tests/domain/test_risk.py` reported zero type errors;
`pytest` and both domain imports also resolved at runtime in `backend/.venv`. Native Windows and VS Code
extension startup remain local verification steps; a remaining extension crash needs its Output log.
