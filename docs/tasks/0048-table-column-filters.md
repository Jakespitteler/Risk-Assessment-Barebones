---
id: 0048
title: Filter the Take 5 table's columns, with a Clear filters button
status: in-progress
owner: claude
branch: claude/project-thread-lva1yr (stacked on #88)
---

## Goal

Jake, 2026-11-25: "With the csvs also let me filter on the columns and have other filters above like how you have
it. Have a button to clear filters." On the All Take 5s page from task 0043, each column gets its own filter, the
filters that aren't a column stay above the table, and one button turns every filter off.

## Acceptance criteria

- [ ] A row under the table's headings filters importance (at least), job, verdict, highest risk (band), thought
  gaps, worker and location (area); words, dates, weekday, time of day and from paper stay above (spec E6).
- [ ] The back end does every column filter, so the CSV holds the rows shown, and the filters are kept in the
  page's address.
- [ ] "Clear filters" is always beside the count, outside the folded filters, and turns every filter off,
  including the typed ones.
- [ ] Worked examples 151 to 154 in the spec, with tests; Vitest and Playwright tests at 360 px and 1280 px,
  light and dark, with screenshots.

## Out of scope

- Sorting by a column (the table stays most important first, E2).
- A filter on the started column: the date range above covers it.

## Notes / assumptions

Added by Claude on 2026-11-25. The other agent's 0043 PRs (#87, #88) had no column filters yet; they clashed with
main after 0044 and 0045 merged, so Claude merged main into both branches (no rewrite) before stacking this.

Jake chose the layout (D135) on 2026-11-25: a filter row under the headings, with verdict, risk band and area
moved into their columns. For Jake to approve (Claude, 2026-11-25): what each column filters by (D136) and where
Clear filters sits (D137).
