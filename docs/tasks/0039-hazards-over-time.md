---
id: 0039
title: Investigate how time of year, week and day relate to hazards and incidents
status: done
owner: claude
branch: claude/project-thread-wpcou2 (#97)
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

Jake then asked for a table of saved Take 5s with filters and CSV export first (task 0043, 2026-11-23), which is
now merged, and this task reads its rows.

**Jake's answers, 2026-11-26** ("go with your recommendations"):

- Signs: high risk (A3), rushed (W5), any thought gap, "Don't start yet", and a Yes to each hazard question.
- Worth a sentence: at least 5 Take 5s in the group and in the rest, the sign at least 3 times in the group, and at
  least twice the rest's rate; the 5 strongest, each with its numbers. With none, say so, and always say small
  numbers can be chance.
- Which count: every saved Take 5, finished or not, paper cards included, each sign among the Take 5s it can apply
  to.
- Each sentence links to the All Take 5s table filtered to its weekday, time of day or month.

1. **Where do incidents come from?** The app has none. Options: a company's incident export, the publicly reported
   WA incidents (`docs/ideas.md`, "Compare with past Take 5s and public incidents"), or Take 5s alone at first.
2. **How much data is enough?** A season needs months of Take 5s; sample data could prove the page meanwhile.
3. **What does a person see?** Charts by month, weekday and hour, or plain sentences such as "Rushed Take 5s
   double after 4 pm".
4. **Shift times:** a mine works day and night shifts, so "time of day" may mean the hour of the shift.

## Acceptance criteria

- [x] `GET /api/patterns?zone=` returns the sentences worth showing and the counts by month, weekday and time of
  day, worked out from the table's rows by fixed rules (spec S1 to S5); nothing is saved and no AI is used.
- [x] "Patterns over time" at `/patterns`, linked from the saved list beside "All Take 5s", shows each sentence
  with a link to its Take 5s in the table, and the counts beneath; it works at 360 px and 1280 px, light and dark.
- [x] The spec gets rules S1 to S5, F12, decisions D138 to D141 and worked examples 156 to 165, each a test.

## Out of scope

- Public incidents (answer 1): Take 5s only for now.
- The hour into a shift (answer 4) and a statistical test.

## Notes / assumptions

Added by Claude on 2026-11-20 from Jake's list of things to investigate. Saved Take 5s already keep when they
were started and saved (K3).

Assumption (Claude, 2026-11-26): "the rest" needs at least 5 Take 5s too, not only the group, so one Take 5 elsewhere
can't make a pattern look certain. Months are each year apart (November 2026 and November 2027 are two groups), as
the table's month column is, so a month links to the table by a date range.
