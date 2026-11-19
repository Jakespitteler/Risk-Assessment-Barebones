---
id: 0031
title: Make every screen work well on a desktop as well as a phone
status: todo
owner:
branch:
---

## Goal

The goal (spec, decision D65) says a Take 5 works on a phone or a desktop. Today every screen is built for a
360 px phone and simply stretches on a wide screen. Reviewing scanned cards and the worst Take 5s of the day
(tasks 0032 and 0033) is desk work, so a desktop layout should come first. Simple: no new library.

## Decide first

Questions for Jake, each with Claude's recommendation. Answered when the task starts.

1. **How wide may a screen get?** (a) Keep each screen one column, capped at a comfortable reading width (about
   720 px) and centred, so it looks deliberate rather than stretched. (b) Use the width: two columns on wide
   screens, for example the hazard list beside the hazard being edited. Recommended: (a). It is the simplest
   change that looks right, keeps one layout to test, and leaves two columns for screens that need them, such
   as 0033's photo beside its filled-in card.
2. **Keyboard and mouse.** Enter already continues (task 0020). Should anything else change for a mouse, such as
   hover states on buttons? Recommended: hover and focus styles only, from the existing components.
3. **Which widths are tested?** Recommended: the existing 360 px Playwright runs, plus one 1280 px run of the main
   flow with a screenshot of each screen.

## Acceptance criteria

These follow the recommendations; they change with Jake's answers.

- [ ] At 1280 px wide every screen is one centred column no wider than the agreed width, and nothing stretches
  across the screen.
- [ ] Buttons and links show hover and focus states.
- [ ] Phone layouts at 360 px are unchanged.
- [ ] A Playwright run of the main flow at 1280 px saves a screenshot of each screen.
- [ ] `docs/spec.md` states the desktop acceptance criterion beside the 360 px one.
- [ ] All checks pass.

## Out of scope

- New screens, and the review screens of tasks 0032 and 0033.
- Dark mode (task 0024, another agent's).

## Notes / assumptions

Added by Claude on 2026-11-19 in task 0030, from the goal Jake agreed that day.
