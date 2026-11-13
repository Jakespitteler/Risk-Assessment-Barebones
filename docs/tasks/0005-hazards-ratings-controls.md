---
id: 0005
title: Fill in a Take 5, part 2 - hazards, ratings and controls (spec F2, F3)
status: todo
owner:
branch:
---

## Goal
Screens 3 and 4 of the workflow: the worker lists hazards in their own words, rates each before and after controls, and writes each control with its kind. The result page then shows the full verdict.

## Acceptance criteria
- [ ] Screens 3 and 4 of the core workflow exist; a Take 5 needs at least one hazard to be submitted.
- [ ] The score and band show as soon as a likelihood and a consequence are both picked, and never a score without its band.
- [ ] Rule R6 is a form error: an after score higher than the before score can't be submitted.
- [ ] Verdict rules V2 and V3 are implemented; spec worked examples 20 to 25 have tests.
- [ ] The result page shows every reason, and each hazard with its controls and its before and after ratings.
- [ ] An end-to-end test fills in every screen and checks the result page for a Good to go and a Don't start yet case.
- [ ] Phone-width (360 px) screenshots of every new or changed page are attached to the PR.
- [ ] All checks pass.

## Out of scope
- Hiding the hazard questions until a hazard is written, T1, and the other thinking rules (task 0006).

## Notes / assumptions
Don't start until the spec is approved (task 0001 is `done`). Depends on 0004.
