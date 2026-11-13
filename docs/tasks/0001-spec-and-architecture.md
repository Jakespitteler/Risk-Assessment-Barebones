---
id: 0001
title: Write the spec and architecture
status: review
owner: claude
branch: claude/project-thread-ih4nvm
---

## Goal
Turn the human's description of the app into docs/spec.md and docs/architecture.md, and choose the stack. This is the highest-leverage task in the project: use the strongest model available and ask the human questions rather than guessing.

## Acceptance criteria
- [x] docs/spec.md has purpose, users/roles, core workflow, risk model, at least 5 worked scoring examples including boundaries, features with acceptance criteria, and out-of-scope.
- [x] docs/architecture.md has the stack, structure, data model, boundaries and testing strategy.
- [x] Stack choice recorded in docs/decisions.md with rationale.
- [x] AGENTS.md "Stack" line updated.
- [x] Follow-up feature tasks created in docs/tasks/ (one per vertical slice).
- [ ] Human has approved the spec.

## Notes / assumptions
- Jake made all twelve product decisions in chat on 2026-11-13; they are listed in the spec under "Decisions
  made". D1 with an AI challenge question added (which also settles D3), D5 as a Python API with a separate
  JavaScript front end, and the rest as Claude recommended. He asked for current, well-established tools that
  can be swapped without much trouble; the library list in `architecture.md` was picked on that brief.
- The last acceptance criterion, "Human has approved the spec", is met when Jake merges this PR. Whoever merges
  it should tick that box and set `status: done` in the same merge, or in the first commit of the next task.
- The description this was built from: the project brief (make the Take 5 as good as possible, make people
  think about the real risk, a back end Jake fully understands) and the Take 5 feature of the original
  Risk-Assessment app. The card's questions, the likelihood and consequence tables and the matrix are copied
  from that app's `src/domain/take5/`.
- The scoring examples 1 to 10 and every matrix cell in the spec were checked by script against the original
  app's matrix.
- New compared with the original app, so look hardest at these: rating each hazard before and after controls
  (R4, R6), the worker picking a kind for each control, the thinking rules T1 to T4, "every Take 5 has at least
  one hazard", and the challenge question with its fallback (C1 to C6).
- The branch is not named `claude/0001-spec-and-architecture` as AGENTS.md asks, because the Claude session
  that did this work could only push to the branch it was given.
- This PR also adds the scaffold itself (AGENTS.md, CLAUDE.md, the docs templates, tasks 0001 and 0002, the PR
  template, the subagents). It existed only on Jake's computer and had not been pushed.
- Task 0002 says its stack commands are still to be filled in; nothing in it was changed here.
