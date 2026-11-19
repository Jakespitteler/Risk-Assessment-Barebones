---
id: 0029
title: Set up, update and start the app with one command
status: review
owner: claude
branch: claude/0029-one-command-start (stacked on task 0013, PR #51)
---

## Goal

Jake, 2026-11-19: "I want to create task to do soon that makes the setup and start-up super simple, I want it to
be done how you would expect it to be done in a professional setting. Check this is the best way but I think a one
command to rule them all would be ideal (sets up if not already setup, updates libraries, starts the app and tells
me only the correct url to follow) (could be something as simple as uv run app.py or instead of app a name more
fitting)."

Today it takes two commands, `uv run scripts/setup.py` (task 0023) and then `uv run scripts/dev.py`, and the
second one prints the wrong address loudest. Uvicorn's "Uvicorn running on <http://127.0.0.1:8000>" line is the
most visible one, so Jake opened that address, which is only the API, instead of Vite's
<http://localhost:5173>. Task 0009's pull request then made `dev.py` print "The Take 5 app is ready. Open
<http://localhost:5173>" last, once Vite answers, but uvicorn's line and Vite's own address box still show above it.
One command should set up whatever isn't set up yet, bring the installs in line with the repo, start both halves,
and print one address: the right one.

Jake, later the same day: "I don't like how sometimes I have to cd into the backend or front end." Today the tests,
lint, format and type-check commands in `AGENTS.md` each say "in `backend/`" or "in `frontend/`", and
`uv run pytest -m real_ai` fails when run from the repo root. So the task also gives every everyday command a form
that runs from the repo root, and nobody needs `cd` (question 10).

## Is one command the right approach?

Yes. It is the usual professional pattern, and the repo already has the pieces.

- **The pattern.** GitHub's "Scripts to Rule Them All" (<https://github.com/github/scripts-to-rule-them-all>) is
  the best-known write-up: every repo has the same few entry points, and the one that starts the app first
  brings the installs up to date, so a person never has to remember a set-up step. Django's `manage.py` in the
  repo root is the Python world's version: one obvious file to run.
- **Why a uv script, and not another tool.** uv is already required, works the same on Windows, macOS and Linux,
  and a script that uses only Python's standard library needs nothing else installed. The alternatives each add
  something:
  - `make` or `npm run dev` at the root: Windows has no `make`; a root `package.json` would need another
    package (such as `concurrently`) to run both halves, and still needs uv for the Python side.
  - A task runner (`just`, Task, Poe the Poet): one more tool to install on every computer, or one more
    dependency. uv has no built-in task runner (third-party ones exist).
  - `uv run start` through a `[project.scripts]` entry point: the repo root would have to become a Python project
    of its own, which changes what every `uv` command in the root does.
  - Docker Compose: needs Docker Desktop on Windows, reloads more slowly when code changes, and is a lot to learn
    for one person. It belongs with hosting, if anywhere.
- **What it doesn't fix.** Two addresses exist because, while developing, Vite serves the screens and FastAPI the
  API. When the app is hosted, the screens are built once and FastAPI serves both on one address, so a crew never
  sees two. That is for hosting, not this task.

## Decide first

**Jake's answers, 2026-11-19:** 1 (a) `uv run start.py`; 10 (a), with the two `.claude` files updated too; 6:
no route at `/`, and the API's address is never put in the terminal to click; every other question as
recommended (2 a, 3 a, 4 a, 5 a, 7 a, 8 yes, 9 yes). Question 11 was settled by the order of work: next after 0013.
Later on review: hide the address lines through each server's settings rather than a pipe; rename the root
`setup.py` to `install.py`, since pip and some tools treat a root `setup.py` as a package build file; keep this
pull request whole. The questions and criteria below keep the old name `setup.py`.

The questions for Jake, each with Claude's recommended pick.

1. **What is the command called, and where does it live?** Options:
   - (a) `uv run start.py`, a new file in the repo root. Short, says what it does, and sits where a person looks
     first, as Django's `manage.py` does. Costs a few lines elsewhere, because the checks only look in `backend/`
     and `scripts/` today: add it to `PYTHON_FOLDERS` in `scripts/check.py` (ruff and pyright) and to `include` in
     the root `pyproject.toml` (Pylance), and let Claude's formatter hook
     (`scripts/claude_hooks/format_edited_file.py`) format a `.py` file in the root, which is a hook change for
     Jake to approve. The tests can already import it.
   - (b) `uv run app.py` in the repo root, as Jake suggested. Short, but the back end already has an `app.py`
     (`backend/src/risk_assessment/api/app.py`, which builds the FastAPI app), and in Python projects `app.py`
     usually means "the file that holds the app". Two files with the same name doing different jobs would confuse
     anyone learning the back end.
   - (c) `uv run scripts/start.py`. Beside the other scripts, with no other changes, but longer to type. "Scripts
     to Rule Them All" keeps its entry points in a folder like this.
   - (d) Keep `uv run scripts/dev.py` and make it do everything. Nothing new to learn, but "dev" is jargon and it
     is the longest.
   - Recommended: (a).
2. **What happens to `setup.py` and `dev.py`?** Options:
   - (a) The new command replaces `dev.py`, which is deleted, and its tests move with it. `setup.py` stays as the
     "install everything again from scratch" command, for when an install is broken; the new command reuses its
     checks rather than copying them.
   - (b) Delete both, since the new command does the first-time set-up too. Fewer files, but then there is no
     command that reinstalls everything when something is broken.
   - (c) Keep `dev.py` as well. Two ways to do one thing.
   - Recommended: (a).
3. **What does "updates libraries" mean?** To be direct: in a professional setting, starting the app never
   upgrades a package to a newer version. It installs exactly the versions in the lock files the repo holds
   (`backend/uv.lock` and `frontend/package-lock.json`), so after a `git pull` you get what the last change was
   tested with. An upgrade is a change of its own, made in a pull request and tested, because a new version can
   break the app with no change to its code, and two computers would then run different versions. Options:
   - (a) Bring the installs in line with the lock files on every start (install what's new, remove what's gone).
   - (b) Also upgrade to the newest allowed versions on every start.
   - Recommended: (a). Keeping packages up to date could be a later task: GitHub's Dependabot opens a pull request
     for each new version, and the checks and the review agent test it like any other change.
4. **What does the first run install?** Options:
   - (a) Everything `setup.py` installs, including the browser the whole-app tests use (about 150 MB, and a
     minute or so once). After that the repo is ready for every check too. The app doesn't need that browser, so
     if its download fails (offline, or a proxy) the command warns and starts the app anyway.
   - (b) Only what the app needs to run. The test browser stays with `setup.py`, and the tests fail until it is
     run.
   - Recommended: (a), since Jake asked for "sets up if not already setup". Later starts reinstall only the half
     whose lock file changed, so a start with nothing new adds a few seconds at most, not the minute `npm ci`
     takes.
5. **What does it print?** Options:
   - (a) Hide uvicorn's "running on" line and Vite's own address box. Once both halves answer, print one clear
     line last, such as "The Take 5 app is ready. Open <http://localhost:5173>. Press Ctrl+C to stop." Keep the
     rest of the servers' output: each request, any error, and the app's own lines (such as which AI model asks
     the challenge question), because Jake wants to see what the back end is doing.
   - (b) Hide all server output except errors, with a `--verbose` switch to see it.
   - (c) Leave the output as it is today, with the ready line at the end. The `:8000` line stays on screen.
   - Recommended: (a). The API's own pages (<http://localhost:8000/docs>) stay listed in the README, not printed.
6. **A safety net at the API's address.** Today opening <http://localhost:8000> shows `{"detail":"Not Found"}`.
   Options:
   - (a) The back end answers `/` with one plain line: "This is the API. Open the app at
     <http://localhost:5173>." (or the Codespace's address, question 8). It is a new route on the API, so it needs
     Jake's yes, and it would be replaced when hosting serves the screens from FastAPI. It is left out of the API's
     description (`include_in_schema=False`), so the generated front-end types don't change.
   - (b) Leave it, since the command no longer prints that address.
   - Recommended: (a). It is a few lines, and it turns the exact mistake Jake made into a pointer to the right
     page.
7. **Open the browser by itself?** Options:
   - (a) No, print the address. In VS Code's terminal it is a Ctrl+click. Vite reloads an open tab by itself
     when code changes, so a tab stays useful across restarts.
   - (b) Yes, on every start. Nothing to click, but each restart opens another tab.
   - (c) Only on the first start after set-up.
   - Recommended: (a).
8. **GitHub Codespaces.** Jake also works in Codespaces (Jake said so on 2026-11-17, during task 0023), where
   `localhost:5173` is the wrong address: Codespaces forwards it to an address like
   `https://<codespace-name>-5173.app.github.dev`. Recommended: when it runs in a Codespace (Codespaces sets
   `CODESPACE_NAME` and `GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN`), print that address instead, so "only the
   correct url" holds there too. VS Code in a Codespace often forwards a Ctrl+clicked `localhost` link by itself,
   but not always, and never from a browser tab opened by hand.
9. **When the app is already running, or a port is taken.** Recommended: before installing anything, check that
   ports 8000 and 5173 are free. If one isn't, say "Something is already using port 5173. The app may already be
   running in another terminal: use that one, or press Ctrl+C there first." and stop. Checking first matters on
   Windows, where an install fails while the app holds its files open. Vite already refuses to move to another
   port (`strictPort` in `vite.config.ts`), so the printed address is never wrong.
10. **Every command from the repo root.** Today set-up, start, `check.py`, markdownlint and cspell run from the
    root; the tests, lint, format, type check and API types each need a `cd` first. Options:
    - (a) One small file per job, each named for what it does, all in the same folder as question 1's command (the
      root at 1(a), `scripts/` at 1(c)). New: `test.py`, and a `--fix` switch for `check.py`, which today only
      checks.
      - `uv run test.py` runs every test; `uv run test.py backend`, `frontend` or `e2e` runs one kind. Anything
        else on the line goes to the test tool, so `uv run test.py backend -m real_ai` runs the real-AI test.
      - `uv run check.py --fix` formats the code, makes the fixes the lint tools can make by themselves, and
        regenerates the API types. `uv run check.py` alone still checks everything, as CI does.
      - Inside, the scripts use the tools' own "run in this folder" options (`uv run --directory backend`,
        `npm --prefix frontend`), so nothing changes in how the tools are set up. Each root script keeps the
        `# /// script` header `check.py` has: without one, `uv run` in the root makes a stray `.venv` and
        `uv.lock` there, because the root `pyproject.toml` isn't a project.
    - (b) One file with a word for each job, like Django's `manage.py`: for example `uv run app.py start`,
      `uv run app.py test`. One name to remember, but one file doing many jobs, and question 1's name clash again.
    - (c) Make the repo root a uv workspace (and an npm workspace), so `uv run pytest` works from the root with no
      script. The tools' own way, but `backend/.venv` and `backend/uv.lock` move to the root, which changes
      Pylance's settings, the hooks, CI, question 3's lock file and most docs. The back end's pytest settings would
      have to move too, or a plain `uv run pytest` would run the paid real-AI test. The front-end commands stay
      long (`npm test --workspace frontend`).
    - Recommended: (a). With question 1 at (a), `setup.py` (if question 2 keeps it) and `check.py` move to the
      root as well, so the commands sit together. Moving `check.py` also changes `.github/workflows/ci.yml`,
      `.github/workflows/agent-review.yml`, `scripts/setup.py`'s "Next" lines, the README, `docs/dev-setup.md`,
      `.claude/agents/reviewer.md` and the allow list in `.claude/settings.json` (which also needs the new
      commands). The two `.claude` files are agent settings, so those changes need Jake's yes. `AGENTS.md`
      "Commands" lists the root commands; the per-folder ones stay in a short note for editors and debugging.
