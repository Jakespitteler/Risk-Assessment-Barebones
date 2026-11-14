# Order of work

Task numbers are IDs, not the order to do them in. Do the `todo` tasks in this order unless the human says
otherwise. Each task file's frontmatter holds its status; this page holds only the order and why.

Recommended by Claude on 2026-11-13, agreed by Jake the same day.

1. **0012, review agent in CI.** First, so every later pull request is reviewed by an agent that did not
   write it before Jake sees it. Jake needs to do its one-off setup first (see the task file).
2. **0010, fix a Don't start yet.** Independent of 0005 to 0009, so it can move anywhere in this list.
3. **0005, the card's questions.** Depends on 0004.
4. **0006, thinking rules.** Depends on 0005.
5. **0007, saved Take 5s.** Depends on 0004 only, so it can swap with 0005 or 0006.
6. **0019, back out of a Take 5 and keep drafts.** Jake asked for it on 2026-11-14. After 0007, so a list of
   drafts can sit beside the list of saved Take 5s. Jake answers its "Decide first" questions before it starts.
7. **0008, the challenge question.** Depends on 0005.
8. **0009, the first AI provider.** Depends on 0008.
9. **0013, glossary and rule tracing.** Last, because its test fails for any spec rule with no test yet, and
   most of those rules arrive in 0005 to 0008.

When a task is added, or the human changes the order, update this list in the same pull request.
