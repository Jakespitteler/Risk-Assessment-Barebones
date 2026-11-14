# Order of work

Task numbers are IDs, not the order to do them in. Do the `todo` tasks in this order unless the human says
otherwise. Each task file's frontmatter holds its status; this page holds only the order and why.

Recommended by Claude on 2026-11-13, agreed by Jake the same day. Tasks 0015 to 0019 added by Claude on
2026-11-14; Jake can move them.

Tasks 0017, 0016 and 0005 are complete. Task 0006 is implemented in three stacked PRs and awaits review;
finish that review before starting the remaining order below.

1. **0018, choose a database library or not.** Next: before 0007, the first new query, so storage changes before more
   code depends on it.
2. **0007, saved Take 5s.** Depends on 0004, which is complete; follows the database decision in 0018.
3. **0019, back out of a Take 5 and keep drafts.** Jake asked for it on 2026-11-14. After 0007, so a list of
   drafts can sit beside the list of saved Take 5s. Jake answers its "Decide first" questions before it starts.
4. **0008, the challenge question.** Depends on 0005, which is complete.
5. **0009, the first AI provider.** Depends on 0008.
6. **0013, glossary and rule tracing.** Last, because its test fails for any spec rule with no test yet, and
    most of those rules arrive in 0005 to 0008.

Task 0020 (Enter does what Continue does) is a small change Jake asked for while testing, done outside this
order.

When a task is added, or the human changes the order, update this list in the same pull request.
