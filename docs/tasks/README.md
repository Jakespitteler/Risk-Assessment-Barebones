# Order of work

Task numbers are IDs, not the order to do them in. Do the `todo` tasks in this order unless the human says
otherwise. Each task file's frontmatter holds its status; this page holds only the order and why.

Recommended by Claude on 2026-11-13, agreed by Jake the same day. Tasks 0015 to 0020 added by Claude on
2026-11-14, 0021 on 2026-11-15 and 0022 on 2026-11-16; Jake can move them. Last brought up to date on 2026-11-16,
when task 0022 was added.

Complete: 0001 to 0007, 0010 to 0012, 0014 to 0018 and 0020. Task 0018 decided to keep the built-in `sqlite3` for
now (`docs/decisions.md`, 2026-11-14), so no task to switch storage is in the order below.

1. **0019, back out of a Take 5 and keep drafts.** Jake asked for it on 2026-11-14 and answered its questions on
   2026-11-15 (spec D19 to D25). Built on 2026-11-15 and marked done in its pull request; done when Jake merges it.
2. **0022, "It's on my list" on the hazard check page.** Jake asked for it on 2026-11-16. Jake answers its
   "Decide first" questions before it starts. Placed before 0008 so that, if the link between a question and a
   hazard is saved, the challenge question can use it. It doesn't block 0008, so Jake can move it later.
3. **0008, the challenge question.** Depends on 0005, which is complete.
4. **0009, the first AI provider.** Depends on 0008.
5. **0013, glossary and rule tracing.** Last of these, because its test fails for any spec rule with no test yet, and
   most of those rules arrive in 0005 to 0008.
6. **0021, the saved list 50 at a time.** Jake chose it on 2026-11-15, for when the app is hosted for a crew.
   Start it when hosting is planned, wherever that falls in this order.

When a task is added, or the human changes the order, update this list in the same pull request.
