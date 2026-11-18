# Risk-Assessment-Barebones

A Take 5 app for mine-site workers, built by a human with AI coding agents (Claude Code and ChatGPT) working in the
same repo.

The app is the confidential property of Jake Spitteler. All rights are reserved: nobody may copy, use or share it
without the owner's written permission. See [LICENSE](LICENSE).

- How agents work here: [AGENTS.md](AGENTS.md)
- What the app does: [docs/spec.md](docs/spec.md)
- How it's built: [docs/architecture.md](docs/architecture.md)
- Current work: [docs/tasks/](docs/tasks/), done in the order in [docs/tasks/README.md](docs/tasks/README.md)
- Ideas for later, not yet tasks: [docs/ideas.md](docs/ideas.md)

## Set it up

Once per computer, install git, [uv](https://docs.astral.sh/uv/) and Node.js 22.22.2 or newer (24.15 or newer
on version 24). On Windows, in PowerShell:

```powershell
winget install --id Git.Git -e
winget install --id astral-sh.uv -e
winget install --id OpenJS.NodeJS.LTS -e
```

On a Mac with [Homebrew](https://brew.sh/): `brew install git uv node`. Then close the terminal and open a new
one, so it finds them.

Clone the repo into a folder that isn't synced to the cloud (see below), and run the set-up in its root folder:

```powershell
mkdir C:\dev
cd C:\dev
git clone https://github.com/Jakespitteler/Risk-Assessment-Barebones.git
cd Risk-Assessment-Barebones
uv run scripts/setup.py
```

The last line is the set-up. It checks for git and Node.js, then installs Python 3.13, the back end's and front
end's packages, and the browser the whole-app tests use. It ends by saying what it did and what to do next, or
what is missing and how to get it. It is safe to run again, for example after pulling changes that add packages.
Stop the app first, because Windows won't let it replace files the app is using. The same command works on macOS
and Linux; use a folder such as `~/dev` there.

### Don't clone into a cloud-synced folder

Keep the repo out of OneDrive, Dropbox, Google Drive and iCloud Drive folders. On Windows, check the path has no
`OneDrive` in it: OneDrive can take over `Documents` and `Desktop`. On a Mac, avoid `Desktop` and `Documents` if
iCloud syncs them. A plain folder such as `C:\dev` is safest. GitHub keeps a copy of everything you push, so
syncing the folder as well adds little, and it causes problems:

- Set-up writes about twenty thousand small files (`frontend/node_modules` and `backend/.venv`). The sync service
  tries to upload them all, and again each time they change.
- It can lock a file while npm, uv or git is writing it, so installs fail with errors such as `EPERM` or "access
  denied".
- It can make "conflicted copy" files, or bring back old ones, inside `.git`, which can damage the repo.
- A file kept "online only" isn't really on the disk until it's opened, which slows or breaks the tools.

The set-up script warns you if it finds the repo in one of these folders. It can't tell when macOS syncs
`Desktop` or `Documents`, because those paths don't change.

## Run it

1. In the repo root: `uv run scripts/dev.py`. It syncs the back end's packages, installs the front end's
   packages if Vite is missing, and waits for the API before starting the front end.
2. Open <http://localhost:5173>. The back end's own API pages are at <http://localhost:8000/docs>.

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
