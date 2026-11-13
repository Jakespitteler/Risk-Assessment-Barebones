# Architecture

Status: **version 1** (task 0001). Jake chose the shape (a Python API with a separate JavaScript front end, spec
decision D5) and asked for well-established tools that can be swapped later without much trouble. The libraries
below were picked on that brief. He approved the front-end list (spec decision D12) and FastAPI, SQLite and
Claude by name; the full back-end list is in `decisions.md`. Adding any other dependency still needs his
approval.

Three aims shape everything here: Jake wants to be able to read and understand the whole back end, the risk
scoring has to be provably right, and no single tool should be hard to replace.

## Stack

The app is two programs that only talk through a web API:

- the **back end**, in Python, which owns every rule and all the data;
- the **front end**, in TypeScript, which owns what the worker sees and taps.

Back end:

| Part | Choice | Why |
| --- | --- | --- |
| Language | Python 3.13 or newer | Project rule |
| API framework | FastAPI | The standard typed Python API framework. It also writes the API's description (OpenAPI) for us |
| Data checking | pydantic, with pydantic-settings for settings | One definition of each shape, checked on the way in. Settings such as the AI key come from the environment |
| Server | uvicorn | The usual server for FastAPI |
| Database | SQLite through Python's built-in `sqlite3` | One file, nothing to install, every SQL statement is in the repo to read |
| AI | One provider's own Python library per adapter, starting with `anthropic` (spec decision D9) | Each provider sits behind the same small interface |
| Packaging | uv | One tool for Python versions, dependencies and running commands |
| Lint and format | ruff | Project rule |
| Type checking | pyright in strict mode | The command-line version of Pylance's strict rules |
| Tests | pytest, with httpx for FastAPI's test client | Standard |

Front end:

| Part | Choice | Why |
| --- | --- | --- |
| Language | TypeScript in strict mode | Type checking for the front end, as pyright gives the back end |
| UI library | React | By far the most widely used, with more than ten years behind it. The least likely to be replaced |
| Build tool | Vite | The standard way to build and run a React app today |
| Styling | Tailwind CSS | Consistent spacing, sizes and colours without a pile of hand-written CSS |
| Talking to the API | TanStack Query | Handles loading, errors and retries for each API call, which matters on a weak signal |
| Screens and URLs | React Router | The long-standing router for React |
| API types | openapi-typescript | Generates the TypeScript types from the back end's API description, so the two can't drift apart |
| Tests | Vitest and React Testing Library for components; Playwright for the whole app in a real browser | Playwright also takes the phone-width screenshots |
| Lint and format | ESLint and Prettier | The long-standing pair |
| Packages | npm | Comes with Node; nothing else to install |

Left out on purpose:

- **Full-stack JavaScript frameworks** (Next.js and the like). They bring a second server and pull back-end logic
  into JavaScript. The back end here is Python, and Jake wants to understand it.
- **A state library** (Redux and the like) and **a form library**. One form does not need them. Add one only when
  a task shows the need.
- **A ready-made component kit.** The app has a handful of controls, and they need to be big, glove-friendly
  and its own. Build those few well.

### How hard each piece is to replace

| Piece | What replacing it touches |
| --- | --- |
| The whole front end (React for something else) | Only `frontend/`. The back end does not know a front end exists |
| The AI provider | One adapter file, its library, one line in `api/app.py` and one setting |
| The database | One file, `storage/sqlite.py` |
| FastAPI | `api/` only. The rules in `domain/` and the use cases in `services/` do not import it |
| TanStack Query, React Router, Tailwind | Each is kept to its own corner of `frontend/` (see Structure) |

The thing that makes this work is the API description. It is the contract between the two halves: the back end
publishes it, the front end's types are generated from it, and either half can be rebuilt as long as it is kept.

## Structure

```
backend/
    pyproject.toml
    src/take5/
        domain/        the rules, as plain data and pure functions
            scales.py      Likelihood, Consequence, RiskBand, ControlKind (enums)
            matrix.py      the 5x5 matrix, rate(), the JHA threshold            (spec R1 to R3)
            card.py        the card's questions, as data
            take5.py       Take5, Hazard, Control: the filled-in card            (spec R4 to R6)
            verdict.py     verdict(take5) -> Verdict with its reasons            (spec V1 to V3)
            thinking.py    the pushback rules                                     (spec T2 to T4)
            challenge.py   what the AI is told, the check on its question,
                           the fallback question, the check on the answer         (spec C1 to C4)
        services/      what the app does
            take5s.py      Take5Service: check a draft, submit, answer, get, list
            ports.py       Take5Repository and ChallengeAsker (Protocols): what the
                           service needs from storage and from an AI
        storage/       where things are kept
            sqlite.py      SqliteTake5Repository
        ai/            one adapter per AI provider
            prompt.py      the instructions every provider is given
            claude.py      ClaudeChallengeAsker
        api/           the web API
            app.py         builds the FastAPI app and plugs the pieces together
            routes.py      one function per endpoint
            schemas.py     the shapes of requests and responses
        settings.py    settings read from the environment (database path, AI provider, AI key)
    tests/             mirrors src/take5/
frontend/
    package.json
    src/
        api/           the generated types and a small typed client (the only place TanStack Query is set up)
        screens/       one file per screen: the four parts of the form, the question, the result, the list
        components/    shared pieces: rating picker, Yes / No / N/A buttons, risk badge
        app.tsx        the routes (the only place React Router is set up)
    e2e/               Playwright tests and screenshots
```

## The API

