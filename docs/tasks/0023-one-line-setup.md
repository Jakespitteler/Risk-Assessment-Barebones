---
id: 0023
title: Set up a freshly cloned repo with one command
status: in-progress
owner: claude
branch: claude/project-thread-vn8i52
---

## Goal

Jake, 2026-11-16: "Can we make a setup script or something so when I clone the repo from a new computer, I can
just put one line in the terminal that takes care of all of the setup. Also add somewhere in the readme to not
clone a repo into a cloud folder if it doesn't already." One command, run in the repo root after cloning, installs
everything the app and its checks need, or says plainly what is missing and how to get it.

## Acceptance criteria

- [ ] `uv run scripts/setup.py`, in the repo root, checks for git and Node.js 22 or newer, then installs Python
  3.13 and the back end's packages, the front end's packages and the browser the whole-app tests use.
- [ ] When git or Node.js is missing or too old, it says which, how to install it, and stops before installing
  anything.
- [ ] When a step fails, it names the step and stops.
- [ ] It ends by listing what it did and what to do next.
- [ ] It warns when the repo is inside a OneDrive, Dropbox, Google Drive or iCloud folder.
- [ ] It is safe to run again.
- [ ] The README gives the one-line set-up and warns not to clone into a cloud-synced folder, and why.
- [ ] Tests cover the checks and the order of the steps.

## Out of scope

- Installing git, uv or Node.js themselves. They are installed once per computer, outside the repo.

## Notes / assumptions

\<Filled in as the work goes.>
