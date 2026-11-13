---
id: 0004
title: Fill in a Take 5, part 1 - the job and think through the task (spec F2, F3)
status: todo
owner:
branch:
---

## Goal
The first two screens of the workflow, end to end: the worker enters their name and the job, answers the seven think-through questions, submits, and sees a saved result page with the verdict. Hazards come in task 0005.

## Acceptance criteria
- [ ] Screens 1 and 2 of the core workflow exist and post to the server.
- [ ] Nothing is selected when a screen opens, and the form can't be submitted with a blank name, a blank job or an unanswered question.
- [ ] The Take 5 is saved through `Take5Repository` before the result page is shown.
- [ ] Verdict rule V1 is implemented in `domain/verdict.py`; spec worked examples 17 to 19 have tests.
- [ ] An end-to-end test fills in both screens and checks the verdict on the result page.
- [ ] Phone-width (360 px) screenshots of every new or changed page are attached to the PR.
- [ ] All checks pass.

## Out of scope
- Hazards, ratings and controls (task 0005).
- The four-word rule for the job, T4 (task 0006).

## Notes / assumptions
Don't start until the spec is approved (task 0001 is `done`). Depends on 0003. Until task 0005 lands, a Take 5 has no hazards; say so in the code where the at-least-one-hazard rule will go.
