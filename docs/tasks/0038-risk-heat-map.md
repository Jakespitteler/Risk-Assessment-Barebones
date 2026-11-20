---
id: 0038
title: Investigate a heat map of high-risk areas, and how area relates to the data
status: todo
owner:
branch:
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

## Acceptance criteria

Written once Jake has answered the questions above.

## Out of scope

- To be settled when it starts.

## Notes / assumptions

Added by Claude on 2026-11-20 from Jake's list of things to investigate. GPS or a fixed list of areas changes the
data model and needs Jake's approval.
