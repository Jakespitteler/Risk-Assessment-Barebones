# Decisions

Newest first. One short entry per non-obvious decision.

## 2026-11-13: Store each Take 5 as one JSON document (proposed)
- Decision: One SQLite table, `take5s`, holding the whole Take 5 as JSON beside the columns the list page needs.
- Why: A Take 5 is always read and written whole. Separate hazard and control tables would add joins and code
  with no benefit yet.
- Alternatives considered: Separate tables per entity. Better for reports across hazards; revisit when a report
  is wanted.
- Decided by: proposed by claude, waiting for human approval

## 2026-11-13: Stack (proposed)
- Decision: Python 3.13+, FastAPI, server-rendered Jinja2 pages with plain CSS and JavaScript, SQLite through the
  built-in `sqlite3` module, uv, ruff, pyright strict, pytest. Dependencies: `fastapi`, `uvicorn`, `jinja2`,
  `python-multipart`; for development `ruff`, `pyright`, `pytest`, `httpx`.
- Why: The whole back end is Python that can be read top to bottom, there is no build step or second codebase,
  and it is the same family as the original Risk-Assessment app, so nothing new has to be learned.
- Alternatives considered: A Python API with a JavaScript front end (slicker interactions, but two codebases).
  SQLAlchemy and Alembic as in the original app (handles table changes, but hides the SQL and is more to learn
  for one table).
- Decided by: proposed by claude, waiting for human approval

## 2026-11-13: Unlikely / Critical scores 19, not the printed 18
- Decision: The matrix cell for Unlikely / Critical is recorded as 19.
- Why: The printed card shows 18 there, which repeats Possible / Major and leaves 19 unused. Every other cell is
  a unique rank from 1 to 25. The band (Extreme) is the same either way.
- Alternatives considered: Keep the printed 18. Two cells would then tie, and "a higher score is a higher risk"
  would have one exception.
- Decided by: carried over from the original Risk-Assessment app; waiting for human confirmation here
