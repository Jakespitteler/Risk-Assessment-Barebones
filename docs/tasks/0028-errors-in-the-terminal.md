---
id: 0028
title: Make errors obvious in the terminal that runs the app
status: review
owner: claude
branch: claude/0028-errors-in-the-terminal
---

## Goal

Jake, 2026-11-19: "It should always be obvious from a glance what/where is going wrong from the terminal that's
running the app." Today it often isn't. Jake opened the app on Windows to a blank page, and the terminal running
`scripts/dev.py` showed nothing wrong. The cause was two files whose names differ only in case
(`frontend/src/features/take5/TimeLeft.tsx` and `timeLeft.ts`): Windows can't hold both, so a module lost an
export. The error was only in the browser's console. While the app runs, every problem the back end or the front
end meets should reach that one terminal as a short line that says which half, what went wrong and where.

## What happens today

- **Front-end errors stay in the browser.** Claude reproduced Jake's blank page on 2026-11-19 with an import of a
  missing export, in a terminal set up as a person's (see the note on agents below). The browser's console said
  ``The requested module '/src/features/take5/timeLeft.ts' does not provide an export named 'noSuchExport'``.
  Vite's terminal said nothing.
- **Vite can already pass them on.** Vite 8, which the repo uses, has a `server.forwardConsole` setting. With it
  set to `true`, the same blank page printed one red line in the terminal: ``[vite] (client) [Unhandled error]
  SyntaxError: The requested module '/src/features/take5/timeLeft.ts' does not provide an export named
  'noSuchExport'``. It also passes on `console.error` and `console.warn`, as the message alone. An error with a
  stack gets one line, then a line per stack frame with the file and line found through source maps. No new
  package is needed.
- **Agents and Jake see different things.** Left unset, `forwardConsole` is off for a person and on when Vite finds
  an AI agent's environment variables (such as `CLAUDECODE` or `AI_AGENT`), which the start script passes on. So an
  agent running the app sees browser errors that Jake, in his own terminal, doesn't.
- **AI failures print a stack trace.** When the AI fails, the back end falls back (spec C3, T6) and logs a warning
  with `exc_info=True`. A provider's error can print dozens of lines for a problem that is expected and handled.
- **A crash in a route prints uvicorn's trace** under its own heading, with nothing on one line saying which
  request failed.
- **Every request prints a line.** The phone checks the draft and asks for nudges as the worker types, so the
  terminal fills with `200 OK` lines and a real problem scrolls away.
- **Lines aren't labelled.** Both servers write to the same terminal, so a line can't be told apart as back end or
  front end. The back end's own info lines only appeared after task 0009 added a handler in `api/app.py`, because
  uvicorn sets up only its own loggers.
- **A server that stops stops the other silently.** The script ends both servers and says nothing about which one
  stopped or why.
- **A back end that is down prints a trace per request.** While the back end restarts, or won't start after a
  mistake in its code, Vite prints `http proxy error`, the `ECONNREFUSED` error and a stack line for every request
  the phone makes.

## Decide first

The questions for Jake, each with Claude's recommended pick. Answer them in chat; Claude writes the answers into
this file and `docs/decisions.md`.

**Jake's answers, 2026-11-19**, asked as four combined questions after task 0029 removed the output pipe:

- 1 (a) and 2 (b): Vite's own `server.forwardConsole`, passing on crashes, `console.error` and `console.warn`.
- 3 and 6: no "back end" or "front end" label on each line; a tidier format for the back end's lines.
- 4 (b): a stack trace only for a bug; a handled AI failure prints one line naming the kind of problem.
- 5: only failed requests print, every 4xx and 5xx (not option (b)'s two quiet 422s).
- 7 (a): no log file.

Claude's notes on how, not Jake's words: labels would bring back the pipe that 0029 removed; the format goes in
`backend/dev_logging.json`; Vite's lines already start with `[vite]`; the request filter is a small log filter.
The two changes that "come with the task unless Jake says otherwise" (below) weren't asked about yet. Task 0029's
`start.py` already names a server that stops, with its exit code, so mainly the "back end is down" line is left;
Asked when the task was claimed: **one short line per failed request** while the back end isn't answering (Jake,
2026-11-20).

