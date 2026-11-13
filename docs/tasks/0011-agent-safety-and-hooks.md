---
id: 0011
title: Agent safety settings and hooks for Claude Code
status: in-progress
owner: claude
branch: claude/project-thread-7tuvvd
---

## Goal

Jake asked (2026-11-13) for current Claude Code safety and verification practice: keep agents away from secrets
such as `.env`, stop them committing to `main`, and check their work automatically. This task covers what runs on
a computer where Claude Code is used. The review agent in CI and the glossary are follow-up tasks (below), so each
pull request stays small.

## Acceptance criteria

- [ ] `.claude/settings.json` denies Claude's file tools reading or editing secrets and worker data: `.env` and
  `.env.*` files, private keys (`*.pem`, `*.key`), any `secrets/` folder, `backend/.data/` (saved Take 5s), and
  `~/.ssh`. It denies force pushes and `--no-verify`. It pre-approves the commands in AGENTS.md, so agents ask
  less often for safe things.
- [ ] A `PreToolUse` hook blocks, with a reason the agent can read, a shell command that names a secret file or
  `backend/.data/`, a commit or push while on `main`, a push to `main`, a force push and `--no-verify`. Deny rules
  only see the file tools and simple commands such as `cat .env`; the hook also catches `python -c` and pipes.
- [ ] A `PostToolUse` hook formats each file an agent edits: Ruff for Python, Prettier for the front end. It
  never blocks; the checks still decide.
- [ ] The hooks are Python scripts run with `uv`, so they work the same on Windows and Linux, and live in
  `scripts/claude_hooks/` so `check.py` lints and type checks them.
- [ ] pytest covers every block and every allow in the guard, and the formatter's choice of tool per file.
- [ ] AGENTS.md, CLAUDE.md and `docs/dev-setup.md` say what the settings and hooks do, and that they protect
  Claude Code on a computer only (see Notes). `docs/decisions.md` records the choice.
- [ ] All checks pass.

## Out of scope

- The review agent in CI that reviews each pull request and pushes fixes (proposed task 0012).
- A glossary of spec terms and rule numbers, with a test that every rule has a test (proposed task 0013).
- Settings for ChatGPT's tools. CI's checks apply to every agent's pull request; this task is Claude Code only.
- Branch protection. GitHub Free enforces it only on public repos (see Notes).

## Notes / assumptions

**Where these settings apply.** Claude Code reads `.claude/settings.json` and runs its hooks on a computer: the
terminal, VS Code, the desktop app, and Remote Control. Cloud threads in a claude.ai project do not apply a
repo's permission rules or hooks (Claude Code docs, "What threads pick up from your repositories"). Those threads
run in a throwaway container with no `.env` or worker data, and can push only to their own `claude/...` branch.
CI is the gate that applies to every agent, wherever it ran.

**Sandbox.** Claude Code's sandbox enforces file and network limits at the operating system level, but it runs
on macOS, Linux and WSL2, not native Windows. It is left off; turning it on is a one-line change for anyone on
those systems.

**Branch protection.** On a private repo GitHub Free does not enforce branch protection or rulesets. Jake was
given three options on 2026-11-13: GitHub Pro, a public repo, or soft guards (the AGENTS.md rule, the hook in
this task, and cloud threads' own branch limit). Recommended: soft guards now, Pro when others use the repo.

**Jake's other questions (2026-11-13), answered in the thread:**

- *A graph database:* not now. A Take 5 is one document saved whole, and nothing yet links Take 5s to each
  other. It may earn a place later, when hazards, controls and company standards are linked across many Take 5s,
  JHAs and sites.
- *An ontology-based semantic layer:* the repo docs are already the shared layer every agent reads. A formal
  ontology would be more to maintain than the app itself. A glossary (spec term, code name, rule number) plus a
  test that every rule has a test gives most of the benefit (task 0013).
- *Unverified code, comprehension debt, intent debt, cognitive surrender:* see the PR for this task.

**Proposed follow-up tasks, waiting on Jake's answers:**

- 0012, review agent in CI: on each pull request, an agent that did not write the code follows
  `.claude/agents/reviewer.md`, runs the checks, pushes fixes it is sure of as new commits (never a force push,
  never to `main`, never a merge), and comments with what it fixed and what it left for Jake. Needs the Claude
  GitHub App on the repo and a secret added by Jake.
- 0013, glossary and rule tracing: `docs/glossary.md`, and a test that fails when a rule number in the spec has
  no test that names it.
