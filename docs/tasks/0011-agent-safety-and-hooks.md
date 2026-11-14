---
id: 0011
title: Agent safety settings and hooks for Claude Code
status: done
owner: claude
branch: claude/project-thread-7tuvvd
---

## Goal

Jake asked (2026-11-13) for current Claude Code safety and verification practice: keep agents away from secrets
such as `.env`, stop them committing to `main`, and check their work automatically. This task covers what runs on
a computer where Claude Code is used. The review agent in CI and the glossary are follow-up tasks (below), so each
pull request stays small.

## Acceptance criteria

- [x] `.claude/settings.json` denies Claude's file tools reading or editing secrets and worker data: `.env` and
  `.env.*` files, private keys and certificates, `.netrc`, any `secrets/`, `.ssh/` or `.aws/` folder, and
  `.data/` (where `backend/.data/` keeps saved Take 5s), wherever they are on the computer. It pre-approves the
  commands in AGENTS.md for Bash and PowerShell, so agents ask less often for safe things. The git rules are in
  the guard only, so they are written down once.
- [x] A `PreToolUse` hook blocks, with a reason the agent can read, a Bash or PowerShell command that names a
  secret file or `backend/.data/`, a commit, merge or push while on `main`, a push to `main`, a force push,
  `--no-verify` and merging a PR. Deny rules only see the file tools and simple commands such as `cat .env`;
  the hook reads the whole command text, so it also catches `python -c`, pipes and chains. Commit and PR text
  that names a secret goes in a file (`git commit -F`), so no message can carry a secret out.
- [x] A `PostToolUse` hook formats each file an agent edits: Ruff for Python, Prettier for the front end, and
  markdownlint's safe fixes for Markdown. It never blocks; the checks still decide.
- [x] The hooks are Python scripts run with `uv`, so they work the same on Windows and Linux, and live in
  `scripts/claude_hooks/` so `check.py` lints and type checks them.
- [x] pytest covers every block and every allow in the guard, the formatter's choice of tool per file, both
  hooks' exit codes, and that `.claude/settings.json` points at scripts that exist.
- [x] AGENTS.md, CLAUDE.md and `docs/dev-setup.md` say what the settings and hooks do, and that they protect
  Claude Code on a computer only (see Notes). `docs/decisions.md` records the choice.
- [x] AGENTS.md step 7 says an agent that did not write a PR reviews it before Jake, and the PR template asks
  for a plain-words summary, the files to read first, and anything that could not be checked.
- [x] All checks pass.

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

**Jake's answers (2026-11-13):** the plan and the split into tasks 0011 to 0013 are approved. The review agent
signs in with his Claude subscription (an OAuth token, `CLAUDE_CODE_OAUTH_TOKEN`), not an API key. It replaces
the other agent's review in AGENTS.md step 7. `main` stays on soft guards for now, not GitHub Pro.

**If a hook can't run.** An error inside the guard exits with code 2, and the guard's `"onFailure": "block"`
(Claude Code 2.1.295 or later) blocks the call when the hook times out, can't start, or fails any other way.
So a broken guard is noticed at once rather than waving calls through. The hooks use exec form
(`"command": "uv"` with `args`), so no shell or Git Bash is involved.

**Independent review (2026-11-13).** A separate reviewer agent found that on Windows commands go through the
PowerShell tool, which the guard first missed; that commit messages naming `.env` were blocked; that Windows
reads hook input in the wrong code page; and a list of bypasses. A second pass found that letting commit and
PR text through also let `git commit -F .env` and `gh pr create --body-file .env` through. The guard now reads
the whole command text with no exceptions. A third pass found line continuations, `"$(git ...)"`, wrappers
such as `if` or `timeout`, and apostrophes that paired with later quotes. All findings were fixed and tested,
except those that only a sandbox could stop, which are listed under Limits in `docs/decisions.md`.

**Follow-up tasks, approved by Jake (task files `0012` and `0013`):**

- 0012, review agent in CI: on each pull request, an agent that did not write the code follows
  `.claude/agents/reviewer.md`, runs the checks, pushes fixes it is sure of as new commits (never a force push,
  never to `main`, never a merge), and comments with what it fixed and what it left for Jake. Needs the Claude
  GitHub App on the repo and a secret added by Jake.
- 0013, glossary and rule tracing: `docs/glossary.md`, and a test that fails when a rule number in the spec has
  no test that names it.
