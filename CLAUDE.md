@AGENTS.md

## Claude Code only

- Use the `explorer` subagent for codebase searches and file summaries, so file dumps stay out of the main thread.
- Run the `reviewer` subagent on the diff before opening a PR. For trivial diffs (docs, typos) skip it.
- Use plan mode for anything touching more than two files; get the plan approved before editing.
- `/clear` after each task is merged.
