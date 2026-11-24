# Risk-Assessment-Barebones

A Take 5 app for mine-site workers, built by a human with AI coding agents (Claude Code and ChatGPT) working in the
same repo.

The repo is public so people can read it, but it is not open source. The app is the property of Jake Spitteler,
and all rights are reserved: nobody may copy, use or share it without the owner's written permission. See
[LICENSE](LICENSE). For the same reason, pull requests from outside aren't accepted. To report a security problem,
see [SECURITY.md](SECURITY.md).

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

Clone the repo into a folder that isn't synced to the cloud (see below), and start the app from its root folder:

```powershell
mkdir C:\dev
cd C:\dev
git clone https://github.com/Jakespitteler/Risk-Assessment-Barebones.git
cd Risk-Assessment-Barebones
uv run start.py
```

The last line sets up and starts the app, every time you use it (see [Run it](#run-it)). The first time, it
checks for git and Node.js, says what is missing and how to get it, then installs Python 3.13, the back end's and
front end's packages, and the browser the whole-app tests use. After that it installs only what a pull has
changed. The same command works on macOS and Linux; use a folder such as `~/dev` there.

If an install seems broken, `uv run install.py` installs everything again from scratch and says what to do next.
Stop the app first, because Windows won't let it replace files the app is using.

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

`start.py` and `install.py` warn you if they find the repo in one of these folders. They can't tell when macOS syncs
`Desktop` or `Documents`, because those paths don't change.

## Run it

1. In the repo root: `uv run start.py`. If a copy of the app was left running, such as by a terminal closed
   without Ctrl+C, it stops that copy first; if another program holds port 8000 or 5173, it says so and stops. Then
   it brings the installs in line with the lock files (the exact versions the repo was tested with; it
   never upgrades a package), then starts the back end and the front end.
2. When it prints "The Take 5 app is ready", open the address on that line, <http://localhost:5173>. It is the
   only address it prints. In a GitHub Codespace it prints the Codespace's forwarded address instead.

Press Ctrl+C to stop. Both halves restart by themselves when their code changes. The API's own pages, for working
on the back end, are at <http://localhost:8000/docs>.

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
4. Restart `uv run start.py`. The back end's log says which model asks the question.

To use another model, add a line such as `TAKE5_AI_MODEL=claude-sonnet-5-5`. To try the AI on five made-up Take
5s and see what each question costs and how long it takes, run `uv run scripts/try_challenge.py` in the repo
root (name models after it to compare them). Vague hazards are judged by Claude Haiku 5.5 unless a line such as
`TAKE5_AI_HAZARD_MODEL=claude-sonnet-5-5` names another; `uv run scripts/try_vague_hazard.py` tries it on twelve
made-up hazards. Photos of paper cards are read by the main model unless a line such as
`TAKE5_AI_SCAN_MODEL=claude-fable-5-2` names another. `uv run test.py backend -m real_ai` runs the two tests
that call the real AI. Each of these costs a little money; the normal tests and CI never call it.

To use ChatGPT's models instead of Claude's, make the key at <https://platform.openai.com> (with credit and a
monthly limit, as above), paste it after `TAKE5_AI_KEY=`, and add the line `TAKE5_AI_PROVIDER=chatgpt` to the same
settings file. An OpenAI API key is billed by use, apart from any ChatGPT subscription. Every AI job then uses
OpenAI's `gpt-6.2-astra`, and vague hazards `gpt-6-luna`; the model lines above take OpenAI's model names. The
try scripts try Claude only, so they stop when ChatGPT is chosen.

The ranking page ranks every saved Take 5 while the app is a proof of concept. To rank only today's, add the
line `TAKE5_RANK_TODAY_ONLY=true` to `backend/.env` and start the app again. Risk by area likewise counts every
saved Take 5; the line `TAKE5_AREA_LAST_30_DAYS_ONLY=true` makes it count only the last 30 days.

Using VS Code? See [docs/dev-setup.md](docs/dev-setup.md) for the editor set-up and fixes for common problems.

## Test it

Every command runs from the repo root:

- `uv run test.py` runs every test: the back end's, the front end's, then the whole app in a browser.
  `uv run test.py backend`, `frontend` or `e2e` runs one kind, and passes anything after it to that kind's test
  tool, such as `uv run test.py backend tests/domain`.
- `uv run check.py` runs every check that CI runs, in the same order, and stops at the first failure.
- `uv run check.py --fix` formats the code, makes the fixes the lint tools can make by themselves, and writes the
  API types again.
- `uv run check.py --no-front-end` runs every check except the front end's, with no npm install or browser
  needed. CI uses it for a pull request that changes only Markdown.

The single commands are listed in [AGENTS.md](AGENTS.md#commands).
