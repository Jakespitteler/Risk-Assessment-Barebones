# Decisions

Newest first. One short entry per non-obvious decision.

## 2026-11-14: The card's questions are one list, answered by question ID (task 0005)

- Decision: `Take5Template.questions` is one list in the card's order. Each `Question` has a short `id` (such as
  `permits`), its `text` and its `role` (`stop` or `hazard`). The phone sends, and the saved Take 5 keeps,
  `answers`: a map from question ID to `Yes`, `No` or `N/A`. A missing answer is the error
  `answers.<question id>`. The front end puts a stop question on the think-through page and a hazard question
  on the page after the hazard list. Rule V1 gives one reason per stop question answered No, in the card's order.
  A No also gives a review warning, like a hazard with no controls (spec D14).
- Why: The page a question goes on follows from its role, so the `sections` that `architecture.md` first listed
  would have said the same thing twice. An ID keeps an answer tied to its question even if the wording is tidied,
  and makes a readable error path; a question's wording could hold a full stop, which would break the dotted
  path. One reason per No reads as a sentence ("You answered No to: Do you have the necessary permits? Sort this
  out first.") where a joined list of questions would not.
- Alternatives considered: The two fields `think_through` and `hazard_questions` that `architecture.md` first
  listed (they name the booklet's two kinds in the data, so another card's kinds would need new fields).
  Answers in a list matched to the questions by position (shorter, but nothing ties an answer to its question
  if the card changes). One combined V1 reason naming every No.
- Decided by: proposed by claude; the human approves it by merging task 0005's pull request. Jake chose the page
  for the hazard questions (spec D13) and that a fix copies the answers with a warning on each No (spec D14) on
  2026-11-14.

## 2026-11-14: Shared test data is plain functions in `tests/samples.py` (task 0016)

- Decision: The API tests get their database and client from fixtures in `backend/tests/api/conftest.py`. The
  made-up drafts, hazards and saved Take 5s that tests in more than one folder use are plain functions in
  `backend/tests/samples.py`, imported as `from tests.samples import sample_draft`. A builder used in one file
  stays in that file. Every builder makes the same example (a moving wheel, 8 then 5 with a barricade) unless a
  test passes arguments.
- Why: Set-up suits fixtures: pytest hands each test a fresh one. Data suits functions: a test can pass
  arguments, and pyright checks each call. A builder in a `conftest.py` is meant to be shared as a fixture, and
  a fixture that returns a function is harder to read. pytest advises against importing from a `conftest.py`
  unless it sits in a package; a plain module avoids the question. The front end does the same with
  `test-utils.tsx`. The import works because `backend/tests/` has an `__init__.py` and pytest uses its default
  import mode, which puts `backend/` on the path; switching to `--import-mode=importlib` would break it.
- Alternatives considered: Builders in a `conftest.py`, as task 0016's notes first suggested (shared, but only
  as fixtures). A separate copy in each folder, as before (each file reads on its own, but the copies had
  started to drift: two `_draft()` builders made different Take 5s).
- Decided by: proposed by claude; the human approves it by merging task 0016's pull request

## 2026-11-14: Anything too long for one line puts one item per line (task 0017)

- Decision: Ruff's `COM812` (missing trailing comma) is on. A `def`, call, list, dictionary or set that doesn't
  fit on one line gets a trailing comma, so Ruff's formatter puts each item on its own line. The format-on-save
  hook runs Ruff's formatter, then `ruff check --fix --select COM812`, then the formatter again, so a short `def`
  split by hand goes back onto one line first. The limit: once something has a trailing comma, Ruff keeps it
  split even if a later edit makes it short enough for one line. Delete the comma to join it again.
- Why: Jake's rule is one parameter per line for a `def` that doesn't fit. Without a trailing comma the
  formatter first puts all the parameters together on one indented line. A check means nobody has to remember
  the rule. `COM812` can't tell a `def` from a call, so calls and collections follow it too: 118 places in 29
  files changed when it was turned on, 22 of them `def` lines.
