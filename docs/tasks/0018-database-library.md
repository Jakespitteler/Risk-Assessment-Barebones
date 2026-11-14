---
id: 0018
title: Decide whether SQLAlchemy (or a similar library) would make the storage code better or simpler
status: todo
owner:
branch:
---

## Goal

Jake asked (2026-11-14) whether SQLAlchemy or a similar library would improve or simplify the code. Storage today
is one file, `storage/sqlite.py` (about 110 lines), using Python's built-in `sqlite3` with hand-written SQL behind
the `Take5Repository` interface. The 2026-11-13 decision "Store each Take 5 as one JSON document" chose that over
SQLAlchemy and Alembic for one table. This task checks that choice against what is coming, and recommends.

## Acceptance criteria

- [ ] A short comparison in this file of: keeping `sqlite3`, SQLAlchemy Core (SQL built in Python, no objects),
  the SQLAlchemy ORM, and SQLModel (SQLAlchemy with pydantic models). For each: code it would replace, code it
  would add, what it makes easier, what it hides, typing with pyright strict, and how mainstream and lasting it is.
- [ ] The comparison weighs what is coming: the saved Take 5 list (0007), changes to the table (which would need
  migrations, for example Alembic), other cards such as JHAs, and a company database (for example PostgreSQL) for
  a private deployment.
- [ ] A recommendation with the trade-offs, and a small code sample of `add` and `get` in the recommended option.
- [ ] Jake's decision recorded in `docs/decisions.md`. If he chooses a library, a follow-up task to switch is added
  to the order of work; adding the dependency needs his approval there.

## Out of scope

- Switching the code. This task only decides.
- Changing the data model (one JSON document per Take 5).

## Notes / assumptions

Best done before 0007, because the saved Take 5 list is the first query beyond "save one" and "get one", and it is
cheaper to change storage before more code depends on it. Any switch touches only `storage/` and its tests, because
the services and routes only know `Take5Repository`.
