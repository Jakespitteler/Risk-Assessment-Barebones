# Editor set-up (VS Code)

Open the repository root, not `backend/` or `frontend/`. The workspace settings in `.vscode/settings.json` run
pytest from `backend/` and use Ruff to format and sort imports.

## First time

1. In `backend/`, run `uv sync --locked`.
2. Run **Python: Select Interpreter** and pick the executable itself, not the `.venv` folder:
   `backend/.venv/Scripts/python.exe` on Windows, `backend/.venv/bin/python` on Linux or macOS.
   VS Code keeps this choice on your computer; it is not in the repo.
3. Run **Developer: Reload Window**, then **Test: Refresh Tests**.

## Claude Code's hooks

`.claude/settings.json` runs two hooks from `scripts/claude_hooks/`. Before each tool call a guard blocks
anything that names a secret or saved Take 5s, and risky git commands. After each edit a formatter tidies the
file. They need `uv` on your `PATH` and, on Windows, Git Bash, which comes with Git for Windows. The
pre-approved commands start once you trust the folder in Claude Code. Run `/hooks` in Claude Code to see the
hooks. Put personal changes in `.claude/settings.local.json`, which git ignores.

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
