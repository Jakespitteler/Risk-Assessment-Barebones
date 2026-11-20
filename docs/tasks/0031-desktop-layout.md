---
id: 0031
title: Prove every screen works on a desktop, with a test at 1280 px
status: todo
owner:
branch:
---

## Goal

The goal (spec, decision D65) says a Take 5 works on a phone or a desktop. Claude checked on 2026-11-19 at
1280 px: every screen already sits in one centred column about 670 px wide (`Screen.tsx`), buttons and links
have hover and focus states, and nothing stretches. So no layout change is needed. This task only proves it, and
keeps it true: one whole-app test at desktop width, and a desktop line in the spec. The review screens of tasks
0032 and 0033 are designed for desktop inside those tasks (Jake, 2026-11-19).

## Decide first

Questions for Jake, each with Claude's recommendation. Answered when the task starts.

1. **Which flow does the desktop test run?** Recommended: the main flow, from a new Take 5 to its saved result,
   with a screenshot of each screen at 1280 by 800, saved beside the phone screenshots.
2. **What does the test check besides screenshots?** Recommended: that no page scrolls sideways and the column is
   no wider than the screen, the same checks the phone tests make at 360 px.

## Acceptance criteria

These follow the recommendations; they change with Jake's answers.

- [ ] A Playwright run of the main flow at 1280 px saves a screenshot of each screen and checks nothing scrolls
  sideways.
- [ ] `docs/spec.md` states the desktop acceptance criterion beside the 360 px one.
- [ ] No screen's layout changes.
- [ ] All checks pass.

## Out of scope

- Layout changes, two columns, and the review screens of tasks 0032 and 0033.
- Dark mode (task 0024, another agent's).

## Notes / assumptions

Added by Claude on 2026-11-19 in task 0030. First written as a layout task on the belief that screens stretch
on a desktop; the review of task 0030 found they don't, and Jake chose to shrink it to this test.
