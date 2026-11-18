---
id: 0027
title: The AI judges vague hazards (spec T6)
status: in-progress
owner: claude
branch: claude/project-thread-p10g0r (stacked on task 0009's claude/project-thread-tsquwa, PR #45)
---

## Goal

Have the AI judge whether a hazard linked to a Yes on the hazard check is too vague, whenever it can be reached,
with task 0022's word rule (fewer than 6 words) as the fallback. Jake asked for it on 2026-11-18 (task 0022's
first question), and chose to give it its own task after 0009 (spec D55).

## Acceptance criteria

- [ ] A new job in `ai/` (for example `ai/vague_hazard.py`), with its own instructions and version, works with any
  `LanguageModel`. No provider file changes.
- [ ] When the AI can't be reached, takes too long or sends back something unusable, the word rule decides, as
  today. The worker never sees an AI error.
- [ ] Spec T6, its worked examples and "Out of scope" are updated, with worked examples for the AI's answers and
  for each way it can fail, tested with a stand-in model.
- [ ] The worker's name is never sent, and the nudge still never stops Continue or Submit (T6, D35).
- [ ] The PR lists the AI's verdict on a set of made-up hazards, short and long, specific and vague, with the
  measured cost and time.
- [ ] Phone-width (360 px) screenshots of any changed screen. All checks pass.

## Out of scope

- The challenge question (task 0009).
- Any other use of the AI.

## Notes / assumptions

Depends on 0009, which adds `LanguageModel`, the Claude adapter and the AI settings.

### Decide first (ask Jake, each with a recommended answer)

1. When is the AI asked? Today the check runs on each typing pause and each Continue. Asking the AI each time
   costs money and adds a wait; asking once per hazard on Continue is cheaper but slower to show.
2. How long does the phone wait for the AI before the word rule decides? Today the check answers at once.
3. What does the AI send back: only "vague or not", or also a reason or a better example in the worker's terms?
   (A suggested rewording risks putting words in the worker's mouth, against T1.)
4. Is the AI's answer remembered for the same words, so retyping or reopening doesn't ask again?
5. Does the AI judge every hazard, or only one linked to a Yes, as T6 does now?
6. What does it cost per Take 5, and does it change which model is used (a cheaper one may be good enough here)?
7. With no signal the word rule decides. Should the worker be told the check was simpler?
