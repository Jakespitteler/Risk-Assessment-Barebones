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
2. When it prints "The Take 5 app is ready", open the address on that line, <http://localhost:5173>. The
   `:8000` address uvicorn prints earlier is only the API; its own pages are at <http://localhost:8000/docs>.

Press Ctrl+C to stop. Both halves restart by themselves when their code changes.

The home page runs a Take 5: the job, the think-through questions, the hazards and the hazard check, a rating
before and after controls for each hazard, a review, the challenge question, then the saved result at
`/take5s/<id>`. The phone remembers only the worker's name. The first screen from task 0002 is at `/rate-risk`.

Saved Take 5s are kept in `backend/.data/take5.sqlite3`, which git ignores. Set `TAKE5_DATABASE_PATH` to use
another file.

### Turn on the AI's question

Without a key the app works, and asks the fixed challenge question every time. To have Claude write the question:

1. Sign in at <https://console.anthropic.com>, add some credit, and set a monthly spend limit under Billing, so a
   mistake can't run up a bill.
2. Make an API key under API keys. Copy it: it is only shown once.
3. Copy the settings template: in PowerShell, in the repo root, `Copy-Item backend\.env.example backend\.env`
   (on a Mac or Linux, `cp backend/.env.example backend/.env`). Open `backend/.env` in VS Code and paste the key
   after `TAKE5_AI_KEY=`. Git ignores `.env`, so the key never goes to GitHub. Never put a key in
   `.env.example` or anywhere else in the repo. (Don't make the file with PowerShell's `>`, which saves it in a
   form the app can't read.)
4. Restart `uv run scripts/dev.py`. The back end's log says which model asks the question.

To use another model, add a line such as `TAKE5_AI_MODEL=claude-sonnet-5-5`. To try the AI on five made-up Take
5s and see what each question costs and how long it takes, run `uv run scripts/try_challenge.py` in the repo
root (name models after it to compare them). Vague hazards are judged by Claude Haiku 5.5 unless a line such as
`TAKE5_AI_HAZARD_MODEL=claude-sonnet-5-5` names another; `uv run scripts/try_vague_hazard.py` tries it on twelve
made-up hazards. `cd backend` then `uv run pytest -m real_ai` runs the two tests that call the real AI. Each of
these costs a little money; the normal tests and CI never call it.

Using VS Code? See [docs/dev-setup.md](docs/dev-setup.md) for the editor set-up and fixes for common problems.

## Test it

In the repo root, `uv run scripts/check.py` runs every check that CI runs, in the same order, and stops at the
first failure. The single commands are listed in [AGENTS.md](AGENTS.md#commands).
