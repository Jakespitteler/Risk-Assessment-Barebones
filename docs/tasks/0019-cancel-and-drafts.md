---
id: 0019
title: Back out of a Take 5, and keep unfinished drafts
status: todo
owner:
branch:
---

## Goal

Jake asked (2026-11-14) for a way to back out of a Take 5 and to save drafts. Today the form has no Cancel,
and an unsaved Take 5 lives only in the browser tab (`sessionStorage`): it survives a reload, but closing the
tab loses it. The spec lists "keeping a half-filled Take 5 if the app is closed" as out of scope, so this task
changes the spec.

## Decide first

Jake makes these choices before the task starts. Write the answers here and in the spec's decisions table.

1. **What "back out" means.** (a) Cancel: the draft is thrown away, with an undo. (b) Leave and come back: the
   draft is kept. (c) Both. Recommended: both.
2. **Where drafts are kept.** (a) On the phone only (`localStorage`): simple and private, but lost with the
   phone or a cleared browser, and a shared phone would show other workers' drafts. (b) On the server: a
   supervisor could see them and they survive a new phone, but it adds a draft record to the data model and
   endpoints. Recommended: the phone first, since there is no sign-in to tell workers apart (spec D4).
3. **How long a draft lasts.** A Take 5 is meant to be done at the job just before starting. A draft kept for
   hours could be started at breakfast and finished at lunch without looking again. Recommended: a draft
   expires after a set time (for example, the end of a 12-hour shift), and opening an old draft asks the worker
   to check every answer again.
4. **How many drafts.** One at a time, or a list. Recommended: one, which keeps the screens simple; a list fits
   beside task 0007's list of saved Take 5s if more are needed.

## Acceptance criteria

To be finished once the choices above are made. Expected:

- [ ] The form has a way to back out on every page, usable one-handed at 360 px with gloves.
- [ ] Throwing a draft away can be undone, as removing a hazard can.
- [ ] A kept draft opens where the worker left it, and an expired one is never silently reused.
- [ ] Any expiry rule is in the back end (`domain/`) with a worked example in the spec and a test, so the screen
  only shows what it is sent.
- [ ] `docs/spec.md` (Out of scope, F2, the decisions table) and `docs/architecture.md` are updated.
- [ ] Vitest and Playwright cover backing out, coming back, and expiry. Phone-width screenshots of every new or
  changed screen are attached to the PR.
- [ ] All checks pass.

## Out of scope

- Editing a saved Take 5. A finished Take 5 never changes (docs/architecture.md, Data model).
- Working with no signal.

## Notes / assumptions

Best done after task 0007 (saved Take 5s), whose list a list of drafts would sit beside. The draft is kept by
`frontend/src/features/take5/useTake5Draft.ts` today; task 0010's `keepFixDraft()` writes a draft there too.
Found in task 0007: the first page of the form links to the saved Take 5s, so a worker can go from a half-done
draft to a saved Don't start yet and press "Fix this in a new Take 5", which replaces that draft without a
warning. This task should decide what happens then.
