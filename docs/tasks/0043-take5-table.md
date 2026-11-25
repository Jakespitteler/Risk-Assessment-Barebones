---
id: 0043
title: A table of saved Take 5s, with filters and CSV export
status: review
owner: claude
branch: claude/0043-take5-table (#87), claude/0043-table-page (#88)
---

## Goal

Jake, 2026-11-23: the saved Take 5s in a table that can be filtered, and exported as CSV, with importance,
location and anything else useful the app collects within reason. For whoever looks through many Take 5s, on a
desktop or a phone.

## Decide first

**Jake's answers, 2026-11-23:**

- Built now, before task 0039, which waits and later reads this table's columns.
- Importance is the ranking's values (W1): the worst score, the risk band and the fixed rules' line, worked out
  on export, not stored, so no data model change. The AI's reworded lines aren't saved (D95), so they aren't in
  it.
- No job type yet: a search box over the job, location and worker.
- Every stored field in the table and the CSV, worker names included, with filters for search, date range,
  verdict, band, area, weekday, time of day and from paper.
- From 0039: time of day is the clock hour where the Take 5 was started, in four 6-hour blocks, by the clock of
  the phone, or of the checker who scanned it.

## Acceptance criteria

Part 1, the back end:

- [x] `GET /api/take5-table` returns one row per saved Take 5, worst importance first, with every column in the
  spec's "Table and export" section, and the choices each filter offers.
- [x] The filters narrow the rows; `GET /api/take5-table.csv` exports the same rows as CSV, with a cell that
  starts like a formula made safe.
- [x] The spec gets the section's rules and worked examples, and the tests are named by them.

Part 2, the page:

- [x] "All Take 5s" at `/take5-table`, linked from the saved list, shows the table with its filters, kept in the
  URL, and a "Download CSV" link for the same rows; it works at 360 px and 1280 px.

## Out of scope

- A job type, and public incidents (task 0039).
- Saving the AI's ranking lines.

## Notes / assumptions

Added by Claude on 2026-11-23 from Jake's request and answers.

For Jake to approve (Claude, 2026-11-23, found in review): the phone saves its start time in UTC and not its
zone, so the table can't read a Take 5's own clock as Jake's answer asked. It reads a phone's start in the zone of
whoever opens the table, which on one site is the phone's; a paper card keeps the date written on it (E3, D132).
The other way, having the phone send its zone, changes the draft and the data model. Jake chose the proof of
concept's simplest way for paper cards' fixes on 2026-11-21, and this follows the same reasoning.

Noted, not fixed (outside this task): while developing, if the back end is down, Vite's proxy logs the address it
couldn't reach, query included, so a search for a worker's name could show in the terminal. Only on a developer's
computer, and only when the back end is restarting.