- Alternatives considered: A small script of our own that checks `def` lines only (exactly the rule, but custom
  code to keep, and it reports rather than fixes). Writing the rule down with no check. Ruff warns on every
  `ruff format` run that `COM812` may conflict with the formatter; the conflict only happens when the formatter
  runs before the fix and nothing runs after, so the warning is left as it is rather than hidden with `--quiet`.
- Decided by: human (Jake, 2026-11-14) set the rule, then chose Claude's recommendation of `COM812` everywhere
  over a `def`-only script or no check.

## 2026-11-14: Open pull requests stack, and a tool's forced branch name is allowed

- Decision: When other pull requests are open, a new task's branch starts from the newest one's branch and its
  pull request targets that branch. An agent whose tool can only push to a branch it names (a Claude cloud
  thread's `claude/project-thread-<id>`) uses that branch instead of `<owner>/<task-id>-<short-name>`, and
  writes it in the task file. Stacked pull requests are merged oldest first, each onto `main`: after a merge,
  the next one's base changes to `main` before the merged branch is deleted. When PR 18's branch was deleted
  first, GitHub closed PR 19 instead of moving it, and PR 20 then merged into PR 19's branch, not `main`.
- Why: Stacked pull requests keep each one small while the next task builds on unmerged work. Cloud threads
  cannot push any other branch name, so the old rule could never be followed there.
- Alternatives considered: Every branch from `main` (later pull requests conflict with or repeat earlier ones).
- Decided by: human (Jake, 2026-11-14), in the task 0015 thread.

## 2026-11-14: The app is Jake's, all rights reserved (task 0015)

- Decision: `LICENSE` is a proprietary "All rights reserved" notice with Jake Spitteler as the owner, in place
  of MIT. Nobody may use, copy, change or share the code without the owner's written permission.
  `frontend/package.json` says `"license": "UNLICENSED"` and `backend/pyproject.toml` says
  `license = "LicenseRef-Proprietary"`, so tools do not read the project as open source. Source files carry no
  copyright header. Copies taken before this change keep their MIT rights.
- Why: Jake wants nobody else to copy or use the app. Jake first named Talison Lithium as the owner, then chose
  to be the owner for now. Changing the owner later means changing the name in `LICENSE` and `README.md`; a
  lawyer should say whether that also needs a signed assignment. This is not legal advice.
- Alternatives considered: PolyForm Strict 1.0.0 (still allows non-commercial use) and Business Source License
  1.1 (becomes open source after a set date). Neither stops all use. A header in every file was left out as
  extra upkeep for little gain while `LICENSE` covers the repo.
- Decided by: human (Jake, 2026-11-14), choosing Claude's recommended template and package settings.

## 2026-11-14: The CI reviewer runs Opus 5.5 with at most 15 turns

- Decision: `agent-review.yml` passes `--model claude-opus-5-5` and `--max-turns 15` (was 40). Without
  `--model` the review runs on the action's default model, because `model:` in `.claude/agents/reviewer.md`
  only applies to the local subagent. That a pull request's own code, such as `scripts/check.py`, runs in its
  review is an accepted risk; the action already restores the agent files from `main`.
- Why: Jake chose Opus 5.5, and asked for a lower turn cap to protect his usage. The first live review (no
  fixes, on the default model) took 7 turns, so 5 would stop it before it posts its comment. 15 leaves room to
  fix one thing and run the checks again. The cap is only a ceiling; a review uses what it needs.
- Alternatives considered: 5 turns (too few, as above) and keeping 40 (more room than a review needs).
- Decided by: human (Jake, 2026-11-14), after Claude's review of task 0012.

## 2026-11-13: Fix a Don't start yet in a new Take 5 that points back (task 0010)

- Decision: A worker told Don't start yet can copy its answers into a new Take 5 and fix them there. The new
  Take 5 records the first one's ID in `fixes`. The first one is never written to: opening it finds its newest
  fix by searching the saved documents (`json_extract` on `fixes`), and the reply carries it as `fixed_by`.
  The copy opens on the review. Once a Take 5 has a fix it links to it and no longer offers another. The back
  end refuses (422) a `fixes` that is not a saved Don't start yet. Before Finish, the check warns about each
  hazard with no controls; a warning never blocks Finish.
- Why: A saved Take 5 is final, so the only way to add a forgotten control was to type everything again. The
  link lets a supervisor see that a job was first planned without a control. Searching for the fix keeps the
  rule that a finished Take 5 never changes, and needs no new column or table change.
- Alternatives considered: Editing the saved Take 5 (breaks "never changed"). Writing `fixed_by` into the first
  one (changes a finished Take 5). A `fixes` column beside the document (faster to search, but existing
  databases would need a table change; add one if the list of Take 5s grows large). Opening the copy on the
  first page (more thinking, but slower; the review's warning already points at what to fix).
- Decided by: the human (the fix and the warning, the `fixes` data model change, the copy opening on the review,
  one offered fix, and refusing a fix of a Good to go); claude proposed the search and the warning's shape

## 2026-11-13: Spell check in Australian English, shared through the repo

- Decision: Spelling is Australian English, checked by cspell with its `en-AU` dictionary, which is what Jake's
  VS Code extension (Australian English - Code Spell Checker) uses. `cspell.json` in the root holds the shared
  settings, and VS Code and the command line both read it. Project words live in `.cspell/project-words.txt`,
  not in `.vscode/settings.json`, so any agent can see and extend them. `.cspell/cli.json` adds the `en-AU`
  dictionary for the command line; the editor gets it from the extension. The `.gitignore` files and `LICENSE` are
  skipped: they are mostly template text and file patterns. `.vscode/extensions.json` recommends the extension,
  because without it VS Code would flag nearly every word (the shared settings ask for a dictionary that only
  the extension or `.cspell/cli.json` supplies).
- Why: Jake asked for the whole repo to pass his spell checker, and ChatGPT can only follow what is in the repo.
- Alternatives considered: importing the dictionary in `cspell.json` (the editor would show an import error,
  because the dictionary is not installed in the repo), and adding cspell as an npm dependency (needs approval;
  `npx` with pinned versions works the same way as markdownlint does now).
- Decided by: human (Jake asked for it, 2026-11-13). He chose the same day to run it in `scripts/check.py`, so
  CI fails on a spelling mistake.

## 2026-11-13: Bound the automated review and skip its own pushes (task 0012)

- Decision: Use the approved Claude App and subscription OAuth authentication. Share the review policy in
  `.claude/agents/reviewer.md`; local reviews report, CI reviews may fix within the approved scope. Use 40 turns,
  a 30-minute timeout and concurrency per PR. Skip drafts, forks, default-branch heads and synchronize events
  sent by `claude[bot]`. Load the trigger policy from the base revision.
- Why: App-authenticated fix pushes start normal CI. Checking the event sender prevents review loops without
  excluding all Claude-authored PRs. Job-level concurrency prevents a skipped fix push cancelling its own review.
- Alternatives considered: `GITHUB_TOKEN` (fix pushes would not start CI), skipping Claude-authored PRs (would
  miss independent review), and a privileged `pull_request_target` workflow (unneeded for this private repo).
- Approval: Jake approved the App, OAuth, fix commits and replacement review in task 0011, requested task 0012,
  and confirmed the App and secret are ready. Limits and event filtering implement that approved scope.
- Limits: The first workflow needs to be on the default branch for App validation. Abrupt cancellation or
  timeout may prevent a final comment. GitHub permissions do not enforce every instruction; human review and
  the existing soft guards still apply. Live App authentication and fix-triggered CI need a subsequent PR.

## 2026-11-13: Claude Code's safety settings and hooks, and who reviews a PR (task 0011)

- Decision: `.claude/settings.json` denies Claude's file tools any `.env`, key, `secrets/` or `backend/.data/`
  file. A guard hook blocks Bash and PowerShell commands that name them, pushes to `main`, commits on `main`,
  force pushes, `--no-verify` and merging a PR. A second hook formats each edited file. Both are Python
  scripts in `scripts/claude_hooks/`, run with `uv`. An agent that did not write a PR reviews it before Jake:
  the review agent in CI (task 0012), which signs in with Jake's Claude subscription (an OAuth token) and
  replaces the other agent's review. `main` stays unprotected on GitHub; the guards above are soft.
- Why: Jake asked for current Claude Code safety practice and for code never to be checked by the agent that
  wrote it. Deny rules miss commands such as `python -c "open('.env')"`, so the guard reads each command.
  Python hooks, started by `uv` with no shell in between, run the same on Windows and Linux, and `check.py`
  lints and tests them. GitHub Free does not
  enforce branch protection on a private repo.
- Alternatives considered: Claude Code's sandbox (stronger, but not on native Windows). Shell-script hooks
  (simpler, but not on Windows without Git Bash, and untested). GitHub Pro to protect `main` (about US$4 a
  month), or a public repo. An API key for the review agent (billed per review). Keeping the other agent's
  review as well (Jake would pass every PR between Claude and ChatGPT by hand).
- Limits: claude.ai cloud threads do not apply a repo's permission rules or hooks, so these protect Claude
  Code on a computer only; CI's checks apply to every agent. The guard matches words, so it misses a command
  that reads a file without naming it (`grep -r KEY .`, `cp -r backend /tmp`), a folder named with no `/`
  (`cd secrets`, `ls .data`), a script that opens a file, a command inside `bash -c '...'`, and a commit after
  `cd` into another repository. It is not a full shell parser, so deliberate tricks get past it: split words
  (`ma''in`), git aliases, `git switch -` back to `main`, and commands built while running. It doesn't hide
  environment variables. It blocks any shell command whose text names a secret, including a commit message or
  a search for the word `.env`; a message goes in a file instead (`git commit -F`), and a search uses the Grep
  tool where Claude Code has one.
- Decided by: human (Jake, 2026-11-13: the plan, the OAuth token, replacing the other agent's review, and soft
  guards for `main`).

## 2026-11-13: A Don't start yet can be fixed in a new Take 5 (task 0010)

- Decision: The review warns about a hazard with no controls before Finish, with a way to add one. A Don't start
  yet result offers to copy its answers into a new Take 5. The saved one stays as it was.
- Why: Jake tried the app and was told "Say how you will control: ..." with no way to add the control. Typing
  everything again is what makes people stop doing Take 5s properly. Keeping the first one unchanged keeps the
  record of what was first planned.
- Alternatives considered: Only the warning (a fix after saving would still mean typing it all again). Only the
  copy (the worker would only find out after saving). Editing a saved Take 5 (a finished Take 5 never changes,
  so its record can be trusted).
- Decided by: human (Jake, 2026-11-13). He also approved a `fixes` field on `SavedTake5` (a data model change):
  the new Take 5 holds the first one's ID, so the two are linked without changing the first.

## 2026-11-13: Keep the unfinished Take 5 in the browser tab (task 0004 review)

- Decision: The draft and its submission ID are kept in the tab's `sessionStorage` until the Take 5 is saved, a
  409 says its ID is used, or the tab is closed. Only the worker's name is kept after that. (Task 0005 added the
  list of hazard questions a hazard was added from, spec D15.)
- Why: On a phone a reload or a slip of the back gesture would otherwise lose everything typed, and the same ID
  must survive a reload so a retry can't save the Take 5 twice.
- Alternatives considered: Keep it in memory only (lost on reload). `localStorage` (kept after the tab closes,
  so the worker's job details would stay on a shared phone).
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
  The card's descriptions help explain ratings without pre-selecting answers or supplying hazards.
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
