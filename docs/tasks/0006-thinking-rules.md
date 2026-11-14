---
id: 0006
title: Thinking rules (spec F4)
status: in-progress
owner: chatgpt
branch: chatgpt/0006-thinking-rules
---

## Goal

Add the fixed rules that stop the app being used on autopilot: own words first, no vague controls, push back on weak
controls for a serious hazard, and a real job description.

## Acceptance criteria

- [ ] T2, T3 and T4 are pure functions in `domain/take5/thinking.py`, with the vague phrases and word counting in
  the shared `domain/wording.py`, reported through `POST /api/take5s/check`; spec worked examples 28 to 39 have
  tests.
- [ ] T1: the hazard questions can't be seen or answered until one hazard has been written.
- [ ] A vague control or a too-short job shows its message beside the field and blocks submitting.
- [ ] The weak-controls question appears when T3 applies, must be answered or met with a strong control, and its
  answer is saved and shown on the result screen.
- [ ] A Playwright test covers each rule.
- [ ] Phone-width (360 px) screenshots of every new or changed screen are attached to the PR.
- [ ] All checks pass.

## Out of scope

- The challenge question (task 0008).

## Notes / assumptions

Don't start until the spec is approved (task 0001 is `done`). Depends on 0005.

Claimed after 0017, 0016 and 0005 were completed. Planned as three stacked PRs: pure rules and their
worked examples; draft checking, API and saved answers; then the phone screens and end-to-end tests.
Jake approved the API/data additions and short-job message on 2026-11-14; see `docs/decisions.md`.
Update `docs/tasks/README.md` with the remaining order when this task is ready for review, as Jake requested.
