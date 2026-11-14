---
id: 0007
title: Saved Take 5s (spec F5)
status: in-progress
owner: claude
branch: claude/project-thread-87dbya
---

## Goal

Let a worker look back at saved Take 5s: a list, newest first, and the result screen of each.

## Acceptance criteria

- [x] `GET /api/take5s` returns the list, newest first.
- [x] A list screen shows the date, worker, job and verdict of each saved Take 5. "Not finished" waits for task
  0008 (see Notes).
- [x] Opening one shows the same result screen the worker saw, with the verdict that was saved then.
- [x] There is no endpoint that changes a finished Take 5.
- [x] Service, storage and API tests cover listing; a Playwright test covers the list and opening one.
- [x] Phone-width (360 px) screenshots of every new or changed screen are attached to the PR.
- [x] All checks pass.

## Out of scope

- Search, filters, export and deleting.

## Notes / assumptions

Don't start until the spec is approved (task 0001 is `done`). Depends on 0004; can be done before or after 0005,
0006 and 0008, and the result screen must cope with whichever of them have landed. "Not finished" can't happen
until task 0008. Everyone can see the list (spec decision D8).

What was built (2026-11-14, Claude), and the assumptions made:

- **Back end.** `Take5Repository.list_newest_first()` (SQLite sorts on `created_at`, then on the row ID so two
  saved in the same instant keep a fixed order), `Take5Service.list_newest_first()`, and `GET /api/take5s`. Each
  line of the list is a `Take5Summary` (`id`, `created_at`, `worker_name`, `job`, `can_start`), not the whole
  card, so the phone downloads little on a weak signal. The storage still reads each whole document; with one
  table and few rows that is simplest, and it can change behind `Take5Repository` if it ever gets slow.
- **"Not finished".** Until task 0008 every saved Take 5 is finished, so `can_start` is always true or false.
  Task 0008 should make it `bool | None` (None for not finished), show "Not finished" in the list, and add a test.
- **The date** is `created_at`, written the phone's way (for example "14 Nov 2026, 6:49 pm"). Until task 0008 it
  is the same as `finished_at`.
- **The whole list is sent**, with no paging, because search, filters and paging are out of scope. Paging is an
  open question for when the app is hosted for a real crew.
- **Getting there.** A "Saved Take 5s" link sits at the right of the top bar on the first page of a new Take 5
  and on the result screen. It is left off the later pages of the form, so nothing invites the worker away
  part-way through. `Screen` gained an optional `aside` for it.
- **Nothing changes a saved Take 5.** An API test lists every route and method, so a new route that edits,
  replaces or deletes one fails it. Task 0008 adds `POST /api/take5s/{id}/answer`, which answers an unfinished
  one, and will add it to that test.
- **Not shown in the list:** the location, and whether a Don't start yet has since been fixed. Both are
  questions for Jake in the pull request.
