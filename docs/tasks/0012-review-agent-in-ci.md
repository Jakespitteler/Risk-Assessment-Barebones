---
id: 0012
title: A review agent in CI that checks and fixes each pull request before Jake reviews it
status: in-progress
owner: chatgpt
branch: chatgpt/0012-review-agent
---

## Goal

Jake wants code never to be checked by the agent that wrote it, and wants the final review of every pull request
himself. An agent in CI reviews each pull request first, fixes what it is sure of, and tells Jake what it fixed
and what it left for him. It replaces the other agent's review (AGENTS.md step 7), so Jake no longer passes pull
requests between Claude and ChatGPT by hand.

## Acceptance criteria

- [ ] `.github/workflows/agent-review.yml` runs `anthropics/claude-code-action@v1` on each pull request that is
  opened, updated or marked ready, and skips drafts and its own pushes, so it can't loop.
- [ ] It signs in with Jake's Claude subscription: `claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}`.
- [ ] Its instructions come from `.claude/agents/reviewer.md`, the same ones the local reviewer uses, so the
  review rules are written once.
- [ ] It runs `uv run scripts/check.py`. It may push fixes it is sure of as new commits on the pull request's
  branch. It never force pushes, never pushes to `main`, never merges or approves, and never changes the spec,
  a decision, or anything AGENTS.md says needs the human.
- [ ] It leaves one comment: what it found, what it fixed (with the commits), what it left for Jake, and anything
  it could not check.
- [ ] It is limited by `--max-turns`, a job timeout, and a concurrency group per pull request.
- [ ] AGENTS.md step 7 drops "and the other agent until then". `docs/decisions.md` records any choice made here.

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
