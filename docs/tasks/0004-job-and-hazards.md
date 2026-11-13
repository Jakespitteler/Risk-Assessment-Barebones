---
id: 0004
title: Fill in a Take 5, part 1 - the job, hazards, ratings and controls (spec F2, F3)
status: todo
owner:
branch:
---

## Goal
The first end-to-end Take 5: the worker enters their name, the job and where it is, lists hazards in their own words, rates each before and after controls, writes each control with its kind, submits, and sees a saved result screen with the verdict. The card's questions come in task 0005 and the challenge question in task 0008.

## Acceptance criteria
- [ ] The API has `GET /api/card`, `POST /api/take5s/check`, `POST /api/take5s` and `GET /api/take5s/{id}`, as described in `docs/architecture.md`.
- [ ] The front end has parts 1, 3 and 4 of the core workflow and the result screen, and holds no copy of the matrix or the rules.
- [ ] Nothing is selected when a screen opens. A Take 5 can't be submitted with a blank name, job or location, without a hazard, or with a rating half picked; each gap is named beside its field.
- [ ] The score and band show as soon as a likelihood and a consequence are both picked, and never a score without its band.
- [ ] Rule R6 holds: an after score higher than the before score can't be submitted, and a hazard with no controls is not rated again.
- [ ] Verdict rules V2 and V3 are in `domain/verdict.py`; spec worked examples 18 and 22 to 25 have tests.
- [ ] The Take 5 is saved with its verdict through `Take5Repository`.
- [ ] The result screen shows the verdict, every reason, and each hazard with its controls and its before and after ratings.
- [ ] The phone remembers the worker's name for next time.
- [ ] Every screen is usable one-handed at 360 px wide, with tap targets at least 48 px high.
- [ ] API tests cover each endpoint; a Playwright test fills in the form and checks the result for a Good to go and a Don't start yet case.
- [ ] Phone-width (360 px) screenshots of every new or changed screen are attached to the PR.
- [ ] All checks pass.

## Out of scope
- The think-through and hazard questions, and V1 (task 0005).
- The thinking rules T1 to T4 (task 0006).
- The challenge question (task 0008).

## Notes / assumptions
Don't start until the spec is approved (task 0001 is `done`). Depends on 0003. Until task 0008 adds the challenge question, a Take 5 is finished as soon as it is submitted. This is the largest slice; if it passes about 400 changed lines, do the API in one PR and the screens in the next.
