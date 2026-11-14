---
id: 0005
title: Fill in a Take 5, part 2 - the card's questions (spec F2, F3)
status: in-progress
owner: claude
branch: claude/project-thread-4h589l
---

## Goal

Add the card's two sets of questions: the seven think-through questions, where a No means don't start, and the
seven hazard questions, where a Yes reminds the worker to list the hazard.

## Acceptance criteria

- [ ] Part 2 of the core workflow (think through the task) exists, and the hazard questions are in part 3.
- [ ] No answer is selected to begin with, there is no way to answer them all at once, and the Take 5 can't be
  submitted with one unanswered.
- [ ] A Yes to a hazard question shows "Make sure it's on your list" with a button to add a hazard.
- [ ] `domain/questions.py` has `Question`, `QuestionRole` and `Answer`, and the booklet's template has its
  fourteen questions. Verdict rule V1 is in `domain/take5/verdict.py` and works from the question's role, not its
  text; spec worked examples 19 to 21, 26 and 27 have tests.
- [ ] The screens draw whatever questions the template holds; a test with a made-up template of two questions proves it.
- [ ] The result screen shows each question with its answer.
- [ ] A Playwright test covers a No (Don't start yet) and an N/A (Good to go).
- [ ] Phone-width (360 px) screenshots of every new or changed screen are attached to the PR.
- [ ] All checks pass.

## Out of scope

- Hiding the hazard questions until a hazard is written, T1 (task 0006).

## Notes / assumptions

Don't start until the spec is approved (task 0001 is `done`). Depends on 0004. Take 5s saved before this task have
no answers to these questions; the result screen must still open them.
