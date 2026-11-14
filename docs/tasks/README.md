# Order of work

Task numbers are IDs, not the order to do them in. Do the `todo` tasks in this order unless the human says
otherwise. Each task file's frontmatter holds its status; this page holds only the order and why.

Recommended by Claude on 2026-11-13, agreed by Jake the same day. Tasks 0015 to 0019 added by Claude on
2026-11-14; Jake can move them.

1. **0017, one parameter per line.** Before more code is written, so less code has to be reformatted.
2. **0016, shared test set-up.** Before 0005, so the tests 0005 to 0008 add use it from the start.
3. **0005, the card's questions.** Depends on 0004.
4. **0006, thinking rules.** Depends on 0005.
5. **0018, choose a database library or not.** Before 0007, the first new query, so storage changes before more
   code depends on it.
6. **0007, saved Take 5s.** Depends on 0004 only, so it can swap with 0005 or 0006.
7. **0019, back out of a Take 5 and keep drafts.** Jake asked for it on 2026-11-14. After 0007, so a list of
   drafts can sit beside the list of saved Take 5s. Jake answers its "Decide first" questions before it starts.
8. **0008, the challenge question.** Depends on 0005.
9. **0009, the first AI provider.** Depends on 0008.
10. **0013, glossary and rule tracing.** Last, because its test fails for any spec rule with no test yet, and
    most of those rules arrive in 0005 to 0008.

Task 0020 (Enter does what Continue does) is a small change Jake asked for while testing, done outside this
order.

When a task is added, or the human changes the order, update this list in the same pull request.
