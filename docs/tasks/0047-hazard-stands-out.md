---
id: 0047
title: The hazard being assessed stands out
status: review
owner: claude
branch: claude/project-thread-e1w0ww
---

## Goal

Jake, 2026-11-25: on the Assess step, "it's not super obvious at a glance what hazard I am making the control
for". The hazard sat as plain body text under the big stage heading ("Before any controls"), so a worker could
rate or control without noticing which hazard it was. Make the hazard obvious on the before, controls and after
pages, with the smallest change.

## Decide first

Three options were mocked up at phone width (`hazard-heading-options.png` in the project files): A, the hazard as
the heading; B, the hazard in a labelled card; C, a bold "Hazard:" label before the line. Claude recommended B
and started on it while Jake chose. Recorded as spec D134.

## Acceptance criteria

- [x] On the before, controls and after pages, the hazard shows in its own card, labelled "Hazard N of M", set
  apart from the page's text, in light and dark.
- [x] The stage heading stays the page's heading and still takes the focus.
- [x] Long hazards wrap inside the card at 360 px; nothing else on the page moves or changes.
- [x] Tests cover the card's label and text; screenshots in light and dark, on a phone and a desktop.

## Out of scope

- The Review page and the result, which already list each hazard under its own heading.

## Notes / assumptions

- "Hazard N of M" moves from the line above the heading into the card, so it is said once, next to the hazard.
- Screenshots with a long hazard ("Hit by Hauler or LV when walking around the sampling area.") at 360 px and
  1280 px, light and dark, are in the project files under `task-0047/`. The usual whole-app screenshots
  (`take5-before`, `desktop-controls` and so on) show the card too, and `uv run check.py` passes.
