---
id: 0021
title: Show the saved Take 5 list 50 at a time (spec D18)
status: in-progress
owner: claude
branch: claude/0021-saved-list-paging
---

## Goal

Jake chose (2026-11-15) that once the app is hosted for a crew, the saved Take 5 list shows the newest 50, with a
"Show more" button for the next 50. Until then the whole list is sent (task 0007), which is fine on a developer's
computer but too slow on a weak signal once hundreds are saved.

## Acceptance criteria

- [ ] `GET /api/take5s` returns at most 50, newest first, and a way to ask for the next 50 that a Take 5 saved in
  the meantime can't shift (for example "older than this one", not "skip the first 50").
- [ ] A "Show more" button under the list loads the next 50 and keeps those already shown. It is gone once there
  are no more.
- [ ] A Don't start yet on any page is still marked "Fixed" when a newer Take 5 fixes it. `fixed_ids()` in
  `domain/take5/fix.py` only sees one page, and the fix is often on an earlier one.
- [ ] Storage, service, API and Vitest tests cover the pages; a Playwright test covers "Show more".
- [ ] Phone-width (360 px) screenshots of every new or changed screen are attached to the PR.
- [ ] All checks pass.

## Out of scope

- Search and filters.

## Notes / assumptions

Start when hosting for a crew is planned (see Open questions in `docs/spec.md`). Reading 50 whole documents a page
is fine; if it is not, the summary columns beside each document can be read instead.
