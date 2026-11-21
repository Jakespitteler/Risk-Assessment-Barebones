---
id: 0042
title: Get the repo ready to be public
status: review
owner: claude
branch: claude/project-thread-b5b8wl
---

## Goal

Jake decided on 2026-11-21 to make this repo public, and asked for it to be set up "as good as can be". Public
means anyone can read the code, the docs and the whole git history, and anyone can open an issue, a pull request
or a comment. This task checks nothing secret is in the history, hardens the GitHub workflows against strangers,
adds the files a public repo needs, and lists the settings Jake turns on. Jake makes the switch himself.

## Acceptance criteria

- [x] Every commit on every branch and pull request is searched for keys, tokens, passwords and secret files.
- [x] Anything about Jake's employer, or personal to Jake, is listed for Jake to decide on (below).
- [x] No workflow that holds a secret or can write to the repo can be started by someone outside the repo:
  `claude.yml` checks the commenter is the owner, a member or a collaborator; the agent review already skips
  forks, and now skips Dependabot too (its PRs get no secrets, so a review could only fail).
- [x] Every action in `.github/workflows/` is pinned to a full commit SHA, with its version in a comment, and
  `.github/dependabot.yml` keeps them current, one grouped PR a month.
- [x] `SECURITY.md` says how to report a problem privately. The README says the repo is public but not open source.
- [x] The licence stays "All rights reserved" in Jake's name (task 0015); only "confidential" is dropped, because
  public code can't be confidential.
- [x] A test covers the review gate skipping Dependabot.
- [ ] Jake answers the questions below, and the matching edits are made.
- [x] Jake makes the repo public and turns on the settings below (public on 2026-11-21).

## Out of scope

- Cutting wasted workflow minutes: the thread "Cut wasted GitHub workflow minutes" owns triggers, paths filters,
  concurrency and installs. This task changes only the `uses:` lines, `claude.yml`'s `if:` and permissions, and
  the review gate.
- Rewriting git history. Nothing secret was found, so there is nothing that needs it (see question 2).
- The Risk-Assessment repo, which stays private.

## How the history was searched

On 2026-11-21, every commit reachable from `main`, all 16 other branches and every pull request head (371
commits). Two passes: every file name ever added (for `.env`, keys, certificates, databases, `secrets/`,
`backend/.data/`), and every added line, for the formats of Anthropic, OpenAI, Google, GitHub, AWS and Slack keys,
private keys, JSON web tokens, `key=`/`password=`/`token=` with a long value, and any long random-looking string.

Result: nothing secret. The only settings file ever committed is `backend/.env.example`, with an empty
`TAKE5_AI_KEY=`. The random-looking hits were all ordinary names, such as `TAKE5_AI_MODEL=claude-sonnet-5-5`.

A ready-made scanner (gitleaks or TruffleHog) could not be downloaded in the cloud thread that did this. Secret
scanning, which GitHub turns on for public repos, scans the whole history again when the repo goes public.

## Settings for Jake, in this order

1. **Your email (before the switch).** github.com → your picture → Settings → Emails: tick "Keep my email
   addresses private" and "Block command line pushes that expose my email". On your PC, run
   `git config --global user.email 125878678+Jakespitteler@users.noreply.github.com` so new commits use the
   private address.
2. **Make it public.** The repo → Settings → General → Danger Zone → Change repository visibility → Public.
3. **Security.** Settings → Advanced Security (called "Code security" on some accounts). Turn on: Private
   vulnerability reporting, Dependency graph, Dependabot alerts, Dependabot security updates, Secret Protection
   (secret scanning) with Push protection, and CodeQL analysis → Set up → Default.
