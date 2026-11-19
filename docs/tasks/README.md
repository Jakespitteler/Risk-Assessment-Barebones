# Order of work

Task numbers are IDs, not the order to do them in. Do the `todo` tasks in this order unless the human says
otherwise. Each task file's frontmatter holds its status; this page holds only the order and why.

Recommended by Claude on 2026-11-13, agreed by Jake the same day. Tasks 0015 to 0020 added by Claude on
2026-11-14, 0021 on 2026-11-15, 0022 on 2026-11-16, 0023 on 2026-11-17, 0024 to 0027 on 2026-11-18, and 0028 and
0029 on 2026-11-19; Jake can move them. Last brought up to date on 2026-11-19, when Jake chose to do 0024 next.

Complete: 0001 to 0012, 0014 to 0020, 0022, 0023, 0025 and 0026. Task 0018 decided to keep the
built-in `sqlite3` for now (`docs/decisions.md`, 2026-11-14), so no task to switch storage is in the order below.

1. **0027, the AI judges vague hazards.** Jake chose on 2026-11-18 to do it straight after 0009 (spec D55). Built
   on 2026-11-19 (spec D56 to D63); it waits on Jake's measurement, as 0009 did.
2. **0013, glossary and rule tracing.** Last of these, because its test fails for any spec rule with no test yet, and
   most of those rules arrive in 0005 to 0008.
3. **0029, one command to set up, update and start the app, and every command from the repo root.** Jake asked
   for it "soon" on 2026-11-19, after opening the API's address instead of the app's. It depends on no other task.
   Recommended next after 0013; Jake can start it sooner, since it barely overlaps the open pull requests. Its
   questions are answered when it starts.
4. **0028, errors obvious in the terminal.** Jake asked for it on 2026-11-19, after a blank page on Windows whose
   error showed only in the browser. It builds on 0029's start script, so it comes straight after 0029, and it
   makes every later task quicker to debug. Jake can move it. Its questions are answered when it starts.
5. **0024, dark mode.** Jake asked for it on 2026-11-18, and on 2026-11-19 chose to build it now (spec D74),
   while another agent works on 0013, 0029 and 0028. It touches only the front end.
6. **0021, the saved list 50 at a time.** Jake chose it on 2026-11-15, for when the app is hosted for a crew.
   Start it when hosting is planned, wherever that falls in this order.

When a task is added, or the human changes the order, update this list in the same pull request.
