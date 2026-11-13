---
id: 0007
title: Saved Take 5s (spec F5)
status: todo
owner:
branch:
---

## Goal

Let a worker look back at saved Take 5s: a list, newest first, and the result screen of each.

## Acceptance criteria

- [ ] `GET /api/take5s` returns the list, newest first.
- [ ] A list screen shows the date, worker, job and verdict of each saved Take 5, or "Not finished".
- [ ] Opening one shows the same result screen the worker saw, with the verdict that was saved then.
- [ ] There is no endpoint that changes a finished Take 5.
- [ ] Service, storage and API tests cover listing; a Playwright test covers the list and opening one.
- [ ] Phone-width (360 px) screenshots of every new or changed screen are attached to the PR.
- [ ] All checks pass.

## Out of scope

- Search, filters, export and deleting.

## Notes / assumptions

Don't start until the spec is approved (task 0001 is `done`). Depends on 0004; can be done before or after 0005,
0006 and 0008, and the result screen must cope with whichever of them have landed. "Not finished" can't happen
until task 0008. Everyone can see the list (spec decision D8).
