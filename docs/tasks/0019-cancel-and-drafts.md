---
id: 0019
title: Back out of a Take 5, and keep unfinished drafts
status: done
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

Jake's answers to the review's follow-up questions, on 2026-11-16 (D26 to D29):

1. **A save whose answer was lost, reopened after 2 hours, opens the saved result**, not "run out" ("fix it").
   The phone looks the submission ID up with `GET /api/take5s/{id}` before saying a draft ran out. (D26)
2. **With no signal to check a kept draft, say so** ("do whatever makes it most clear what is actually going on
   to the user"): an amber notice with when it was started, that it can't be saved if it has run out, and Try
   again. A run-out draft is still drawn until a check gets through, but never saved. (D27)
3. **"Carry on your Take 5"** replaces "Start a new Take 5" on a result screen while a draft is kept. Jake's
   answer was "carry on", read as yes to this label. (D28)
4. **The time left shows on the form and the list** ("It should say somewhere how long the take 5 has left"):
   "1 hr 42 min left to finish, until 16 Nov 2026, 8:52 pm", counted down from the check's `runs_out_at`. A
   brand-new draft shows it from its first Continue, the first time the back end is asked. (D29)

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
- The form only checks the draft for running out as it opens, on a Continue with changed answers, and on the
  review and Finish. A worker who sits on one page past the limit finds out at the next of those. Finish always
  asks, so nothing that has run out is ever saved.
- Undo of a thrown-away draft never replaces a newer draft started since; the newer one stays.

Not done here, noted for later (from the review on 2026-11-15):

- "Fix this in a new Take 5" swapping to its question, and back, doesn't move the focus.
- The back gesture while the Leave question is open changes the page underneath it. Back from the list after
  throwing a draft away on a later page opens an empty form on that page's earlier page.
- After a 409, Leave still offers "Keep it for later", which keeps nothing.
- A fix whose own copy is the kept draft asks to throw that copy away, rather than offering to carry on.

Also noted for later (from the reviews of the follow-ups on 2026-11-17):

- Past its time, the time left says "Under 1 min left" until a check gets through. Continue and Finish check
  again, so nothing run out is saved, but it could say "Run out" instead. That is a wording choice for Jake.
- The list reuses the opening check from earlier in the same visit, so it can say a draft is in time a few
  minutes after it ran out. "Carry on" reloads the form, which checks again.
- A failed look-up for a saved Take 5 counts as not saved, so a draft that ran out is thrown away even if it was
  saved. The saved copy is still in the list.
- The "Checking your Take 5…" heading isn't focused or announced, and `Take5Form.tsx` is 372 lines and could be
  split.

- The UI calls a draft "Your unfinished Take 5". Task 0008 plans a "Not finished" tag on the list for a saved Take 5
  whose challenge question is unanswered. Check the two read differently when 0008 is built.
- The result screen doesn't show the start time, or how long the Take 5 took. Measuring the three-minute target
  (spec Open questions) is now possible from `started_at` and `created_at`.
