# Architecture

Status: **draft, waiting for Jake's approval** (task 0001). The stack below is *proposed* (spec decision D5);
no dependency is added until Jake approves it.

Two aims shape everything here: Jake wants to be able to read and understand the whole back end, and the risk
scoring has to be provably right. So the design is small, layered, and keeps the rules in plain functions.

## Stack

| Part | Choice | Why |
| --- | --- | --- |
| Language | Python 3.13 or newer | Project rule |
| Web framework | FastAPI | Typed, small, and the same as the original app |
| Pages | Server-rendered HTML with Jinja2 templates, plain CSS, a little plain JavaScript | No build step and no second codebase; pages stay small on a weak signal |
| Data checking | pydantic (comes with FastAPI) | One definition of each shape, checked on the way in |
| Database | SQLite through Python's built-in `sqlite3` | One file, nothing to install, every SQL statement is in the repo to read |
| Packaging | uv | One tool for Python versions, dependencies and running commands |
| Lint and format | ruff | Project rule |
| Type checking | pyright in strict mode | The command-line version of Pylance's strict rules |
| Tests | pytest, with httpx for FastAPI's test client | Standard |

Runtime dependencies to approve: `fastapi`, `uvicorn`, `jinja2`, `python-multipart` (FastAPI needs it to read
form posts). Development dependencies to approve: `ruff`, `pyright`, `pytest`, `httpx`.

The database is the one place the proposal differs from the original app, which used SQLAlchemy and Alembic.
With one table, the built-in `sqlite3` module is less to learn and nothing is hidden. The cost is that table
changes are written by hand. The storage layer sits behind an interface (below), so swapping it later touches
one file.

## Structure

```
src/take5/
    domain/        the rules, as plain data and pure functions
        scales.py      Likelihood, Consequence, RiskBand, ControlKind (enums)
        matrix.py      the 5x5 matrix, rate(), the JHA threshold          (spec R1 to R3)
        card.py        the card's questions, as data
        take5.py       Take5, Hazard, Control: the filled-in card          (spec R4 to R6)
        verdict.py     verdict(take5) -> Verdict with its reasons          (spec V1 to V3)
        thinking.py    the pushback rules                                   (spec T2 to T4)
    services/      what the app does
        take5s.py      Take5Service: submit, get, list
        ports.py       Take5Repository (a Protocol): what the service needs from storage
    storage/       where things are kept
        sqlite.py      SqliteTake5Repository
    web/           what the worker sees
        app.py         builds the FastAPI app and wires the pieces together
        routes.py      one function per page or form post
        forms.py       turns a posted form into a Take5, or a list of form errors
        templates/     Jinja2 pages
        static/        CSS and JavaScript
tests/             mirrors src/take5/
```

## Data model

| Entity | Key fields | Notes |
| --- | --- | --- |
| `Take5` | `id`, `created_at`, `worker_name`, `job`, `location`, `think_through` (question to answer), `hazard_questions` (question to answer), `hazards` | One filled-in card. Never changed after it is saved |
| `Hazard` | `description`, `before` (rating), `controls`, `after` (rating), `weak_controls_reason` | Belongs to one Take 5. `weak_controls_reason` is the worker's answer to spec T3, when it was asked |
| `Control` | `description`, `kind` (`ControlKind`) | Belongs to one hazard |
| `RiskRating` | `likelihood`, `consequence`, and from the matrix: `score`, `band` | A value, not a stored row. Score and band are always worked out, never typed in |
| `Verdict` | `can_start`, `reasons` | Worked out from a `Take5` every time it is shown; not stored |

Storage is one table. The whole Take 5 is saved as one JSON document, with the few columns the list page needs
beside it:

```
take5s(id TEXT PRIMARY KEY, created_at TEXT, worker_name TEXT, job TEXT, document TEXT)
```

A Take 5 is always read and written whole, so splitting it into hazard and control tables would add joins and
code for no benefit yet. If reports across hazards are wanted later ("which hazards come up most"), that is the
time to split it, and it is a recorded decision to revisit.

## Boundaries

A package only imports from packages below it:

```
web       ->  services  ->  domain
storage   ->  services.ports, domain
```

- **`domain`** owns every scoring, verdict and thinking rule. It uses only the standard library and pydantic. It
  never reads a file, a database, a clock or the network, so each rule is a function of its inputs and can be
  tested with a one-line example from the spec.
- **`services`** owns the use cases. It depends on the `Take5Repository` Protocol, not on SQLite.
- **`storage`** owns the SQL. It stores and fetches; it makes no decisions.
- **`web`** owns HTTP and HTML. It holds no rules: a route calls a service and renders what comes back.
- **`web/app.py`** is the only place that knows which real pieces are plugged in (the composition root). Tests
  plug in an in-memory repository instead.

Anything outside the app sits behind a Protocol like `Take5Repository`, so it can be replaced without touching
its callers. The database is the only such thing in the first version. An AI check, when it comes, will be a
`Take5Reviewer` Protocol with one adapter per provider (Claude, ChatGPT, Gemini).

## Testing strategy

| Kind | Covers | How |
| --- | --- | --- |
| Unit, domain | Every worked example in the spec, by number, plus all 25 matrix cells | Parametrised pytest tables that mirror the spec's tables. No fakes needed |
| Unit, services | Submit, get and list | An in-memory `Take5Repository` |
| Integration, storage | A Take 5 saved to SQLite comes back identical | A temporary database file per test |
| End to end, web | A worker fills in every screen and reaches the right verdict; form errors show | FastAPI's test client against the real app with a temporary database |
| Architecture | The import rules under Boundaries | One test that reads the imports of every module |
| Visual | Each changed page looks right on a phone | Screenshots at 360 px wide, attached to the PR; checked by eye, not in CI |

CI runs `ruff check`, `ruff format --check`, `pyright` and `pytest` on every PR and every push to `main`
(task 0002).
