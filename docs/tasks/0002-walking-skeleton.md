---
id: 0002
title: Walking skeleton with CI
status: done
owner: claude
branch: claude/project-thread-k14nwr
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

## Review corrections (ChatGPT, PR #5)

Jake asked ChatGPT for corrections after PR #4. They are on `main`:

- `scripts/dev.py` syncs the back end, reinstalls the front end if Vite is missing, and waits for the API before
  it starts Vite.
- One strict Pyright configuration, in the root `pyproject.toml`, serves both VS Code and the checks.
- Python assignments carry explicit type annotations (Jake's convention, now in `AGENTS.md`).
- `frontend/.npmrc` pins the HTTPS npm registry.
- VS Code set-up help is in `docs/dev-setup.md`.
