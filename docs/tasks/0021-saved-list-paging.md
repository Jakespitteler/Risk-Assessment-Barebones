---
id: 0021
title: Show the saved Take 5 list 50 at a time (spec D18)
status: done
owner: claude
branch: claude/0021-saved-list-paging
---

## Goal

Jake chose (2026-11-15) that once the app is hosted for a crew, the saved Take 5 list shows the newest 50, with a
"Show more" button for the next 50. Until then the whole list is sent (task 0007), which is fine on a developer's
computer but too slow on a weak signal once hundreds are saved.

## Acceptance criteria

- [x] `GET /api/take5s` returns at most 50, newest first, and a way to ask for the next 50 that a Take 5 saved in
  the meantime can't shift (for example "older than this one", not "skip the first 50").
- [x] A "Show more" button under the list loads the next 50 and keeps those already shown. It is gone once there
  are no more.
- [x] A Don't start yet on any page is still marked "Fixed" when a newer Take 5 fixes it. `fixed_ids()` in
  `domain/take5/fix.py` only sees one page, and the fix is often on an earlier one.
- [x] Storage, service, API and Vitest tests cover the pages; a Playwright test covers "Show more".
- [x] Phone-width (360 px) screenshots of every new or changed screen are attached to the PR.
- [x] All checks pass.

## Out of scope

- Search and filters.

## Notes / assumptions

Start when hosting for a crew is planned (see Open questions in `docs/spec.md`). Reading 50 whole documents a page
is fine; if it is not, the summary columns beside each document can be read instead.

- Jake parked this task on 2026-11-19 (task 0030), then on 2026-11-20 asked for "the task after" the other agent's
  next, and took all seven recommended answers (spec D80 to D86). Built 2026-11-20 on branch
  `claude/0021-saved-list-paging`, stacked on dark mode (#55).
- The Playwright test for "Show more" can't save 50 Take 5s in reasonable time, and other tests share its
  database, so it cuts the real first page down to its own Take 5 with that as `next`. "Show more" then asks the
  real back end for everything older.
- Found while testing: the light and dark runs of `e2e/saved-take5s.spec.ts` saved the same job names at the same
  time, so a test could pick up the other run's Take 5. Each run's jobs now end in its shift ("day shift" or
  "night shift").
- A separate reviewer agent checked the diff on 2026-11-20 and found no bugs. Fixed from its review: the test
  stand-in now gives an empty page for an unknown `before`, as SQLite does (with an API test for it); the route
  says "up to 50"; and this order of work no longer says the task is parked. Left for Jake: decision D18 still
  says "Until then, all of them", which D80 to D86 now replace. Left as a suggestion: when the last page loads,
  keyboard focus could move to the first new line instead of the page.
