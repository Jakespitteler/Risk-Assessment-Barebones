---
id: 0046
title: Say how to set the AI key when none is set
status: in-progress
owner: claude
branch: claude/project-thread-9loys7
---

## Goal

Jake, 2026-11-25: "When no API key is set the terminal should tell me how to set it. Ideally it would just be a
command or something that I can easily input. If it needs to be a .env file update then say that." Today the
terminal only says the AI is off. It should say where to make a key for the chosen provider and give one command
that saves it.

## Acceptance criteria

- [ ] With no AI key, the back end's start-up log has one warning that names the page where the chosen
  provider's keys are made and the one command to run, `uv run set_ai_key.py`, on a line of its own to copy.
- [ ] `uv run set_ai_key.py`, in the repo root on Windows, Mac or Linux, asks for the key without showing it,
  and saves it as the `TAKE5_AI_KEY=` line in `backend/.env`: it makes the file if there is none, replaces the
  line if there is one, and keeps every other line.
- [ ] The key is never printed, logged or put in the shell's history.
- [ ] Tests cover the warning for each provider, no warning with a key, and the command's file changes, without
  touching the real `backend/.env`.
- [ ] The README's "Turn on the AI's question" uses the command.

## Out of scope

- Checking that the key works, or that it matches the chosen provider.
- The two try scripts' own "Set TAKE5_AI_KEY" line.

## Notes / assumptions

Added by Claude on 2026-11-25 from Jake's request.
