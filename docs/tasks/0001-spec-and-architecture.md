---
id: 0001
title: Write the spec and architecture
status: in-progress
owner: claude
branch: claude/project-thread-ih4nvm
---

## Goal
Turn the human's description of the app into docs/spec.md and docs/architecture.md, and choose the stack. This is the highest-leverage task in the project: use the strongest model available and ask the human questions rather than guessing.

## Acceptance criteria
- [ ] docs/spec.md has purpose, users/roles, core workflow, risk model, at least 5 worked scoring examples including boundaries, features with acceptance criteria, and out-of-scope.
- [ ] docs/architecture.md has the stack, structure, data model, boundaries and testing strategy.
- [ ] Stack choice recorded in docs/decisions.md with rationale.
- [ ] AGENTS.md "Stack" line updated.
- [ ] Follow-up feature tasks created in docs/tasks/ (one per vertical slice).
- [ ] Human has approved the spec.

## Notes / assumptions
