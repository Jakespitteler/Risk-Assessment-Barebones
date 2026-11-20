---
id: 0038
title: Investigate a heat map of high-risk areas, and how area relates to the data
status: done
owner: claude
branch: claude/0038-risk-by-area
---

## Goal

Jake asked on 2026-11-20 for a heat map of high-risk areas from the location each Take 5 gives, and to explore
how the area relates to the rest of the data (which hazards, ratings and thought gaps come up where).

## Decide first

Questions to investigate with Jake when it starts.

1. **Where does the location come from?** Today it is free text the worker types ("Light vehicle workshop"), so
   the same place has many spellings. Options: a site's fixed list of areas, the phone's GPS (needs permission,
   and a mine site may have poor signal), or the AI grouping the typed names.
2. **What is the map drawn on?** A site plan image, a real map, or a simple ranked list of areas first.
3. **What makes an area hot?** The highest before-controls scores, how many Take 5s say "Don't start yet",
   thought gaps (task 0032's W2 to W5), or later, incidents.
4. **Which relationships matter most** to a safety person, and over what time span?

Jake's answers (2026-11-21): "go with all your recommendations".

1. The location as typed, grouped ignoring capitals, spaces and punctuation (A1, D111). No data model change.
2. A ranked list of areas, each with a bar, first (D112). A site plan or real map later.
3. High-risk Take 5s (a hazard needing a JHA before controls, R3), then "Don't start yet", then thought gaps
   (A3, A4, D113). Incidents aren't recorded yet.
4. The hazard questions answered Yes most often in each area, over the last 30 days (A2, A5, D114, D115).
   How things change over time is task 0039's.

## Acceptance criteria

- [x] The saved list links to "Risk by area" once anything is saved.
- [x] The page lists every area with a Take 5 in the last 30 days, hottest first, by A1 to A4.
- [x] Each area shows its high-risk count out of its Take 5s, a bar, its highest risk, "Don't start yet", thought
  gaps and up to 3 most common Yes answers (A5).
- [x] Tests cover each worked example (119 to 130); all checks pass; screenshots at 360 px, light and dark.

## Out of scope

- A fixed list of areas, the phone's GPS, an AI grouping the names, or a drawn map (in spec "Planned for later").
- Incidents, and trends over time (task 0039).

## Notes / assumptions

Added by Claude on 2026-11-20 from Jake's list of things to investigate. Built by Claude on 2026-11-21.
Assumptions:

- Two spellings that differ by more than capitals, spaces and punctuation ("LV workshop" and "Light vehicle
  workshop") are two areas. A fixed list of areas would fix that, and needs Jake's approval as a data model change.
- The 30 days are 29 days of 24 hours back from the phone's midnight. In a state with daylight saving, for
  29 days after a clock change the start is an hour off midnight. Sending the phone's named time zone would fix
  it, a change to the API left for later.
- A location with only punctuation (" - ") passes the job page but can't be placed, so it is left out, and the
  empty page says "No Take 5s with a location in the last 30 days."
- No AI: every number can be checked by hand, and the page costs nothing to open (D116).
- Each Take 5 is judged on its own card's JHA threshold, so a card with another matrix still works.
- The bar is drawn beside the hottest area's high-risk count, and only repeats the words, so it is hidden from
  screen readers.
