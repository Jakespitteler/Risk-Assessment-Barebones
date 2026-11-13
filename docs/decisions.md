# Decisions

Newest first. One short entry per non-obvious decision.

## 2026-11-13: A Don't start yet can be fixed in a new Take 5 (task 0010)

- Decision: The review warns about a hazard with no controls before Finish, with a way to add one. A Don't start
  yet result offers to copy its answers into a new Take 5. The saved one stays as it was.
- Why: Jake tried the app and was told "Say how you will control: ..." with no way to add the control. Typing
  everything again is what makes people stop doing Take 5s properly. Keeping the first one unchanged keeps the
  record of what was first planned.
- Alternatives considered: Only the warning (a fix after saving would still mean typing it all again). Only the
  copy (the worker would only find out after saving). Editing a saved Take 5 (a finished Take 5 never changes, so its record could not be trusted).
- Decided by: human (Jake, 2026-11-13).

## 2026-11-13: The card's guidance belongs to the template (task 0004 review)

- Decision: The likelihood, consequence and control guidance are fields of `Take5Template`, and
  `GET /api/take5/template` sends the service's template, not a hard-coded constant.
- Why: Each saved Take 5 keeps a copy of its template, so it should keep the guidance the worker was shown. A
  company's own card (the long-term plan) brings its own wording with no new code.
- Alternatives considered: Keep the guidance as separate constants beside the template (ChatGPT's first
  version). It would not be in the saved copy, and a second template would need a second set of constants.
- Decided by: human (Jake approved it on 2026-11-13).

## 2026-11-13: Phone workflow, one hazard at a time and expandable guidance (task 0004)

- Decision: Design for the worker's own phone at the job, including sun and gloves. After listing hazards,
  assess one at a time with separate before, controls and after steps. Show guidance in expandable sections.
- Why: Jake confirmed that usage context and chose focused hazard assessment and expandable guidance.
  The card's descriptions help explain ratings without preselecting answers or supplying hazards.
- Alternatives considered: Shared tablets or desktop-first use; every hazard on one long page; always-visible
  explanations or labels alone. Front-end copies of card guidance would drift, so the API supplies it.
- Decided by: human (Jake), selecting these options in task 0004's questions.

## 2026-11-13: Save immutable submissions once through a repository port (task 0004)

- Decision: Keep the reusable scoring `Take5` and extend it as `SavedTake5` for submission metadata and the saved
  verdict. Store its JSON in the documented SQLite table through `Take5Repository`. A form uses one UUID for
  submission and retries; the first stored document wins, and different input with the same ID is refused.
- Why: This preserves task 0003's scoring interface, makes storage replaceable and handles a lost response
  without duplicate assessments. Scores come from the server's template, never the request. Check requests
  save nothing; the browser sends the completed draft only when the worker finishes the form.
- Alternatives considered: SQLite in routes, overwriting a finished document, or a new ID on every retry.
  Each would break a documented boundary or risk losing the original verdict or creating duplicates.
- Decided by: human. ChatGPT built it before asking; Jake approved the client-made UUID and the 409 on
  2026-11-13, after Claude's review of task 0004.

## 2026-11-13: Select the actual Python executable instead of a directory default (task 0003 review)

- Decision: The shared VS Code settings name no interpreter. Each person selects `backend/.venv`'s `python`
  executable in VS Code, which keeps that choice locally. Python Environments integration stays on.
- Why: A shared setting that named the `.venv` folder made the Python Environments extension try to run the
  folder itself, so test discovery failed on Jake's Windows machine. Naming the executable instead would only
  work on one operating system.
- Alternatives considered: A shared Windows-only path (breaks Linux and macOS). Turning the Environments
  integration off (hides the cause; rejected by Jake).
- Decided by: human for fixing the cause rather than working around it; chatgpt for the portable setting

## 2026-11-13: Scoring models contain only the fields needed for R1 to R6 (task 0003)

- Decision: Add frozen `Control`, `Take5Template`, `Hazard` and `Take5` models with the scoring fields already
  specified in the architecture. A hazard keeps explicit before and after ratings; without controls the
  caller reuses its before rating, and validation refuses a changed after rating. A Take 5 checks both ratings
  against its template and derives its rating and JHA decision from the highest after score.
- Why: These are enough to implement and test R1 to R6. Rechecking the matrix prevents an incorrect supplied
  score or band from overriding the template. Job details, questions, verdicts and storage belong to later tasks.
- Alternatives considered: Build every field of the eventual Take 5 now; accept supplied scores without
  checking them against the template.
- Decided by: chatgpt for implementation, within Jake's approved task 0003 and spec rules R1 to R6.

## 2026-11-13: One type-checking configuration for the editor and checks (task 0002 review)

