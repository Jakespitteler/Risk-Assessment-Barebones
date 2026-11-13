---
id: 0014
title: Make the repo pass Jake's Australian English spell checker
status: done
owner: claude
branch: claude/project-thread-dohnxr
---

## Goal

Jake checks spelling with the VS Code extension "Australian English - Code Spell Checker" (cspell with the `en-AU`
dictionary). He asked (2026-11-13) for every file to pass it, with legitimate project words added to a dictionary
that both agents share.

## Acceptance criteria

- [x] `cspell.json` sets the language to `en-AU` and uses the project dictionary `.cspell/project-words.txt`.
  VS Code and the command line read the same settings.
- [x] The words that were in `.vscode/settings.json` moved to the project dictionary.
- [x] The spell check command in AGENTS.md finds nothing in any tracked file.
- [x] Real misspellings are fixed. Deliberate non-words (shortened git flags in the guard and its tests, option
  letters in a pattern, a VS Code setting name) are ignored in their own file, not added to the dictionary.
- [x] AGENTS.md gives the command and the rule, so ChatGPT keeps it passing too.
- [x] `scripts/check.py`, and so CI, runs the spell check (Jake chose this on 2026-11-13).

## Out of scope

- Checking the spelling of commit messages and pull request text.

## Notes / assumptions

The repo was already in Australian English. The only real fixes were "pre-selecting" (hyphenated) in the
decisions log, "look-ahead checks" in a guard comment, and the end-to-end screenshot name, now
`take5-do-not-start`. Most findings were library and tool names.

The same pull request holds Claude's review of task 0012 (in that task's file), renames that task's test so the
name says what it proves, sets tasks 0011 and 0012 to `done` (both were merged), and drops 0012 from the order of
work in `docs/tasks/README.md`.

After that review Jake chose (2026-11-14) to pin the CI reviewer to Opus 5.5 with at most 15 turns, and accepted
that a pull request's own code runs in its review.

The command line pins cspell 10.5.0 and `@cspell/dict-en-au` 1.1.31. The `en-AU` dictionary accepts some American
forms (`organization`, and `color` through the software terms dictionary), so it does not catch every American
spelling.

Jake's follow-ups the same day, also in this pull request: the `$schema` lines came out of the cspell settings
(VS Code would not load the schema from an untrusted address), VS Code now allows the app's typographic
apostrophe and multiplication sign, AGENTS.md has the one-parameter-per-line rule, and tasks 0015 to 0018 were
added to the order of work.
