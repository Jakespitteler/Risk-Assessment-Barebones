---
id: 0019
title: Back out of a Take 5, and keep unfinished drafts
status: review
owner: claude
branch: claude/project-thread-frta7h
---

## Goal

Jake asked (2026-11-14) for a way to back out of a Take 5 and to save drafts. Today the form has no Cancel,
and an unsaved Take 5 lives only in the browser tab (`sessionStorage`): it survives a reload, but closing the
tab loses it. The spec lists "keeping a half-filled Take 5 if the app is closed" as out of scope, so this task
changes the spec.

## Decided

Jake answered on 2026-11-15 ("Do all of your recommendations", and for the time limit: "I'd like the timer to be
toggle off completely if I change it to no limit"). They are spec decisions D19 to D25 and rules K1 to K3.

1. **What "back out" means: both.** Leave, on every page once anything is filled in, offers "Keep it for later",
   "Throw it away" (with Undo) and "Keep going". Either way out goes to the saved list, where a kept draft sits at
   the top with "Carry on". (D19)
2. **Where drafts are kept: on the phone** (`localStorage`). (D20)
3. **How long a draft lasts: 2 hours from its start.** The back end decides. The limit is
   `Take5Template.draft_time_limit_minutes` (120 in `BOOKLET_TEMPLATE`); setting it to `None` turns the check off
   completely. If it runs out part-way, Continue and Finish say so. (D21)
4. **A draft that has run out is thrown away**, and the worker is told why, with when it was started. (D22)
5. **One draft at a time.** (D23)
6. **"Fix this in a new Take 5" with a draft kept asks first:** "You have an unfinished Take 5 for '\<job\>'.
   Fixing this one throws it away." (D24)
7. **Each saved Take 5 keeps when it was started** (`SavedTake5.started_at`), a data model change. (D25)

## Acceptance criteria

- [x] The form has a way to back out on every page, usable one-handed at 360 px with gloves.
- [x] Throwing a draft away can be undone, as removing a hazard can.
- [x] A kept draft opens where the worker left it, and an expired one is never silently reused.
- [x] The expiry rule is in the back end (`domain/take5/time_limit.py`) with worked examples 57 to 64 in the spec
  and tests, so the screen only shows what it is sent.
- [x] `docs/spec.md` (Out of scope, F2, the new Drafts section, the decisions table) and `docs/architecture.md`
  are updated.
- [x] Vitest and Playwright cover backing out, coming back, and expiry. Phone-width screenshots of every new or
  changed screen are attached to the PR.
- [x] All checks pass.

## Out of scope

- Editing a saved Take 5. A finished Take 5 never changes (docs/architecture.md, Data model).
- Working with no signal.

## Notes / assumptions

Best done after task 0007 (saved Take 5s), whose list a list of drafts would sit beside. The draft is kept by
`frontend/src/features/take5/useTake5Draft.ts` today; task 0010's `keepFixDraft()` writes a draft there too.
Found in task 0007: the first page of the form links to the saved Take 5s, so a worker can go from a half-done
draft to a saved Don't start yet and press "Fix this in a new Take 5", which replaces that draft without a
warning. This task should decide what happens then. (Decided: it asks first, D24.)

Assumptions made while building (2026-11-15):

- The clock starts at the worker's first change, so opening the form and leaving without typing keeps nothing.
  A fix's copy starts its clock when "Fix this in a new Take 5" is pressed.
- The phone's clock is trusted to be roughly right: it stamps `started_at`, and the back end compares that with
  its own clock. A phone whose clock is set hours wrong would see drafts run out early or late; the template's
  limit can be turned off if that becomes a problem.
- A draft with no `started_at` (sent by a phone from before this task) isn't checked (example 62).
- A draft kept in the old place (`sessionStorage`, in a tab left open across the update) is not carried over.
- Two tabs on one phone share the one draft; the last change wins.
- The form only checks the draft for running out as it opens, on Continue and on the review. A worker who sits on
  one page past the limit finds out at the next Continue.

Not done here, noted for later:

- The UI calls a draft "Your unfinished Take 5". Task 0008 plans a "Not finished" tag on the list for a saved Take 5
  whose challenge question is unanswered. Check the two read differently when 0008 is built.
- With a draft kept, "Start a new Take 5" on a result screen opens the draft, since there is only one. A label
  such as "Carry on your Take 5" there may read better.
- The result screen doesn't show the start time, or how long the Take 5 took. Measuring the three-minute target
  (spec Open questions) is now possible from `started_at` and `created_at`.