**Question 3's sample line and the notes below still follow the original recommendations**, such as a label on
every line. The criteria were rewritten when the task was claimed, on 2026-11-20; where anything else differs
from Jake's answers, the answers win.

1. **How do front-end errors reach the terminal?** Options:
   - (a) Vite's own `server.forwardConsole: true`, one line in `frontend/vite.config.ts`. No new package. It
     works only while developing, not in a built app. Setting it also means Jake and agents see the same thing.
   - (b) A small plugin of our own (about 40 lines) that sends browser errors to the dev server. More code to keep.
   - (c) A package such as `vite-plugin-terminal`. A new dependency for what Vite now does itself.
   - Recommended: (a). It is mainstream, swappable and already proven on Jake's blank page.
2. **Which browser messages reach the terminal?** Options:
   - (a) Crashes only (unhandled errors and rejected promises).
   - (b) Crashes, `console.error` and `console.warn`.
   - (c) Everything, including `console.log`.
   - Recommended: (b). React's warnings in development, such as a missing `key`, are real bugs worth seeing.
     `console.log` is left out so the terminal stays readable.
3. **What does a back-end line look like?** Proposed:
   `14:22:11  WARNING  back end   The AI timed out after 10 s, so the fixed question was asked (services.take5s)`.
   Front-end lines keep Vite's own words, behind the same label (question 6). Options:
   - (a) Plain text as above: local time, level, which half, the message, then where it came from. Errors in red
     and warnings in yellow when the terminal shows colour.
   - (b) JSON, one object per line. Easy for a log tool to read later, hard for a person at a glance.
   - Recommended: (a). JSON can be added when the app is hosted and something collects its logs.
4. **When does a stack trace print?** Options:
   - (a) Always, as today.
   - (b) An expected problem the app already handles prints one line naming the kind of problem: the AI timed
     out, couldn't be reached, refused the key, or sent an unusable reply. An unexpected crash (a bug) prints one
     line saying which request failed, then the trace under it.
   - (c) One line only, always; traces go to a log file.
   - Recommended: (b). A handled problem needs no trace; a bug can't be fixed without one. The line names the kind,
     not the provider's own message, which can repeat the text the AI was sent.
5. **Which request lines print?** Options:
   - (a) All, as today.
   - (b) Only failed requests, except two 422s that are the app working as designed: a Take 5 submitted with gaps
     and a challenge answer that is too short. A 422 for a request the back end couldn't read is a front-end bug,
     so it prints.
   - (c) None.
   - Recommended: (b). The rest hide the lines that matter. It needs the error handlers to mark the two quiet
     422s, because the status code alone can't tell them apart.
6. **How is each line labelled?** Options:
   - (a) `back end` and `front end`, padded so the messages line up, in two colours. The words the docs use.
   - (b) Short tags such as `api` and `web`.
   - Recommended: (a).
