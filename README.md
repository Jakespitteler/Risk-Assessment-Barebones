# Risk-Assessment-Barebones

A Take 5 app for mine-site workers, built by a human with AI coding agents (Claude Code and ChatGPT) working in the
same repo.

The app is the confidential property of Jake Spitteler. All rights are reserved: nobody may copy, use or share it
without the owner's written permission. See [LICENSE](LICENSE).

- How agents work here: [AGENTS.md](AGENTS.md)
- What the app does: [docs/spec.md](docs/spec.md)
- How it's built: [docs/architecture.md](docs/architecture.md)
- Current work: [docs/tasks/](docs/tasks/), done in the order in [docs/tasks/README.md](docs/tasks/README.md)

## Run it

You need git, [uv](https://docs.astral.sh/uv/) and Node.js 22 or newer.

1. Install, once and after any dependency change:
   - in `backend/`: `uv sync`
   - in `frontend/`: `npm ci`, then `npx playwright install chromium`
2. In the repo root: `uv run scripts/dev.py`. It syncs the back end's packages, installs the front end's
   packages if Vite is missing, and waits for the API before starting the front end.
3. Open <http://localhost:5173>. The back end's own API pages are at <http://localhost:8000/docs>.

Press Ctrl+C to stop. Both halves restart by themselves when their code changes.

The home page runs a Take 5: the job, the hazards, a rating before and after controls for each, a review, then
the saved result at `/take5s/<id>`. The phone remembers only the worker's name. The first screen from task 0002
is at `/rate-risk`. The card's questions and the AI's challenge question come in later tasks.

Saved Take 5s are kept in `backend/.data/take5.sqlite3`, which git ignores. Set `TAKE5_DATABASE_PATH` to use
another file.

Using VS Code? See [docs/dev-setup.md](docs/dev-setup.md) for the editor set-up and fixes for common problems.

## Test it

In the repo root, `uv run scripts/check.py` runs every check that CI runs, in the same order, and stops at the
first failure. The single commands are listed in [AGENTS.md](AGENTS.md#commands).
