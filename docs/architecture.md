# Architecture

Status: **version 1** (task 0001). Jake chose the shape (a Python API with a separate JavaScript front end, spec
decision D5) and asked for well-established tools that can be swapped later without much trouble. The libraries
below were picked on that brief. He approved the front-end list (spec decision D12) and FastAPI, SQLite and
Claude by name; the full back-end list is in `decisions.md`. Adding any other dependency still needs his
approval.

Four aims shape everything here: Jake wants to be able to read and understand the whole back end, the risk
scoring has to be provably right, no single tool should be hard to replace, and the Take 5's building blocks
should be reusable by what may come later (other companies' Take 5s, JHAs, hazard report cards, journey plans).
[Ready for later](#ready-for-later) says how far that last aim is taken, and where it deliberately stops.

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
| Tests | pytest, with httpx2 for FastAPI's test client | Standard. httpx2 replaced httpx in task 0002; see `decisions.md` |

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
| The AI provider | One file in `ai/providers/`, its library, one line in `api/app.py` and one setting |
| The database | One file, `storage/sqlite.py` |
| FastAPI | `api/` only. The rules in `domain/` and the use cases in `services/` do not import it |
| TanStack Query, React Router, Tailwind | Each is kept to its own corner of `frontend/` (see Structure) |

The thing that makes this work is the API description. It is the contract between the two halves: the back end
publishes it, the front end's types are generated from it, and either half can be rebuilt as long as it is kept.

## Structure

```text
backend/
    pyproject.toml
    src/risk_assessment/
        domain/            the rules, as plain data and pure functions
            risk.py            RiskMatrix (a matrix as data), RiskCell, RiskRating,
                               rate()                                                 (spec R1 to R3)
            controls.py        ControlKind, Control, which kinds are strong
            questions.py       Question, QuestionRole (stop or hazard), Answer
            wording.py         the vague phrases and word counting                     (used by T2, T4, C4)
            take5/             everything that is only about a Take 5
                template.py        Take5Template: the questions, the matrix and the guidance a
                                   Take 5 is filled in on. BOOKLET_TEMPLATE is the only one for now
                take5.py           Take5, Hazard: the filled-in card                      (spec R4 to R6)
                draft.py           Take5Draft (what the phone sends) and check_draft(): every
                                   gap, warning and thinking question by field path       (spec R5, R6, V2, T2 to T4)
                fix.py             which saved Take 5 a new one may fix                   (spec F3)
                time_limit.py      when a draft has run out, given the time now           (spec K2)
                saved.py           SavedTake5: a Take 5 as it was saved, with its verdict
                verdict.py         verdict(take5) -> Verdict with its reasons            (spec V1 to V3)
                thinking.py        the pushback rules                                     (spec T2 to T4)
                challenge.py       what the AI is told, the check on its question,
                                   the fallback question, the check on the answer         (spec C1 to C4)
        services/          what the app does
            take5s.py          Take5Service: check a draft, submit, answer, get, list. It is
                               given a clock, so tests can set the time
            ports.py           Take5Repository and ChallengeAsker (Protocols): what the
                               service needs from storage and from an AI
        storage/           where things are kept
            sqlite.py          SqliteTake5Repository
        ai/                everything that talks to an AI
            model.py           LanguageModel (a Protocol): instructions and text in, text out
            challenge.py       the challenge question's instructions, and a ChallengeAsker
                               that works with any LanguageModel
            providers/
                claude.py          ClaudeModel, the first LanguageModel
        api/               the web API
            app.py             builds the FastAPI app and plugs the pieces together
            take5_routes.py    one function per Take 5 endpoint
            schemas.py         the shapes of requests and responses, including the error replies
            errors.py          turns errors into the declared error replies
        settings.py        settings read from the environment (database path, AI provider, AI key)
    tests/                 mirrors src/risk_assessment/
        samples.py         the made-up Take 5s that tests in more than one folder share
        api/conftest.py    the API tests' set-up: an empty database and a client for each test
frontend/
    package.json
    src/
        api/               the generated types and a small typed client (the only place TanStack Query is set up)
        components/        pieces any feature can use: rating picker, Yes / No / N/A buttons, risk badge,
                           control editor, button, card, field, guidance, notice, warning, undo bar,
                           and the screen with its top bar
        features/take5/    the Take 5's screens: the four parts of the form, the question, the result, and
                           the list of saved Take 5s (SavedTake5sScreen.tsx). formatDateTime.ts writes
                           every date the one way the spec sets (D17)
                           stage.ts is which page shows (kept in the URL); useTake5Draft.ts keeps the one
                           draft on the phone (localStorage), with its start time and the page it was left on.
                           LeavePanel.tsx asks keep or throw away; RunOutPanel.tsx and runOut.ts show a draft
                           the back end says has run out; KeptDraftCard.tsx is the draft at the top of the list;
                           TimeLeft.tsx counts down to the check's runs_out_at; UncheckedNotice.tsx says a kept
                           draft couldn't be checked;
                           WeakControlsQuestion.tsx draws the server's thinking prompt on the controls page,
                           checking once typing pauses (useSettledValue.ts)
        test-utils.tsx     the fake card, drafts and API replies the Vitest tests share
        app.tsx            the routes (the only place React Router is set up)
    e2e/                   Playwright tests and screenshots
scripts/
    dev.py                 starts both halves for development
    check.py               runs every check, as CI does
    agent_review.cjs       decides which PR events may start the CI reviewer
    claude_hooks/          Claude Code's hooks (set in .claude/settings.json): a guard that blocks
                           secrets and risky git commands, and a formatter that runs after each edit
```

The four files directly under `domain/` know nothing about a Take 5. They are the shared building blocks, and
`domain/take5/` is built from them. The same split is in the front end: `components/` is shared and
`features/take5/` is not.

## The API

| Endpoint | What it does |
| --- | --- |
| `GET /api/take5/template` | The template a new Take 5 is filled in on: its questions, its matrix and its guidance, plus the answers a question can have and the control kinds |
| `POST /api/take5s/check` | Checks a draft and returns what is missing, its warnings (allowed, but they will stop the job) and which thinking rules apply. A draft that has run out (spec K2) has an error on `started_at`, and `runs_out_at` says when it runs out (empty with no time limit). Saves nothing |
| `POST /api/take5s` | Checks and saves a Take 5, asks the AI (or the fallback) for its question, and returns both |
| `POST /api/take5s/{id}/answer` | Saves the answer, works out the verdict, and returns the finished Take 5 |
| `GET /api/take5s` | The list, newest first. Each line is a `Take5Summary`: the ID, when it was saved, the worker, the job, the verdict (`can_start`) and whether a newer Take 5 fixes it (`fixed`), not the whole card |
| `GET /api/take5s/{id}` | One Take 5, with `fixed_by` (the newest Take 5 that fixes it, if any) and `offers_fix` (whether its result offers a fix) |

Every error reply is declared in the OpenAPI description, so the front end's generated types know it. A 422 is
always `FormErrors` (`detail` and a list of field errors, each with its dotted `path`), whether the draft has a
gap or the request couldn't be read. A 404 or a 409 is `ErrorMessage` (`detail`). The front end retries a
request that got no answer, never one that did; `POST /api/take5s` is safe to retry because the phone makes its
ID once and sends it every time.

The check also returns `thinking_questions`: each has the answer's dotted `path` and the question's
`message`. A question stays present when answered, while an unanswered required question also has a field
error. `HazardDraft` and saved `Hazard` carry `weak_controls_reason`, defaulting to an empty string for older
drafts and documents. The phone's draft keeps the answer even if a later edit adds a strong control, so editing
never discards the worker's words, but the rated `Hazard` (and so the saved Take 5) keeps it only while T3 still
asks. It never changes the verdict.

**The front end holds no rules and no card.** It gets the questions and the matrix from
`GET /api/take5/template`, draws whatever it is sent, and shows a score by looking it up in that matrix. It finds
out what is missing or needs another look by asking
`POST /api/take5s/check`. So there is exactly one copy of every rule, in Python, under test. A few behaviours live
in the front end, because they are about what is on the screen: spec T1 (hiding the hazard questions until a
hazard is written), skipping the after-controls page of a hazard with no controls, putting each question on the
page for its role (stop questions on the think-through page, hazard questions after the hazard list), and
showing "Make sure it's on your list" after a Yes to a hazard question, then "Added to your list" once a hazard
has been added from it (spec D15). The back end still decides that the after rating of a hazard with no controls
is its before rating (R6).

**Drafts (task 0019).** The phone keeps one draft in `localStorage` from the worker's first change, which also
stamps `Take5Draft.started_at` by the phone's clock (with its time zone; a time without one is a 422). Opening the
app with no page in the URL carries on from the page the draft was left on. The phone never decides whether a
draft has run out: it checks the draft once as it opens, on a Continue with changed answers (an unchanged one reuses the
last answer), and on Finish, and acts on an error
whose path is `started_at`. The back end compares `started_at` with its own clock against the template's
`draft_time_limit_minutes` (`domain/take5/time_limit.py`, with the time given by the service). The check only
trusts the phone's clock to be roughly right, which phones that set their time from the network are. Leave and
Undo, carrying on, and asking before a fix replaces the draft are about what is on the screen, so they live in
the front end. Before saying a draft has run out, the phone looks its submission ID up with
`GET /api/take5s/{id}`, and opens the saved result if the save went through and only its answer was lost. The
time left is counted down from the check's `runs_out_at`, which the back end works out.

While developing, Vite serves the front end and passes `/api` calls on to FastAPI. When hosted, FastAPI serves
the built front-end files itself, so there is still only one program to run.

## Data model

| Entity | Key fields | Notes |
| --- | --- | --- |
| `Take5` | `id`, `created_at`, `worker_name`, `job`, `location`, `answers` (question ID to answer), `hazards`, `challenge`, `finished_at`, `verdict`, `template` | One filled-in card. `template` is a copy of the template it was filled in on, so it always shows the questions and matrix the worker was given. `finished_at` and `verdict` are empty until the challenge question is answered (spec C6). Never changed once finished |
| `SavedTake5` (task 0004) | Extends the scoring `Take5` with `id`, `created_at`, `worker_name`, `job`, `location`, `finished_at`, `verdict`, `fixes`, `started_at` | The implemented submitted document. Until task 0008 it is finished immediately. The base `Take5` holds what the verdict needs (the template, `answers` and the hazards); later tasks add the remaining card fields. `answers` (task 0005) has one answer for each of the template's questions, by question ID. A Take 5 saved before task 0005 has none, and its template copy has no questions, so it still opens. `fixes` (task 0010) is the ID of the Don't start yet it fixes, or empty. It points back only, so the first one is never changed; its fix is found by searching for its ID in `fixes`. `started_at` (task 0019) is when its draft was started, by the phone's clock, or empty for one saved before then (spec K3) |
| `Hazard` | `description`, `before` (rating), `controls`, `after` (rating), `weak_controls_reason` | Belongs to one Take 5. With no controls `after` is `before` (spec R6). `weak_controls_reason` is the worker's answer to spec T3, when it was asked |
| `Control` | `description`, `kind` (`ControlKind`) | Belongs to one hazard |
| `RiskRating` | `likelihood`, `consequence`, and from the matrix: `score`, `band` | A value, not a stored row. Score and band are always worked out, never typed in |
| `Take5Template` | `name`, `questions` (each an `id`, its `text` and its `role`: `stop` or `hazard`), `matrix`, `likelihood_guidance`, `consequence_guidance` (each a level and its meaning), `control_guidance`, `draft_time_limit_minutes` | The card as data. The rules never name a question: a *stop* question answered No stops the job, whichever card it is on. The page a question shows on follows from its role, so there are no separate sections. `draft_time_limit_minutes` (task 0019) is how long a draft lasts (spec K2): 120 on the booklet, or none, which turns the check off. `GET /api/take5/template` leaves it out and the phone never reads it, though the copy of the template inside a checked or saved Take 5 carries it |
| `RiskMatrix` | the likelihood and consequence scales, the score and band of each cell, the score that needs a JHA | The matrix as data. `rate()` is given the matrix, so another company's matrix needs no new code |
| `Challenge` | `question`, `asked_by` (`ai` or `fallback`), `model`, `instructions_version`, `answer` | Belongs to one Take 5. `answer` is empty until the worker gives one. `model` and `instructions_version` say which AI asked and with which version of its instructions; both are empty for the fallback |
| `Verdict` | `can_start`, `reasons` | Worked out once by `domain/take5/verdict.py` when the Take 5 is finished, then saved inside it, so a later rule change never rewrites an old verdict |

Storage is one table. The whole Take 5 is saved as one JSON document, with a few columns beside it for finding
and sorting:

```text
take5s(id TEXT PRIMARY KEY, created_at TEXT, worker_name TEXT, job TEXT, document TEXT)
```

A Take 5 is always read and written whole, so splitting it into hazard and control tables would add joins and
code for no benefit yet. If reports across hazards are wanted later ("which hazards come up most"), that is the
time to split it, and it is a recorded decision to revisit.

## Boundaries

What each back-end package may import:

```text
domain        ->  nothing in the app
domain/take5  ->  the shared files in domain (never the other way round)
services      ->  domain
storage       ->  services.ports, domain
ai            ->  services.ports
ai/providers  ->  ai/model.py only
api           ->  services, domain
api/app.py is the one exception: it also imports storage, ai and settings, to plug them in
```

- **`domain`** owns every scoring, verdict, thinking and challenge rule. It uses only the standard library and
  pydantic. It never reads a file, a database, a clock or the network, so each rule is a function of its inputs
  and can be tested with a one-line example from the spec. A rule about time, such as K2, is given the time.
- **`services`** owns the use cases. It depends on the `Take5Repository` and `ChallengeAsker` Protocols, not on
  SQLite or on any AI provider.
- **`storage`** owns the SQL. It stores and fetches; it makes no decisions.
- **`ai`** owns talking to an AI, in two layers. A *provider* (`ai/providers/claude.py`) is a `LanguageModel`: it
  is given instructions and text and returns text, and knows nothing about this app. A *job* (`ai/challenge.py`)
  holds the instructions for one task and works with any provider. Neither decides anything:
  `domain/take5/challenge.py` checks what comes back, and `services` falls back to the fixed question on any
  failure or after 10 seconds.
- **`api`** owns HTTP. It holds no rules: a route calls a service and returns what comes back.
- **`api/app.py`** is the only place that knows which real pieces are plugged in (the composition root). Tests
  plug in an in-memory repository and a stand-in AI instead.

Anything outside the app sits behind a Protocol, so it can be replaced without touching its callers. There are
two: the database (`Take5Repository`) and the AI (`ChallengeAsker`, filled by any `LanguageModel`). Adding
ChatGPT, Gemini, or a model a company runs itself means adding one file in `ai/providers/`, its library, and one
line in `api/app.py` to plug it in; no rule and no job changes.

The worker's name is never passed to an adapter (spec C1). The AI's key lives in the server's environment and
is never in the repo or sent to the phone.

## Ready for later

None of this is built in version 1. It is here so that version 1 is built in a way that does not block it.

| Later feature | What it reuses | What it would add |
| --- | --- | --- |
| A company's own Take 5 | `Take5Template` and `RiskMatrix` are data, and every rule works from question roles and the template's matrix | A stored template per company, a screen to edit one, and a way to pick the worker's company |
| A template made from a photo, Word file or PDF of a blank card | `LanguageModel`, with images and files added to what it accepts | One new job, `ai/template_reader.py`, that turns the document into a draft `Take5Template`. A person always checks and edits the draft before anyone fills it in |
| JHAs, hazard report cards, journey plans | `domain/risk.py`, `controls.py`, `questions.py`, `wording.py`; `ChallengeAsker`; the front end's `components/` | Its own `domain/<kind>/`, service, repository, routes and `features/<kind>/` |
| A company's risk standards given to the AI | `LanguageModel`; the job in `ai/challenge.py` | A `StandardsSource` Protocol: given a Take 5, return the passages that matter. See below |
| An AI the company runs or rents privately | `LanguageModel` | One file in `ai/providers/` |
| Feedback on the AI's questions, used to improve them | Each `Challenge` already records the model and the version of the instructions that asked | A rating on each question, a place to read the ratings, and a set of sample Take 5s that every new version of the instructions is tested against before it goes live. A person changes the instructions; the app does not rewrite them itself |

**What the AI is given, and keeping it trustworthy.** Four ways an AI's context can go wrong, and what stops each.
Version 1 covers the first three because the AI's job is small: one question, one call, nothing remembered
between Take 5s.

| Risk | What it means | What stops it |
| --- | --- | --- |
| Poisoning | Wrong or hostile text gets in and is relied on | C2 checks every reply before it is shown. The AI's text is never fed into another AI call and never decides the verdict. A worker could type instructions into the job ("ignore your rules"); the instructions in `ai/challenge.py` must treat the Take 5 as data, and C2 limits any reply to one short question |
| Distraction | Too much in front of the model | Each call sends one Take 5 and nothing builds up, so nothing needs compacting |
| Confusion | Irrelevant material mixed in | Only that Take 5's own fields are sent (C1) |
| Clash | Sources that disagree | One source today. When company standards arrive, `StandardsSource` picks only the sections that matter. What happens when a standard and the card disagree is a product decision for then |

If the app later has several AI jobs or a large body of standards, give the model a short index first and load
the full text only when a job needs it (the "progressive disclosure" idea behind Agent Skills), rather than
sending everything every time.

**Where the reuse deliberately stops.** The shared pieces are small things that are the same in every risk
document: a matrix, a control, a Yes / No question, a check on wording. There is no general "document" or "form
engine" that a Take 5 is configured out of. That would make the Take 5's own code harder to read and test, for
features that may never be built. When a second kind of document is actually added, whatever it and the Take 5
turn out to share gets pulled out then, with two real examples to shape it.

**Company risk standards: all of it, or only the relevant parts?** Not decided; this is how to decide it. Giving
the AI the whole standard every time is the simplest, but models get less reliable as more is put in front of
them, and it costs more per question. A vector index finds passages by meaning, but it can miss the one clause
that matters, it needs an embedding model (one more outside service, or one more thing to run), and its misses
are hard to test for. A company's standards are usually a modest number of pages under clear headings, so the
first thing to try is the plainest: split the standard at its headings and pick the sections that match the
Take 5's hazards, on our own server. `StandardsSource` hides which method is used. The choice is made by
measuring: a set of sample Take 5s, each with the section that should be found, run through each method. Move to
a vector index only if the plain method misses, and then keep it inside the database the app already has
rather than adding a separate vector database.

**Keeping company information private.** Three things together make this possible. The app and its database are
hosted where the company chooses. The app sends the AI as little as it can, and never the worker's name. And the
AI provider is one file: it can be a provider's business service, a model reached through the company's own
cloud account, or a model the company runs itself.

## Testing strategy

| Kind | Covers | How |
| --- | --- | --- |
| Unit, domain | Every worked example in the spec, by number, plus all 25 matrix cells. Also one made-up template and matrix, to prove nothing about the booklet is hard-coded in the rules | Parametrised pytest tables that mirror the spec's tables. No fakes needed |
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