11. **Where it goes in the order of work.** Jake asked for it "soon". Options:
    - (a) Next after 0013, which is in progress on another branch, and before 0024 (dark mode).
    - (b) Straight away, while 0027 waits on Jake's measurement. It touches `scripts/`, the README,
      `AGENTS.md`, `docs/dev-setup.md`, the structure in `docs/architecture.md`, perhaps `frontend/vite.config.ts`
      and a small logging setting in `backend/` (to hide the address lines), and one back-end route (if question 6
      is a yes), plus the CI workflows if question 10 moves `check.py`, so it barely overlaps the open pull
      requests.
    - Recommended: (a), placed there in `docs/tasks/README.md`; Jake can pick (b).

## Acceptance criteria

- [x] In the repo root, the command question 1 picks, on a freshly cloned repo, checks for git and Node.js as
  `setup.py` does, installs what question 4 decides, starts both halves and prints the one ready line question 5
  describes.
- [x] Run again with nothing changed, it installs nothing new, and the ready line appears within 3 seconds of
  when `dev.py` is ready today on the same computer. Both times measured and written in the pull request.
- [x] After a change to `backend/uv.lock`, or to `frontend/package-lock.json`, it brings that half's installs in
  line before starting. It never upgrades a package (question 3).
- [x] The only address printed is the app's: `http://localhost:5173`, or the forwarded address in a Codespace
  (question 8). Neither uvicorn's nor Vite's own address lines appear.
