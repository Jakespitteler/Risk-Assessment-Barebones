---
id: 0037
title: Investigate refusing made-up hazards and stock wording
status: done
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

Jake took every recommendation on 2026-11-20, including the data model change (spec T7, W10, D105 to D110,
examples 111 to 118).

- [x] The hazard check's AI can say a hazard is stock or unfit, and the nudge says so in the app's own words; the
  worker is never stopped.
- [x] Each hazard still flagged at submit is saved with its flag; a retry gets the first save's flags; submitting
  sends the AI nothing new.
- [x] Today's review counts a kept flagged hazard as a thought gap, once, and it can't be the best.
- [x] The nudge tells the worker that keeping it shows in today's review.
- [x] Tests cover each worked example; all checks pass.

## Out of scope

- Judging Take 5s saved before this again (D110; Jake's idea of checking the field against new standards is in
  `docs/ideas.md`).
- Spotting a hazard copied from the worker's last Take 5.

## Notes / assumptions

Added by Claude on 2026-11-20 from Jake's list of things to investigate.

Built by Claude on 2026-11-20. Assumptions:

- The flags are the same AI call as T6's, with its instructions now "vague-hazard-2" (one word: specific, vague,
  stock or unfit). With no AI, only T6's word rule applies.
- "Kept" means still nudged when submitted, worked out on the server from the AI's remembered verdicts, so the
  phone holds no rule. A flag counts only if the server showed the worker that flag on the same words, so a
  verdict that came too late to show, or a hazard never checked, saves no flag.
- A flag can be lost in the worker's favour, never added: when the job, location or link changes after the nudge
  was kept (the words the AI judged are different), when the server restarts between the check and submitting,
  or past the 1000 remembered verdicts or shown flags. For a proof of concept this is fine.
- Each nudge in the API reply now carries `flag` (vague, stock or unfit), so the phone can tell them apart.
- A kept hazard under 6 words is counted once, by W2.
