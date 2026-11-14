# Risk Assessment App

Shared instructions for every AI agent working in this repo (Claude Code, ChatGPT/Codex, others).
This file is the single source of truth for how to work here. Keep it under ~150 lines.

## What this is

A risk assessment app. Full product definition lives in `docs/spec.md`.
Stack: **a Python 3.13+ FastAPI back end (`backend/`) and a React + TypeScript front end (`frontend/`), with
SQLite**. The full library list and the reasons are in `docs/architecture.md`.

## Commands

Every agent must use exactly these. You need git, [uv](https://docs.astral.sh/uv/) and Node.js 22 or newer.
Run each from the folder shown.

- Install: in `backend/`, `uv sync`. In `frontend/`, `npm ci` then `npx playwright install chromium`.
- Run: in the repo root, `uv run scripts/dev.py`, then open <http://localhost:5173>. Ctrl+C stops it.
- Test: in `backend/`, `uv run pytest`. In `frontend/`, `npm test` and `npm run test:e2e`.
- Lint/format: in `backend/`, `uv run ruff check .` and `uv run ruff format .`. In `frontend/`, `npm run lint`
  and `npm run format`. Markdown, in the repo root: `npx markdownlint-cli2@0.24.0 "**/*.md"`.
  `check.py` also lints `scripts/` with the back end's settings and type checks it with the root `pyproject.toml`.
- Spelling (Australian English), in the repo root: `npx -y -p cspell@10.5.0 -p @cspell/dict-en-au@1.1.31 cspell
  -c .cspell/cli.json "**"`.
- Typecheck: in `backend/`, `uv run pyright --project ..`. In `frontend/`, `npm run typecheck`.
- API types: in `frontend/`, `npm run generate:api` after any change to the API. Commit both files it writes.
- All checks (what CI runs): in the repo root, `uv run scripts/check.py`.

## Source of truth

- `docs/spec.md` — what the app does, scoring rules, acceptance criteria.
- `docs/architecture.md` — structure, data model, module boundaries.
- `docs/decisions.md` — dated log of non-obvious choices and why.
- `docs/tasks/` — one file per unit of work, with status and owner.
- Read `docs/spec.md` and `docs/architecture.md` before any change.
- If the code and the spec disagree, stop and ask the human. Don't silently pick one.

## How work happens

1. Pick the next `todo` task in the order in `docs/tasks/README.md`, or ask the human to create one.
2. Claim it: set `status: in-progress` and `owner: <claude|chatgpt|human>` and commit that first.
3. Work on a branch named `<owner>/<task-id>-<short-name>`. Never commit directly to `main`.
4. Keep the change to the task's scope. Note unrelated problems in the task file instead of fixing them.
5. Done means: acceptance criteria met, tests added, all checks pass.
6. Set `status: review`, open a PR using the template, and summarise what changed and how it was tested.
   When the work is ready to merge, the PR's last commit sets `status: done` and ticks any box that waits on the
   human's approval. The task file only reaches `main` when the human merges, and the merge is the approval, so
   no follow-up PR is needed to mark a task done.
7. An agent that did not write the change reviews the PR before the human does. That is the review agent in CI
   configured by task 0012. The human always does the final review and merges.

## Rules

- Every behaviour change ships with tests. Risk scoring logic needs tests built from the worked examples in
  `docs/spec.md`.
- Don't add dependencies, change the data model, or change public interfaces without the human's approval. Record
  approved changes in `docs/decisions.md`.
- If you change behaviour described in the spec, update `docs/spec.md` in the same PR.
- Ask the human about product decisions rather than guessing. Write down any assumption you had to make in the task
  file.
- Explain consequential choices before implementing them: evidence, intended effect, relevant alternatives,
  tradeoffs and how they will be verified. Diagnose the cause before adding bypass settings or workarounds.
- Don't edit another agent's in-progress task or branch.
- No secrets, credentials, or real personal data in the repo. Use obviously fake sample data.
- Never read or change `.env` files, keys, `secrets/` or `backend/.data/` (saved Take 5s). Never skip checks
  (`--no-verify`), force push, push to `main`, or merge a PR. On a computer, Claude Code's settings and hooks
  (`.claude/settings.json`) back this up, but they only match words, so the rule stands without them.
- Prefer small PRs (one task, ideally under ~400 changed lines).

## Conventions

- **Layout.** Follow the Structure in `docs/architecture.md`. Back-end tests mirror `src/risk_assessment/`.
  A front-end test sits beside its component as `Name.test.tsx`; whole-app tests are in `frontend/e2e/`.
- **Names.** A name says what the thing is, so it needs no comment: `jha_threshold`, not `t`. Python uses
  `snake_case` and `PascalCase` classes; TypeScript uses `camelCase`, and each file exports one `PascalCase` component.
- **Python.** Type hints everywhere (pyright strict). A Google-style docstring on every module, class and
  function, in plain words. Small single-purpose functions; plain data and pure functions in `domain/`.
  Values are frozen pydantic models. Explicitly annotate assigned variables and module constants, except
  direct constructor calls where the class already makes the type clear (for example, `app = FastAPI(...)`).
  Keep annotations for collections and computed results. A `def` that doesn't fit on one line puts each
  parameter on its own line, with a trailing comma (task 0017 makes Ruff enforce it). Pyright and Pylance
  share `[tool.pyright]` in the root `pyproject.toml`; the back end's package and Ruff settings stay in
  `backend/pyproject.toml`.
- **TypeScript.** Strict mode. API types only come from the generated `src/api/schema.d.ts`; never write them
  by hand. The front end holds no rules: it draws what the back end sends.
- **Errors.** `domain/` raises `ValueError` with a message a person can read. Routes turn errors into HTTP
  responses; the worker never sees a stack trace or an AI error.
- **Logging.** Use `logging.getLogger(__name__)`, never `print`, in the back end. Never log the worker's name.
- **Tests.** pytest for the back end; a test's name says what it proves, and a test of a spec worked example is
  named `test_example_<number>_...`. Vitest and React Testing Library find things by role or label, as a
  person would. Playwright runs at 360 px wide and saves screenshots to `frontend/test-results/screenshots/`.
- **Spelling.** Australian English (`colour`, `organise`), the same as Jake's VS Code spell checker. The spell
  check must find nothing. Add a real project or technical word to `.cspell/project-words.txt`, in sorted order;
  for a deliberate non-word in one file, write `cspell:ignore <word>` in a comment there.
- **Markdown.** No markdownlint warnings (settings in `.markdownlint-cli2.jsonc`). Wrap prose at about 115
  characters.

## Notes for agents

- Neither agent can see the other's chat history or memory. Anything the other agent needs must be in this repo.
- Keep this file short. Put long reference material in `docs/` and link to it.