4. **Actions.** Settings → Actions → General:
   - "Approval for running fork pull request workflows from contributors": "Require approval for all external
     contributors".
   - "Workflow permissions": "Read repository contents and packages permissions", and leave "Allow GitHub
     Actions to create and approve pull requests" off. Each workflow already asks for what it needs.
   - "Actions permissions": keep "Allow all actions and reusable workflows", and tick "Require actions to be
     pinned to a full-length commit SHA" if your page shows it, but only once the pins are on `main`. Turned on
     earlier, every PR whose workflows aren't pinned fails at "Set up job" (found on 2026-11-21). Every action
     here, and the one action that `claude-code-action` runs itself, is pinned in this task.
5. **Protect `main`.** Settings → Rules → Rulesets → New ruleset → New branch ruleset. Name it `main`,
   Enforcement status Active, Target branches → Add target → Include default branch. Tick: Restrict deletions,
   Block force pushes, Require a pull request before merging (Required approvals 0, because GitHub won't let you
   approve a PR opened from your own account), and Require status checks to pass → Add checks → `checks` (the CI
   job). Leave the bypass list empty. Save. A required check that never starts blocks the merge, so if CI is
   ever made to skip some pull requests (such as by a paths filter), change this rule in the same PR.
6. **Leave "Automatically delete head branches" off** (Settings → General → Pull Requests). With stacked PRs, a
   deleted base branch closes the next PR (lesson of 2026-11-14 in AGENTS.md step 3).
7. **Tidy.** Settings → General → Features: turn off Wikis and Projects if you don't use them. On the repo's front
   page, the cog beside "About": add a one-line description and topics such as `take5`, `mining`, `safety`.

## Questions for Jake

1. **Your personal email is in 22 old commits** (as "Jacob Spitteler"). Anyone can read it once the repo is
   public. Recommended: accept it and do step 1 above, so no new commit shows it. The only way to remove it is to
   rewrite the whole history, which force pushes `main` and breaks every open PR.
2. **Your employer is named in three files**: `docs/tasks/0015-licence.md`, `docs/decisions.md` (the licence
   entry) and `.cspell/project-words.txt`. Task 0015 says you said the app is your employer's property. Public,
   that reads as a statement about your employer. Recommended: reword those lines to drop the name (the old
   wording stays in the git history).
3. **The Take 5 card's wording** in `backend/.../take5/template.py` and `docs/spec.md` (the questions, the 5x5
   matrix's labels and the likelihood and consequence meanings) appears to be copied from your work's Take 5
   booklet. It names no company, and wording like it is common across sites, but it is your employer's
   document. Recommended: ask your manager if they mind, or keep it as is if the booklet is already handed out
   freely.
4. **Outside contributions.** Recommended: the README says pull requests from outside aren't accepted (as now
   written), which matches "All rights reserved".

## Notes / assumptions

- Assumed "as good as can be" means safe and tidy, not a redesigned README: the README keeps its content, with a
  short public note at the top.
- When the repo is public, GitHub-hosted runner minutes are free, so the minutes question changes. The API key and
  the Claude login used by the review workflows still cost money.
- The `claude-code-action` also checks the commenter can write to the repo. The new `if:` is a second check that
  stops the job before it starts, so a stranger's comment costs nothing. It also stops comments from
  `claude[bot]` (a bot is not a collaborator), so the workflow's `allowed_bots: "claude[bot]"` no longer starts a
  run: one Claude can't start another by writing `@claude` in a comment.
- Don't write `@claude` on a pull request from a fork: the job would run a stranger's code with the API key and a
  token that can push.
- `agent-review.yml` runs on `pull_request`, not `pull_request_target`, so a fork's PR never gets the secrets or
  a token that can write. `scripts/agent_review.cjs` also refuses forks before the review job starts.

## Jake's answers (2026-11-21, in chat)

1. Accepted. Jake turned on GitHub's email privacy; the 22 old commits keep the old address.
2. Reworded: the app is meant for any company, so the docs no longer name his employer (task 0015, the licence
   decision, the spelling list). The old wording stays in the git history.
3. Explained in chat; waiting on Jake.
4. Explained in chat (the promise is to whoever reports a security problem); waiting on Jake.
