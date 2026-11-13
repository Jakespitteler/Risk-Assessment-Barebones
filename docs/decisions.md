# Decisions

Newest first. One short entry per non-obvious decision.

## 2026-11-13: Front-end libraries (proposed)
- Decision: React, TypeScript, Vite, Tailwind CSS, TanStack Query, React Router, openapi-typescript; Vitest,
  React Testing Library and Playwright for tests; ESLint and Prettier; npm.
- Why: Jake asked for the best of what is current without anything obscure or likely to be replaced in a few
  years, and for the ability to change systems without much trouble. React is the most widely used UI library
  and the least likely to go away. The others are the mainstream choice for their job, and each is kept to one
  corner of `frontend/` so it can be swapped alone.
- Alternatives considered: Svelte or Vue (pleasant, smaller communities). Next.js (adds a second server and
  moves back-end logic into JavaScript). Server-rendered pages with no framework (the first proposal; rejected by
  Jake as less slick).
- Decided by: proposed by claude on the human's brief, waiting for human approval of the list

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
- Decided by: human. Still open: which provider first (D9), what happens with no AI (D10), and whether the AI
  judges the answer (D11); see `spec.md`.

## 2026-11-13: Own words first, hazards rated twice, no sign-in
- Decision: The worker writes hazards before seeing the card's hazard questions, and fixed rules push back on
  thin answers. Each hazard is rated before and after its controls. There is no sign-in; the worker types their
  name.
- Why: These were the recommended options for spec decisions D1, D2 and D4. Jake was asked to name the ones he
  would change; he changed D1 only by adding the AI question (above) and left D2 and D4 as recommended.
- Alternatives considered: The card's ticks only; one rating per hazard, as on paper; accounts from the start.
- Decided by: human

## 2026-11-13: Store each Take 5 as one JSON document (proposed)
- Decision: One SQLite table, `take5s`, holding the whole Take 5 as JSON beside the columns the list needs,
  reached through Python's built-in `sqlite3` behind a `Take5Repository` interface.
- Why: A Take 5 is always read and written whole. Separate hazard and control tables would add joins and code
  with no benefit yet, and the built-in module keeps every SQL statement in the repo to read.
- Alternatives considered: Separate tables per entity (better for reports across hazards; revisit when a report
  is wanted). SQLAlchemy and Alembic as in the original app (handles table changes and other databases, but
  hides the SQL and is more to learn for one table). Either swap touches one file.
- Decided by: proposed by claude, waiting for human approval

## 2026-11-13: Unlikely / Critical scores 19, not the printed 18
- Decision: The matrix cell for Unlikely / Critical is recorded as 19.
- Why: The printed card shows 18 there, which repeats Possible / Major and leaves 19 unused. Every other cell is
  a unique rank from 1 to 25. The band (Extreme) is the same either way.
- Alternatives considered: Keep the printed 18. Two cells would then tie, and "a higher score is a higher risk"
  would have one exception.
- Decided by: carried over from the original Risk-Assessment app; waiting for human confirmation here
