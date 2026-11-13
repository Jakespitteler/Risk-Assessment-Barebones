---
id: 0013
title: A glossary of spec terms, and a test that every spec rule has a test
status: todo
owner:
branch:
---

## Goal

Agents and people should use one name for one thing, and every rule in the spec should be provably tested. A
short glossary links each spec term to its code name and rule number. A test fails when a rule number in the
spec has no test that names it. This is the light version of the "shared semantic layer" Jake asked about on
2026-11-13: it gives most of the benefit for much less upkeep than a formal ontology.

## Acceptance criteria

- [ ] `docs/glossary.md` has one row per term in the spec (for example Take 5, hazard, control, verdict, JHA):
  the term, what it means in a sentence, its name in the back end and the front end, and its rule numbers.
- [ ] AGENTS.md links the glossary and says to use its names.
- [ ] A back-end test reads `docs/spec.md`, finds every rule number (such as R1, V2, T3, C4), and fails with
  the missing numbers when one is not named in any test's name or docstring.
- [ ] The tests that are missing a rule number are named or documented so the new test passes.
- [ ] All checks pass.

## Out of scope

- A graph database, or a formal ontology with its own tools.
- Renaming code to match the glossary. Mismatches are listed in this file for Jake to decide.

## Notes / assumptions

Independent of tasks 0010 and 0012.
