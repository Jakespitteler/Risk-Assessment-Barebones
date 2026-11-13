# Risk Assessment App

Shared instructions for every AI agent working in this repo (Claude Code, ChatGPT/Codex, others).
This file is the single source of truth for how to work here. Keep it under ~150 lines.

## What this is
A risk assessment app. Full product definition lives in `docs/spec.md`.
Stack: **Python 3.13+, FastAPI, server-rendered Jinja2 pages, SQLite** (proposed in task 0001 and waiting for
the human's approval; details in `docs/architecture.md`).

## Commands
Fill these in once the stack is chosen (task 0002). Every agent must use exactly these.
- Install: `TBD`
- Run: `TBD`
- Test: `TBD`
- Lint/format: `TBD`
- Typecheck: `TBD`
- All checks (what CI runs): `TBD`

## Source of truth
- `docs/spec.md` — what the app does, scoring rules, acceptance criteria.
- `docs/architecture.md` — structure, data model, module boundaries.
- `docs/decisions.md` — dated log of non-obvious choices and why.
- `docs/tasks/` — one file per unit of work, with status and owner.
- Read `docs/spec.md` and `docs/architecture.md` before any change.
- If the code and the spec disagree, stop and ask the human. Don't silently pick one.

## How work happens
1. Pick a task in `docs/tasks/` with `status: todo`, or ask the human to create one.
2. Claim it: set `status: in-progress` and `owner: <claude|chatgpt|human>` and commit that first.
3. Work on a branch named `<owner>/<task-id>-<short-name>`. Never commit directly to `main`.
4. Keep the change to the task's scope. Note unrelated problems in the task file instead of fixing them.
5. Done means: acceptance criteria met, tests added, all checks pass.
6. Set `status: review`, open a PR using the template, and summarise what changed and how it was tested.
7. The PR is reviewed by the *other* agent (or the human) before merge.

## Rules
- Every behaviour change ships with tests. Risk scoring logic needs tests built from the worked examples in `docs/spec.md`.
- Don't add dependencies, change the data model, or change public interfaces without the human's approval. Record approved changes in `docs/decisions.md`.
- If you change behaviour described in the spec, update `docs/spec.md` in the same PR.
- Ask the human about product decisions rather than guessing. Write down any assumption you had to make in the task file.
- Don't edit another agent's in-progress task or branch.
- No secrets, credentials, or real personal data in the repo. Use obviously fake sample data.
- Prefer small PRs (one task, ideally under ~400 changed lines).

## Conventions
Fill in once the stack is chosen. Cover: naming, file layout, error handling, logging, test style.

## Notes for agents
- Neither agent can see the other's chat history or memory. Anything the other agent needs must be in this repo.
- Keep this file short. Put long reference material in `docs/` and link to it.
