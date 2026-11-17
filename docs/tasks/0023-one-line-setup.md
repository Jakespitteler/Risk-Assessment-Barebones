---
id: 0023
title: Set up a freshly cloned repo with one command
status: done
owner: claude
branch: claude/project-thread-vn8i52
---

## Goal

Jake, 2026-11-16: "Can we make a setup script or something so when I clone the repo from a new computer, I can
just put one line in the terminal that takes care of all of the setup. Also add somewhere in the readme to not
clone a repo into a cloud folder if it doesn't already." One command, run in the repo root after cloning, installs
everything the app and its checks need, or says plainly what is missing and how to get it.

## Acceptance criteria

- [x] `uv run scripts/setup.py`, in the repo root, checks for git and Node.js 22.22.2 or newer, then installs Python
  3.13 and the back end's packages, the front end's packages and the browser the whole-app tests use.
- [x] When git or Node.js is missing or too old, it says which, how to install it, and stops before installing
  anything.
- [x] When a step fails, it names the step and stops.
- [x] It ends by listing what it did and what to do next.
- [x] It warns when the repo is inside a OneDrive, Dropbox, Google Drive or iCloud folder.
- [x] It is safe to run again.
- [x] The README gives the one-line set-up and warns not to clone into a cloud-synced folder, and why.
- [x] Tests cover the checks and the order of the steps.

## Out of scope

- Installing git, uv or Node.js themselves. They are installed once per computer, outside the repo.

## Notes / assumptions

Jake runs Windows and PowerShell. The script uses only Python's standard library, so `uv run` needs nothing
installed first except uv, and it works the same on macOS and Linux. On Linux, Playwright's browser may also
need system libraries (`npx playwright install-deps chromium`, with sudo); the script says so at the end. Tested
in a Linux container: a full run from an empty `frontend/node_modules`, a second run straight after, and a run
with Node.js missing from `PATH`. Not run on Windows or macOS by Claude.

Choices made, and recorded in `docs/decisions.md` (2026-11-17):

- It doesn't install git, uv or Node.js. The README lists the three `winget` commands for a new Windows
  computer. Git is needed to clone anyway, and uv to run the script.
- `npm ci` runs every time, so a second run takes as long as the first (about a minute) but always matches
  `package-lock.json`. On Windows it fails if the app is running, because the app holds files open; the failure
  message says to stop the app first.
- In a cloud-synced folder it warns at the start and again at the end, but carries on.
- No git hooks or pre-commit are set up: the repo has none. Claude Code's hooks only need uv and the installs
  above. `scripts/check.py` downloads markdownlint and cspell through `npx` the first time it runs.
- The locked front-end packages need Node.js 22.22.2 or newer, or 24.15 or newer on version 24 (jsdom; vitest
  and Vite need 22.12), not the "22 or newer" AGENTS.md and the README said. npm only warned about it, so an older
  22 installed fine and the tests failed later. The script checks for 22.22.2 and runs `npm ci --engine-strict`,
  so npm stops on any version a package doesn't accept (such as 23, 24.0 to 24.14, or 25). AGENTS.md and the
  README now give the real minimum. A Node.js LTS installed today is new enough.
- The README's install steps moved into a new "Set it up" section with the cloud folder warning.

The same pull request points AGENTS.md's install command, `docs/dev-setup.md` and the structure in
`docs/architecture.md` at the script.