| Endpoint | What it does |
| --- | --- |
| `GET /api/card` | The card's questions, the control kinds, the likelihood and consequence tables and the matrix |
| `POST /api/take5s/check` | Checks a draft and returns what is missing and which thinking rules apply. Saves nothing |
| `POST /api/take5s` | Checks and saves a Take 5, asks the AI (or the fallback) for its question, and returns both |
| `POST /api/take5s/{id}/answer` | Saves the answer, works out the verdict, and returns the finished Take 5 |
| `GET /api/take5s` | The list, newest first |
| `GET /api/take5s/{id}` | One Take 5 |

**The front end holds no rules.** It gets the matrix and questions from `GET /api/card` and shows a score by
looking it up in what it was sent. It finds out what is missing or needs another look by asking
`POST /api/take5s/check`. So there is exactly one copy of every rule, in Python, under test. The one behaviour
that lives in the front end is spec T1 (hiding the hazard questions until a hazard is written), because it is
about what is on the screen.

While developing, Vite serves the front end and passes `/api` calls on to FastAPI. When hosted, FastAPI serves
the built front-end files itself, so there is still only one program to run.

## Data model

| Entity | Key fields | Notes |
| --- | --- | --- |
| `Take5` | `id`, `created_at`, `worker_name`, `job`, `location`, `think_through` (question to answer), `hazard_questions` (question to answer), `hazards`, `challenge`, `finished_at`, `verdict` | One filled-in card. `finished_at` and `verdict` are empty until the challenge question is answered (spec C6). Never changed once finished |
| `Hazard` | `description`, `before` (rating), `controls`, `after` (rating), `weak_controls_reason` | Belongs to one Take 5. With no controls `after` is `before` (spec R6). `weak_controls_reason` is the worker's answer to spec T3, when it was asked |
| `Control` | `description`, `kind` (`ControlKind`) | Belongs to one hazard |
| `RiskRating` | `likelihood`, `consequence`, and from the matrix: `score`, `band` | A value, not a stored row. Score and band are always worked out, never typed in |
| `Challenge` | `question`, `asked_by` (`ai` or `fallback`), `answer` | Belongs to one Take 5. `answer` is empty until the worker gives one |
| `Verdict` | `can_start`, `reasons` | Worked out once by `domain/verdict.py` when the Take 5 is finished, then saved inside it, so a later rule change never rewrites an old verdict |

Storage is one table. The whole Take 5 is saved as one JSON document, with a few columns beside it for finding
and sorting:

```
take5s(id TEXT PRIMARY KEY, created_at TEXT, worker_name TEXT, job TEXT, document TEXT)
```

A Take 5 is always read and written whole, so splitting it into hazard and control tables would add joins and
code for no benefit yet. If reports across hazards are wanted later ("which hazards come up most"), that is the
time to split it, and it is a recorded decision to revisit.

## Boundaries

What each back-end package may import:

```
domain    ->  nothing in the app
services  ->  domain
storage   ->  services.ports, domain
ai        ->  services.ports
api       ->  services, domain
api/app.py is the one exception: it also imports storage, ai and settings, to plug them in
```

- **`domain`** owns every scoring, verdict, thinking and challenge rule. It uses only the standard library and
  pydantic. It never reads a file, a database, a clock or the network, so each rule is a function of its inputs
  and can be tested with a one-line example from the spec.
- **`services`** owns the use cases. It depends on the `Take5Repository` and `ChallengeAsker` Protocols, not on
  SQLite or on any AI provider.
- **`storage`** owns the SQL. It stores and fetches; it makes no decisions.
- **`ai`** owns talking to a provider. An adapter is given text and returns text. It does not know what a Take 5
  is, and it decides nothing: `domain/challenge.py` checks what comes back, and `services` falls back to the
  fixed question on any failure or after 10 seconds.
- **`api`** owns HTTP. It holds no rules: a route calls a service and returns what comes back.
- **`api/app.py`** is the only place that knows which real pieces are plugged in (the composition root). Tests
  plug in an in-memory repository and a stand-in AI instead.

Anything outside the app sits behind a Protocol, so it can be replaced without touching its callers. There are
two: the database (`Take5Repository`) and the AI (`ChallengeAsker`). Adding ChatGPT or Gemini means adding
`ai/openai.py` or `ai/gemini.py`, its library, and one line in `api/app.py` to plug it in; no rule changes.

The worker's name is never passed to an adapter (spec C1). The AI's key lives in the server's environment and
is never in the repo or sent to the phone.

## Testing strategy

| Kind | Covers | How |
| --- | --- | --- |
| Unit, domain | Every worked example in the spec, by number, plus all 25 matrix cells | Parametrised pytest tables that mirror the spec's tables. No fakes needed |
| Unit, services | Check, submit, answer, get and list, including every way the AI can fail | An in-memory `Take5Repository` and a stand-in `ChallengeAsker` |
| Integration, storage | A Take 5 saved to SQLite comes back identical | A temporary database file per test |
| Integration, API | Each endpoint: the right answers, and the right errors for a bad request | FastAPI's test client against the real app with a temporary database and a stand-in AI |
| Architecture | The import rules under Boundaries | One test that reads the imports of every module |
| Contract | The front end's generated types match the back end | CI regenerates the types and fails if they differ from what is committed |
| Unit, front end | Each component and screen behaves: nothing pre-selected, errors beside fields, T1 | Vitest and React Testing Library |
| End to end | A worker fills in every screen in a real browser and reaches the right verdict | Playwright against the real front end and back end, with a stand-in AI |
| Visual | Each changed screen looks right on a phone | Playwright screenshots at 360 px wide, attached to the PR; checked by eye, not in CI |
| AI adapter | The real provider answers and the adapter reads it | A small test that only runs when a key is set; never in CI |

CI runs, on every PR and every push to `main` (task 0002): for the back end `ruff check`, `ruff format --check`,
`pyright` and `pytest`; for the front end ESLint, Prettier's check, the TypeScript compiler, Vitest, and the
Playwright tests.
