---
id: 0035
title: The "5" logo links to the start page
status: review
owner: claude
branch: claude/0035-logo-link
---

## Goal

Jake, 2026-11-20: "Make the logo a button to start a new take 5. This will be a button for the homepage if we ever
add one." The "5" in the top bar becomes a link to `/`, the start page.

## Acceptance criteria

- [x] The "5" is a link to `/` on every screen built on `Screen.tsx`, named "Take 5 home" for a screen reader.
- [x] It changes under the mouse and shows the app's focus outline (D89).
- [x] Tests: a component test for the link, and a whole-app test that follows it from the saved list.
- [x] `docs/spec.md` F2 and D90.
- [ ] Jake confirms what it does partway through a Take 5 (below).
- [x] All checks pass.

## Out of scope

- A home page of its own.

## Notes / assumptions

- **Assumption, put to Jake on 2026-11-20:** partway through a Take 5 the link doesn't throw the answers away.
  `/` carries on an unfinished Take 5, as it already does, and Leave is still the way to bin one. Named "Take 5
  home" rather than "Start a new Take 5" for that reason, and so it still fits if a home page is added.
- On hover the "5" turns a lighter amber, a new `brand-hover` colour (amber-300 in light and dark), so the slate
  "5" on it stays dark on light.
- A separate reviewer agent checked the diff on 2026-11-20 and found no bugs. It added a whole-app test that the
  "5" partway through a Take 5 carries on with the same answers, and the spec now says "kept draft" (the
  glossary's word) instead of "unfinished", which the glossary keeps for a saved Take 5 awaiting its question.
- Found by the review, not changed: someone who opens the app at the saved list and then presses the "5" (or
  "Start a new Take 5") is taken to their unanswered question, if they have one, because the app only goes back
  to it the first time `/` opens in a tab (D46). That was already so before this task.
