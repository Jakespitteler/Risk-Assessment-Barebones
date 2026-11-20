---
id: 0031
title: Prove the main screens work on a desktop, with a test at 1280 px and even hover and focus
status: in-progress
owner: claude
branch: claude/0031-desktop-test
---

## Goal

The goal (spec, decision D65) says a Take 5 works on a phone or a desktop. Claude checked on 2026-11-19 at 1280 px:
nothing stretches. The five screens built on `Screen.tsx` sit in one centred column 672 px wide, and the old
`/rate-risk` screen in its own centred 448 px column. So no layout change is needed. This task proves it and keeps
it true: one whole-app test at desktop width and a desktop line in the spec, plus, if Jake agrees, hover and focus
styles where they're missing (question 3). The review screens of tasks 0032 and 0033 are designed for desktop
inside those tasks (Jake, 2026-11-19).

Hover and focus are uneven: some things a person can click change on hover and have the app's own focus style,
others have only one of the two, and a few have neither and rely on the browser's focus ring. Two reviews of task
0030 found the gaps by reading the code; the task lists them all from the code when it starts.

## Decide first

Questions for Jake, each with Claude's recommendation. Answered when the task starts.

1. **Which flow does the desktop test run?** Recommended: the main flow, from a new Take 5 to its saved result,
   then the saved list, with a screenshot of each screen at 1280 by 800, saved beside the phone screenshots.
2. **What does the test check besides screenshots?** Recommended: that no page scrolls sideways and the column is
   no wider than the screen, the same checks the phone tests make at 360 px.
3. **Hover and focus on everything a person can click?** Claude first said every button and link had both, which
   was wrong (see above). Recommended: give everything a person can click (links, buttons of every kind, answer
   and rating choices, the "What do … mean?" help) a hover style and the app's own focus style, a few class names
   each, since a mouse user expects them.

## Acceptance criteria

These follow the recommendations; they change with Jake's answers.

- [ ] A Playwright run of the main flow and the saved list at 1280 px saves a screenshot of each screen and checks
  nothing scrolls sideways.
- [ ] Everything a person can click changes on hover and shows a focus style of the app's own.
- [ ] `docs/spec.md` states the desktop acceptance criterion beside the 360 px one.
- [ ] No screen's layout changes beyond those hover and focus styles.
- [ ] All checks pass.

## Out of scope

- Layout changes, two columns, and the review screens of tasks 0032 and 0033.
- Dark mode (task 0024, another agent's).

## Notes / assumptions

Added by Claude on 2026-11-19 in task 0030. First written as a layout task on the belief that screens stretch
on a desktop; the review of task 0030 found they don't, and Jake chose to shrink it to this test.

The gaps, listed from the code on 2026-11-20 when Claude claimed the task (stacked on task 0021). The shared
`Button` gives every button the app's focus outline; its primary and secondary looks also change on hover.

- **Focus but no hover:** the quiet `Button` look (remove, undo-style and "add another" buttons in the form),
  the step bar's steps, the answer and rating choices, and the plain text links ("Saved Take 5s", "New Take 5" on
  the saved list, the fix panel's links and the kept draft's link).
- **Neither, so only the browser's own focus ring:** the undo bar's close "×", the "What do … mean?" help, the old
  `/rate-risk` screen's button, the save problem's link, and the result screen's "New Take 5" links.
