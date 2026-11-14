---
id: 0018
title: Decide whether SQLAlchemy (or a similar library) would make the storage code better or simpler
status: done
owner: claude
branch: claude/project-thread-2vyyeo
---

<!-- cspell:ignore fetchone isoformat tablename -->

## Goal

Jake asked (2026-11-14) whether SQLAlchemy or a similar library would improve or simplify the code. Storage today
is one file, `storage/sqlite.py` (about 130 lines), using Python's built-in `sqlite3` with hand-written SQL behind
the `Take5Repository` interface. The 2026-11-13 decision "Store each Take 5 as one JSON document" chose that over
SQLAlchemy and Alembic for one table. This task checks that choice against what is coming, and recommends.

## Acceptance criteria

- [x] A short comparison in this file of: keeping `sqlite3`, SQLAlchemy Core (SQL built in Python, no objects),
  the SQLAlchemy ORM, and SQLModel (SQLAlchemy with pydantic models). For each: code it would replace, code it
  would add, what it makes easier, what it hides, typing with pyright strict, and how mainstream and lasting it is.
- [x] The comparison weighs what is coming: the saved Take 5 list (0007), changes to the table (which would need
  migrations, for example Alembic), other cards such as JHAs, and a company database (for example PostgreSQL) for
  a private deployment.
- [x] A recommendation with the trade-offs, and a small code sample of `add` and `get` in the recommended option.
- [x] Jake's decision recorded in `docs/decisions.md`. If he chooses a library, a follow-up task to switch is added
  to the order of work; adding the dependency needs his approval there.

## Out of scope

- Switching the code. This task only decides.
- Changing the data model (one JSON document per Take 5).

## How the options were checked

Each library option was written in a scratch folder outside the repo, doing the jobs `storage/sqlite.py` does
(save unless the ID is already saved, get one, find the newest fix) plus the newest-first list that task 0007
needs. Each ran against a real SQLite file and was type checked with pyright 1.1.414 in strict mode. Versions
current on 2026-11-14: SQLAlchemy 2.1.8, SQLModel 0.0.50, Alembic 1.20.1. None of that code is committed.

Size is not a reason to switch. Leaving out docstrings, comments and blank lines, `sqlite.py` has 64 lines of code;
the library versions had 43 to 56, and they skipped the "make the folder on first use" step that `sqlite.py` has.

## Comparison

### Keep `sqlite3` (today)

- **Replaces:** nothing.
- **Adds:** nothing. Task 0007's list is one more SQL statement in the same file.
- **Makes easier:** reading and debugging. Every statement the app runs is in one file, in plain SQL, and there
  is no library to learn, update or watch for breaking changes.
- **Hides:** nothing, so everything is by hand. A change to a table that already holds Take 5s needs a migration
  written by hand (a version number kept in SQLite's `PRAGMA user_version` and a short list of steps, roughly 20
  lines). The SQL is SQLite's: `?` placeholders and `json_extract` would be `%s` and `->>` on PostgreSQL, so a
  second database means a second repository file with the same queries rewritten.
- **Typing with pyright strict:** `sqlite3` returns untyped rows, so each read is annotated by hand
  (`row: tuple[str] | None`) and pyright trusts it. Pydantic then checks the whole document as it comes out,
  which is where a real mistake would show.
- **Mainstream and lasting:** part of Python's standard library since Python 2.5. It will not go away.

### SQLAlchemy Core

- **Replaces:** the four SQL strings, with a `Table` definition and queries built in Python, such as
  `select(take5s.c.document).where(take5s.c.id == str(take5_id))`.
- **Adds:** one dependency (it needs only `typing-extensions`) and an `Engine` that opens connections.
- **Makes easier:** one set of queries for SQLite and PostgreSQL. In the prototype, reading `document["fixes"]`
  compiled to `JSON_EXTRACT` for SQLite and to `->>` for PostgreSQL (compiled only, not run against PostgreSQL).
  Alembic can write migrations by comparing the `Table` with the database (autogenerate). There is no session to
  learn: a query runs when it is called, as with `sqlite3`.
- **Hides:** the SQL itself, which the library writes. "Insert unless the ID is saved" can be written for one
  database (`sqlalchemy.dialects.sqlite.insert(...).on_conflict_do_nothing()`) or, for any database, as "insert,
  and catch `IntegrityError`".