- [x] A busy port stops it before any install, with the message question 9 describes.
- [x] A missing tool, a failed install or a server that stops says which and what to do, as `setup.py` and
  `dev.py` do today. The cloud-synced folder warning from task 0023 is still on screen once the app is ready (Vite
  clears the terminal when it starts, see the notes).
- [ ] Ctrl+C stops both halves and everything they started, on Windows too, as `dev.py` does today.
- [x] If question 6 is a yes, the back end answers `/` with the pointer to the app, with a test, and
  `npm run generate:api` changes nothing.
- [x] `dev.py` and `setup.py` end up as question 2 decides. With (a): `dev.py` is gone, its tests are moved to the
  new command, `setup.py`'s checks are shared rather than copied, and `test_setup.py` and
  `test_format_edited_file.py` no longer name `dev.py`.
- [x] The browser opens, or doesn't, as question 7 decides.
- [x] Tests cover: when each half needs installing, which address is printed, the busy-port check, and that the
  address lines are hidden.
- [x] `README.md` ("Set it up" and "Run it"), `AGENTS.md` (Install and Run), `docs/dev-setup.md`, the structure in
  `docs/architecture.md`, and `setup.py`'s closing "Next" lines name the new command. `docs/decisions.md` records
  the choices.
- [x] A copy of the terminal output of a first run and a second run is in the pull request.
- [x] Every everyday command runs from the repo root, as question 10 decides: start, set-up, every kind of test
  (including the real-AI test, `-m real_ai`), lint, format, type check and API types. Cloning, and the
  per-folder note for editors, are the only places a `cd` is left in `AGENTS.md` and the README.
