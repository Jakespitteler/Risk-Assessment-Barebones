---
id: 0010
title: Fix a Don't start yet - warn at the review, and copy the answers into a new Take 5 (spec F3)
status: review
owner: claude
branch: claude/project-thread-jd8go0
---

## Goal

A worker told "Say how you will control: ..." had no way to add the control: a saved Take 5 is final, and the
only fix was to type everything again. Jake chose (2026-11-13) two fixes. The review warns about a hazard with no
controls before Finish. A "Don't start yet" result offers to copy the answers into a new Take 5, and the first
one stays saved as it was.

## Acceptance criteria

- [x] `POST /api/take5s/check` also returns warnings: things that are allowed but will stop the job. For now,
  one per hazard with no controls (spec V2), on the path `hazards.<n>.controls`, with the text "No controls:
  you'll be told not to start." The rule is in `domain/`, not in TypeScript, and the front end draws what it is
  sent.
- [x] The review shows each warning on its hazard, with a button that opens that hazard's controls page. After
  adding a control there, Continue goes back to the review.
- [x] A warning never blocks Finish; a worker may still save a Take 5 that says Don't start yet.
- [x] A "Don't start yet" result has a "Fix this in a new Take 5" button. It opens the form with a new draft
  that holds the saved answers (name, job, location, each hazard's description, ratings and controls) and a new
  submission ID. The saved Take 5 is not changed.
- [x] A "Good to go" result has no such button.
- [x] The new Take 5 records which one it fixes: `SavedTake5` gains `fixes`, the first one's ID, or nothing.
  The phone sends it with the submission, and the back end refuses (422) an ID that isn't a saved Take 5.
  The new result screen links to the Take 5 it fixes. The first one's result screen links to its fix, found
  when it is opened, so the first one is still never changed.
- [x] Back-end tests cover the warning (examples 17 and 22) and that a draft with a warning can still be
  submitted. Vitest covers the warning on the review and the copy. A Playwright test goes from a Don't start yet,
  through "Fix this in a new Take 5" and adding the control, to Good to go, and checks the first Take 5 is
  unchanged.
- [x] Phone-width (360 px) screenshots of every new or changed screen are attached to the PR.
- [x] All checks pass.

## Out of scope

- Editing a saved Take 5. A finished Take 5 never changes (docs/architecture.md, Data model).
- Warnings for the JHA reason (V3) and the card's questions (V1, task 0005). The warnings list is shaped so they
  can be added later, but this task adds only V2's.
- A list of a worker's Take 5s (task 0007).

## Notes / assumptions

Depends on task 0004's follow-up PR #12. Independent of 0005 to 0009, so it can be done before or after them.

Jake approved (2026-11-13) the `fixes` field, a data model change, so a supervisor can see that a job was
first planned without a control. Add `fixes` to the data model table in `docs/architecture.md` when it is built.

Built by Claude. Jake chose (2026-11-13), on Claude's recommendations:

- The copy opens on the review, where the warning points at the hazard with no controls.
- After "Add a control", Continue goes to that hazard's after-controls page, then back to the review. A gap on
  the very next page opens as normal, without being marked as a mistake.
- Once a Take 5 has a fix, it links to the newest fix and no longer offers "Fix this in a new Take 5".
- The back end refuses (422) a `fixes` that points at a Good to go, as well as one that isn't saved, and one
  that names the Take 5's own ID.

What there is:

- Domain: `check_draft()` returns `warnings` beside `errors`, each a `FieldWarning` with a dotted path.
  `domain/take5/fix.py` says which saved Take 5 may be fixed. `Take5Draft` and `SavedTake5` gain `fixes`.
- Service and storage: `submit` checks `fixes` and saves it. `Take5Repository.fixed_by()` finds the newest fix;
  SQLite searches the documents with `json_extract`, so the table is unchanged. `Take5Response` gains
  `fixed_by`.
- Screens: the review shows each warning on its hazard (`components/Warning.tsx`). The result screen's
  `FixPanel` offers the fix or links the two. `keepFixDraft()` in `useTake5Draft.ts` writes the copy into the
  tab's draft with a new submission ID; the form then opens it as any other draft.

Assumptions and limits:

- Pressing Fix replaces any unsaved draft in that tab. A draft is cleared when it is saved, so this only
  matters if a worker starts a new Take 5 and then goes back to an old result in the same tab.
- If the first Take 5 vanished before the fix is saved (only possible by deleting the database), Finish gets a
  422 on `fixes`, which has no field on screen to show it beside.
- A long list of Take 5s would make the `json_extract` search slow; a `fixes` column with an index is the fix
  then (task 0007 or later).
