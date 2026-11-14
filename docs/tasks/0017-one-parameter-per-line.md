---
id: 0017
title: Put each parameter on its own line when a Python signature is too long for one line
status: done
owner: claude
branch: claude/project-thread-az3qy9
---

## Goal

Jake set a rule (2026-11-14): a `def` that fits on one line stays on one line. One that doesn't puts each parameter
on its own line with a trailing comma, not all parameters on one indented line:

```python
def create_app(
    repository: Take5Repository | None = None,
    settings: Settings | None = None,
) -> FastAPI:
```

Ruff can enforce this, so nobody has to remember it.

## Acceptance criteria

- [x] `backend/pyproject.toml` turns on Ruff's `COM812` (missing trailing comma). With a trailing comma, Ruff's
  formatter puts each item on its own line.
- [x] `scripts/check.py` runs the lint before the format check, and `.claude/` hooks keep working.
- [x] Every Python file in `backend/` and `scripts/` follows the rule, and all checks pass.
- [x] `docs/decisions.md` records the rule.

## Out of scope

- TypeScript. Prettier already puts each parameter on its own line when they don't fit.

## Notes / assumptions

`COM812` cannot apply to `def` lines only: it also splits calls, lists and dictionaries that are already broken
over several lines. Turning it on changed 118 places in 29 files, 22 of them `def` lines and the rest mostly
calls. Question for Jake: is the same layout fine for calls and collections? Answered 2026-11-14: yes, `COM812`
everywhere (Claude's recommendation), rather than a `def`-only script of our own or no check.

Ruff's documentation warns that `COM812` and its formatter can disagree. Assumption (Claude): the hook runs
`ruff format`, then `ruff check --fix --select COM812`, then `ruff format` again. Formatting first puts a short
`def` that was split by hand back onto one line, so only what is really too long gets a comma; the last format
then splits those items. Running the fix first would keep a short hand-split `def` split. `check.py` runs the
lint before the format check, so a missing comma is reported as `COM812`. Ruff keeps anything with a trailing
comma split, so a signature shortened later stays split until its comma is deleted.

Mechanical reformat: its own commit, made only by the three Ruff commands; every changed file has the same syntax
tree as before. Ruff prints its `COM812` conflict warning on every format run; it is left visible.

Best done soon, before more code is written, and in its own pull request because it touches many files.