- [x] Tests cover how each root command maps to the tool it runs, including `check.py --fix` and extra arguments
  passed through to the test tool.
- [x] All checks pass.

## Out of scope

- Upgrading packages to newer versions, or setting up Dependabot (question 3).
- Pulling new code from GitHub. "Updates" means the installs, not `git pull`, which stays Jake's to run.
- Installing git, uv or Node.js themselves (as in task 0023).
- Serving the built screens from FastAPI on one address, which is part of hosting.
- Docker, a dev container for Codespaces, or VS Code tasks and launch settings. Each could be a later task.
- How errors and log lines look once the app is running, and how each server's lines are labelled. That is the
  task "Make app errors obvious in the terminal", being written in another thread on 2026-11-19 as 0028; this task
  owns only what is printed at start-up.

## Notes / assumptions

- Asked for by Jake on 2026-11-19, as a task file only. Written stacked on task 0027's pull request (#46, which
  GitHub closed when 0009's branch was deleted; 0027 is now #50).
- Today: `scripts/dev.py` runs `uv sync --locked`, runs `npm ci` only when Vite is missing (so a pull that adds a
  front-end package isn't installed until something breaks), then starts uvicorn on port 8000 and, once the API
  answers, Vite on 5173, and prints its ready line once Vite answers (`READY_MESSAGE`, added in 0009's pull
  request). `scripts/setup.py` checks git and Node.js 22.22.2 or newer, warns about cloud-synced
  folders, and runs `uv sync --locked`, `npm ci --engine-strict` and `npx playwright install chromium` every time.
  Its tests are `backend/tests/test_setup.py`; `dev.py`'s are `backend/tests/test_dev.py` and import it as
  `from scripts import dev`. `backend/tests/test_format_edited_file.py` uses `scripts/dev.py` as its sample file.
- Knowing when the front end needs installing: npm writes `node_modules/.package-lock.json` on every install, or
  the script can keep a fingerprint of `package-lock.json` inside `node_modules`. Either way, an interrupted
  install must still be noticed (`dev.py` guards against that today). `uv sync --locked` is already quick when
  nothing has changed, so it can run every time. Playwright's browser needs reinstalling only when
  `@playwright/test` changes in `package-lock.json`.
- Hiding the address lines: uvicorn's "running on" line comes from its `uvicorn.error` logger, so a small logging
  filter (through `--log-config`) can drop it. The filter must be an importable Python class, so it lives under
  `backend/`, and the config is JSON (PyYAML isn't installed). Reading the server's output through a pipe and
  dropping the line also works, but can lose colours and delay lines. Vite's address box can be left out with a
  custom logger in `vite.config.ts`, or by reading its output. The implementer picks whichever is simplest and
  says why.
- Vite clears the terminal when it starts (in a real terminal, when it hasn't printed anything itself yet), which
  scrolls away the install output and the cloud-sync warning. Set `clearScreen: false` in `vite.config.ts`, or
  print the warning again after the ready line.
- The port check must cover IPv6 too: Vite binds `localhost`, which can be `::1`, so a check on `127.0.0.1` alone
  can call 5173 free while the app is running.
- The back end's AI key (task 0009) comes from a `.env` file the scripts must not read; the command only starts
  the back end, which reads it as it does today.
- Assumption: "updates libraries" means installing the locked versions, not upgrading (question 3).

### What was built (Claude, 2026-11-19)

- `start.py`, `install.py` (was `scripts/setup.py`), `check.py` and `test.py` in the repo root; `scripts/dev.py` is
  gone, and its tests moved to `backend/tests/test_start.py`. `install.py`'s tool checks, cloud-sync warning and
  install steps are imported by `start.py`, not copied.
- How the address lines are hidden, and why that way: `docs/decisions.md`, 2026-11-19. In short, each server's
  own settings turn its start-up lines off (`backend/dev_logging.json` for uvicorn, `--logLevel warn` for Vite),
  and their output goes straight to the terminal. A first version read the output through a pipe instead; Jake
  chose this simpler way on review.
- Measured here (Linux, in a cloud container): with nothing to install, `scripts/dev.py` was ready in 1.4 s and
  `uv run start.py` in 1.8 s (three runs each; the extra 0.4 s is the quiet `uv sync --locked`, which now runs
  every time). A fresh clone was ready in 9 s; a changed `package-lock.json` in 7 s. A busy port stopped it in
  0.1 s. Both first and second runs are in the pull request.

### Left for Jake

- **Ctrl+C on Windows.** The criterion is not ticked: stopping works as `dev.py` did (its own process group, then
  `taskkill /T`), and Ctrl+C was checked on Linux, but no Windows computer was available. Please try
  `uv run start.py` and Ctrl+C in PowerShell, then check that nothing is left on ports 8000 and 5173. If a server
  stops by itself, `start.py` still runs `taskkill /T` on it, in case npm or uv ended before what it started; a
  review found Windows may no longer find that tree once its first process has ended, so it is worth trying too.

### Notes

- Ctrl+C can reach the script twice (uv passes it on as well). A second one used to break into the shutdown and
  could leave Vite running, as `dev.py` did (it exited with code 130 in the timing runs). `start.py` acts on the
  first Ctrl+C only. Stopping a server asks first, then forces it after 10 seconds, and signals the server's
  whole process group even when npm or uv has already ended.
- `install.py` leaves the same "installed for this lock file" fingerprint as `start.py`, so a start straight after
  `uv run install.py` installs nothing more.
- The test browser is installed after each front-end install. If that download fails, the app still starts, and
  `uv run install.py` tries it again; `start.py` doesn't retry it until the lock file next changes.
- With `--logLevel warn`, Vite no longer prints "page reloaded" notes while you work. The page still reloads.
- The back end's sync on later starts is quiet: a pulled change to `uv.lock` is installed without a list of what
  changed (errors still show).
- Vite stops by itself when its keyboard input closes, so `uv run start.py < /dev/null` stops at once. This is
  Vite's behaviour, the same as before; a terminal is never affected.
- The port check connects to each port rather than binding it: binding would call a port busy for a minute or so
  after a restart, while the old socket finishes closing.
- `check.py --fix` runs every fix even when one reports a problem it can't fix (such as a line Ruff can't
  shorten), then lists those, so the formatters after it still run.
