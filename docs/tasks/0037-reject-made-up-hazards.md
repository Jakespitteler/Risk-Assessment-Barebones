---
id: 0037
title: Investigate refusing made-up hazards and stock wording
status: in-progress
owner: claude
branch: claude/0037-made-up-hazards
---

## Goal

Jake asked on 2026-11-20 to look at rejecting hazards that are made up or written in poor stock wording, the
same few words anyone could type for any job. Today the vague-hazard nudge (T6) only asks the worker to say more,
and the ranking (task 0032) only counts it against them afterwards.

## Decide first

Questions for Jake, each with Claude's recommendation. Put to him on 2026-11-20 when the task started.

1. **Refuse, or push back harder?** Recommended: push back harder, never refuse. A worker on site must always be
   able to finish (spec goal: "A worker can always finish a Take 5 without it"), and the AI will sometimes be
   wrong. The nudge stays, "Keep it as it is" stays, but keeping a flagged hazard is recorded and counts as a
   thought gap in today's review (W2 to W5 gain one), so the safety person sees it.
2. **How is "made up" told apart?** Recommended: the AI judges whether each hazard fits the job and where it is
   done ("Falling from height" for "Answer emails at my desk" doesn't). Copied from the worker's last Take 5 is
   left out: with no sign-in the app can't tell one worker's Take 5s from another's reliably.
3. **What counts as stock wording?** Recommended: the AI's judgement: words that would fit any job ("Slips, trips
   and falls in the work area"), not a fixed list, which would always be out of date. With no AI, T6's word rule
   still catches the short ones.
4. **How does it fit "own words first" and T6?** Recommended: it is part of T6, in the same nudge and the same
   one AI call (the quick model, 5 seconds). The AI's answer grows from "vague" or "specific" to also "stock" or
   "doesn't fit the job", and the nudge's words change to match: "This could be written about any job. What is it
   about this job?" and "This doesn't seem to fit the job. Is it right?". Own words still come first: the AI
   never suggests a hazard.
5. **Is a kept flagged hazard saved?** Recommended: yes, each hazard keeps what the AI said and that the worker
   kept it, so the review can count it. This changes the data model, so it needs Jake's approval. Without it,
   the review can't know.
6. **Does the review re-judge older Take 5s?** Recommended: no. Only Take 5s saved after this task carry the
   flag; older ones are judged as today.

## Acceptance criteria

Written once Jake has answered the questions above.

## Out of scope

- To be settled when it starts.

## Notes / assumptions

Added by Claude on 2026-11-20 from Jake's list of things to investigate.
