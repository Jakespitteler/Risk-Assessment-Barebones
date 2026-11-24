---
id: 0044
title: start.py frees its ports from a leftover copy of the app
status: in-progress
owner: claude
branch: claude/0044-free-ports
---

## Goal

Jake, 2026-11-24: `uv run start.py` should free its ports on start-up. Today it stops with "Something is
already using port 8000" (or 5173) when an earlier run was left behind, such as a terminal closed without
Ctrl+C.

## Decide first

**Jake's answer, 2026-11-24:** stop only this app's leftovers: its own back end or Vite, recognised by their
command lines inside this repo's folder. Anything else on the port is left alone, and the message says what to
do, as today. No new package. Based on `main`, with its own pull request to `main`.

## Acceptance criteria

- [ ] When port 8000 or 5173 is held only by a leftover copy of this app, `start.py` says so, stops it, and
  starts as usual.
- [ ] When anything else holds the port, nothing is stopped and today's message shows, with nothing installed or
  started.
- [ ] It works on Windows, macOS and Linux with no new package; when the system can't say what holds the port,
  today's message shows.
- [ ] Tests cover finding what listens on a port, recognising this app, and both outcomes in `main`.

## Out of scope

- Stopping any program that isn't this app.

## Notes / assumptions

Added by Claude on 2026-11-24 from Jake's request and answer.
