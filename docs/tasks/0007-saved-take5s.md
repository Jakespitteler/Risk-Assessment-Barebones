---
id: 0007
title: Saved Take 5s (spec F5)
status: todo
owner:
branch:
---

## Goal
Let a worker look back at saved Take 5s: a list, newest first, and the result page of each.

## Acceptance criteria
- [ ] A list page shows the date, worker, job and verdict of each saved Take 5, newest first.
- [ ] Opening one shows the same result page the worker saw when they submitted it.
- [ ] There is no route or form that changes a saved Take 5.
- [ ] Service and storage tests cover listing; an end-to-end test covers the list and opening one.
- [ ] Phone-width (360 px) screenshots of every new or changed page are attached to the PR.
- [ ] All checks pass.

## Out of scope
- Search, filters, export and deleting.

## Notes / assumptions
Don't start until the spec is approved (task 0001 is `done`). Depends on 0004; can be done before or after 0005 and 0006. Who can see the list is spec decision D8.
