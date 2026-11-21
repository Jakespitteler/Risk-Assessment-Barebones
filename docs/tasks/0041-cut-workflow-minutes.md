---
id: 0041
title: Cut wasted GitHub Actions minutes
status: review
owner: claude
branch: claude/project-thread-cu38ru
---

## Goal

Jake was running out of GitHub Actions minutes (GitHub Free gives a private repo 2,000 a month). Find where the
minutes go and stop spending them on runs that can't find anything, without dropping a check he relies on. He is
also making the repo public, which makes standard runners free; the changes still give quicker results and start
fewer AI reviews.

## Where the minutes went

Measured from the Actions API on 2026-11-21, for every run since 2026-11-13 (423 runs, 594 jobs). GitHub bills
each job rounded up to the next whole minute.

| Workflow and job | Jobs | Billed minutes |
| --- | ---: | ---: |
| CI, `checks`, passed | 172 | 804 |
| Agent review, `review`, passed | 101 | 487 |
| Agent review, `eligible` (a six-second gate, billed a minute each) | 173 | 173 |
| CI, `checks`, cancelled by a newer push | 39 | 168 |
| Everything else (failures, Claude Assistant) | 31 | 104 |
| **Total** | | **1,736** |

- A CI run now takes about 10 minutes, and 7.5 of them are the browser tests (113 tests, 1 worker). Installing
  the front end and its browser takes another 47 seconds. Markdown, spelling and the whole back end take under 30
  seconds.
- 41 CI runs (174 minutes) were on pull requests that changed only Markdown, such as task files.
- 56 of the 173 `eligible` jobs ended in a skipped review (draft pull requests and the reviewer's own pushes):
  a billed minute each to decide nothing.
- A push to a stacked branch re-runs only the pull request whose head it is, not the ones above it, so
  stacking itself doesn't multiply runs.

## Acceptance criteria

- [x] A pull request that changes only Markdown, `.cspell/` or `.markdownlint-cli2.jsonc` (none in `frontend/`)
  skips the front end's install and checks. Markdown, spelling and every back-end check still run, since the
  back-end tests read `docs/spec.md` and `docs/glossary.md`. Any other file, a push to `main`, or a change to a
  workflow gets the full run.
- [x] `uv run check.py --no-front-end` runs every check outside `frontend/`, in the usual order, with a test.
- [x] CI doesn't run on a draft pull request; it runs when the pull request is marked ready for review.
- [x] Agent review's `eligible` job doesn't start a runner for a draft or a push by `claude[bot]`, the two
  events `scripts/agent_review.cjs` always skips. The script on the base branch still decides every other event.
- [x] No check is removed: every non-draft pull request that changes code still gets every check and an AI review.
- [x] The browser tests pass with 2 workers, the number Playwright picks on a public repo's 4-core runner.
- [ ] Jake confirms on the first pull requests after the merge: a task-file pull request's CI takes about a
  minute, and a code pull request's CI is unchanged.

## Out of scope

- Security changes to the workflows (pinning actions, gating `@claude` comments, Dependabot): task 0042, the
  go-public work, owns those lines.
- Running the dark-mode browser tests for fewer tests. Every test runs twice, light and dark (spec F7), which is
  about half the 7.5 minutes. Not changed without Jake's say.
- Re-reviewing only on request rather than on each push. Each push by an agent thread starts a new AI review.
- Caching the Playwright browser: it would save about 20 seconds a run and add a cache key to keep right.

## Notes / assumptions

- Assumption: draft pull requests don't need CI. Agents run `uv run check.py` before marking a pull request
  ready (AGENTS.md, "Done means"), and marking it ready starts CI. A skipped job shows as passed, but GitHub
  doesn't merge a draft.
- The Markdown-only test is a `git diff` of the merge commit against its first parent (the base), so it needs
  `fetch-depth: 2` on the checkout and no extra action.
