---
id: 0012
title: A review agent in CI that checks and fixes each pull request before Jake reviews it
status: done
owner: chatgpt
branch: chatgpt/0012-review-agent
---

## Goal

Jake wants code never to be checked by the agent that wrote it, and wants the final review of every pull request
himself. An agent in CI reviews each pull request first, fixes what it is sure of, and tells Jake what it fixed
and what it left for him. It replaces the other agent's review (AGENTS.md step 7), so Jake no longer passes pull
requests between Claude and ChatGPT by hand.

## Acceptance criteria

- [x] `.github/workflows/agent-review.yml` runs `anthropics/claude-code-action@v1` on each pull request that is
  opened, updated or marked ready, and skips drafts and its own pushes, so it can't loop.
- [x] It signs in with Jake's Claude subscription: `claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}`.
- [x] Its instructions come from `.claude/agents/reviewer.md`, the same ones the local reviewer uses, so the
  review rules are written once.
- [x] It runs `uv run scripts/check.py`. It may push fixes it is sure of as new commits on the pull request's
  branch. It never force pushes, never pushes to `main`, never merges or approves, and never changes the spec,
  a decision, or anything AGENTS.md says needs the human.
- [x] It leaves one comment: what it found, what it fixed (with the commits), what it left for Jake, and anything
  it could not check.
- [x] It is limited by `--max-turns`, a job timeout, and a concurrency group per pull request.
- [x] AGENTS.md step 7 drops "and the other agent until then". `docs/decisions.md` records any choice made here.

## Out of scope

- Branch protection on `main` (Jake chose soft guards, 2026-11-13).
- Reviewing ChatGPT's work with ChatGPT's own review tools.

## Notes / assumptions

Recommended next, before task 0005 (Claude, 2026-11-13), so every later pull request is reviewed by it.
Task numbers are IDs, not the order of work.

Before the workflow can run, Jake must:

1. Install the Claude GitHub App on the repo: <https://github.com/apps/claude>.
2. Run `claude setup-token` in a terminal (it needs the Claude Code command line, not only the VS Code
   extension) and save the token as the repo secret `CLAUDE_CODE_OAUTH_TOKEN`
   (Settings, Secrets and variables, Actions).

The token from `claude setup-token` lasts one year, so it must be made again and the secret replaced each year.
Skip `/install-github-app`: it opens its own workflow pull request, and this task writes the workflow instead.

Reviews use his subscription's limits, not a separate bill. GitHub Actions minutes are free up to a monthly
limit on GitHub Free.

The review agent's pushes must start CI again. GitHub doesn't run workflows for pushes made with the default
`GITHUB_TOKEN`, so the action signs in as the Claude GitHub App (its default).

Implementation: `agent-review.yml` uses a tested event gate, Claude App authentication, the shared reviewer
policy, 40 turns and a 30-minute job limit. Fix commits trigger normal CI; reviewer synchronize events are
skipped. Failure steps update the same marked report. Jake confirmed the App and secret are ready.
No app API, data model or package dependencies changed. No UI changed, so screenshots are not applicable.

Validation: `uv run scripts/check.py` passes (279 Python, 72 Vitest, 14 Playwright tests);
actionlint passes; independent reviewer findings addressed (bootstrap, bot actors,
failure reports). The bootstrap run deliberately skips until its policy exists on the base branch. Live OAuth,
comment updates and a fix push triggering CI must be verified on the next PR after human merge. Abrupt timeout
or cancellation can prevent a report. Do not treat a skipped/failed run as a completed review.

## Review by Claude (2026-11-13)

Every acceptance criterion is met, and the gate's test covers each kind of event. Fixed in the spell check pull
request (task 0014): the test's name now says what it proves, and this file says `done`. Task 0014's pull request
was the first live run: sign-in, the checks and the marked comment worked. A fix push starting CI is not proven
yet, because that review had nothing to fix.

When a pull request changes `agent-review.yml`, the Claude App refuses to run it, because the workflow must match
the default branch. The job still shows a green tick and the old comment stays, naming the older commit it
reviewed. So check the commit in the comment, and review a workflow change yourself.

Jake's answers (2026-11-14) are under each point:

1. A pull request can change the rules it is reviewed by. `.claude/agents/reviewer.md`, `CLAUDE.md`,
   `.claude/settings.json` and `scripts/check.py` all come from the pull request's branch. Only the gate loads
   from the base branch, and a changed workflow file is not run at all (above). Closing this needs `pull_request_target`
   (rejected in the decision above) or branch protection (not on GitHub Free for a private repo). It is an
   accepted risk while only Jake, Claude and ChatGPT push, and Jake's own review is the backstop.
   Jake accepted the risk.
2. `model: fable` in `reviewer.md` only applies to the local subagent. In CI the review runs on the action's
   default model, unless `--model` is added to `claude_args`, which uses more of the subscription's limits.
   Jake chose to pin it to Opus 5.5: `agent-review.yml` now passes `--model claude-opus-5-5`.
3. The gate is JavaScript (`scripts/agent_review.cjs`) in a Python scripts folder. Nothing lints or type checks
   it, and the back end's tests now need Node. It works; rewrite it in Python only if it changes again.
   Left as it is.