- **Typing with pyright strict:** the weakest library option. A `Table`'s columns are typed `Any`, so
  `select(take5s.c.document)` is `Select[Any]` and a wrong column type passes pyright without a word.
- **Mainstream and lasting:** SQLAlchemy is the standard Python database toolkit (first released 2006, version 2
  in 2023), and Core is the layer the rest of it is built on.

### SQLAlchemy ORM (version 2's typed style)

- **Replaces:** the SQL strings and `_connect()`, with a row class (`Take5Row`, its five columns declared as
  `Mapped[str]`) and a `Session` for each request.
- **Adds:** one dependency, the row class, and the ORM's ideas: sessions, the unit of work and the identity map.
  Relationships and lazy loading exist but would go unused, because a Take 5 is one JSON document in one table.
- **Makes easier:** everything Core does, plus full types. A JHA table would be one more row class.
- **Hides:** more than Core: the session decides when it writes and reads. The well-known surprises (lazy loading,
  stale objects) mostly come with relationships, which this design doesn't use.
- **Typing with pyright strict:** the best. `select(Take5Row.id, Take5Row.job)` is `Select[str, str]`, and pyright
  found nothing to fix.
- **Mainstream and lasting:** the most widely used Python ORM, and what the original Risk-Assessment app uses.

### SQLModel

- **Replaces:** the same as the ORM, with a row class that is also a pydantic model.
- **Adds:** SQLModel on top of SQLAlchemy and pydantic (it needs both).
- **Makes easier:** the shortest prototype (43 lines). Its main selling point, one class as both the API model and
  the table, doesn't fit here: a Take 5 is saved as a document, and `domain/` may import nothing from the app or a
  database library, so `SavedTake5` can't become a table class.
- **Hides:** everything the ORM hides, plus where pydantic stops and SQLAlchemy starts.
- **Typing with pyright strict:** needs workarounds. `__tablename__ = "take5s"` is a type error without a
  `# type: ignore`, and columns look like plain `str`, so sorting needs `col(Take5Row.created_at).desc()`.
- **Mainstream and lasting:** popular in FastAPI tutorials and written by FastAPI's author, but still versioned
  0.0.x five years after its first release in 2021. Jake asked for nothing that looks likely to be replaced.

## What is coming

- **Saved Take 5 list (0007).** One more query. With `sqlite3` it is one more SQL string; no option changes the
  work much.
- **Drafts (0019).** Recommended on the phone, which needs no table change. If Jake chooses the server instead, a
  new drafts table needs no migration (it is made the way `take5s` is, on first use), but it is a second table
  with its own repository code; a draft column on `take5s` would be the first migration.
- **Table changes.** A new field in the Take 5 needs no migration: a field with a default reads old documents, as
  `weak_controls_reason` did in task 0006. A new table doesn't either. Only changing a table that already holds
  rows does, such as a new column beside the document. With `sqlite3` that is a short hand-written step; with
  SQLAlchemy it is Alembic, which brings two more dependencies (Mako and MarkupSafe) and a `migrations/` folder.
- **Other cards such as JHAs.** Each gets its own repository (docs/architecture.md, Ready for later). With
  `sqlite3` each would copy much of `sqlite.py`; a shared helper for "a table of JSON documents" would fix that,
  whichever option is used. With the ORM, each is one row class.
- **A company database (for example PostgreSQL).** The strongest reason for SQLAlchemy. With `sqlite3`, a
  PostgreSQL deployment needs a second file (`storage/postgres.py`) with the same queries in PostgreSQL's SQL,
  plus a driver such as `psycopg`. With SQLAlchemy the queries stay the same, but the `document` column must be
  declared as JSON (PostgreSQL's `->>` doesn't work on plain text), the same driver is still needed, and this was
  only compiled, not run against PostgreSQL. The storage tests could then run against both.

## Recommendation

Keep `sqlite3` for now. When the first of these is planned, switch to the SQLAlchemy ORM (version 2's typed style,
no relationships) with Alembic, as its own task:

1. a deployment on a company database such as PostgreSQL;
2. the first change to a table that already holds rows, such as a new column beside the document;
3. a second table with its own repository: another kind of card, or drafts kept on the server.

