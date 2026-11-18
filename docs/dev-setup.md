# Editor set-up (VS Code)

Open the repository root, not `backend/` or `frontend/`. The workspace settings in `.vscode/settings.json` run
pytest from `backend/` and use Ruff to format and sort imports.

## First time

1. In the repo root, run `uv run scripts/setup.py` (see the [README](../README.md#set-it-up)).
2. Run **Python: Select Interpreter** and pick the executable itself, not the `.venv` folder:
   `backend/.venv/Scripts/python.exe` on Windows, `backend/.venv/bin/python` on Linux or macOS.
   VS Code keeps this choice on your computer; it is not in the repo.
3. Run **Developer: Reload Window**, then **Test: Refresh Tests**.

## Claude Code's hooks

`.claude/settings.json` runs two hooks from `scripts/claude_hooks/`. Before each file tool and Bash or
PowerShell command, a guard blocks anything that names a secret or saved Take 5s, and risky git commands. After
each edit a formatter tidies the file.

- Start Claude Code in the repository root. It reads `.claude/settings.json` from the folder it starts in.
- The hooks need `uv` on your `PATH` and Claude Code 2.1.295 or later. The formatter also needs the install
  step above (`uv sync` in `backend/`, `npm ci` in `frontend/`).
- The pre-approved commands start once you trust the folder in Claude Code. Run `/hooks` to see the hooks.
- If the guard breaks, times out or can't start, it blocks the call rather than letting it through, and says
  why.
- A commit message or PR body that names a secret, such as `.env`, is blocked too. Write the text to a file and
  pass the file: `git commit -F message.txt`, `gh pr create --body-file body.md`.
- Put personal changes in `.claude/settings.local.json`, which git ignores.

## How type checking is set up

Pylance and the command-line checks share one strict Pyright configuration, `[tool.pyright]` in the root
`pyproject.toml`. It points at `backend/src` and `backend/.venv`. From `backend/`, run
`uv run pyright --project ..`, so the repo root is the import root and the launcher's `scripts/` folder is not
mixed up with `backend/scripts/`. The back end's packages and Ruff settings stay in `backend/pyproject.toml`.

## Common problems

| Problem | Fix |
| --- | --- |
| Pylance can't find the app's modules or `pytest` | Do the three steps under First time |
| Tests won't load, and **Output → Python Environments** shows `spawn ... ENOENT` | The selected interpreter is the `.venv` folder. Select the `python` executable inside it (step 2) |
| The Ruff extension reports a missing binary | Update or reinstall the **Ruff** extension and reload. It uses its own bundled copy |
| Imports are sorted twice, or differently | Disable the **isort** extension for this workspace. Ruff already sorts imports |
| `.prettierignore` shows markdown warnings | **Change Language Mode** to **Ignore** (or **Plain Text**) |
| uv warns that `VIRTUAL_ENV` belongs to another environment | Deactivate that environment first. The run script already removes it for the servers |

`frontend/.npmrc` only pins npm to `https://registry.npmjs.org/`. It holds no credentials.

## Automated PR review

Install the [Claude GitHub App](https://github.com/apps/claude) on this repository. Run `claude setup-token`
in the Claude Code terminal CLI and save the result as the Actions secret `CLAUDE_CODE_OAUTH_TOKEN` in GitHub.
Never paste the token into a chat or commit it. Replace it when it expires (currently one year).
Jake confirmed both setup steps are complete on 2026-11-13.

The Agent review workflow reviews opened, updated, reopened and ready PRs. Drafts, forks and pushes from
`claude[bot]` are skipped. A Claude-authored PR is still reviewed when opened or marked ready. Each review has
15 turns and 30 minutes; a newer eligible run cancels the older run for that PR. Skipped bot pushes do not
cancel the reviewer publishing its report. Only trusted collaborators should push branches in this repo.

The reviewer follows `.claude/agents/reviewer.md`, runs all checks and may push certain fixes as new commits.
Its App token allows those pushes to trigger normal CI; the workflow does not substitute `GITHUB_TOKEN`.
Read its single updated comment, check CI on the latest commit and do your final review before merging.
Failed steps update the same marked PR comment with a run link. A failed or cancelled job is not a completed
review. Check the Actions log if no report appears; an abrupt
job timeout can prevent the final comment. Rerun the eligible review from Actions after resolving the cause.

The initial workflow must reach the default branch before App authentication can validate it. The gate also
loads its policy from the PR base revision. Therefore task 0012 itself needs independent review before merge;
confirm the first live review on a subsequent PR, including that a fix push triggers CI without another review.
The guard hooks remain soft safeguards, as described in the decisions log.