- Decision: Put strict Pyright settings under `[tool.pyright]` in the root `pyproject.toml`, including
  `backend/src` and `backend/.venv`. VS Code defaults to that environment. Explicitly annotate assigned
  Python variables and constants, except direct constructor calls whose class already makes the type clear.
- Why: Opening the whole repository left Pylance unable to resolve the app import in `export_openapi.py`.
  A shared root configuration gives the editor and command-line checks the same paths and strict rules.
  Strict checking alone permits inferred types, while Jake wants explicit annotations for computed results
  and collections. His follow-up review clarified that `app = FastAPI(...)` needs no redundant annotation.
- Alternatives considered: Editor-only import paths, which could diverge from the command-line checks.
  The initial root JSON configuration was replaced with TOML at Jake's request. Keeping only the nested
  back-end configuration would leave Pylance without configuration when the whole repository is opened.
- Decided by: human for the annotation exception and TOML preference; chatgpt for root configuration placement.

## 2026-11-13: Tools and the first end-to-end path for the walking skeleton (task 0002)

- Decision:
  - **httpx2** instead of httpx for FastAPI's test client.
  - **TypeScript 5.9**, not 6.
  - **markdownlint-cli2** 0.24.0, run through `npx` at that fixed version, with its settings in
    `.markdownlint-cli2.jsonc` (lines up to 120 characters; agent prompts and the PR template need no title).
  - The small packages the approved front-end libraries need in order to work: `@vitejs/plugin-react` and
    `@tailwindcss/vite` (plug React and Tailwind into Vite), `jsdom` and `@testing-library/dom` (a pretend
    browser for Vitest), `typescript-eslint`, `@eslint/js` and `eslint-plugin-react-hooks` (ESLint rules for
    TypeScript and React), and the `@types/...` packages for React and Node.
  - Two short Python scripts run by uv, `scripts/dev.py` (starts both halves) and `scripts/check.py` (runs every
    check, and is what CI runs), rather than a tool such as `concurrently` or `make`.
  - The skeleton's end-to-end path is rating a risk on the matrix the back end sends, not saving and viewing a
    Take 5.
- Why: Starlette, which FastAPI is built on, now deprecates httpx for its test client and asks for httpx2, the
  pydantic team's continuation of it; with httpx, pyright strict can't see the test client's types.
  openapi-typescript and typescript-eslint don't support TypeScript 6 yet. Jake asked for no markdownlint
  warnings, and a check in CI keeps it that way. The scripts add nothing to install, work the same on Windows,
  and keep the list of checks in one place. Saving a Take 5 needs the data model that tasks 0003 and 0004 build;
  rating a risk still runs through every layer of the stack and is the first real piece of the app.
- Alternatives considered: Keep httpx and silence the warning. Use `concurrently` for the run command. Create a
  throwaway "assessment" table for the skeleton (it would be replaced by task 0004).
- Decided by: human (Jake said yes to each), on claude's proposal

## 2026-11-13: Front-end libraries

- Decision: React, TypeScript, Vite, Tailwind CSS, TanStack Query, React Router, openapi-typescript; Vitest,
  React Testing Library and Playwright for tests; ESLint and Prettier; npm.
- Why: Jake asked for the best of what is current without anything obscure or likely to be replaced in a few
  years, and for the ability to change systems without much trouble. React is the most widely used UI library
  and the least likely to go away. The others are the mainstream choice for their job, and each is kept to one
  corner of `frontend/` so it can be swapped alone.
- Alternatives considered: Svelte or Vue (pleasant, smaller communities). Next.js (adds a second server and
  moves back-end logic into JavaScript). Server-rendered pages with no framework (the first proposal; rejected by
  Jake as less slick).
- Decided by: human, on claude's proposal (spec decision D12)

## 2026-11-13: Shared building blocks, the card as data, and one port for any AI

- Decision: The matrix, controls, Yes / No questions and wording checks live in shared files that know nothing
  about a Take 5; `domain/take5/` is built from them. The card (its questions and its matrix) is a
  `Take5Template`, which is data, and the rules work from question roles and the template's matrix. Every AI
  provider is a `LanguageModel` (instructions and text in, text out), and each AI task is a job written once on
  top of it. Each AI question records the model and the version of the instructions that asked it.
- Why: Jake expects other companies' Take 5s (built from a photo, Word file or PDF of the blank card), possibly
  JHAs, hazard report cards and journey plans, company risk standards given to the AI, a privately hosted AI,
  and feedback used to improve the AI's questions. He asked for the Take 5's building blocks to be generic
  where they can be. These three seams are cheap now and expensive to add later.
- Alternatives considered: A general "document" or form engine that a Take 5 is configured out of (rejected:
  harder to read and test, for features that may never be built; shared code is pulled out when a second kind
  of document really exists). Building the questions and matrix into the code (simplest today, a rewrite for
  the second company). A separate vector database for company standards (not decided; `architecture.md` says
  how to decide, starting with the plainest method).
