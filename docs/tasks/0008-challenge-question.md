---
id: 0008
title: The challenge question (spec F6)
status: done
owner: claude
branch: claude/0008-challenge-question
---

## Goal

Add the one question the app asks before the result, with everything except a real AI: the interface an AI plugs
into, the check on its question, the fixed fallback, the answer, and the unfinished state. After this task the app
asks the fallback question every time; task 0009 plugs in a real AI.

## Acceptance criteria

- [x] `services/ports.py` has the `ChallengeAsker` Protocol; `domain/take5/challenge.py` has the text the AI is
  given, the check on its question, the fallback question and the check on the answer (spec C1 to C4).
- [x] Spec worked examples 40 to 56, and 76 (added by this task), have tests, using a stand-in `ChallengeAsker`.
- [x] `POST /api/take5s` saves the Take 5 first, then returns it with its question; `POST /api/take5s/{id}/answer`
  saves the answer, works out the verdict and finishes it, and refuses a second answer.
- [x] The service falls back to the fixed question when the asker raises, returns something C2 rejects, or takes
  longer than 10 seconds; the worker never sees an error.
- [x] The front end has the question screen between the form and the result. Opening an unfinished Take 5 shows its
  question.
- [x] The result screen shows the question and the worker's answer.
- [x] A Playwright test covers answering the question, and leaving and coming back to an unfinished Take 5.
- [x] Phone-width (360 px) screenshots of every new or changed screen are attached to the PR.
- [x] All checks pass.

## Out of scope

- Any real AI provider (task 0009).
- The AI marking the answer or asking a follow-up.

## Notes / assumptions

Don't start until the spec is approved (task 0001 is `done`). Depends on 0005 (example 53 needs the think-through
questions and V1); best after 0006.

Left for this task by task 0007 (the saved Take 5 list): make `Take5Summary.can_start` `bool | None` (None for an
unfinished Take 5), show "Not finished" in `SavedTake5sScreen.tsx` with a test, and add the answer endpoint to
`test_no_endpoint_changes_a_saved_take5` in `backend/tests/api/test_saved_take5s.py`. Also decide whether an
unfinished fix should mark the Take 5 it fixes as "Fixed" in the list; today any fix does (`fixed_ids()`).

The instructions in `ai/challenge.py` must treat the worker's text as data, not as instructions (see
"What the AI is given" in `docs/architecture.md`). Add a worked example with a job description that tries to
change the AI's instructions.

### Decided with Jake (2026-11-18)

Jake took every recommended answer (spec D44 to D51):

1. The review's button is **Submit**; **Finish Take 5** is the button on the question screen (D44).
2. No way back to the form from the question: the Take 5 is saved (D45).
3. Opening the app again goes back to an unanswered question (D46).
4. Only the phone that submitted a Take 5 answers its question; any other phone sees it and "Not finished yet"
   (D47).
5. No time limit on answering (D48).
6. A saved fix marks its original Fixed even before the fix is answered, as `fixed_ids()` already did (D49).
7. The worker isn't told whether the AI or the fallback asked; revisit in task 0009 (D50).
8. C4 stays at four words, so "I will be careful" passes for now (D51).

He also approved the storage change: `Take5Repository` gains `save_question` and `finish`, each of which only
changes a Take 5 that is still unfinished. The table is unchanged; the question and the answer go in the JSON
document.

### Assumptions made while building (not product decisions)

- The text the AI is given is JSON (`challenge_text()`), so the worker's words are quoted values. The worker's
  name isn't a parameter, so it can't be sent (example 49). Example 76 checks a job that gives the AI orders.
- `GET /api/take5s/{id}` gives an unfinished Take 5 with no question the fallback (example 56), never the AI, so
  opening it is never slow.
- The same answer sent again returns the finished Take 5 (a retry after a lost reply); only a different answer is
  refused (example 55).
- The phone waits up to 20 seconds for Submit's reply, as the back end may wait 10 for the AI.
- The phone remembers the submission ID as unanswered just before it is sent, so a Take 5 saved with its reply
  lost can still be answered on that phone; a 422, a finished Take 5 or a 404 forgets it again. "Opening the app"
  is the first visit to the start page in a browser tab (`sessionStorage`), so a "Start a new Take 5" link while
  the app is open still starts one.
- The saved list's "Not finished" tag is amber, the app's attention colour, so it isn't mistaken for a verdict.

### Found in review, left as they are

- D47 is kept by the phone, not the API: with no sign-in (D4) the back end can't tell phones apart, so any request
  with the ID can answer.
- Opening an unfinished Take 5 during the AI's 10-second wait gives it the fallback question (C6), and the AI's
  question then loses to it. Harmless today, with no AI.
- The service stops waiting for the AI after 10 seconds, but the call's thread runs on until the AI answers, and
  stopping the server waits for it. Task 0009's adapter needs its own network time limit (noted there).
- Submit can take about a minute at worst: the phone waits 20 seconds and retries twice when there is no answer.

### Not done here

- The saved list's "Start a new Take 5" doesn't mention an unanswered question this phone has. Opening the app
  goes back to it, and the list shows it as Not finished at the top. Worth asking Jake if it should say more.
