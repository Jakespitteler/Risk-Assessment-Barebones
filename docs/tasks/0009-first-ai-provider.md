---
id: 0009
title: The first AI provider (spec F6)
status: done
owner: claude
branch: claude/project-thread-tsquwa
---

## Goal

Plug a real AI into the challenge question, behind the `ChallengeAsker` interface, so that swapping providers later
means adding one file and changing one setting.

## Acceptance criteria

- [x] `ai/model.py` has the `LanguageModel` Protocol. `ai/challenge.py` holds the challenge question's
  instructions, with a version, and a `ChallengeAsker` that works with any `LanguageModel`.
  `ai/providers/claude.py` implements `LanguageModel` and imports nothing from the app except `ai/model.py`.
- [x] Each AI question is saved with the model and the instructions version that asked it.
- [x] The provider, model and key are settings read from the environment. With no key set, the app runs and uses
  the fallback question.
- [x] No key, and no real name or real job, is in the repo; the sample Take 5s are obviously made up.
- [x] A test proves the worker's name is not in what is sent (spec example 49), against the real adapter with the
  network call replaced.
- [x] A test that only runs when a key is set calls the real provider once and gets a usable question.
- [x] When an AI is set up, the review says above Submit what is sent to it (spec D52).
- [x] The PR lists the questions the AI asked for at least five sample Take 5s, and the measured cost and time per
  question.
- [x] `README.md` explains how to set the key locally.
- [x] All checks pass.

## Out of scope

- A second provider. Add a file in `ai/providers/` as its own task when wanted.
- Changing any rule in `domain/`.
- Rating the AI's questions and using the ratings (spec, "Planned for later").

## Notes / assumptions

Don't start until the spec is approved (task 0001 is `done`). Depends on 0008. The new dependency is the provider's
own Python library; record it in `docs/decisions.md`.

Jake, 2026-11-18 (task 0022): once an AI is set up, it should also judge whether a hazard linked to a Yes on the
hazard check is vague, whenever it can be reached, with task 0022's word rule as the fallback. That widens the
AI's use beyond the challenge question (spec D3 and "Out of scope"), so change the spec in the same PR, or give
it its own task after this one.

From task 0008: the service stops waiting for the AI after 10 seconds, but can't stop the call itself, so its
thread runs on, and stopping the server waits for it. Give the provider's own client a network time limit just
over 10 seconds.

### Decided with Jake (2026-11-18)

Jake took every recommended answer (spec D52 to D55):

1. Claude Opus 5.5 (`claude-opus-5-5`) on low effort writes the question; `TAKE5_AI_MODEL` changes it (D53).
2. The question may be about a hazard the job plainly has that isn't on the list; C1 says so (D54).
3. When an AI is set up, one line above Submit says what goes to it and that the name doesn't. The question
   itself is still not labelled (D52, keeping D50).
4. The AI judging vague hazards is its own task, 0027, straight after this one (D55).
5. Jake makes his own API key at console.anthropic.com with a monthly spend limit, keeps it in `backend/.env`,
   and runs `uv run scripts/try_challenge.py` to measure. The key never goes in the repo or the cloud.

### Assumptions made while building (not product decisions)

- Instructions version `challenge-1` (`ai/challenge.py`). Changing the wording means a new version.
- The adapter never retries and gives up after 11 seconds (task 0008's note). A refusal, or a reply with no text,
  raises `LanguageModelError`, and the service asks the fallback. Anthropic's server-side refusal fallbacks are
  not used, because the fixed question already covers a refusal.
- The key can be in `backend/.env` as well as the environment, so it is easy to set on Windows. Every back-end
  test hides it (`tests/conftest.py`) and the whole-app tests set it empty, so no test calls the real AI by
  accident. The real-AI test runs only with `uv run pytest -m real_ai`, in `backend/`.
- `backend/.env.example` is the settings template (Jake asked for one): copy it to `backend/.env` and fill it in.
  `.gitignore` keeps it while ignoring every other `.env.*`. A test checks that it names every setting and that
  its key line stays empty.
- `ai_notice` comes from the back end on `GET /api/take5/template`, and is empty when no key is set, so the line
  above Submit is only shown when it is true. Its words sit beside `challenge_text()` in
  `domain/take5/challenge.py`, which is what decides what is sent.
- `ai/` may import `domain` (as `storage/` may), because `AiQuestion` lives in `domain/take5/challenge.py`.
- The adapter logs the tokens each reply used, never any text, so cost can be followed in the back end's log.

### Measured by Jake (2026-11-19)

Jake ran `uv run scripts/try_challenge.py claude-opus-5-5 claude-sonnet-5-5 claude-haiku-5-5` with his own key.
The full table of questions is in the PR. All 15 questions passed C2, and none needed the fixed question.

| Model | Time per question | Tokens in / out | Cost per question |
| --- | --- | --- | --- |
| Opus 5.5 (low effort, the setting) | 2.8 to 3.6 s | about 1,240 / 140 to 290 | 0.8 to 1.1 US cents |
| Sonnet 5.5 (low effort) | 1.3 to 2.3 s | about 1,240 / 55 to 75 | about 0.3 cents |
| Haiku 5.5 (low effort) | 2.1 to 2.8 s | about 1,240 / 340 to 400 | about 0.03 cents |

- All three accept `effort` "low". Every question came well inside the 11 second limit.
- At 100 Take 5s a day, Opus 5.5 costs about US$30 a month, Sonnet 5.5 about $9 and Haiku 5.5 under $1.
- Opus 5.5 asked the sharpest questions on the crusher chute (material falling from upstream) and the crib hut
  light (both hands on the light means no three points of contact). Sonnet 5.5 was the only one to ask about
  falling off the trailer deck, the hazard missing from that sample.
- No model asked about electrical isolation for the crib hut light, the hazard missing from that sample. Each
  chose the weak ladder control instead. Worth watching when the instructions are next changed.

### Found in review

- The app's own info lines (which model asks, and the tokens each reply used) were dropped, because uvicorn sets
  up only its own loggers. `create_app()` now shows the `risk_assessment` logger's info lines.
- A `.env` saved by PowerShell 5.1's `>` is UTF-16 and is read as no key, without an error. The README says to
  copy the template with `Copy-Item` (which keeps it UTF-8) and edit it in VS Code; a UTF-8 file with a byte
  order mark is read too.
- Not checked on Windows: the whole-app tests set `TAKE5_AI_KEY` to empty so a key in `backend/.env` isn't used.
  Windows keeps an empty variable when Node starts a program, so it should hold. If the fallback-question tests
  fail on Windows with a key in `.env`, this is why.

### Fixed here, though outside the task

- On Windows the app opened blank: `import { TimeLeft } from "./TimeLeft"` found `timeLeft.ts` (task 0019's
  countdown words) before `TimeLeft.tsx`, because Windows ignores the case of file names and Vite tries `.ts`
  first. Linux and CI never saw it. The words file is now `timeLeftText.ts`, so no two files in `frontend/` differ
  only by case. Worth a check that keeps it that way (not added here).
