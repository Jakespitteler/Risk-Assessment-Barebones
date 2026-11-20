# Order of work

Task numbers are IDs, not the order to do them in. Do the `todo` tasks in this order unless the human says
otherwise. Each task file's frontmatter holds its status; this page holds only the order and why.

Recommended by Claude on 2026-11-13, agreed by Jake the same day. Tasks 0015 to 0020 added by Claude on
2026-11-14, 0021 on 2026-11-15, 0022 on 2026-11-16, 0023 on 2026-11-17, 0024 to 0027 on 2026-11-18, and 0028 to
0033 on 2026-11-19; Jake can move them. Last brought up to date on 2026-11-19, in task 0030's pull request, after
Jake agreed the app's goal (top of `docs/spec.md`). Every task is judged against that goal.

Complete: 0001 to 0020, 0022, 0023, 0025 and 0026. Task 0030 is in review. Task 0027 is merged, but stays `review`
until Jake's measurement of the AI's verdicts is in its pull request, as its last criterion asks. Task 0029 stays
`review` until Jake tries Ctrl+C on Windows. Task 0018 decided to keep the built-in `sqlite3` for now
(`docs/decisions.md`, 2026-11-14), so no task to switch storage is in the order below.

1. **0028, errors obvious in the terminal.** Jake asked for it on 2026-11-19, after a blank page on Windows whose
   error showed only in the browser. It builds on 0029's start script and makes every later task quicker to
   debug. Claude takes it next, and writes Jake's answers into its file when it claims it.
2. **0031, a desktop test.** The goal says phone or desktop. Screens already fit a desktop, so this only adds a
   whole-app test at 1280 px to keep it so. Small.
3. **0032, rank Take 5s worst first.** Works on today's Take 5s with nothing new to enter, and builds the one
   ranking job that 0033 reuses for a scanned batch.
4. **0033, photograph paper cards into Take 5s.** The biggest of the three, and it needs 0032's ranking.

Another agent's: **0024, dark mode**, claimed on 2026-11-19 (pull requests #53 and #55). Don't start it.

Parked, not in the order: **0021, the saved list 50 at a time**, for when the app is hosted for a crew. Jake
parked it on 2026-11-19: "worst of today" (0032) is a better way to look through many Take 5s for now.

When a task is added, or the human changes the order, update this list in the same pull request.
