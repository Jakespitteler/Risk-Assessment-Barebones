---
id: 0006
title: Thinking rules (spec F4)
status: todo
owner:
branch:
---

## Goal
Add the rules that stop the app being used on autopilot: own words first, no vague controls, pushback on weak controls for a serious hazard, and a real job description.

## Acceptance criteria
- [ ] T2, T3 and T4 are pure functions in `domain/thinking.py`; spec worked examples 28 to 39 have tests.
- [ ] T1: the hazard questions can't be seen or answered until one hazard has been written.
- [ ] A vague control or a too-short job shows its message beside the field and blocks submitting.
- [ ] The weak-controls question appears when T3 applies, must be answered or met with a strong control, and its answer is saved and shown on the result page.
- [ ] An end-to-end test covers each rule.
- [ ] Phone-width (360 px) screenshots of every new or changed page are attached to the PR.
- [ ] All checks pass.

## Out of scope
- Any AI check.

## Notes / assumptions
Don't start until the spec is approved (task 0001 is `done`). Depends on 0005.
