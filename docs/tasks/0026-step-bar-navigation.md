---
id: 0026
title: Tap the step bar to move around a Take 5
status: done
owner: claude
branch: claude/project-thread-g9d8uh
---

## Goal

Jake asked on 2026-11-18 for the five steps at the top of the form (Job, Think, Hazards, Assess, Review) to work
like a navigation bar. Until now they only showed where the worker was, and the only ways to move were Back and
Continue. A bar that can be tapped makes it quicker to go back and fix something, for example a typo in the job
from the review.

The risk is that a bar becomes a way round the thinking: tapping Review from Job would skip every page Continue
checks. So the bar only goes where the worker has already been, and going forward is checked as Continue is.

## Decided

Jake answered on 2026-11-18: "all your picks" (spec D38 to D43).

1. **Which steps can be tapped?** Any step already reached in this Take 5. Steps not reached yet are grey and
   can't be tapped (D38). Not chosen: back only; every step at any time.
2. **Jumping forward to a step reached before.** This page is checked first, as Continue checks it. A gap keeps
   the worker here, marked; otherwise they jump. The review still checks everything. Going back is never checked,
   as Back isn't (D39).
3. **Where a tap lands.** The step's first page: Hazards opens the list, Assess opens the first hazard's before
   rating (D40). Not chosen: the last page the worker was on in that step.
4. **After going back and adding a hazard.** The bar still remembers how far the worker got, so Review can be
   tapped; the review then sends them to the new hazard's empty ratings (D41). Not chosen: lock the later steps
   again until Continue reaches them.
5. **The look.** A reached step's bar is filled dark like a progress bar. The current step is bold, and its bar
   is the amber of the app's "5" badge. A step not reached yet stays light grey. Each step is a 48 px tall tap
   target. No ticks, because a tick would say "done" when the step may still have a gap (D42). After seeing the
   screenshots on 2026-11-18, Jake asked for the amber bar and for no underline on the step names.
6. **The phone's back gesture** undoes a tap, as it undoes Continue (D43).

## Acceptance criteria

- [x] A step reached in this Take 5 can be tapped and opens that step's first page; a step not reached yet can't.
- [x] Tapping an earlier step sends no check. Tapping a later step checks this page first and stays on a gap,
  with the gap marked and the cursor in it.
- [x] How far the worker got is kept with the draft on the phone, so a reload, Leave and carry on, or Undo after
  throwing it away keeps it. A draft kept before this task counts the page it was left on as reached.
- [x] The steps wait while a check or a save is under way, as Back does.
- [x] The phone's back gesture undoes a tap.
- [x] Each step is at least 48 px high, and the bar fits a 360 px wide phone (screenshots below).
- [x] Tests: `stage.test.ts`, `StepBar.test.tsx`, `Take5Form.test.tsx` and `e2e/step-bar.spec.ts`.
- [x] `docs/spec.md` (core workflow, F2 and decisions D38 to D43) says what the bar does.

## Out of scope

- Nothing else: the bar only moves between pages that already exist.

## Notes / assumptions

- How far the worker got is kept as `furthestStep` beside the page in the phone's stored draft
  (`useTake5Draft.ts`). It is optional, so drafts already on phones still load and the draft version is unchanged.
- A step is counted as reached as soon as any of its pages opens, including from a direct link such as
  `?page=review`. That link already opened the review before this task, and the review checks every answer.
- A fix of a Don't start yet opens on the review, so every step of a fix can be tapped. All its answers are
  copied in, so that is the same as a Take 5 filled in to the end.
- The current step is a button only when the worker is not on its first page, so a tap always goes somewhere.
- Screenshots at 360 px: `frontend/test-results/screenshots/step-bar-*.png` from `npm run test:e2e`.
