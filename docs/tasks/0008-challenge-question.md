---
id: 0008
title: The challenge question (spec F6)
status: todo
owner:
branch:
---

## Goal
Add the one question the app asks before the result, with everything except a real AI: the interface an AI plugs into, the check on its question, the fixed fallback, the answer, and the unfinished state. After this task the app asks the fallback question every time; task 0009 plugs in a real AI.

## Acceptance criteria
- [ ] `services/ports.py` has the `ChallengeAsker` Protocol; `domain/challenge.py` has the text the AI is given, the check on its question, the fallback question and the check on the answer (spec C1 to C4).
- [ ] Spec worked examples 40 to 52 have tests, using a stand-in `ChallengeAsker`.
- [ ] `POST /api/take5s` saves the Take 5 first, then returns it with its question; `POST /api/take5s/{id}/answer` saves the answer, works out the verdict and finishes it.
- [ ] The service falls back to the fixed question when the asker raises, returns something C2 rejects, or takes longer than 10 seconds; the worker never sees an error.
- [ ] The front end has the question screen between the form and the result. Opening an unfinished Take 5 shows its question.
- [ ] The result screen shows the question and the worker's answer.
- [ ] A Playwright test covers answering the question, and leaving and coming back to an unfinished Take 5.
- [ ] Phone-width (360 px) screenshots of every new or changed screen are attached to the PR.
- [ ] All checks pass.

## Out of scope
- Any real AI provider (task 0009).
- The AI marking the answer or asking a follow-up.

## Notes / assumptions
Don't start until the spec is approved (task 0001 is `done`). Depends on 0004; best after 0006. Needs spec decisions D10 and D11 answered first.
