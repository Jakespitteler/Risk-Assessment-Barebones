---
id: 0004
title: Fill in a Take 5, part 1 - the job, hazards, ratings and controls (spec F2, F3)
status: done
owner: claude
branch: claude/project-thread-k14nwr
---

## Goal

The first end-to-end Take 5: the worker enters their name, the job and where it is, lists hazards in their own
words, rates each before and after controls, writes each control with its kind, submits, and sees a saved result
screen with the verdict. The card's questions come in task 0005 and the challenge question in task 0008.

## Acceptance criteria

- [x] The API has `GET /api/take5/template`, `POST /api/take5s/check`, `POST /api/take5s` and
  `GET /api/take5s/{id}`, as described in `docs/architecture.md`.
- [x] The front end has parts 1, 3 and 4 of the core workflow and the result screen, and holds no copy of the
  matrix, the questions or the rules: it draws the template it is sent. Pieces another feature could use go in
  `components/`, the Take 5's screens in `features/take5/`.
- [x] Nothing is selected when a screen opens. A Take 5 can't be submitted with a blank name, job or location,
  without a hazard, or with a rating half picked; each gap is named beside its field.
- [x] The score and band show as soon as a likelihood and a consequence are both picked, and never a score without
  its band.
- [x] Rule R6 holds: an after score higher than the before score can't be submitted, and a hazard with no controls
  is not rated again.
- [x] Verdict rules V2 and V3 are in `domain/take5/verdict.py`; spec worked examples 18 and 22 to 25 have tests.
- [x] The Take 5 is saved with its verdict and a copy of its template through `Take5Repository`.
- [x] The result screen shows the verdict, every reason, and each hazard with its controls and its before and after
  ratings.
- [x] The phone remembers the worker's name for next time.
- [x] The submit button can't be pressed twice while a Take 5 is being sent, so one Take 5 is never saved twice.
- [x] Every screen is usable one-handed at 360 px wide, with tap targets at least 48 px high.
- [x] API tests cover each endpoint; a Playwright test fills in the form and checks the result for a Good to go and
  a Don't start yet case.
- [x] Phone-width (360 px) screenshots of every new or changed screen are attached to the PR.
- [x] All checks pass.

## Out of scope

- The think-through and hazard questions, and V1 (task 0005).
- The thinking rules T1 to T4 (task 0006).
- The challenge question (task 0008).

## Notes / assumptions

Built by ChatGPT in PRs #8 (API) and #9 (screens), then reworked by Claude after review
(the findings are listed in the follow-up PR's description).

What there is:

- API: the four endpoints in `docs/architecture.md`. Every error reply is declared in OpenAPI: a 422 is always
  `FormErrors`, a 404 or 409 is `ErrorMessage`. `POST /api/take5s` takes `{id, draft}`; the phone makes the
  UUID once, so a retry can't save twice, and other answers with the same ID get a 409 (Jake approved this).
- Domain: `draft.py` checks a draft in one pass and names each gap by its dotted path. R6 is checked
  directly. The card's guidance is part of `Take5Template`, so a saved Take 5 keeps it (Jake approved this).
- Screens: job, hazards, then each hazard's before, controls and after, then review and result. The page is in
  the URL, so the back gesture steps back a page. Each Continue asks `POST /api/take5s/check` and shows that
  page's gaps there. The review and result draw what the back end returns. Removing a hazard or control can be
  undone. The saved Take 5 goes straight into the result screen's cache.

Assumptions:

- The draft and its submission ID are kept in the tab's `sessionStorage`, so a reload or a slip of the back
  gesture loses nothing. They are cleared when the Take 5 is saved, or when the tab is closed. Only the
  worker's name is kept after that, in `localStorage`, as before.
- With no signal, Continue moves on without the check; the review checks everything again before Finish.
- Reads and the submit retry three times when they get no answer or a 5xx, and every request times out after
  15 seconds.

For the next tasks: task 0005 adds the card's questions to `Take5Template` and `Take5Draft`; `stageOfError()` in
`frontend/src/features/take5/stage.ts` needs to place their error paths on the right page.
