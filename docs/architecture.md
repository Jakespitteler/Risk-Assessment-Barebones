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
| AI | One provider's own Python library per adapter, starting with `anthropic` (spec decision D9; added in task 0009) | Each provider sits behind the same small interface |
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
| Accessibility checks | `@axe-core/playwright` (Deque's axe), a development dependency only (task 0024) | The mainstream checker; it checks the screens as drawn, in both modes |
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
    dev_logging.json       the back end's log settings for start.py: one line format, uvicorn's
                           status lines turned down, failed requests only (see Logging)
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
                                   gap, warning and thinking question by field path (spec R5, R6, V2, T2 to T5)
                hazard_nudges.py   which hazards T6 judges, the text the AI is given about one
                                   (without the worker's name), the check on its one-word reply,
                                   and the nudges (vague, stock or unfit), with the word rule
                                   when the AI can't decide; the flags kept on submit (spec T6, T7)
                fix.py             which saved Take 5 a new one may fix                   (spec F3)
                time_limit.py      when a draft has run out, given the time now           (spec K2)
                saved.py           SavedTake5: a Take 5 as it was saved, with its verdict
                verdict.py         verdict(take5) -> Verdict with its reasons            (spec V1 to V3)
                thinking.py        the pushback rules                                     (spec T2 to T6)
                challenge.py       what the AI is told (the Take 5 as JSON, without the
                                   worker's name), the check on its question,
                                   the fallback question, the check on the answer         (spec C1 to C4)
                ranking.py         the fixed score and its line, what the AI is given to rank,
                                   and the check on its order and lines; the best's shortlist,
                                   its line and the check on the AI's pick; the typical time (spec W1 to W9)
                areas.py           Take 5s grouped by area, hottest first; no AI        (spec A1 to A5)
        services/          what the app does
            take5s.py          Take5Service: check a draft, nudge, submit, answer, get, list. It is
                               given a clock, so tests can set the time
            hazard_nudges.py   HazardNudger: asks the AI about each hazard for up to 5 seconds,
                               remembers its verdicts until the server restarts      (spec T6)
            ranking.py         Take5RankingService: today's Take 5s by the fixed rules, then the
                               worst 10 ordered and the best picked by the AI, side by side, for
                               up to 20 seconds; remembers the result until the server restarts
                                                                                      (spec W6 to W9)
            areas.py           AreaRiskService: the last 30 days by area             (spec A2)
            ports.py           Take5Repository, ChallengeAsker, HazardJudge and Take5Ranker (Protocols): what
                               the service needs from storage and from an AI; AiReplyError, the
                               AI failures it expects
            ai_failures.py     names the kind of AI failure for its one log line
        storage/           where things are kept
            sqlite.py          SqliteTake5Repository
        ai/                everything that talks to an AI
            model.py           LanguageModel (a Protocol): instructions and text in, text out;
                               LanguageModelError for a reply with no usable text
            challenge.py       the challenge question's instructions and their version, and
                               AiChallengeAsker, a ChallengeAsker that works with any LanguageModel
            vague_hazard.py    the hazard-check instructions (vague, stock or unfit) and their
                               version, and AiHazardJudge, a HazardJudge that works with any
                               LanguageModel                                         (spec T6, T7)
            ranking.py         the ranking and best-pick instructions and their versions, and
                               AiTake5Ranker, a Take5Ranker that works with any LanguageModel
                                                                                      (spec W6, W8)
            providers/
                claude.py          ClaudeModel, the first LanguageModel: one Messages API call, an
                                   11-second network limit and no retries. QUICK_MODEL names the
                                   model for short jobs (Haiku 5.5)
        api/               the web API
            app.py             builds the FastAPI app and plugs the pieces together
            take5_routes.py    one function per Take 5 endpoint
            ranking_routes.py  the ranking endpoint                                   (spec W1 to W9)
            area_routes.py     the risk-by-area endpoint                              (spec A1 to A5)
            schemas.py         the shapes of requests and responses, including the error replies
            errors.py          turns errors into the declared error replies; names the request
                               of an unexpected error in one log line above its trace
            request_log.py     FailedRequestsOnly: keeps the server's request lines to failures
        settings.py        settings read from the environment or `backend/.env`, which git ignores
                           (database path, AI provider, AI model, hazard AI model, AI key, rank today only)
    tests/                 mirrors src/risk_assessment/
        conftest.py        hides any AI key from every test not marked `real_ai`
        samples.py         the made-up Take 5s that tests in more than one folder share
        ai/fake_anthropic.py  a stand-in for Anthropic's API, so the real adapter runs with no network
        api/conftest.py    the API tests' set-up: an empty database and a client for each test
frontend/
    package.json
    src/
        api/               the generated types and a small typed client (the only place TanStack Query is set up)
        components/        pieces any feature can use: rating picker, Yes / No / N/A buttons, risk badge,
                           control editor, button, card, field, guidance, notice, warning, undo bar,
                           the screen with its top bar, and the light or dark switch in it (ThemeSwitch.tsx)
        theme/             light or dark (spec F7): colourScheme.ts decides which to show and keeps the
                           worker's choice on the phone (localStorage); useColourScheme.ts follows the phone
        index.css          every colour, named by its job (page, ink, danger and so on), each with a light and
                           a dark value. Components use these names, never a shade such as `bg-stone-100`; only
                           the risk band colours in RiskBadge.tsx are fixed, the same in both modes
        features/take5/    the Take 5's screens: the four parts of the form, the question, the result, and
                           the list of saved Take 5s (SavedTake5sScreen.tsx), and today's best and
                           worst first (ReviewTodayScreen.tsx, spec F8), and risk by area
                           (RiskByAreaScreen.tsx, spec F9). formatDateTime.ts writes
                           every date the one way the spec sets (D17)
                           stage.ts is which page shows (kept in the URL); useTake5Draft.ts keeps the one
                           draft on the phone (localStorage), with its start time, the page it was left on and
                           the furthest step reached, which StepBar.tsx lets the worker tap back to
                           LeavePanel.tsx asks keep or throw away; RunOutPanel.tsx and runOut.ts show a draft
                           the back end says has run out; KeptDraftCard.tsx is the draft at the top of the list;
                           TimeLeft.tsx counts down to the check's runs_out_at; UncheckedNotice.tsx says a kept
                           draft couldn't be checked;
                           WeakControlsQuestion.tsx draws the server's thinking prompt on the controls page,
                           checking once typing pauses (useSettledValue.ts)
                           ChallengeScreen.tsx asks the challenge question; ChallengeSummary.tsx shows it with
                           its answer on the result; unanswered.ts remembers which unanswered Take 5s this
                           phone submitted, so only it answers them and opening the app goes back to one
        dev/               startLogger.ts: Vite's terminal output while developing (only
                           vite.config.ts imports it; not part of the app)
        test-utils.tsx     the fake card, drafts and API replies the Vitest tests share
        test-phone-scheme.ts  a stand-in for the phone's light or dark setting, which Vitest's jsdom lacks
        app.tsx            the routes (the only place React Router is set up)
    index.html             also sets light or dark before the app draws, so a dark phone never flashes white
    e2e/                   Playwright tests and screenshots, run once on a light phone and once on a dark one
scripts/
    try_challenge.py       asks the real AI about five made-up Take 5s and prints each question, its time
                           and its cost, to compare models or versions of the instructions
    try_vague_hazard.py    asks the real AI about twelve made-up hazards and prints each verdict beside
                           the word rule's, with its time and cost
    agent_review.cjs       decides which PR events may start the CI reviewer
    claude_hooks/          Claude Code's hooks (set in .claude/settings.json): a guard that blocks
                           secrets and risky git commands, and a formatter that runs after each edit
start.py                   sets up what isn't set up, installs what the lock files changed, starts both
                           halves and prints the app's one address (task 0029)
install.py                 installs everything again from scratch: checks git and Node.js, then the rest
test.py                    runs the tests, all or one kind, passing extra words to the test tool
check.py                   runs every check, as CI does; `--fix` fixes what the tools can fix;
                           `--no-front-end` skips frontend/ (CI, for Markdown-only changes)
```

The four files directly under `domain/` know nothing about a Take 5. They are the shared building blocks, and
`domain/take5/` is built from them. The same split is in the front end: `components/` is shared and
`features/take5/` is not.

## Logging

What the terminal running `uv run start.py` shows (task 0028). The aim: a glance says what went wrong and where.

- **Back end.** `backend/dev_logging.json`, which `start.py` gives uvicorn with `--log-config`, sets one format for
  uvicorn's lines and the app's own: local time, level, message, then the logger in brackets. Uvicorn's status
  lines (start-up, restarts, shutdown) are turned down to warnings. Its request lines go through
  `api/request_log.py`'s `FailedRequestsOnly`, so only a 4xx or 5xx prints. Without that file, as in the tests,
  `api/app.py` gives the app's own logger a plain handler of its own.
- **Stack traces only for bugs.** An AI failure is expected and handled (spec C3, T6): a time-out, or an
  `AiReplyError` (`services/ports.py`) that the adapter raises with the provider's own error as its cause. It logs
  one warning naming the kind of problem (`services/ai_failures.py`), never the provider's message, which can
  repeat what the AI was sent. Any other error while asking the AI is a bug, and keeps its trace. An unexpected
  error in a route logs one line naming the method and path (`api/errors.py`), then uvicorn prints its trace.
- **Front end.** `frontend/vite.config.ts` sets `server.forwardConsole: true`, so a crash in the browser,
  `console.error` and `console.warn` print in the terminal; `console.log` doesn't. Its `customLogger`
  (`src/dev/startLogger.ts`) prints one line per request while the back end isn't answering, in place of Vite's
  proxy error and stack. A custom logger makes Vite ignore the command line's `--logLevel` and the config's
  `clearScreen: false`, so it reads the first and never clears the screen.
- **Never logged:** the worker's name, what they typed, a request's body, or the AI's reply.

## The API

| Endpoint | What it does |
| --- | --- |
| `GET /api/take5/template` | The template a new Take 5 is filled in on: its questions, its matrix and its guidance, plus the answers a question can have and the control kinds. `ai_notice` (task 0009) is the line the review shows above Submit saying what is sent to the AI, or empty when no AI is set up (spec D52). `hazard_ai_notice` (task 0027) is the line the hazard check page shows when an AI judges hazards, or empty (spec D63) |
| `POST /api/take5s/check` | Checks a draft and returns what is missing, its warnings (allowed, but they will stop the job), and which thinking rules apply. A draft that has run out (spec K2) has an error on `started_at`, and `runs_out_at` says when it runs out (empty with no time limit). Saves nothing |
| `POST /api/take5s/nudges` | The T6 nudges for a draft (task 0027): one for each vague hazard linked to a Yes, judged by the AI for up to 5 seconds, then by the word rule. Saves nothing. Its own endpoint, not part of the check, so the phone asks it only when a hazard's words change and Continue never waits for an AI |
| `POST /api/take5s` | Checks and saves a Take 5, unfinished, then asks the AI (or the fallback) for its question, and returns it with the question. A retry returns what was saved, with the same question |
| `POST /api/take5s/{id}/answer` | Saves the answer, works out the verdict, and returns the finished Take 5 (task 0008). A short answer is a 422 on `answer`; a different answer to a finished one is a 409; the same answer again returns the finished Take 5 |
| `GET /api/take5s` | The list, newest first, 50 at a time: a `Take5ListPage` of `take5s` and `next`, the ID to send as `?before=` for the page after it (empty when there are no more). Each line is a `Take5Summary`: the ID, when it was saved, the worker, the job, the verdict (`can_start`, empty while the question is unanswered) and whether a newer Take 5 fixes it (`fixed`), not the whole card |
| `GET /api/take5s/{id}` | One Take 5, with `fixed_by` (the newest Take 5 that fixes it, if any) and `offers_fix` (whether its result offers a fix) |
| `GET /api/ranked-take5s?since=` | Every Take 5 started since a moment (sent with its time zone, such as midnight where the phone is), worst first (task 0032, spec W1 to W7): `RankedTake5s`, each a `RankedTake5Line` with the ID, when it was saved, the worker, the job, the verdict, its `line` and `ranked_by_ai`. Fixed rules in `domain/take5/ranking.py` score them, then `Take5RankingService` gives the worst 10 to the AI in `ai/ranking.py` for up to 20 seconds. It also sends the `best` careful one as a `BestTake5Line` (or null), picked by the AI from up to 5 shortlisted by the rules, with `picked_by_ai` and `minutes_taken`, and `typical_minutes`, the median (task 0036, spec W8, W9). Saves nothing; a result is remembered in memory until the server restarts. A moment with no time zone is a 422 |
| `GET /api/risk-by-area?today=` | Every area with a Take 5 started in the last 30 days, hottest first (task 0038, spec A1 to A5). `today` is midnight where the phone is, with its offset from UTC, and the 30 days are 29 days of 24 hours back from it; the reply is `RiskByArea`: `areas`, each an `AreaRisk` with its name, counts, highest score and band, and `common_yes`. Worked out by the fixed rules in `domain/take5/areas.py`; no AI, nothing saved. A moment with no time zone is a 422 |

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
asks. It never changes the verdict. In the same way `HazardDraft.covers` keeps every question the worker linked to the
hazard, and the rated `Hazard` keeps only those still answered Yes, each once, in the order the worker linked
them (spec T5). `POST /api/take5s/nudges` returns the nudges (task 0022, moved off the check by task 0027):
each has a dotted `path`, a `message` and the `question_id` it shows under, and none ever stops a Take 5 being
submitted. For now the only one is T6, on `hazards.<n>.description`, under the first Yes in card order that the
hazard is linked to. Which nudge the worker chose to keep is remembered on the phone, not sent, because it is
about what is on the screen. The hazard check page asks once for the whole page, again only when the draft
changes, and never while the worker types in a nudge's box (spec D56). It sends the draft without the links of
hazards whose words were kept, so those are never judged.

**The front end holds no rules and no card.** It gets the questions and the matrix from
`GET /api/take5/template`, draws whatever it is sent, and shows a score by looking it up in that matrix. It finds
out what is missing or needs another look by asking
`POST /api/take5s/check`. So there is exactly one copy of every rule, in Python, under test. A few behaviours live
in the front end, because they are about what is on the screen: spec T1 (hiding the hazard questions until a
hazard is written), skipping the after-controls page of a hazard with no controls, putting each question on the
page for its role (stop questions on the think-through page, hazard questions after the hazard list), and, under
a Yes to a hazard question, the list to pick a hazard from (spec T5). The back end still decides whether each Yes
has a hazard linked to it (T5), and that the after rating of a hazard with no controls is its before rating (R6).

**Drafts (task 0019).** The phone keeps one draft in `localStorage` from the worker's first change, which also
stamps `Take5Draft.started_at` by the phone's clock (with its time zone; a time without one is a 422). Opening the
app with no page in the URL carries on from the page the draft was left on. The phone never decides whether a
draft has run out: it checks the draft once as it opens, on a Continue with changed answers (an unchanged one reuses the
last answer), and on Submit, and acts on an error
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
| `SavedTake5` (task 0004) | Extends the scoring `Take5` with `id`, `created_at`, `worker_name`, `job`, `location`, `finished_at`, `verdict`, `fixes`, `started_at`, `challenge` | The implemented submitted document. The base `Take5` holds what the verdict needs (the template, `answers` and the hazards); later tasks add the remaining card fields. `answers` (task 0005) has one answer for each of the template's questions, by question ID. A Take 5 saved before task 0005 has none, and its template copy has no questions, so it still opens. `fixes` (task 0010) is the ID of the Don't start yet it fixes, or empty. It points back only, so the first one is never changed; its fix is found by searching for its ID in `fixes`. `started_at` (task 0019) is when its draft was started, by the phone's clock, or empty for one saved before then (spec K3). From task 0008 it is saved unfinished, with `finished_at` and `verdict` empty; `challenge` is added once, then the answer, `verdict` and `finished_at` once (`Take5Repository.save_question` and `finish`, each of which only changes a row that is still unfinished). One finished before task 0008 has a verdict and no `challenge` |
| `Hazard` | `description`, `before` (rating), `controls`, `after` (rating), `weak_controls_reason`, `covers`, `kept_flag` | Belongs to one Take 5. With no controls `after` is `before` (spec R6). `weak_controls_reason` is the worker's answer to spec T3, when it was asked. `covers` (task 0022) is the IDs of the hazard questions answered Yes that the worker linked to it (spec T5); it is empty for a Take 5 saved before then. The link lives on the hazard, so removing a hazard removes its links, and nothing else needs an ID. `kept_flag` (task 0037) is what the hazard check still said about its words when it was submitted (`vague`, `stock` or `unfit`, spec T7), so the worker kept them; null when nothing was flagged, or for a Take 5 saved before then. Today's review counts it (W10) |
| `Control` | `description`, `kind` (`ControlKind`) | Belongs to one hazard |
| `RiskRating` | `likelihood`, `consequence`, and from the matrix: `score`, `band` | A value, not a stored row. Score and band are always worked out, never typed in |
| `Take5Template` | `name`, `questions` (each an `id`, its `text`, its `role`: `stop` or `hazard`, and its `example`), `matrix`, `likelihood_guidance`, `consequence_guidance` (each a level and its meaning), `control_guidance`, `draft_time_limit_minutes`, `specific_hazard_words` | The card as data. The rules never name a question: a *stop* question answered No stops the job, whichever card it is on. The page a question shows on follows from its role, so there are no separate sections. `draft_time_limit_minutes` (task 0019) is how long a draft lasts (spec K2): 120 on the booklet, or none, which turns the check off. `GET /api/take5/template` leaves it out and the phone never reads it, though the copy of the template inside a checked or saved Take 5 carries it. `specific_hazard_words` and each hazard question's `example` (task 0022) are spec T6's minimum (6 on the booklet, or none to turn it off) and the example its nudge shows; `GET /api/take5/template` leaves the minimum out too |
| `RiskMatrix` | the likelihood and consequence scales, the score and band of each cell, the score that needs a JHA | The matrix as data. `rate()` is given the matrix, so another company's matrix needs no new code |
| `Challenge` | `question`, `asked_by` (`ai` or `fallback`), `model`, `instructions_version`, `answer` | Belongs to one Take 5. `answer` is empty until the worker gives one. `model` and `instructions_version` say which AI asked and with which version of its instructions; both are empty for the fallback. Kept inside its `SavedTake5` (task 0008) |
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
ai            ->  services.ports, domain
ai/providers  ->  ai/model.py only
api           ->  services, domain
api/app.py is the one exception: it also imports storage, ai and settings, to plug them in
```

- **`domain`** owns every scoring, verdict, thinking and challenge rule. It uses only the standard library and
  pydantic. It never reads a file, a database, a clock or the network, so each rule is a function of its inputs
  and can be tested with a one-line example from the spec. A rule about time, such as K2, is given the time.
- **`services`** owns the use cases. It depends on the `Take5Repository`, `ChallengeAsker` and `HazardJudge`
  Protocols, not on SQLite or on any AI provider.
- **`storage`** owns the SQL. It stores and fetches; it makes no decisions.
- **`ai`** owns talking to an AI, in two layers. A *provider* (`ai/providers/claude.py`) is a `LanguageModel`: it
  is given instructions and text and returns text, and knows nothing about this app. A *job* (`ai/challenge.py`,
  `ai/vague_hazard.py`, `ai/ranking.py`) holds the instructions for one task and works with any provider. Neither decides
  anything: `domain/take5/challenge.py` and `domain/take5/hazard_nudges.py` check what comes back, and
  `services` falls back to the fixed question on any failure or after 10 seconds, and to the word rule for a
  hazard on any failure or after 5 seconds.
- **`api`** owns HTTP. It holds no rules: a route calls a service and returns what comes back.
- **`api/app.py`** is the only place that knows which real pieces are plugged in (the composition root). Tests
  plug in an in-memory repository and a stand-in AI instead.

Anything outside the app sits behind a Protocol, so it can be replaced without touching its callers. There are
two: the database (`Take5Repository`) and the AI (`ChallengeAsker` and `HazardJudge`, each filled by any
`LanguageModel`). Adding ChatGPT, Gemini, or a model a company runs itself means adding one file in
`ai/providers/`, its library, and one line in `api/app.py` to plug it in; no rule and no job changes. The
adapter wraps its library's errors in `LanguageModelError`, keeping each as the cause, so a failed call is logged
in one line and not as a bug (see Logging).

The worker's name is never passed to an adapter (spec C1). The AI's key lives in the server's environment (or
`backend/.env` on a developer's computer, copied from the template `backend/.env.example`, which names every
setting and holds no key) and is never in the repo or sent to the phone. With no key, no AI is plugged in: the
fixed question is always asked and the word rule judges every hazard. `api/app.py` has one table from
`AiProvider` (a setting) to the adapter that builds that provider's models and the name of its quick model, which
judges hazards unless `TAKE5_AI_HAZARD_MODEL` names another (spec D61).

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
| Poisoning | Wrong or hostile text gets in and is relied on | C2 checks every reply before it is shown, and W6 checks every ranking: each number once, one short line each, and no line that names the worker. W8 checks the best's pick the same way. The AI's text is never fed into another AI call and never decides the verdict. A worker could type instructions into the job ("ignore your rules"); the instructions in `ai/challenge.py` tell the model the Take 5 is only data and to ignore any instructions in it (task 0009), and C2 limits any reply to one short question |
| Distraction | Too much in front of the model | Each call sends one Take 5 and nothing builds up, so nothing needs compacting. A ranking sends at most the worst 10, picked by fixed rules (W6), and the best's pick at most 5 (W8) |
| Confusion | Irrelevant material mixed in | Only that Take 5's own fields are sent (C1). A ranking sends the same for each, plus its question, answer and minutes taken, and never a worker's name (W6) |
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
| Unit, services | Check, nudge, submit, answer, get and list, including every way the AI can fail | An in-memory `Take5Repository` and a stand-in `ChallengeAsker` or `HazardJudge` |
| Integration, storage | A Take 5 saved to SQLite comes back identical | A temporary database file per test |
| Integration, API | Each endpoint: the right answers, and the right errors for a bad request | FastAPI's test client against the real app with a temporary database and a stand-in AI |
| Architecture | The import rules under Boundaries | One test that reads the imports of every module |
| Contract | The front end's generated types match the back end | CI regenerates the types and fails if they differ from what is committed |
| Unit, front end | Each component and screen behaves: nothing pre-selected, errors beside fields, T1 | Vitest and React Testing Library |
| End to end | A worker fills in every screen in a real browser and reaches the right verdict | Playwright against the real front end and back end, with a stand-in AI |
| Visual | Each changed screen looks right on a phone, and on a desktop | Playwright screenshots at 360 px wide, and at 1280 px for `e2e/desktop.spec.ts` (which also checks hover and focus), attached to the PR; checked by eye, not in CI |
| Accessibility | Every screenshot the whole-app tests take, in both modes, is readable: text contrast to 7 to 1 (spec D76) and axe's other WCAG 2.2 AA rules | `@axe-core/playwright`, Deque's checker, inside the screenshot helper (`capture` in `e2e/helpers.ts`) |
| AI adapter | The adapter sends what it should and reads the reply, refusals and errors | The real adapter against a stand-in for the provider's API (`tests/ai/fake_anthropic.py`), so nothing leaves the computer |
| Real AI | The real provider answers with a usable question | `uv run test.py backend -m real_ai`, skipped with no key; plain `pytest` and CI never run it. `scripts/try_challenge.py` measures questions, and `scripts/try_vague_hazard.py` verdicts on hazards, with time and cost |

CI runs, on every PR and every push to `main` (task 0002): for the back end `ruff check`, `ruff format --check`,
`pyright` and `pytest`; for the front end ESLint, Prettier's check, the TypeScript compiler, Vitest, and the
Playwright tests. A draft PR waits until it is marked ready, and a PR that changes only Markdown or the spelling
and Markdown settings skips the front end's checks (task 0041).
