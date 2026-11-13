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

Open the repository root in VS Code. After `uv sync`, the workspace settings select `backend/.venv` and
`pyrightconfig.json` resolves the `backend/src` package for Pylance in strict mode. If you previously selected
another interpreter, use **Python: Select Interpreter** to choose `backend/.venv`.

If uv warns that `VIRTUAL_ENV` belongs to another environment, deactivate that environment first. The warning
comes from uv before the script starts; the launcher already removes that variable for its child processes.
The front end's `.npmrc` uses the HTTPS npm registry.

## Test it

In the repo root, `uv run scripts/check.py` runs every check that CI runs, in the same order, and stops at the
first failure. The single commands are listed in [AGENTS.md](AGENTS.md#commands).
