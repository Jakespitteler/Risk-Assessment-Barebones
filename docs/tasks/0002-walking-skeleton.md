---
id: 0002
title: Walking skeleton with CI
status: todo
owner:
branch:
---

## Goal
Build the thinnest end-to-end version of the app on the chosen stack, with CI enforcing lint, typecheck and tests, before any real features.

## Acceptance criteria
- [ ] App runs locally with one command.
- [ ] One real end-to-end path works (e.g. create and view a trivial assessment).
- [ ] Risk scoring module exists with tests for spec worked example #1.
- [ ] .github/workflows/ci.yml runs lint, typecheck and tests on every PR and push to main.
- [ ] AGENTS.md Commands and Conventions sections filled in.
- [ ] README explains how to run and test.

## Notes / assumptions
Depends on 0001.
