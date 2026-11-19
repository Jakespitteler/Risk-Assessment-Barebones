---
id: 0013
title: A glossary of spec terms, and a test that every spec rule has a test
status: review
owner: claude
branch: claude/funny-ptolemy-7u9m8v
---

## Goal

Agents and people should use one name for one thing, and every rule in the spec should be provably tested. A
short glossary links each spec term to its code name and rule number. A test fails when a rule number in the
spec has no test that names it. This is the light version of the "shared semantic layer" Jake asked about on
2026-11-13: it gives most of the benefit for much less upkeep than a formal ontology.

## Acceptance criteria

- [x] `docs/glossary.md` has one row per term in the spec (for example Take 5, hazard, control, verdict, JHA):
  the term, what it means in a sentence, its name in the back end and the front end, and its rule numbers.
- [x] AGENTS.md links the glossary and says to use its names.
- [x] A back-end test reads `docs/spec.md`, finds every rule number (such as R1, V2, T3, C4), and fails with
  the missing numbers when one is not named in any test's name or docstring.
- [x] The tests that are missing a rule number are named or documented so the new test passes.
- [x] All checks pass.

## Out of scope

- A graph database, or a formal ontology with its own tools.
- Renaming code to match the glossary. Mismatches are listed in this file for Jake to decide.

## Notes / assumptions

Independent of tasks 0010 and 0012. Recommended after tasks 0005 to 0008 (Claude, 2026-11-13): the test fails
for any spec rule with no test, and most rules not yet built (V1, T2 to T4, C1 to C4) arrive in those tasks.
Done earlier, it needs a list of rules not built yet that changes with every task.

### What was built (Claude, 2026-11-19)

- `docs/glossary.md`: one row per spec term, grouped as the spec is, with its back-end and front-end names and
  its rules.
- `backend/tests/test_spec_rules.py`: reads the rule definitions (`- **R1 ...**`) from the spec and checks each
  number is in a test's name or docstring. A second test checks all 24 rules (R1 to R6, V1 to V3, T1 to T6, C1
  to C6, K1 to K3) are read, so a change to how the spec writes them can't make the check pass with nothing.
- Before this task, R1 to R4 and K1 were tested (worked examples 1 to 13, and the draft tests) but no test named
  them. Their docstrings and names now do; no test changed what it checks.

### Assumptions

- **What counts as a test naming a rule.** A back-end test function's own name or docstring, or the name of a
  front-end `it(...)` or `test(...)`. Front-end names count because T1 and K1 are about the screen and the phone,
  so only front-end tests can check them (the spec says so for T1). Module docstrings, comments and ranges such
  as "C1 to C6" don't count, so each rule points to a real test. The new test's own file is left out, since it
  names rules only as examples.
- **What a rule is.** The bold numbered definitions under the spec's rule headings. Decision numbers (D1 ...)
  and feature headings (F1 to F6) are not rules.

### Mismatches for Jake to decide

Not renamed (out of scope). Each is where the spec's word and the code's name differ:

| Spec says | Code says | Note |
| --- | --- | --- |
| where it is | `location` | The spec uses both; the glossary uses "where it is" as the term. |
| think-through question | `QuestionRole.STOP` | Named for what a No does, not the card's heading. |
| hazard question | `QuestionRole.HAZARD` | Matches. The front end's page is `HazardCheckPage`, the spec's "hazard check page". |
| linked to a Yes | `Hazard.covers` | "covers" is the code's only name for a link. |
| Good to go / Don't start yet | `Verdict.can_start` | A true/false, not the words. |
| the template's minimum (words) | `specific_hazard_words` | |
| time limit | `draft_time_limit_minutes` | |
| kept draft | `StoredDraft`, `keptDraft` | Two names in the front end. |
| finished | `finished_at` set | No `finished` flag; a date stands for it. |
