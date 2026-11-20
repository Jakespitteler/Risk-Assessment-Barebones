---
id: 0036
title: Find the best Take 5 of the day as well as the worst
status: in-progress
owner: claude
branch: claude/0036-best-of-today
---

## Goal

Jake asked on 2026-11-20 for this to come as soon as "worst of today" (task 0032) is in. Beside the worst Take 5s,
show the best one of the day: a careful, specific Take 5 that took real time. It gives the safety person something
good to point at, not only things to fix, and shows how long a good Take 5 takes.

## Decide first

Questions for Jake, each with Claude's first thought. Answered when the task starts.

1. **What makes one the best?** First thought: the reverse of task 0032's score among finished Take 5s: no thought
   gaps (W2 to W5), then the most time taken, with the AI choosing among the top few as it does for the worst.
   A low-risk job with nothing to think about shouldn't win just for being safe.
2. **One, or a few?** First thought: one, with its line saying why it is good.
3. **Where does it show?** First thought: at the top or bottom of the "Worst of today" page, so one AI call covers
   both; or its own link on the saved list.
4. **"See how long it takes":** show the time the best one took, and maybe the day's typical time beside it?
5. **Does the worker hear about it?** Praise could make the app more worth using (spec goal), but there is no
   sign-in to reach them by. First thought: not in this task.

## Acceptance criteria

Written once Jake has answered the questions above.

## Out of scope

- Telling the worker, or any leaderboard.

## Notes / assumptions

Added by Claude on 2026-11-20 from Jake's list of things to investigate. Builds on `domain/take5/ranking.py` and
`services/ranking.py` from task 0032.
