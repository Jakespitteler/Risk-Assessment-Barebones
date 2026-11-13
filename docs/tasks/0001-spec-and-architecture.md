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
- Everything is a draft until Jake answers the eight decisions in the spec's "Decisions waiting on Jake" table.
  Each was written up on Claude's recommended option so there is something concrete to react to. When a
  decision is made: update the spec, remove its row, and remove the matching "proposed" markers in the spec,
  `architecture.md`, `decisions.md` and the AGENTS.md stack line.
- The description this was built from: the project brief (make the Take 5 as good as possible, make people
  think about the real risk, a back end Jake fully understands) and the Take 5 feature of the original
  Risk-Assessment app. The card's questions, the likelihood and consequence tables and the matrix are copied
  from that app's `src/domain/take5/`.
- The scoring examples 1 to 10 and every matrix cell in the spec were checked by script against the original
  app's matrix.
- New compared with the original app, so look hardest at these: rating each hazard before and after controls
  (R4, R6), the worker picking a kind for each control, the thinking rules T1 to T4, and "every Take 5 has at
  least one hazard".
- The branch is not named `claude/0001-spec-and-architecture` as AGENTS.md asks, because the Claude session
  that did this work could only push to the branch it was given.
- This PR also adds the scaffold itself (AGENTS.md, CLAUDE.md, the docs templates, tasks 0001 and 0002, the PR
  template, the subagents). It existed only on Jake's computer and had not been pushed.
- Task 0002 says its stack commands are still to be filled in; nothing in it was changed here.
