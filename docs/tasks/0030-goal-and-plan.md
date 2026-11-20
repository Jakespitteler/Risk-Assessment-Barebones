---
id: 0030
title: Put the agreed goal at the top of the spec, and plan the work it needs
status: review
owner: claude
branch: claude/0030-goal-and-plan (stacked on task 0013's second pull request, #54)
---

## Goal

Jake and Claude agreed the app's goal on 2026-11-19. Every agent should judge new work against it, so it goes at
the top of `docs/spec.md`, the spec's scope changes to match, and the work the goal needs gets task files.

The goal, as agreed:

> **Make a mine site safer by making every Take 5 count.**
>
> 1. **Filling one in:** on a phone or a desktop, the worker has to actually think about today's job instead of
>    ticking boxes. It stays quick and pleasant enough that crews want to use it, because an app people avoid
>    makes no one safer.
> 2. **Finding the weak ones:** a batch of paper cards can be photographed. The AI fills in each one as a normal
>    saved Take 5, marked "from paper", and a person confirms it beside the photo before it's saved. Any set of
>    Take 5s (a scanned batch, or everything from today) can be ranked worst first. "Worst" weighs how risky the
>    job is against how little thought the answers show, with one line saying why. Anyone can do this; there's
>    no sign-in.
>
> **The AI is used wherever it makes a Take 5 safer.** A worker can always finish a Take 5 without it. Scanning
> and ranking need it, and that's fine because no worker waits on them.
>
> **How we judge it:** by feel in demos, for both safety people and crews. There's no fixed time target. Every
> feature, and every bit of polish, has to earn its place against this goal.

## Acceptance criteria

- [x] `docs/spec.md` starts with the goal, word for word as above, and its Purpose agrees with it.
- [x] The spec's "Out of scope" no longer rules out scanning paper cards or AI ranking, and still rules out
  sign-in, supervisors and crews. The three-minute target is gone from "Where and when it is used" and from
  Open questions, since Jake chose no fixed number.
- [x] The spec says the app is used on a phone or a desktop; task 0031 adds a desktop test.
- [x] `AGENTS.md` says to judge every task against the goal and keep the app as simple as possible.
- [x] `docs/decisions.md` records Jake's answers of 2026-11-19 that shaped the goal.
- [x] Task files exist for 0031 (a desktop test), 0032 (rank Take 5s worst first) and 0033 (photograph paper
  cards into Take 5s), each with its goal, its questions for Jake with a recommendation each, and acceptance
  criteria that follow the recommendations.
- [x] `docs/tasks/README.md` orders the work: 0028, then 0031, 0032 and 0033; 0024 is the other agent's; 0021 is
  parked.
- [x] All checks pass.

## Out of scope

- Building any of the new features. Each is its own task.
- Changing app behaviour. This task changes docs only.

## Notes / assumptions

Jake's answers, 2026-11-19, in chat:

- The goal above, worked out over several messages until both agreed it.
- "Scan existing Take 5s" means photographing paper cards, which the AI fills in as normal saved Take 5s, marked
  "from paper"; a person confirms each beside its photo before it is saved.
- The AI ranks a set of Take 5s worst first, and the same ranking serves a scanned batch and "worst of the day".
  "Worst" weighs risk against how little thought the answers show.
- Anyone can scan and rank; there is no sign-in or supervisor role.
- Proving it to both safety people and crews; the AI is used wherever it makes a Take 5 safer; no fixed speed
  target.
- This task gets its own file (0030); the new tasks go in the order desktop, ranking, scanning, after 0028; 0021
  is parked.
- On this task's review: screens already fit a desktop, so 0031 shrinks to a whole-app test at 1280 px, and the
  review screens of 0032 and 0033 are designed for desktop inside those tasks. The ranked page shows each
  worker's name, as the saved list does.
- Outside the quoted goal, the spec says the app is a proof of concept, "really nice to use, and as simple as
  possible". These are Jake's words from 2026-11-19, the same as the line in AGENTS.md.
