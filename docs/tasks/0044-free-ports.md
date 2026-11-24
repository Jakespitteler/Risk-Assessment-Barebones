---
id: 0044
title: start.py frees its ports from a leftover copy of the app
status: review
owner: claude
branch: claude/0044-free-ports (#89)
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

- [x] When port 8000 or 5173 is held only by a leftover copy of this app, `start.py` says so, stops it, and
  starts as usual.
- [x] When anything else holds the port, nothing is stopped and today's message shows, with nothing installed or
  started.
- [x] It works on Windows, macOS and Linux with no new package; when the system can't say what holds the port,
  today's message shows.
- [x] Tests cover finding what listens on a port, recognising this app, and both outcomes in `main`.
- [x] The app running in another terminal, and the whole-app tests' servers, are not leftovers and keep their ports
  (from the review).

## Out of scope

- Stopping any program that isn't this app.

## Notes / assumptions

Added by Claude on 2026-11-24 from Jake's request and answer. Tried in a Linux container: a run whose
`start.py` was killed left both servers running; the next `uv run start.py` stopped them and started. An
unrelated program on port 8000 was left alone, with the old message. Jake to try it on Windows.

The review of `536ad99` found: netstat's `-p TCP` hid Vite's IPv6 socket on Windows; the folder check matched
other copies of the repo, worktrees inside it and words holding "vite"; a copy still running in another terminal
or under the whole-app tests would be stopped; and PowerShell's output could fail to decode. All are fixed: plain
`netstat -ano`, read by the empty remote address rather than the translated state; a match on start.py's own
commands only; the `.start.pid` check; UTF-8 output. A leftover that ignores the request to stop is forced after
5 seconds. Tried again in the Linux container: a second `uv run start.py` beside a running one left it alone;
after the first was killed it stopped the leftovers and started; a server started as the whole-app tests start
it was left alone.