7. **Should logs also go to a file?** Options:
   - (a) No, the terminal only.
   - (b) Also a file, such as `backend/.logs/app.log`, which git ignores, kept to a few megabytes.
   - Recommended: (a). A file adds rotation and a place a worker's data could leak to, for no one who reads it
     yet. Hosting will bring its own log collection (0021's timing).

Two more changes come with the task unless Jake says otherwise, because without them a glance at the terminal
still misleads: when a server stops, the start script says which one, its exit code, and that its error is just
above; and when the back end is down, the front end prints one line saying it can't reach it, not a trace per
request.

## Acceptance criteria

Rewritten on 2026-11-20 to follow Jake's answers above; the first version followed the original recommendations.

- [x] An error in the browser while developing, an uncaught crash, `console.error` and `console.warn` each print a
  line in the terminal; `console.log` does not (Vite's `server.forwardConsole: true` in `frontend/vite.config.ts`).
- [x] Every back-end line, uvicorn's and the app's own, has one format: local time, level, message, then where it
  came from in brackets (`backend/dev_logging.json`). No "back end" or "front end" label (Jake's answer 3 and 6).
- [x] An AI failure the app handles (a time-out, or the adapter's `AiReplyError`, with the provider's own error as
  its cause) prints one warning line that names the kind of problem and no stack trace; the provider's own
  message, which can repeat what the AI was sent, is never printed. Any other error while asking the AI is a bug,
  so it keeps its trace, and the worker still gets the fallback.
- [x] An unexpected error in a route prints one line naming the request (method and path, never the body), then
  uvicorn's trace. The reply is the same plain 500 as before.
- [x] Successful requests print no line; every failed request (4xx or 5xx) prints one.
- [x] When the back end isn't answering, the front end prints one line per failed request naming the path, not
  Vite's proxy error and stack (Jake, 2026-11-20).
- [x] When either server stops, the script names it with its exit code (already true since task 0029).
- [x] No line holds a worker's name or what they typed: tests prove it for an AI failure and a route crash.
- [x] Tests cover the log settings, the request filter, the one-line AI warnings, the route-crash line, and the
  front end's back-end-down line and log level. The browser's lines reaching the terminal were checked by hand
  in the running app (output in the pull request): a test of the terminal itself would need a second browser
  run inside the tests.
- [x] `docs/architecture.md` describes how logging is set up, and AGENTS.md's Logging rule points to it.
- [x] All checks pass.

## Out of scope

- Start-up: setting up, which address to open, and hiding uvicorn's `:8000` line and Vite's address box. That is
  task 0029, the one-command start. Everything printed after the app is ready is this task.
- A screen on the phone that says something went wrong instead of a blank page. Worth its own task: a module that
  fails to load stops React before any screen can draw.
- Logs for a hosted app, such as JSON lines or a log service. Later, with hosting.
- Fixing the `TimeLeft.tsx` and `timeLeft.ts` clash, and stopping the next one. Task 0009 renamed `timeLeft.ts`
  to `timeLeftText.ts`, and added `backend/tests/test_file_names.py`, which fails when two tracked files in one
  folder differ only in case.

## Notes / assumptions

- Depends on task 0029 (pull request #47); don't start until it is merged. Labelling lines and saying which
  server stopped means the start script reads each server's output instead of letting it pass straight through.
  Task 0029 may add that reading to hide start-up lines, or may use a logging filter instead; if output still
  passes straight through, this task adds the reading. 0029 may also replace `scripts/dev.py` with a root
  `start.py`. Build on whichever script 0029 leaves.
  (0029, built 2026-11-19: the root `start.py` lets each server print straight to the terminal. It hides
  start-up lines through settings: `--log-config backend/dev_logging.json` for uvicorn and `--logLevel warn` for
  Vite. It already names a server that stops, with its exit code. Labelling lines needs a pipe added here.)
- Logging stays standard library `logging`. Uvicorn's reloader prints from its own process, before the app is
  built, so a set-up function inside the app can't reach it. A log settings file in `backend/`, handed to uvicorn
  with `--log-config` by the start script, can: it configures the `risk_assessment` and `uvicorn` loggers
  together, and replaces the handler task 0009 added in `api/app.py`. If 0029 already made that file (JSON, since
  PyYAML isn't installed), extend it rather than adding a second.
- A browser error's message could in theory hold what a worker typed. Front-end code must never pass a worker's
  name or answers to `console.error` or `console.warn`; the reviewer checks for it.
- Tested by Claude on 2026-11-19 in a Linux container with Vite 8.3.8 and Chromium; not yet tried on Windows.

<!-- cspell:ignore CLAUDECODE -->
