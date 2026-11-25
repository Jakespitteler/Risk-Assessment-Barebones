---
id: 0039
title: Investigate how time of year, week and day relate to hazards and incidents
status: todo
owner:
branch:
---

## Goal

Jake asked on 2026-11-20 to explore how the time of year, the day of the week and the time of day relate to the
hazards in Take 5s, and to incidents. For example: more heat hazards in summer, rushed Take 5s at the end of a
shift, or riskier jobs on a Monday.

## Decide first

Questions to investigate with Jake when it starts.

**Jake's answers, 2026-11-23:**

- 1: Take 5s alone for now; public incidents may be added later.
- 3: plain sentences on their own page, "Patterns over time", linked from the saved list, with the counts by
  month, weekday and hour beneath. Fixed rules, no AI.
- 4: the clock hour where the Take 5 was started, not the hour into a shift.

Jake then asked for a table of saved Take 5s with filters and CSV export first (task 0043, 2026-11-23). This task
waits, and will read that table's columns (month, weekday and time of day in four 6-hour blocks). Still to settle
when it starts: which signs, when a pattern is worth a sentence, and which Take 5s count (Claude's
recommendations are in the closed draft pull request #86's thread).

1. **Where do incidents come from?** The app has none. Options: a company's incident export, the publicly reported
   WA incidents (`docs/ideas.md`, "Compare with past Take 5s and public incidents"), or Take 5s alone at first.
2. **How much data is enough?** A season needs months of Take 5s; sample data could prove the page meanwhile.
3. **What does a person see?** Charts by month, weekday and hour, or plain sentences such as "Rushed Take 5s
   double after 4 pm".
4. **Shift times:** a mine works day and night shifts, so "time of day" may mean the hour of the shift.

## Acceptance criteria

Written once Jake has answered the questions above.

## Out of scope

- To be settled when it starts.

## Notes / assumptions

Added by Claude on 2026-11-20 from Jake's list of things to investigate. Saved Take 5s already keep when they
were started and saved (K3).