**Why not now.** Nothing in the next tasks needs it: 0007 adds one query, and 0019 is recommended on the phone. The
file would get 8 to 21 lines shorter out of 64, which is not a reason on its own. Jake wants to understand the back
end fully, and a handful of plain SQL statements are easier to follow than a query builder and a session's rules. A
switch costs about the same later as now, because only `storage/` and its tests know how Take 5s are stored; the
services and routes only know `Take5Repository`. Later adds two small steps: an Alembic starting point for
databases that already hold Take 5s, and deciding whether `created_at`, `worker_name` and `job` stay nullable
(today they may be empty; the ORM sample's `Mapped[str]` columns may not).

**Why the ORM, when the time comes.** Core and the ORM both get Alembic's autogenerate and an "insert unless
saved" that works on any database. The difference is typing: under pyright strict the ORM's columns have real types,
while Core's are `Any`, so a wrong column type would pass unnoticed. The price is the session and its rules, which
Core doesn't have. Since the project runs pyright strict everywhere, the types win, but this is close, and Core
is a sound choice if Jake prefers fewer ideas to learn. Not SQLModel: it is still 0.0.x, needs type workarounds,
and invites joining the domain model to the table, which the boundaries forbid.

**Trade-off accepted.** Until then the SQL works only on SQLite, and the first migration or PostgreSQL deployment
pays for the switch: one file and its tests, plus Jake's approval of the new dependencies.

### Code sample: `add` and `get` in the recommended option

This is today's code with docstrings left out. The SQL strings are the module constants in `storage/sqlite.py`.

```python
def add(self, take5: SavedTake5) -> SavedTake5:
    with closing(self._connect()) as connection, connection:
        connection.execute(
            _INSERT,  # INSERT ... ON CONFLICT(id) DO NOTHING
            (
                str(take5.id),
                take5.created_at.isoformat(),
                take5.worker_name,
                take5.job,
                take5.model_dump_json(),
            ),
        )
        stored: SavedTake5 | None = _read(connection, take5.id)
    if stored is None:
        raise LookupError(f"Take 5 {take5.id} was not saved.")
    return stored


def get(self, take5_id: UUID) -> SavedTake5 | None:
    with closing(self._connect()) as connection:
        return _read(connection, take5_id)


def _read(connection: sqlite3.Connection, take5_id: UUID) -> SavedTake5 | None:
    row: tuple[str] | None = connection.execute(
        _SELECT_DOCUMENT,  # SELECT document FROM take5s WHERE id = ?
        (str(take5_id),),
    ).fetchone()
    return SavedTake5.model_validate_json(row[0]) if row is not None else None
```

For comparison, the same two methods in the SQLAlchemy ORM, as the prototype ran them:

```python
class Take5Row(Base):
    __tablename__ = "take5s"
    id: Mapped[str] = mapped_column(primary_key=True)
    created_at: Mapped[str]
    worker_name: Mapped[str]
    job: Mapped[str]
    document: Mapped[str] = mapped_column(Text)


def add(self, take5: SavedTake5) -> SavedTake5:
    try:
        with Session(self._engine) as session, session.begin():
            session.add(
                Take5Row(
                    id=str(take5.id),
                    created_at=take5.created_at.isoformat(),
                    worker_name=take5.worker_name,
                    job=take5.job,
                    document=take5.model_dump_json(),
                ),
            )
    except IntegrityError:
        pass  # Already saved: the first one wins.
    stored: SavedTake5 | None = self.get(take5.id)
    if stored is None:
        raise LookupError(f"Take 5 {take5.id} was not saved.")
    return stored


def get(self, take5_id: UUID) -> SavedTake5 | None:
    with Session(self._engine) as session:
        row: Take5Row | None = session.get(Take5Row, str(take5_id))
        return SavedTake5.model_validate_json(row.document) if row is not None else None
```

## Notes / assumptions

Best done before 0007, because the saved Take 5 list is the first query beyond "save one" and "get one", and it is
cheaper to change storage before more code depends on it. Any switch touches only `storage/` and its tests, because
the services and routes only know `Take5Repository`.

The recommendation is recorded in `docs/decisions.md` as proposed by Claude. Jake confirms it by merging this
task's pull request, or chooses another option in the thread, and the decision, this file and the order of work
are changed to match before he merges.
