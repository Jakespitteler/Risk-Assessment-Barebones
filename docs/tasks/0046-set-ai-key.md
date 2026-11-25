---
id: 0046
title: Say how to set the AI key when none is set
status: review
owner: claude
branch: claude/project-thread-9loys7
---

## Goal

Jake, 2026-11-25: "When no API key is set the terminal should tell me how to set it. Ideally it would just be a
command or something that I can easily input. If it needs to be a .env file update then say that." Today the
terminal only says the AI is off. It should say where to make a key for the chosen provider and give one command
that saves it.

## Acceptance criteria

- [x] With no AI key, the back end's start-up log has one warning that names the page where the chosen
  provider's keys are made and the one command to run, `uv run set_ai_key.py`, on a line of its own to copy.
- [x] `uv run set_ai_key.py`, in the repo root on Windows, Mac or Linux, asks for the key without showing it,
  and saves it as the `TAKE5_AI_KEY=` line in `backend/.env`: it makes the file if there is none, replaces the
  line if there is one, and keeps every other line.
- [x] The key is never printed, logged or put in the shell's history.
- [x] Tests cover the warning for each provider, no warning with a key, and the command's file changes, without
  touching the real `backend/.env`.
- [x] The README's "Turn on the AI's question" uses the command.

## Out of scope

- Checking that the key works, or that it matches the chosen provider.
- The two try scripts' own "Set TAKE5_AI_KEY" line.

## Notes / assumptions

Added by Claude on 2026-11-25 from Jake's request.

- One command rather than a line to paste into `.env`: a PowerShell line holding the key would stay in
  PowerShell's history and pile up a second key line, and Mac or Linux would need a different one (decisions
  log, 2026-11-25).
- Tried on 2026-11-25 with `uv run start.py` and no key: the warning is the last back-end line before "The Take 5
  app is ready", with the command on its own indented line. `uv run set_ai_key.py` in a throwaway folder filled
  in the template's empty `TAKE5_AI_KEY=` line and showed nothing as the made-up key was typed.
- The warning also prints when `check.py --fix` writes the API types, beside the four info lines that already
  print there.
- This PR starts from `main` rather than stacking on #88: task 0043's open PRs don't have task 0045 (ChatGPT) yet,
  which this change builds on.
