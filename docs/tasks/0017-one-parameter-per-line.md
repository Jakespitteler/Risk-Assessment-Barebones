---
id: 0017
title: Put each parameter on its own line when a Python signature is too long for one line
status: todo
owner:
branch:
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

- [ ] `backend/pyproject.toml` turns on Ruff's `COM812` (missing trailing comma). With a trailing comma, Ruff's
  formatter puts each item on its own line.
- [ ] `scripts/check.py` runs the lint before the format check, and `.claude/` hooks keep working.
- [ ] Every Python file in `backend/` and `scripts/` follows the rule, and all checks pass.
- [ ] `docs/decisions.md` records the rule.

## Out of scope

- TypeScript. Prettier already puts each parameter on its own line when they don't fit.

## Notes / assumptions

`COM812` cannot apply to `def` lines only: it also splits calls, lists and dictionaries that are already broken
over several lines. A trial run changed 98 places in 28 files (about 320 lines), mostly calls. Question for Jake:
is the same layout fine for calls and collections? If not, the rule can only be written down in AGENTS.md, and no
check will catch it.

Ruff's documentation warns that `COM812` and its formatter can disagree. Running `ruff check --fix` before
`ruff format` gives a stable result, so `check.py` and the format-on-save hook must run them in that order.

Best done soon, before more code is written, and in its own pull request because it touches many files.
