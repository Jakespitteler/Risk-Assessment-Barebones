---
id: 0004
title: Fill in a Take 5, part 1 - the job, hazards, ratings and controls (spec F2, F3)
status: in-progress
owner: chatgpt
branch: chatgpt/0004-take5-ui
---

## Goal

The first end-to-end Take 5: the worker enters their name, the job and where it is, lists hazards in their own
words, rates each before and after controls, writes each control with its kind, submits, and sees a saved result
screen with the verdict. The card's questions come in task 0005 and the challenge question in task 0008.

## Acceptance criteria

- [ ] The API has `GET /api/take5/template`, `POST /api/take5s/check`, `POST /api/take5s` and
  `GET /api/take5s/{id}`, as described in `docs/architecture.md`.
- [ ] The front end has parts 1, 3 and 4 of the core workflow and the result screen, and holds no copy of the
  matrix, the questions or the rules: it draws the template it is sent. Pieces another feature could use go in
  `components/`, the Take 5's screens in `features/take5/`.
- [ ] Nothing is selected when a screen opens. A Take 5 can't be submitted with a blank name, job or location,
  without a hazard, or with a rating half picked; each gap is named beside its field.
- [ ] The score and band show as soon as a likelihood and a consequence are both picked, and never a score without
  its band.
- [ ] Rule R6 holds: an after score higher than the before score can't be submitted, and a hazard with no controls
  is not rated again.
- [ ] Verdict rules V2 and V3 are in `domain/take5/verdict.py`; spec worked examples 18 and 22 to 25 have tests.
- [ ] The Take 5 is saved with its verdict and a copy of its template through `Take5Repository`.
- [ ] The result screen shows the verdict, every reason, and each hazard with its controls and its before and after
  ratings.
- [ ] The phone remembers the worker's name for next time.
- [ ] The submit button can't be pressed twice while a Take 5 is being sent, so one Take 5 is never saved twice.
- [ ] Every screen is usable one-handed at 360 px wide, with tap targets at least 48 px high.
- [ ] API tests cover each endpoint; a Playwright test fills in the form and checks the result for a Good to go and
  a Don't start yet case.
- [ ] Phone-width (360 px) screenshots of every new or changed screen are attached to the PR.
- [ ] All checks pass.

## Out of scope

- The think-through and hazard questions, and V1 (task 0005).
- The thinking rules T1 to T4 (task 0006).
- The challenge question (task 0008).

## Notes / assumptions

Don't start until the spec is approved (task 0001 is `done`). Depends on 0003. Until task 0008 adds the challenge
question, a Take 5 is finished as soon as it is submitted. This is the largest slice; if it passes about 400
changed lines, do the API in one PR and the screens in the next.

Claimed by ChatGPT. Plan: implement and test verdicts, draft validation, a repository port, SQLite storage
and the four endpoints first, then the worker screens in a second branch/PR based on this branch, as the
size note above directs. No new dependencies. UI choices are pending Jake's answers: usage context,
one-hazard-at-a-time versus scrolling, and guidance visibility. Do not assume those answers.

Jake answered: own phone at the job; one hazard at a time; labels with expandable guidance. These choices
are recorded in the spec and decision log. The browser keeps its in-progress answers until final submission.

Backend implementation: `SavedTake5` extends the existing scoring model with submission details and a saved
verdict. Drafts accept scale choices only, never scores/bands. `/check` returns dotted field paths/messages
and a valid scoring model without writing storage. `/api/take5s` accepts `{id, draft}`; keep the UUID stable
across retries. Submitting different input with the same ID returns 409. The first stored document wins
atomically, including concurrent requests. Retrieval returns the stored verdict and template snapshot.
The response envelope contains `take5` and its overall `rating`. The template endpoint also supplies card
guidance and control kinds. SQLite defaults to ignored `backend/.data/take5.sqlite3`; `TAKE5_DATABASE_PATH`
overrides it. No new dependencies. The UI is implemented in the next PR on top of this backend branch.

Backend validation passed: `uv run scripts/check.py`, including 74 Python tests, strict Pyright, Ruff,
markdown, front-end lint/format/types, three front-end tests, generated API consistency and the original
browser test. API tests cover empty/partial drafts, increased after risk, missing controls, retrieval,
immutable documents and safe retries; a service test also races duplicate submissions. UI acceptance
criteria remain in progress in the stacked screens PR.

Backend PR: #8 (`chatgpt/0004-take5-api`). Screens are claimed on `chatgpt/0004-take5-ui`, based on it.
