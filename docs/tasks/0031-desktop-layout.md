---
id: 0031
title: Prove the main screens work on a desktop, with a test at 1280 px
status: todo
owner:
branch:
---

## Goal

The goal (spec, decision D65) says a Take 5 works on a phone or a desktop. Claude checked on 2026-11-19 at 1280 px:
nothing stretches. The five screens built on `Screen.tsx` sit in one centred column 672 px wide, and the old
`/rate-risk` screen in its own centred 448 px column. Hover and focus are uneven, for example: buttons made with
`Button.tsx`, hazard links and saved-list cards change on hover; the step bar, the header's "Saved Take 5s", "Open
it", the saved list's "Start a new Take 5" and the fix and kept-draft links have a focus style but no hover; Undo's
close button, the result's "Start a new Take 5", the save problem's "Open the saved Take 5" and `/rate-risk`'s "Try
again" have neither; and the answer and rating choices have focus but no hover (question 3). So no layout change is
needed. This task proves it and keeps it true: one whole-app test at desktop width, and a desktop line in the spec.
The review screens of tasks 0032 and 0033 are designed for desktop inside those tasks (Jake, 2026-11-19).

## Decide first

Questions for Jake, each with Claude's recommendation. Answered when the task starts.

1. **Which flow does the desktop test run?** Recommended: the main flow, from a new Take 5 to its saved result,
   then the saved list, with a screenshot of each screen at 1280 by 800, saved beside the phone screenshots.
2. **What does the test check besides screenshots?** Recommended: that no page scrolls sideways and the column is
   no wider than the screen, the same checks the phone tests make at 360 px.
3. **Hover and focus on everything a person can click?** Claude first said every button and link had both; two
   reviews found the gaps listed above. Recommended: give every link, button and answer or rating choice the
   same hover and focus styles as `Button.tsx` and the saved-list cards, a few class names each, since a mouse
   user expects them.

## Acceptance criteria

These follow the recommendations; they change with Jake's answers.

- [ ] A Playwright run of the main flow and the saved list at 1280 px saves a screenshot of each screen and checks
  nothing scrolls sideways.
- [ ] Every link, button and answer or rating choice changes on hover and shows a focus style of the app's own.
- [ ] `docs/spec.md` states the desktop acceptance criterion beside the 360 px one.
- [ ] No screen's layout changes beyond those hover and focus styles.
- [ ] All checks pass.

## Out of scope

- Layout changes, two columns, and the review screens of tasks 0032 and 0033.
- Dark mode (task 0024, another agent's).

## Notes / assumptions

Added by Claude on 2026-11-19 in task 0030. First written as a layout task on the belief that screens stretch
on a desktop; the review of task 0030 found they don't, and Jake chose to shrink it to this test.
