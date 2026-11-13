---
id: 0010
title: Fix a Don't start yet - warn at the review, and copy the answers into a new Take 5 (spec F3)
status: in-progress
owner: claude
branch: claude/project-thread-jd8go0
---

## Goal

A worker told "Say how you will control: ..." had no way to add the control: a saved Take 5 is final, and the
only fix was to type everything again. Jake chose (2026-11-13) two fixes. The review warns about a hazard with no
controls before Finish. A "Don't start yet" result offers to copy the answers into a new Take 5, and the first
one stays saved as it was.

## Acceptance criteria

- [ ] `POST /api/take5s/check` also returns warnings: things that are allowed but will stop the job. For now,
  one per hazard with no controls (spec V2), on the path `hazards.<n>.controls`, with the text "No controls:
  you'll be told not to start." The rule is in `domain/`, not in TypeScript, and the front end draws what it is
  sent.
- [ ] The review shows each warning on its hazard, with a button that opens that hazard's controls page. After
  adding a control there, Continue goes back to the review.
- [ ] A warning never blocks Finish; a worker may still save a Take 5 that says Don't start yet.
- [ ] A "Don't start yet" result has a "Fix this in a new Take 5" button. It opens the form with a new draft
  that holds the saved answers (name, job, location, each hazard's description, ratings and controls) and a new
  submission ID. The saved Take 5 is not changed.
- [ ] A "Good to go" result has no such button.
- [ ] The new Take 5 records which one it fixes: `SavedTake5` gains `fixes`, the first one's ID, or nothing.
  The phone sends it with the submission, and the back end refuses (422) an ID that isn't a saved Take 5.
  The new result screen links to the Take 5 it fixes. The first one's result screen links to its fix, found
  when it is opened, so the first one is still never changed.
- [ ] Back-end tests cover the warning (examples 17 and 22) and that a draft with a warning can still be
  submitted. Vitest covers the warning on the review and the copy. A Playwright test goes from a Don't start yet,
  through "Fix this in a new Take 5" and adding the control, to Good to go, and checks the first Take 5 is
  unchanged.
- [ ] Phone-width (360 px) screenshots of every new or changed screen are attached to the PR.
- [ ] All checks pass.

## Out of scope

- Editing a saved Take 5. A finished Take 5 never changes (docs/architecture.md, Data model).
- Warnings for the JHA reason (V3) and the card's questions (V1, task 0005). The warnings list is shaped so they
  can be added later, but this task adds only V2's.
- A list of a worker's Take 5s (task 0007).

## Notes / assumptions

Depends on task 0004's follow-up PR #12. Independent of 0005 to 0009, so it can be done before or after them.

Jake approved (2026-11-13) the `fixes` field, a data model change, so a supervisor can see that a job was
first planned without a control. Add `fixes` to the data model table in `docs/architecture.md` when it is built.
