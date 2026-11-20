# Order of work

Task numbers are IDs, not the order to do them in. Do the `todo` tasks in this order unless the human says
otherwise. Each task file's frontmatter holds its status; this page holds only the order and why.

Recommended by Claude on 2026-11-13, agreed by Jake the same day. Tasks 0015 to 0020 added by Claude on 2026-11-14,
0021 on 2026-11-15, 0022 on 2026-11-16, 0023 on 2026-11-17, 0024 to 0027 on 2026-11-18, 0028 to 0033 on
2026-11-19, and 0034 to 0040 on 2026-11-20; Jake can move them. Last brought up to date on 2026-11-20, when Jake's
list of things to investigate was added. Task 0030's set it after Jake agreed the app's goal (top of
`docs/spec.md`). Every task is judged against that goal.

Complete: 0001 to 0026, 0030 to 0032 and 0034 to 0037. Jake chose on 2026-11-19 to build 0024 (dark mode) then (spec D79).
Task 0027 is merged, but stays `review` until Jake's measurement of the AI's verdicts is in its pull request, as
its last criterion asks. Task 0029 stays `review` until Jake tries Ctrl+C on Windows. Task 0018 decided to keep the
built-in `sqlite3` for now (`docs/decisions.md`, 2026-11-14), so no task to switch storage is in the order below.

1. **0028, errors obvious in the terminal.** Jake asked for it on 2026-11-19, after a blank page on Windows whose
   error showed only in the browser. It builds on 0029's start script and makes every later task quicker to
   debug. Claude takes it next. Jake's answers are already in its file; its criteria and a decisions log entry
   follow them when it is claimed.
2. **0033, photograph paper cards into Take 5s.** The biggest of these, and it needs 0032's ranking.

Built out of the order:

- **0021, the saved list 50 at a time.** Jake parked it on 2026-11-19, as "worst of today" (0032) is a better
  way to look through many Take 5s for now, then asked for it on 2026-11-20 (spec D80 to D86).
- **0034, keep the app running on Windows when back-end code changes.** A bug Jake hit on 2026-11-20.
- **0035, the "5" logo links to the start page.** Jake asked for it on 2026-11-20.

To investigate when we get to them (Jake, 2026-11-20). Each file holds the questions to settle first; none has
a place in the order yet:

- **0038, a heat map of high-risk areas, and how area relates to the data.**
- **0039, how time of year, week and day relate to hazards and incidents.**
- **0040, a photo of the job with the hazards circled**, later used to train or test an AI.

When a task is added, or the human changes the order, update this list in the same pull request.
