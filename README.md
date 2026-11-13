# Risk-Assessment-Barebones

A Take 5 app for mine-site workers, built by a human with AI coding agents (Claude Code and ChatGPT) working in the
same repo.

- How agents work here: [AGENTS.md](AGENTS.md)
- What the app does: [docs/spec.md](docs/spec.md)
- How it's built: [docs/architecture.md](docs/architecture.md)
- Current work: [docs/tasks/](docs/tasks/)

## Run it

You need git, [uv](https://docs.astral.sh/uv/) and Node.js 22 or newer.

1. Install, once and after any dependency change:
   - in `backend/`: `uv sync`
   - in `frontend/`: `npm ci`, then `npx playwright install chromium`
2. In the repo root: `uv run scripts/dev.py`. It syncs the back end's packages, installs the front end's
   packages if Vite is missing, and waits for the API before starting the front end.
3. Open <http://localhost:5173>. The back end's own API pages are at <http://localhost:8000/docs>.

Press Ctrl+C to stop. Both halves restart by themselves when their code changes.

The home page now runs a complete Take 5: enter the job and hazards, assess each hazard, review and finish.
The result is saved at `/take5s/<id>`; keep that URL to reopen it. Draft answers stay in memory while the form
is open and are lost on reload or close. The phone remembers only the worker name. The original standalone
matrix screen is at `/rate-risk`. Card questions and the AI challenge arrive in later tasks.

Submitted Take 5s are stored in `backend/.data/take5.sqlite3`, which git ignores. Set
`TAKE5_DATABASE_PATH` to use a different SQLite file. Back up that file to keep submitted assessments;
removing the local database removes those records. Checking a draft does not save it.

Open the repository root in VS Code. `[tool.pyright]` in the root `pyproject.toml` resolves `backend/src`
for the app and tests in strict mode. The back end's own `pyproject.toml` still owns its dependencies and Ruff.
From `backend/`, use `uv run pyright --project ..` so the checker uses the repository as its import root.
This keeps the launcher's `scripts` package distinct from the back end's OpenAPI export scripts.

If Pylance reports missing app imports or `pytest`:

1. Run `uv sync --locked` in `backend/` to install the app and development tools.
2. Run **Python: Select Interpreter** in VS Code and select `backend/.venv/Scripts/python.exe` on Windows
   (`backend/.venv/bin/python` on Linux/macOS). Select the executable, not the `.venv` directory.
   VS Code keeps this machine-specific choice locally; it does not need to be committed to the repo.
3. Run **Developer: Reload Window**. The test explorer is configured to run pytest from `backend/`.

The workspace leaves Python Environments integration enabled when installed and enabled by your editor.
It deliberately has no directory-valued `python.defaultInterpreterPath`: the Environments launcher was
observed trying to execute `backend/.venv` itself instead of the Python executable it had discovered,
causing `spawn ... ENOENT` before pytest could start. Selecting the executable directly fixes the launch
target and works across operating systems without a shared Windows-only path or disabling the integration.
After pulling this correction, select that executable, reload the window and run **Test: Refresh Tests**.
If discovery still fails, check **Output → Python Environments** for `Running in background`: its quoted
launch target must end in `Scripts/python.exe` on Windows or `bin/python` on Linux/macOS.

The Ruff extension uses its bundled executable and the back end's Ruff configuration, so it can format
and sort imports without discovering a binary in a different Python environment. If it still reports a
binary error, update or reinstall the **Ruff** extension and reload the window. Its Output log is needed
to diagnose a remaining failure. Disable the separate **isort** extension **for this workspace**: Ruff
already sorts imports with its `I` rules. It is not a project dependency.

Ignore files such as `.prettierignore` are associated with the **Ignore** language, not Markdown. If an
already-open file still shows Markdown diagnostics after reloading, use **Change Language Mode** to select
**Ignore**. With no Ignore language extension installed, select **Plain Text** instead.

If uv warns that `VIRTUAL_ENV` belongs to another environment, deactivate that environment first. The warning
comes from uv before the script starts; the launcher already removes that variable for its child processes.
The front end's `.npmrc` is npm's project configuration. Its one line selects `https://registry.npmjs.org/`
to avoid the plaintext HTTP registry warning; it contains no credentials or additional dependencies.

## Test it

In the repo root, `uv run scripts/check.py` runs every check that CI runs, in the same order, and stops at the
first failure. The single commands are listed in [AGENTS.md](AGENTS.md#commands).
