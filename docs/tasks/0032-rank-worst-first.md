---
id: 0032
title: Rank a set of Take 5s worst first, with one line saying why
status: in-progress
owner: claude
branch: claude/0032-rank-worst-first
---

## Goal

The goal (spec, decision D66): any set of Take 5s, a scanned batch or everything from today, can be ranked worst
first, so the weakest are looked at first. "Worst" weighs how risky the job is against how little thought the
answers show, and each gets one line saying why. One ranking job serves both uses; task 0033 reuses it for a
scanned batch. This task builds the job and "worst of the day". Anyone can use it, with no sign-in, and the
ranked page shows each worker's name, as the saved list does (Jake, 2026-11-19). Its screens are designed for a
desktop as well as a phone.

## Decide first

Questions for Jake, each with Claude's recommendation. Answered when the task starts.

1. **Who decides the order: the AI alone, or fixed rules plus the AI?** (a) The app scores each Take 5 by fixed
   rules first (rating, verdict, weak controls, nudged hazards, short challenge answer), and the AI reads the top
   ones to order them and write the one line. (b) The AI reads them all and orders them. Recommended: (a). It
   stays useful without an AI (the fixed score still orders them), costs less, and the fixed part can be tested
   exactly. The AI adds what rules can't see, such as copied or generic answers. If Jake picks (a), a new spec
   decision replaces D66's "one AI ranking" with "one ranking, with the AI ordering the top ones", as D30 replaced
   D15, restating the rest of D66, and the decisions log gets a new entry.
2. **How many are shown?** Recommended: the worst 5, with "Show all" for the rest in order.
3. **Where does it live?** Recommended: a "Worst of today" link on the saved list, opening a page with the ranked
   Take 5s, each with its line and a link to the saved Take 5.
4. **What is "today"?** Recommended: Take 5s filled in since midnight where the phone is, finished or not. For a
   Take 5 made in the app that is its `started_at`, or its `created_at` when it has none (saved before task 0019);
   for a scanned card it would be the time written on the card, if Jake agrees in task 0033, so that a pile of old
   paper cards scanned today isn't counted as today's. Dates are already shown in the phone's time zone; midnight
   on a server in another zone would make "today" start at the wrong hour. The page sends its own midnight with the
   zone, as `started_at` already carries one.
5. **Is the ranking saved?** Recommended: no. It is worked out when the page opens, and remembered only until the
   server restarts, as task 0027's verdicts are. Saving it would change the data model.
6. **What does the AI get?** Recommended: the same as the challenge question (spec C1): the job, where, the
   answers, the hazards with ratings and controls, and the challenge answer. Never the worker's name.

## Acceptance criteria

These follow the recommendations; they change with Jake's answers.

- [ ] A fixed score in `domain/take5/` scores any set of saved Take 5s, and a job in `ai/` orders the worst of
  them and writes each one line saying why. With no AI, or when it fails, the fixed score orders them and the
  line says what the score found.
- [ ] A "Worst of today" page lists today's Take 5s worst first: the worst 5, then "Show all".
- [ ] The worker's name is never sent to the AI.
- [ ] Tests cover the fixed score, the AI's order and lines, the fallback, and the page.
- [ ] The ranked page shows each worker's name beside their Take 5 (decided by Jake, 2026-11-19).
- [ ] `docs/spec.md` gets the ranking's rules, worked examples and a feature section, and its "Users and roles"
  says anyone can rank. `docs/architecture.md` gets the new job and route, and its section on the AI's risks
  covers what the ranking sends and how its text is checked (the paragraph "What the AI is given, and keeping it
  trustworthy").
- [ ] All checks pass.

## Out of scope

- Scanning paper cards (task 0033), which reuses this job.
- Sign-in or a supervisor role.

## Notes / assumptions

Added by Claude on 2026-11-19 in task 0030, from the goal Jake agreed that day.
