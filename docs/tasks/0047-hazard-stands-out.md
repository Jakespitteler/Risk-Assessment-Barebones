---
id: 0047
title: The hazard being assessed stands out
status: in-progress
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
and started on it while Jake chose.

## Acceptance criteria

- [ ] On the before, controls and after pages, the hazard shows in its own card, labelled "Hazard N of M", set
  apart from the page's text, in light and dark.
- [ ] The stage heading stays the page's heading and still takes the focus.
- [ ] Long hazards wrap inside the card at 360 px; nothing else on the page moves or changes.
- [ ] Tests cover the card's label and text; screenshots in light and dark, on a phone and a desktop.

## Out of scope

- The Review page and the result, which already list each hazard under its own heading.

## Notes / assumptions

- "Hazard N of M" moves from the line above the heading into the card, so it is said once, next to the hazard.
