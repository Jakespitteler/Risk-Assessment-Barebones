---
id: 0027
title: The AI judges vague hazards (spec T6)
status: review
owner: claude
branch: claude/project-thread-p10g0r (first stacked on task 0009, PR #45; reopened against main after it merged)
---

## Goal

Have the AI judge whether a hazard linked to a Yes on the hazard check is too vague, whenever it can be reached,
with task 0022's word rule (fewer than 6 words) as the fallback. Jake asked for it on 2026-11-18 (task 0022's
first question), and chose to give it its own task after 0009 (spec D55).

## Acceptance criteria

- [x] A new job in `ai/` (`ai/vague_hazard.py`), with its own instructions and version, works with any
  `LanguageModel`. No provider file changes, beyond naming Claude's quick model in `claude.py` (D61).
- [x] When the AI can't be reached, takes too long or sends back something unusable, the word rule decides, as
  today. The worker never sees an AI error.
- [x] Spec T6, its worked examples and "Out of scope" are updated, with worked examples for the AI's answers and
  for each way it can fail (77 to 87), tested with a stand-in model.
- [x] The worker's name is never sent, and the nudge still never stops Continue or Submit (T6, D35).
- [ ] The PR lists the AI's verdict on a set of made-up hazards, short and long, specific and vague, with the
  measured cost and time. Waits on Jake: `uv run scripts/try_vague_hazard.py claude-haiku-5-5 claude-sonnet-5-5
  claude-opus-5-5` with his key, output pasted into the PR.
- [x] Phone-width (360 px) screenshots of any changed screen. All checks pass.

## Out of scope

- The challenge question (task 0009).
- Any other use of the AI.

## Notes / assumptions

Depends on 0009, which adds `LanguageModel`, the Claude adapter and the AI settings.

### Decided (Jake, 2026-11-19: "continue", taking every recommendation; spec D56 to D63)

1. When is the AI asked? Once for each hazard's words: when it is linked to a Yes, and when the worker leaves the
   nudge's box with new words. Never while they type (D56).
2. How long does the server wait? 5 seconds, then the word rule. Nothing shows under the Yes meanwhile (D57).
3. What does the AI send back? Only "vague" or "specific"; the nudge keeps its fixed words (D58).
4. Is the answer remembered? Yes, in the server's memory, for the same hazard, question, job and location,
   until it restarts. "Keep it as it is" stays on the phone (D59, D37).
5. Which hazards? Only one linked to a Yes, as before (D60).
6. Cost and model? Its own setting, `TAKE5_AI_HAZARD_MODEL`; by default the provider's quick model, Claude
   Haiku 5.5. Estimated 0.02 cents an ask on Haiku, 0.3 on Sonnet 5.5, 0.6 on Opus 5.5; 3 or 4 asks a Take 5
   (D61). Jake measures it with his key.
7. Tell the worker when the word rule decided? No, as D50 (D62).
8. (Added) Tell the worker hazards go to the AI before Submit? One line on the hazard check page, when an AI is
   set up: "The hazards you link to a Yes are checked by an AI. Your name isn't sent." (D63).

### Assumptions made while building (not product decisions)

- The nudges have their own endpoint, `POST /api/take5s/nudges`, and `DraftCheck` no longer has `nudges`. The
  check runs on many typing pauses and every Continue, so an AI inside it would be asked far more often and would
  make Continue wait. Recorded in `docs/decisions.md` (2026-11-19).
- Instructions version `vague-hazard-1` (`ai/vague_hazard.py`). Changing the wording means a new version.
- A template with no word minimum turns T6 off altogether, AI included, as it did before.
- A hazard's words are sent exactly as typed, so trailing spaces make a different text and a second ask.
- The AI is asked in up to 16 background threads kept for the server's life, so a verdict that comes after the
  5 seconds is still remembered. Two checks of the same words share one ask. At most 1,000 verdicts are kept;
  past that the oldest is forgotten.
- The hazard check page makes one nudges request for the whole page (in `FormPage.tsx`), not one per nudge, so
  typing in one nudge's box never makes another ask. It sends the draft without the links of hazards whose words
  were kept, so kept words are never judged or sent to an AI.
- On the phone, the last answer stays on screen while a new one is asked for, so a nudge doesn't blink off and
  on when something else on the page changes. A hazard newly linked shows nothing until its first answer. Spec
  T6 says so (a clarification of D57 for Jake to confirm).
- Typing new words in the box and then tapping "Keep it as it is" leaves the box first, which asks once about
  the new words before they are kept.
- The background threads are never shut down, so stopping the server can wait up to 11 seconds for a call still
  with the AI. `hazard_ai_notice` shows whenever an AI is set up, even on a template with no word minimum, where
  nothing is sent; the booklet has a minimum.
- `ClaudeModel` keeps its 11-second network limit, so a late call ends soon after the service has moved on.
- Not checked in the cloud: real verdicts, times and costs (no key here, by Jake's choice in task 0009), and
  whether Haiku 5.5 accepts `effort: low` (Anthropic's docs say it does). `scripts/try_vague_hazard.py` shows both.
- Screenshots (`/mnt/project-files/task-0027/`) were taken with a made-up key, so the AI failed and the word rule
  decided, which is the no-signal path. They show the line on the hazard check page and the nudge.
