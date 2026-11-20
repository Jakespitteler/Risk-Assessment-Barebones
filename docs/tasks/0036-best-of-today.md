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

Questions for Jake, each with Claude's recommendation. Put to him on 2026-11-20 when the task started.

1. **What makes one the best?** Recommended: the rules shortlist up to 5 finished Take 5s with no thought gaps
   (W2 to W5), riskiest job first, then the most time taken. The AI picks one of them and writes one line saying
   what was good about it, never seeing names. With no AI, or when it fails, the rules' first pick wins, with a
   rule line. A low-risk job with nothing to think about doesn't win just for being safe, and the AI can tell
   specific answers from long stock ones, which the rules can't.
2. **One, or a few?** Recommended: one.
3. **Where does it show?** Recommended: a "Best of today" card on the "Worst of today" page, under the heading and
   above the worst list, with the same look as a ranked Take 5 but a green box for its line. The page's link and
   heading stay "Worst of today", as fixing things comes first.
4. **"See how long it takes."** Recommended: the card says how long the best one took, and the typical (median)
   time of today's finished Take 5s beside it, such as "Took 9 minutes. Today's typical Take 5 took 3."
5. **When none qualifies?** Recommended: the card says "No Take 5 today was free of signs of a rushed one." so the
   absence is itself a message.
6. **Does the worker hear about it?** Recommended: not in this task; there is no sign-in to reach them by.
7. **Is it saved?** Recommended: no, worked out with the ranking and remembered with it until a Take 5 is added
   or finished, as D95 does for the worst.

## Acceptance criteria

Written once Jake has answered the questions above.

## Out of scope

- Telling the worker, or any leaderboard.

## Notes / assumptions

Added by Claude on 2026-11-20 from Jake's list of things to investigate. Builds on `domain/take5/ranking.py` and
`services/ranking.py` from task 0032.
