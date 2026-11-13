@AGENTS.md

## Claude Code only

- Use the `explorer` subagent for codebase searches and file summaries, so file dumps stay out of the main thread.
- Run the `reviewer` subagent on the diff before opening a PR. For trivial diffs (docs, typos) skip it.
- Use plan mode for anything touching more than two files; get the plan approved before editing.
- `/clear` after each task is merged.
- `.claude/settings.json` denies reading secrets and worker data, and runs two hooks from `scripts/claude_hooks/`:
  a guard before each tool call and a formatter after each edit. They work on a computer, not in claude.ai cloud
  threads. If a hook blocks something you need, stop and ask the human; never work around it.
