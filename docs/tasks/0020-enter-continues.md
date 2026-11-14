---
id: 0020
title: Pressing Enter on a Take 5 page does what Continue does
status: review
owner: claude
branch: claude/project-thread-iodiic
---

## Goal

Jake, 2026-11-14, looking at the job page: "pressing enter on this page after entering the values should be the
same as pressing continue". Each page of the Take 5 form becomes a real form, so Enter in a one-line box runs
the same check and moves on exactly as Continue does.

## Acceptance criteria

- [x] Enter in a one-line box (such as "Where will you do it?") does the same as pressing Continue: the same
  back-end check, the same errors, the same next page.
- [x] Enter does nothing while Continue is disabled (checking or saving).
- [x] Enter never presses Finish on the review: saving the Take 5 still needs the button.
- [x] Back, Add and Remove buttons are not pressed by Enter.
- [x] Enter in a bigger box, such as "What is the job?", starts a new line (Jake's decision, below).
- [x] Tests cover Enter on the job page, and the existing Continue and Finish tests still pass.
- [x] Checked in the running app at 360 px wide; nothing on screen changes.

## Out of scope

- The Rate a risk screen from task 0003.
- Any change to what Continue itself does.

## Decision

Jake, 2026-11-14: Enter in a bigger box (the job, each hazard and each control) starts a new line, as Claude
recommended. So Enter continues from "Your name", "Where will you do it?" and a picked rating, but not on the
hazards or controls pages, where every box is a bigger one.

## Notes / assumptions

- Claude assumed Enter should not press Finish on the review, because saving is the one step that can't be
  taken back by pressing Back. The review has no boxes to type in today. A browser still submits a form with no
  submit button when it has exactly one one-line box, so a later task that adds one box to the review should
  make the form ignore a submit there.
- The branch is `claude/project-thread-iodiic`, the name the cloud thread is given, not `claude/0020-...`.
- Checked in headless Chromium only, not Firefox, Safari or a phone keyboard.
- Enter on a picked rating also continues, because the browser submits a form from a radio button too.
- Enter only presses a Continue that is enabled, so it can't start a second check while one is running.
- jsdom can't press Enter in a form, so the unit test submits the form and the Playwright test presses Enter.
- Task number: PR 16 holds 0015 to 0018 and PR 17 adds 0019, so this is 0020.
- PR 17 (task 0010) also changes `Take5Form.tsx`, in other lines. Whichever merges second needs a small merge.
