---
id: 0009
title: The first AI provider (spec F6)
status: todo
owner:
branch:
---

## Goal
Plug a real AI into the challenge question, behind the `ChallengeAsker` interface, so that swapping providers later means adding one file and changing one setting.

## Acceptance criteria
- [ ] `ai/model.py` has the `LanguageModel` Protocol. `ai/challenge.py` holds the challenge question's instructions, with a version, and a `ChallengeAsker` that works with any `LanguageModel`. `ai/providers/claude.py` implements `LanguageModel` and imports nothing from the app except `ai/model.py`.
- [ ] Each AI question is saved with the model and the instructions version that asked it.
- [ ] The provider, model and key are settings read from the environment. With no key set, the app runs and uses the fallback question.
- [ ] No key, and no real name or real job, is in the repo; the sample Take 5s are obviously made up.
- [ ] A test proves the worker's name is not in what is sent (spec example 49), against the real adapter with the network call replaced.
- [ ] A test that only runs when a key is set calls the real provider once and gets a usable question.
- [ ] The PR lists the questions the AI asked for at least five sample Take 5s, and the measured cost and time per question.
- [ ] `README.md` explains how to set the key locally.
- [ ] All checks pass.

## Out of scope
- A second provider. Add a file in `ai/providers/` as its own task when wanted.
- Changing any rule in `domain/`.
- Rating the AI's questions and using the ratings (spec, "Planned for later").

## Notes / assumptions
Don't start until the spec is approved (task 0001 is `done`). Depends on 0008. The new dependency is the provider's own Python library; record it in `docs/decisions.md`.