- Decided by: human for the aim; claude for where the seams go, approved by the human merging task 0001's pull
  request

## 2026-11-13: The rating after controls decides a JHA; control kinds from the card; saved Take 5s open to all

- Decision: A JHA is needed when a hazard's rating *after* controls is 11 or more (D6). The worker labels each
  control with one of the card's six "Make the changes" options, and remove, isolate and barricade count as
  strong (D7). Everyone using the app can see every saved Take 5 (D8).
- Why: D6 follows the paper card, whose columns run hazard, controls, score. D7 uses the wording the crew
  already know. D8 follows from having no sign-in.
- Alternatives considered: The *before* rating for D6 (stricter and harder to talk down, but almost any job with
  a fatal hazard would then need a JHA). The booklet's formal hierarchy of controls for D7. Take 5s visible only
  on the phone that made them for D8.
- Decided by: human, on claude's recommendation

## 2026-11-13: Back-end libraries

- Decision: FastAPI, pydantic and pydantic-settings, uvicorn, SQLite through the built-in `sqlite3`, and the
  `anthropic` library for the first AI adapter. For development: uv, ruff, pyright in strict mode, pytest and
  httpx (FastAPI's test client needs it).
- Why: FastAPI is the standard typed Python API framework and the original app already uses it; the others are
  what it is normally run and tested with. ruff, strict type checking and Python 3.13 are project rules.
- Alternatives considered: Django (more built in, but heavier and less direct to read). Flask (older, with no
  built-in data checking or API description).
- Decided by: human for FastAPI, SQLite and Claude, which he was shown by name. The rest were proposed by claude
  and are approved by the human merging task 0001's pull request.

## 2026-11-13: A Python API with a separate JavaScript front end

- Decision: Two programs that talk only through a web API. The back end owns every rule; the front end holds
  none and gets the matrix, the questions and all checks from the API.
- Why: Jake chose the slicker front end over server-rendered pages. Keeping every rule in the back end means
  there is one copy of each, in Python, under test, and either half can be replaced as long as the API is kept.
- Alternatives considered: Server-rendered pages (one codebase, less slick).
- Decided by: human

## 2026-11-13: An AI challenge question in the first version

- Decision: Before the result, the app asks one question about the weakest part of the Take 5. An AI writes it,
  behind a `ChallengeAsker` interface that any provider can fill. The safety rules stay in code; the AI never
  decides the verdict.
- Why: Jake chose this over fixed rules alone. Fixed rules can be learned and satisfied without thinking; a
  question written for this job can't be seen coming.
- Alternatives considered: Fixed rules only (cheaper, works with no signal, easier to test).
- Decided by: human. He also chose: Claude as the first provider (D9); a fixed fallback question when the AI
  can't be reached, so a Take 5 can always be finished (D10); and that the AI only asks and never judges the
  answer (D11).

## 2026-11-13: Own words first, hazards rated twice, no sign-in

- Decision: The worker writes hazards before seeing the card's hazard questions, and fixed rules push back on
  thin answers. Each hazard is rated before and after its controls. There is no sign-in; the worker types their
  name.
- Why: These were the recommended options for spec decisions D1, D2 and D4. Jake was asked to name the ones he
  would change; he changed D1 only by adding the AI question (above) and left D2 and D4 as recommended.
- Alternatives considered: The card's ticks only; one rating per hazard, as on paper; accounts from the start.
- Decided by: human

## 2026-11-13: Store each Take 5 as one JSON document

- Decision: One SQLite table, `take5s`, holding the whole Take 5 as JSON beside the columns the list needs,
  reached through Python's built-in `sqlite3` behind a `Take5Repository` interface.
- Why: A Take 5 is always read and written whole. Separate hazard and control tables would add joins and code
  with no benefit yet, and the built-in module keeps every SQL statement in the repo to read.
- Alternatives considered: Separate tables per entity (better for reports across hazards; revisit when a report
  is wanted). SQLAlchemy and Alembic as in the original app (handles table changes and other databases, but
  hides the SQL and is more to learn for one table). Either swap touches one file.
- Decided by: proposed by claude; the human approves it by merging task 0001's pull request

## 2026-11-13: Unlikely / Critical scores 19, not the printed 18

- Decision: The matrix cell for Unlikely / Critical is recorded as 19.
- Why: The printed card shows 18 there, which repeats Possible / Major and leaves 19 unused. Every other cell is
  a unique rank from 1 to 25. The band (Extreme) is the same either way.
- Alternatives considered: Keep the printed 18. Two cells would then tie, and "a higher score is a higher risk"
  would have one exception.
- Decided by: carried over from the original Risk-Assessment app; the human approves it by merging task 0001's
  pull request
