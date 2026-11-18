---
id: 0025
title: Control 1 is open, and typing goes straight into the text box
status: in-progress
owner: claude
branch: claude/project-thread-axb1g9
---

## Goal

Jake, 2026-11-18, looking at the "What will stop it?" page with "No controls listed yet": "this page should have
control 1 open by default. Throughout the app, you should be able to start typing without clicking anything and it
should start typing in the box, only do where intuitively feels right". Fewer clicks before the worker writes in
their own words, without the app writing anything for them.

## Acceptance criteria

- [ ] A hazard with no controls opens its controls page with control 1 already open and empty. Nothing is added
  to the draft until the worker types in it or picks its kind, so a hazard can still have no controls.
- [ ] While control 1 is that empty box, not yet added, it has no Remove button and "Add a control" is hidden, as
  pressing it would only add the box already showing.
- [ ] On a computer, a page that opens with an empty text box puts the cursor in the first one, so typing goes
  straight in: the job page (your name, or the job when the name is remembered), the hazard list and the
  controls page. A page with no empty box, or only answers to pick, focuses the heading as before.
- [ ] On a phone, pages open with the heading focused as before, so the keyboard doesn't cover the page unasked
  (Jake's decision, below).
- [ ] "Add a control" and "Add another hazard" put the cursor in the new box, on a phone too.
- [ ] Opening a page to fix a gap still focuses the first gap; "Add a hazard" on the hazard check still focuses
  the new hazard.
- [ ] Tests cover each of these. Checked in the running app at 360 px wide, with screenshots.

## Out of scope

- The challenge question's answer box (task 0008). When it is built, its box should take the cursor in the same
  way.
- An empty hazard list. The list always starts with hazard 1 open; removing every hazard leaves "Add another
  hazard", as now.

## Decision

Claude asked Jake on 2026-11-18 whether the cursor should go into the box on phones too, or only on computers.
Claude recommended computers only: on Android the keyboard pops up as each page opens and covers about half of a
360 px screen, pushing the heading and the hazard being assessed off it, and iPhones mostly ignore a cursor that
isn't moved by a tap, so phones would behave differently from each other. Jake chose computers only the same day.

## Notes / assumptions

- "A computer" means the main pointer is a mouse or trackpad (the CSS media query `pointer: fine`). A tablet with
  a keyboard but no mouse counts as a phone.
- When the cursor goes into a box, a screen reader reads that box's label instead of the page heading.
- Removing the only control leaves an empty control 1 open, not yet added, with Undo, as removing any control does.
- The branch is `claude/project-thread-axb1g9`, the name the cloud thread is given. It is stacked on task 0024's
  pull request (#38).
