---
id: 0006
title: Thinking rules (spec F4)
status: review
owner: chatgpt
branch: chatgpt/0006-thinking-ui
---

## Goal

Add the fixed rules that stop the app being used on autopilot: own words first, no vague controls, push back on weak
controls for a serious hazard, and a real job description.

## Acceptance criteria

- [x] T2, T3 and T4 are pure functions in `domain/take5/thinking.py`, with the vague phrases and word counting in
  the shared `domain/wording.py`, reported through `POST /api/take5s/check`; spec worked examples 28 to 39 have
  tests.
- [x] T1: the hazard questions can't be seen or answered until one hazard has been written.
- [x] A vague control or a too-short job shows its message beside the field and blocks submitting.
- [x] The weak-controls question appears when T3 applies, must be answered or met with a strong control, and its
  answer is saved and shown on the result screen.
- [x] A Playwright test covers each rule.
- [x] Phone-width (360 px) screenshots of every new or changed screen are attached to the PR.
- [x] All checks pass.

## Out of scope

- The challenge question (task 0008).

## Notes / assumptions

Don't start until the spec is approved (task 0001 is `done`). Depends on 0005.

Claimed after 0017, 0016 and 0005 were completed. Split into three stacked PRs: pure rules and their
worked examples; draft checking, API and saved answers; then the phone screens and end-to-end tests.
Jake approved the API/data additions and short-job message on 2026-11-14; see `docs/decisions.md`.
The work order now names 0018 as the next task after this stack is reviewed and merged.

- Part 1: PR #25 (`chatgpt/0006-thinking-rules`), pure rules and examples 28 to 34 and 37 to 39.
- Part 2: PR #26 (`chatgpt/0006-thinking-api`), draft checking and saved answers, including examples 35 and 36.
  The draft keeps an answer after a strong control is added, so an edit never discards the worker's words.
  It never changes the verdict.
- Part 3: PR #28 (`chatgpt/0006-thinking-ui`), the phone prompt, saved summary and T1 navigation guard. The last
  server question stays visible during rechecking to keep focus while typing; Finish never uses an old check.
  A written answer also stays visible if an unfinished new control temporarily removes the server's question.
  Existing tab drafts keep version 2 because the new answer has an empty default.
- Six new Playwright tests cover T1 to T4, including offline navigation, reload, undo and saving/reopening.
  Seven 360 px screenshots were inspected. CI uploads them as `phone-screenshots`, rather than committing them.
  PR #28 links to the uploaded artifact. Test the complete app from its branch; the middle API branch does
  not yet have the answer box for T3.
