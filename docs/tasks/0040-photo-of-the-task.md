---
id: 0040
title: Investigate a photo of the job with the hazards circled
status: todo
owner:
branch:
---

## Goal

Jake asked on 2026-11-20 to look at making the worker take a photo of the job and circle each hazard on it. The
circled photos would later help train or test an AI that spots hazards in photos (`docs/ideas.md`, "Spot hazards
and controls in photos").

## Decide first

Questions to investigate with Jake when it starts.

1. **Forced, or asked for?** Making it required adds time to every Take 5; some sites ban phone cameras in
   places, and some jobs have nothing to photograph.
2. **How is a hazard marked?** Drawing a circle with a finger, then linking it to one of the hazards typed.
3. **Where are photos kept, and for how long?** Photos may show people and site details, so privacy and the
   company's rules on site photos come first. Storing them changes the data model.
4. **Training:** whose model, with what consent, and is a few hundred circled photos enough to be useful, or is
   it better used to test a ready-made model?

## Acceptance criteria

Written once Jake has answered the questions above.

## Out of scope

- Training a model, until enough photos exist.

## Notes / assumptions

Added by Claude on 2026-11-20 from Jake's list of things to investigate. Photos of the job are out of scope in
`docs/spec.md` today.
