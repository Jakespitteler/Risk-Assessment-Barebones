---
id: 0013
title: A glossary of spec terms, and a test that every spec rule has a test
status: review
owner: claude
branch: claude/funny-ptolemy-7u9m8v (PR #51), then claude/0013-glossary-code-names for the glossary-names check
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
- [x] The rule test also fails when a test names a rule number the spec no longer defines.
- [x] A test fails when a worked example in the spec has no test named by its number. A test named for a run of
  examples covers only those its cases list.
- [x] A test checks each code name in the glossary against the code, back end and front end
  (`backend/tests/test_glossary_names.py`, in its own stacked pull request, `claude/0013-glossary-code-names`).
- [x] All checks pass.

## Out of scope

- A graph database, or a formal ontology with its own tools.
- Renaming code to match the glossary. Jake chose to keep both names (see below).

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

### Jake's answers (2026-11-19)

Asked on pull request #51's review, each with Claude's recommendation. Jake took every recommendation except
the fifth, where Claude had recommended trusting a run test's name.

1. **Fail on old rule numbers?** Yes. `test_no_test_names_a_rule_the_spec_no_longer_has` fails on a rule number
   that a test names and the spec doesn't define. A rule number is one of the spec's rule letters (R, V, T, C, K
   today) and a number, so decisions (D6) and features (F3) are never caught.
2. **Check that every worked example has a test named by its number?** Yes. `backend/tests/test_spec_examples.py`
   reads the 87 numbered rows under "Worked examples" and fails with any number no back-end test covers.
3. **Check the glossary's code names against the code?** Yes, back end and front end, in its own pull request,
   stacked after task 0029's, to keep this one small. `backend/tests/test_glossary_names.py` reads the code
   rather than running it. A back-end name is a class, function or constant, a class's own field, method or
   enum member written with its class (`Hazard.covers`, `Answer.YES`), a function's parameter
   (`submission_id`), or a file (`fix.py`). A front-end name is a file under `frontend/src` (not a test file), a
   name a file exports, or a field of a schema in the generated API types. A name the check can't see, such as
   an attribute set in `__init__` or an inherited member, would be reported missing; none is in the glossary.
4. **What counts as a test naming a rule?** A back-end test's docstring, or the name of a front-end `it(...)` or
   `test(...)`. Front-end names must count, because T1 and K1 can only be tested in the front end. Comments,
   file-level docstrings, `describe` names and ranges such as "C1 to C6" don't count, so each rule points to a
   real test. The same goes for the old-rule check, so an old number left in a comment isn't caught.
5. **May a test named for a run of examples (`test_example_2_to_10_...`) cover them by its name alone?** No: it
   covers only the examples its cases list, as a `pytest.param` id or an `ids=` entry such as `test_example_3`
   or `example_50_one_word`, and the check fails on a run test that leaves one out. One test,
   `test_examples_50_and_51_...` in `tests/services/test_challenge.py`, became two listed cases.
6. **The name mismatches below?** Keep both names. The glossary maps each spec word to its code name, and
   nothing is renamed.

### How the checks work

- **Rules:** a rule is a bold numbered definition under the spec's rule headings. The test pins the exact list of
  24, so a change to the spec's layout can't make it pass with nothing; a task that adds a rule adds it to that
  list as well as naming it in a test. The test's own file is left out, since it names rules only as examples.
- **Worked examples:** only back-end tests count, since every example is a back-end test today. A test covers an
  example by its name, and a run test also by its case ids: only `pytest.param(..., id=...)` and
  `parametrize(..., ids=[...])` (a list or a tuple) are read, never a case's values or an `ids` kept in a variable.
  The test pins examples 1 to 87 for the same reason as the rules. A test marked to be skipped would still count;
  none is.
- **Old rule numbers** are one of the spec's current rule letters and a number. If every rule with one letter
  left the spec, a test still naming one of them wouldn't be caught; the pinned list of 24 would still fail.

### Name mismatches (decided: keep both)

Where the spec's word and the code's name differ. Jake chose on 2026-11-19 to keep both; the glossary maps them:

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
