# Decisions

Newest first. One short entry per non-obvious decision.

## 2026-11-20: Errors obvious in the terminal that runs the app (task 0028)

- Decision: Browser crashes, `console.error` and `console.warn` print in the terminal through Vite's own
  `server.forwardConsole`. The back end's lines share one format through `backend/dev_logging.json`, with no
  "back end" or "front end" label. A handled AI failure logs one line naming its kind, with no trace; a bug in a
  route logs one line naming the request, then its trace. Only failed requests print, through a small log
  filter (`api/request_log.py`). No log file. While the back end isn't answering, Vite prints one short line per
  failed request instead of a proxy error and stack, through a small custom logger.
- Why: Jake's answers of 2026-11-19 and 2026-11-20: "it should always be obvious from a glance what/where is
  going wrong". Labels would have brought back the output pipe that task 0029 removed for being complicated.
- How: a custom logger makes Vite ignore the command line's `--logLevel` and `clearScreen`, so the logger reads
  the level from the command line itself and never clears the screen. Only a time-out or an `AiReplyError` counts
  as an expected AI failure; anything else while asking the AI is a bug and keeps its trace. So every AI adapter
  wraps its library's errors in `LanguageModelError` (a kind of `AiReplyError`), keeping each as the cause; the
  Claude adapter now does.
- Not chosen: a plugin of our own or `vite-plugin-terminal` for browser errors; labels on each line; a stack trace
  for every AI failure; two quiet 422s; a log file.
- Decided by: human (the behaviour), agent (how).

## 2026-11-20: `start.py` restarts the back end itself (task 0034)

- Decision: `start.py` runs uvicorn without `--reload`, watches `backend/src` for saved Python files, and restarts
  the back end itself. A change that won't start prints its error, and the app waits for the next save.
- Why: on Windows uvicorn's reloader restarts with a Ctrl+C that Windows gives to every program in the terminal,
  so `start.py` stopped the whole app on each save, and hid the error of a broken change.
- Not chosen: a new package such as `watchfiles` (needs approval, and a once-a-second look is enough); ignoring
  Ctrl+C on Windows while the back end restarts (a real Ctrl+C then can't be told apart).
- Decided by: human.

## 2026-11-20: A desktop test, and hover and focus on everything clickable (task 0031)

- Decision: one whole-app test runs a Take 5 and the saved list at 1280 by 800. On each screen it checks nothing
  scrolls sideways, then hovers over everything a person can click and expects its look to change, then tabs
  through the page and expects the app's own 4 px focus outline on each stop. The gaps it found are filled with
  a few class names each: a darker fill for buttons and button-like links, a thicker underline for text links, a
  light fill for choices and the step bar (spec D87 to D89).
- Why: the goal says a phone or a desktop (D65). Screens already sit in a centred column on a desktop, so no
  layout change was needed, but a mouse user expects things to react, and some links relied on the browser's own
  focus ring. Jake took every recommended answer on 2026-11-20.
- Not chosen: running every test at desktop width too, which doubles the run again for little gain.
- Decided by: human.

## 2026-11-20: The saved list 50 at a time (task 0021)

- Decision: `GET /api/take5s` sends a page of 50, newest first, as `{take5s, next}`. The next page is asked for
  with `?before=` the last one shown, which the database compares on the same pair the list sorts by (the time
  saved, then the save order), so a Take 5 saved meanwhile can't shift or repeat one. "Fixed" is found for each
  page with one look for fixes of that page's IDs. The list screen adds a "Show more" button (spec D80 to D86).
- Why: Jake took every recommended answer on 2026-11-20. Sending every Take 5 at once is too slow on a weak signal
  once hundreds are saved (D18). A cursor rather than "skip 50" is the standard way to page a list that grows at
  the top.
- How: the API's reply changes from a list to an object, a change to a public interface that Jake approved. The
  front end uses TanStack Query's `useInfiniteQuery`. `fixed_ids()` in `domain/take5/fix.py` is gone: it needed
  every Take 5, and the repository's new `fixed_among()` does the job for one page. No new column or index.
- Not chosen: skip and take; a total count; loading more on scroll; a page size the phone picks.
- Decided by: human.

## 2026-11-19: Dark mode, colours named by their job, and axe in the browser tests (task 0024)

- Decision: The app follows the phone's light or dark setting, and a sun or moon button in the top bar overrides
  it until the phone's own setting next changes. The choice is kept on the phone with the phone's setting at the
  time. Every colour is named once by its job in `frontend/src/index.css`, with a light and a dark value; the
  risk band colours stay fixed. A few lines in `index.html` set the mode before the app draws. Text reaches 7 to
  1 in both modes, checked by `@axe-core/playwright` on every screenshot the whole-app tests take, and those tests
  now run twice, on a light phone and a dark one (spec D69 to D79).
- Why: Jake took every recommended answer, and added "how it looks" as a reason. Light reads best in full sun,
  so a gloved worker needs a way back without the phone's settings, and a phone that goes dark at sunset should
  take the app with it. Named colours mean a new component gets dark mode for free. axe checks the pages as
  drawn, not a list of colour pairs someone remembered to write down.
- How: axe-core is a new development dependency, approved by Jake on 2026-11-19; nothing new reaches the
  worker's phone. To reach 7 to 1 in light, a step not yet reached now uses the quieter ink (slate-700, was
  slate-600), and a text box with a gap now has the same red edge as its message (red-800, was red-700). Running
  every browser test in both modes takes about 2.7 minutes instead of 1.2.
- Not chosen: the phone's setting only; a three-way switch; a `dark:` class beside every colour; a Vitest test of
  colour pairs; WCAG AA only.
- Decided by: human (the product choices), agent (how).

## 2026-11-19: The app's goal, and the work it needs (task 0030)

- Decision: The goal at the top of `docs/spec.md`: make a mine site safer by making every Take 5 count. A Take 5
  on a phone or a desktop makes the worker think and stays quick and pleasant enough to be used; paper cards
  can be photographed into normal saved Take 5s, confirmed by a person beside the photo; and any set of Take 5s
  can be ranked worst first by the AI, weighing risk against how little thought the answers show. Anyone can
  scan and rank, with no sign-in. The AI is used wherever it makes a Take 5 safer, but a worker never needs it to
  finish one. Speed is judged by feel in demos, not a fixed target (spec D64 to D68).
- Why: Jake is proving a point to safety people and crews alike, and an app nobody uses makes no one safer. He
  wants it simple and focused on one goal, so that usability doesn't distract from what it proves.
- How: three new tasks, in this order after 0028: 0031 a desktop test (screens already fit a desktop), 0032 rank
  Take 5s worst first (one ranking for a scanned batch and for "worst of the day", with workers' names shown, as
  on the saved list), 0033 photograph paper cards into Take 5s. Task 0021 (the saved list 50 at a time) is parked.
- Not chosen: a phone-only app; a supervisor role for scanning and ranking; saving scans without a person's check;
  a fixed time target such as two hazards in under three minutes.
- Decided by: human (Jake and Claude worked on the goal over several messages until both agreed it).

## 2026-11-19: One command starts the app, and every command runs from the repo root (task 0029)

- Decision: `uv run start.py` in the repo root replaces `scripts/dev.py`. It stops if port 8000 or 5173 already
  answers (on IPv4 or IPv6), before installing anything; checks git and Node.js with `install.py`'s checks; runs
  `uv sync --locked` every time; runs `npm ci` only when `package-lock.json` differs from the fingerprint kept in
  `node_modules` after the last install (`install.py` writes it too); installs the test browser after each
  front-end install, warning and carrying on if that fails; then starts both halves and prints one ready line with
  the app's address (the forwarded one in a Codespace). `scripts/setup.py` moves to the root as `install.py`,
  `check.py` moves there too, and a new `test.py` runs the tests (all, or `backend`, `frontend` or `e2e` with the
  rest of the line passed on). `check.py --fix` runs the formatters, the lint tools' own fixes and the API types.
  CI, the reviewer's instructions and Claude's allow list name the new commands.
- Why: Jake asked for one command that sets up, updates the installs and prints only the right address, and for
  no `cd` before everyday commands. He took the recommended answers, except that the API gets no page at `/` and
  its address is never printed. Installing only the locked versions means a start never brings in a version the
  repo wasn't tested with.
- How the address lines are hidden: in each server's own settings, and their output goes straight to the terminal.
  Uvicorn gets `--log-config backend/dev_logging.json`: its default log settings with the `uvicorn.error` logger at
  warnings, which drops "Uvicorn running on ..." and its other start-up, restart and shutdown lines but keeps
  requests, reload notices, errors and the app's own lines. Vite gets `--logLevel warn`, which drops its address
  box (and its "page reloaded" notes) but keeps warnings and errors. Vite's `clearScreen` is off, so `npm run dev`
  alone doesn't clear earlier output either.
- Why not a pipe: the first version read both servers' output through a pipe and dropped the address lines. It
  worked, but needed reader threads, colours forced back on, UTF-8 forced on Windows, and waiting for the last
  lines before exiting, which was about 250 lines with tests and where most review findings were. Jake chose the
  settings approach on review. Task 0028 can add a pipe if labelling each line still needs one.
- Not chosen: `uv run app.py` (clashes with the back end's `app.py`); a task runner, `make` or a root
  `package.json` (another tool on every computer, or no Windows `make`); a uv workspace (moves `.venv` and the lock
  file); upgrading packages on start; reading the servers' output through a pipe (above); a port
  check that binds the port (a socket waiting to close after a restart would read as busy).
- Also: Claude's format hook now formats a `.py` file in the repo root too, the hook change question 1 (a)
  named. The "install everything again" command is `install.py`, not `setup.py`: by an old convention a root
  `setup.py` is a Python package build file, which pip and some tools would try to run (Jake chose the name on
  2026-11-19).
- Decided by: human (the product choices, 2026-11-19), agent (how).

## 2026-11-19: An AI judges vague hazards, with the word rule as the fallback (task 0027)

- Decision: Whether a hazard linked to a Yes is vague (spec T6) is judged by an AI when one is set up, through a
  new `HazardJudge` Protocol filled by any `LanguageModel`. By default the provider's quick model judges (Claude
  Haiku 5.5), or the one `TAKE5_AI_HAZARD_MODEL` names. The AI replies "vague" or "specific" only, and the nudge
  keeps its fixed words. It has 5 seconds; with no AI, a failure, a late answer or any other reply, task 0022's
  word rule decides. Each usable verdict is remembered in the server's memory for the same hazard, question, job
  and location. The phone asks once for each hazard's words, never while the worker types in the nudge's box. The
  hazard check page says hazards go to an AI when one is set up (spec D56 to D63).
- Why: Jake took every recommended answer. The word rule nudges a short specific hazard ("Crusher dust") and
  passes a long vague one; a model can read what the words say. A one-word verdict is cheap, quick and testable,
  and can't put words in the worker's mouth (T1). Haiku 5.5 costs about 0.02 cents an ask against about 0.6 on
  Opus 5.5, and the worker is mid-form. Remembering verdicts stops paying twice for the same words.
- How: the nudges move off `POST /api/take5s/check` to their own `POST /api/take5s/nudges`, and `DraftCheck` loses
  `nudges`. The check runs on many pauses in typing and on every Continue, so an AI inside it would be asked far
  more often and would hold up Continue. This is a change to a public interface, made to carry out Jake's answer
  to question 1 (D56), and it waits on his approval in the pull request. The hazard check page makes one ask for
  the whole page, and leaves out the links of hazards whose words were kept, so those are never sent. The AI is
  asked in background threads, so a late verdict is still remembered for the next check, and two checks of the
  same words share one ask. Verdicts are kept for at most 1,000 texts. The worker's name is never sent; the hazard
  is a quoted value in JSON, as the challenge question's Take 5 is.
- Not chosen: the AI inside the check; asking on every pause in typing; saving verdicts in the database (a data
  model change); a reason or rewording from the AI.
- Decided by: human (the eight product choices), agent (how). The separate endpoint is the agent's proposal;
  the human approves it by merging the pull request.

## 2026-11-18: Claude Opus 5.5 writes the challenge question, and the review says what it is sent (task 0009)

- Decision: The challenge question is written by Claude Opus 5.5 (`claude-opus-5-5`) on low effort, through
  Anthropic's own `anthropic` library, behind the `LanguageModel` Protocol. The provider, model and key are
  settings (`TAKE5_AI_PROVIDER`, `TAKE5_AI_MODEL`, `TAKE5_AI_KEY`), read from the environment or `backend/.env`.
  With no key the fallback question is always asked. The adapter gives up after 11 seconds and never retries.
  The question may be about a hazard the job plainly has that isn't on the list. When an AI is set up, one line
  above Submit says what goes to it, and the question itself is still not labelled. The AI judging vague hazards
  is its own task, 0027 (spec D52 to D55).
- Why: Jake took every recommended answer. The question is the one part of the Take 5 a worker can't see coming,
  so its quality matters more than its cost: about 1.5 to 2 cents a question, estimated, measured in the PR. Low
  effort keeps it well inside the service's 10-second wait. A missed hazard is often the weakest point, and by
  then the worker has already listed hazards in their own words, so T1 still holds. Telling workers what is sent
  answers the open question about names typed into the job; labelling the question would make the fallback look
  second-best. Judging vague hazards runs while the worker types, which raises its own questions (how often to
  call, cost, no signal), and would have doubled this PR.
- How: a retry inside the adapter would run past the service's 10 seconds, so `max_retries` is 0, and the network
  limit is 11 seconds so a call the service gave up on ends soon after. A refusal or a reply with no text raises
  `LanguageModelError`, and the service asks the fallback. The adapter logs the tokens each reply used, never any
  text. Every test hides the key (`tests/conftest.py`), the whole-app tests run with an empty key, and the one
  test that calls the real AI runs only with `pytest -m real_ai`. `ai_notice` on `GET /api/take5/template` comes
  from the back end, so the line shows only when an AI is really plugged in. `ai/` may import `domain`, as
  `storage/` may, because `AiQuestion` lives there.
- Not chosen: Sonnet 5.5 or Haiku 5.5 (one setting away); Anthropic's server-side refusal fallbacks (a refusal
  already falls back to the fixed question); the key in the cloud environment's secrets (it stays on Jake's
  computer); a fixed sentence in the front end (it would claim an AI is asked when none is set up).
- Decided by: human (the four product choices), agent (how).

## 2026-11-18: The challenge question is asked after Submit, and only that phone answers it (task 0008)

- Decision: The review's button is Submit. It saves the Take 5 unfinished, and the challenge question follows on
  its own screen with no way back to the form; Finish there saves the answer and the verdict. Only the phone that
  submitted a Take 5 answers its question, opening the app again goes back to an unanswered one, and there is no
  time limit on answering. A saved fix marks its original Fixed even before it is answered. The worker isn't told
  whether the AI or the fallback asked, and C4 stays at four words (spec D44 to D51). `Take5Repository` gains
  `save_question` and `finish`, each of which only changes a Take 5 that is still unfinished. The AI is given the
  Take 5 as JSON, and the service waits for it in a thread for at most 10 seconds.
- Why: Jake took every recommended answer. The Take 5 is saved before the question so a slow AI never loses it,
  and so it can't be changed after: going back would let a worker keep asking until the question is easy. Once
  saved, the answers and the verdict are fixed, so a time limit on answering would only strand a record as Not
  finished. Storage had no way to change a saved Take 5; the two guarded updates keep "a finished Take 5 is never
  changed" true in the database itself, so two answers at once can't both win. JSON puts everything the worker
  typed inside quoted values, so a job that says "ignore your instructions" stays a job (spec example 76). The
  phone remembers the submission ID before it sends it, so a Take 5 saved with its reply lost can still be
  answered on that phone; a link to an unknown or finished Take 5 forgets it again.
- Alternatives considered: Keeping Finish on the review; a Back button from the question; the saved list on
  reopening; anyone answering; the draft's 2-hour limit on answering; marking Fixed only once a fix is answered;
  replacing the whole document with one generic update (it couldn't refuse a second answer on its own).
- Decided by: human (Jake, 2026-11-18, in chat), from Claude's recommended picks

## 2026-11-18: The step bar can be tapped, but only to steps already reached (task 0026)

- Decision: The five steps at the top of the form can be tapped to open a step's first page, but only steps
  already reached in this Take 5. A tap forward checks the page being left, as Continue does; a tap back doesn't.
  How far the worker got is kept with the draft on the phone (spec D38 to D43).
- Why: Jake asked for the steps to work as a navigation bar. A bar that opens any step would let a worker skip
  every page Continue checks, which is what the app exists to stop. Going back to fix something is the useful
  part, and it is also where a tap saves the most taps.
- Alternatives considered: Back only (a fix from the review would then need Continue through every page again);
  every step at any time (skips the thinking, and leaves the checks to the review alone).
- Decided by: human, from Claude's recommended picks

## 2026-11-18: Nudge a short hazard picked for a Yes to say what and where (task 0022, part 2)

- Decision: A hazard linked to a Yes with fewer than 6 words (`Take5Template.specific_hazard_words`) is nudged
  to say what could hurt and where, with an example kept beside that question in the template (spec T6). The
  worker can reword it in place or keep it; keeping it is remembered on the phone for those exact words. It
  never blocks. The check returns it in a new `nudges` list, beside errors, warnings and thinking questions.
- Why: Jake chose the word rule for now (2026-11-18), and an AI once one is set up. A word count is simple and
  exact to test, but it can't tell a short specific hazard from a vague one, so it only nudges and can be kept.
  A nudge isn't a warning (that says the job will stop) or a thinking question (that must be answered), so it
  has its own kind. The examples and the minimum are template data, so another company's card can change them.
  The minimum and the examples add to the data model and the API.
- Alternatives considered: A list of category words like "vehicles" (never nags a specific hazard, but misses
  "Get hit by a car"). An AI now (needs signal and widens D3). Required rewording (would nag a short specific
  hazard). Keeping "Keep it as it is" on the server (it is about the screen, like Leave and Undo).
- Decided by: human (Jake, 2026-11-18: "(A) for now ... All else do the recommended").

## 2026-11-18: Each Yes to a hazard question is linked to a hazard on the list (task 0022, part 1)

- Decision: A Yes to a hazard question needs a hazard on the worker's list linked to it before Continue (spec
  T5). The worker picks it with "It's on my list", or adds a new one from that Yes. The link is kept on the
  hazard, as `covers` (the IDs of the questions it is linked to), on the phone's draft and on the saved hazard,
  and shown under each Yes on the review and the result. One hazard can cover several questions. The phone-only
  "Added to your list" mark (D15) is gone; a hazard added from a Yes is simply linked to it.
- Why: Jake chose "It's on my list" with a pick from the list on 2026-11-16, over a one-tap button that could be
  passed without looking at the list. Without T5 a Yes could still be tapped past, which is what the app exists
  to stop. Keeping the link on the hazard, rather than giving each hazard an ID and keeping links beside the
  hazards, needs no new ID: removing a hazard removes its links, Undo puts both back, and removing an earlier
  hazard can't point a link at the wrong one. Saving it lets the review and result show what each Yes was about.
  `covers` is a data model and API change; a Take 5 saved before it reads as linked to nothing.
- Alternatives considered: A hazard ID made on the phone, with links beside the hazards (the task's first
  recommendation; more to keep in step for the same result). Keeping links only on the phone (smaller, but the
  result couldn't show them). A reminder that can be passed by, as before.
- Decided by: human. Jake chose the picker on 2026-11-16, and Claude's recommended picks for the rest on
  2026-11-18 ("All else do the recommended").

## 2026-11-17: Set-up is a Python script run by uv, and leaves git, uv and Node.js to the person (task 0023)

- Decision: `uv run scripts/setup.py` sets up a freshly cloned repo. It checks for git and Node.js 22.22.2 or
  newer and stops, saying how to install them, if either is missing. Then it installs what AGENTS.md lists
  (`uv sync --locked`, `npm ci --engine-strict`, `npx playwright install chromium`). It warns, but carries on,
  when the repo is in a cloud-synced folder.
- Why: uv is already how every script here runs, and it installs Python 3.13 itself, so one Python script works
  on Windows, macOS and Linux and can be tested like `dev.py`. Installing git or Node.js changes the whole
  computer, may ask for an administrator, and needs a new terminal before the tools are found, so the script says
  how instead of doing it. The locked front-end packages need Node.js 22.22.2 or newer (jsdom), or 24.15 or newer
  on version 24. That is stricter than the "22 or newer" the docs said, and npm only warns about it, so
  `--engine-strict` makes npm stop instead. `npm ci` runs every time rather than being skipped when the packages
  look current: it is slower, but always matches `package-lock.json`.
- Alternatives considered: A PowerShell script (Windows only, and it can't be tested with pytest). A script that
  also installs uv and Node.js with winget (fewer steps on a new Windows computer, but it changes the computer
  without asking and works only on Windows). Stopping, rather than warning, in a cloud-synced folder (safer, but a
  folder that only looks synced would have no way through).
- Decided by: proposed by claude; the human approves it by merging task 0023's pull request.

## 2026-11-16: What a kept draft tells the worker (task 0019)

- Decision: A draft the back end says has run out is first looked up by its submission ID; if it was saved and
  only the answer was lost, its result opens instead of "run out". When a kept draft can't be checked as it
  opens, the form and the list say so, with when it was started. While a draft is kept, a result screen says
  "Carry on your Take 5". Each check returns `runs_out_at`, and the form and the list count down the time left.
  Spec D26 to D29.
- Why: Jake asked for each, on Claude's follow-up questions from the review: "fix it", "do whatever makes it
  most clear what is actually going on to the user", and "It should say somewhere how long the take 5 has
  left". The look-up uses the existing `GET /api/take5s/{id}`, so no new endpoint was needed. The back end
  works out `runs_out_at`, so the phone only counts down to a time it is given and holds no time rule.
- Alternatives considered: Sending the submission ID with the check (a request shape change). Sending the
  time limit in the template, for the phone to add to `started_at` (a rule copied into TypeScript).
- Decided by: human (Jake, 2026-11-16, in chat).

## 2026-11-15: Leave a Take 5, keep one draft on the phone, and a 2-hour limit (task 0019)

- Decision: Every page of the form has Leave, which keeps the Take 5 for later or throws it away (with Undo).
  One unfinished Take 5 is kept on the phone (`localStorage`) from the first change until it is saved or thrown
  away. It runs out 2 hours after it was started: the back end refuses it on the check and on submit, the phone
  throws it away and says why. The limit is `Take5Template.draft_time_limit_minutes`; setting it to `None` turns
  the check off completely. "Fix this in a new Take 5" asks before it replaces an unfinished Take 5. Each saved
  Take 5 keeps when it was started (`started_at`). Spec D19 to D25 and K1 to K3.
- Why: A worker gets called away mid-way, and closing the app lost everything. But a Take 5 is meant to be done
  at the job, just before starting: a draft started at breakfast and finished at lunch is a Take 5 done without
  looking. Two hours covers a radio call or lending a hand. Counting from the start, not the last change, means
  tapping it now and then can't keep it alive. An old draft is thrown away rather than reopened, because reopening
  it hands back an old hazard list to tick through. One draft keeps the screens simple. On the phone needs no
  data model change and keeps drafts private while there is no sign-in (D4). The start time lets the three-minute
  target be measured later.
- How the time is checked: the phone sends `started_at` by its own clock, with its time zone, and the back end
  compares it with the server's clock (`domain/take5/time_limit.py`, given the time by `Take5Service`'s
  injected clock). Phones set their clocks from the network, so the two agree; a phone whose clock is set hours
  wrong would see drafts run out early or late. A retry of a Take 5 that was saved in time is never refused.
- Alternatives considered: Throw away only, or keep only. Drafts on the server (a supervisor could see them and
  they survive a new phone, but a new table and endpoints). 12 hours, or no limit. Reopening an old draft with its
  answers cleared, or with a "check everything" warning. A list of drafts. Replacing a draft with a fix without
  asking (as before), or refusing the fix. Not saving the start time.
- Decided by: human (Jake, 2026-11-15, in chat: "Do all of your recommendations", with no limit switching the
  timer off completely), on Claude's questions in task 0019's thread.

## 2026-11-15: Fixed on the saved list, one date format, and paging later (task 0007)

- Decision: A Don't start yet that a newer Take 5 fixes shows "Fixed" in the saved list (`Take5Summary.fixed`),
  whatever the newer one's verdict, as its result screen already says. The location stays off the list. Every date
  and time, on the list and the result screen, is written "14 Nov 2026, 6:52 pm" in the phone's time zone. Once
  the app is hosted for a crew, the list shows the newest 50 with "Show more" (task 0021). Spec D16 to D18.
- Why: A red card that has been sorted out shouldn't look like an open problem. One date format reads the same
  everywhere; the browser's default ("14/11/2026, 6:52:04 pm") was harder to read. Sending the whole list is fine
  until there are hundreds.
- Alternatives considered: The location on each card. "Fixed" only once a fix says Good to go (a stricter
  reading, but it would disagree with the result screen). Each phone's own date format. Paging now.
- Decided by: human (Jake, 2026-11-15, in chat), on Claude's questions in pull request #30. `fixed` is worked out
  from the whole list by `fixed_ids()`; task 0021's pages will need another way.

## 2026-11-14: The saved Take 5 list sends one short line per Take 5 (task 0007)

- Decision: `GET /api/take5s` returns a list of `Take5Summary` (`id`, `created_at`, `worker_name`, `job`,
  `can_start`), newest first, with no paging. `Take5Repository` gains `list_newest_first()`. The verdict is the one
  saved with each Take 5, never worked out again. Task 0008 makes `can_start` `bool | None`, None meaning "Not
  finished". The 2026-11-15 entry adds `fixed`.
- Why: The list screen shows only the date, worker, job and verdict (spec F5). Sending the whole card, with its
  template copy, for every Take 5 would be slow on a weak signal. Paging, search and filters are out of scope for
  now.
- Alternatives considered: Sending each whole `SavedTake5` (no new shape, but much bigger). A `Verdict` with its
  reasons in each line (the list doesn't show the reasons). Paging now (more code before there are enough Take 5s
  to need it).
- Decided by: claude, in task 0007; Jake approves by merging its pull request.

## 2026-11-14: Keep the built-in sqlite3 until storage needs more (task 0018)

- Decision: Storage stays on Python's built-in `sqlite3` with hand-written SQL. It moves to the SQLAlchemy ORM
  (version 2's typed style, no relationships) with Alembic, as its own task, when the first of these is planned:
  a company database such as PostgreSQL, the first change to a table that already holds rows, or a second table
  with its own repository (another kind of card, or drafts kept on the server). No dependencies are added now.
- Why: The next tasks need one more query (0007) and no table change. In a tried-out version, a library made the
  file 8 to 21 lines shorter out of 64, and plain SQL is easier for Jake to follow. Only `storage/` knows how Take 5s
  are stored, so switching later costs about what it costs now. When the time comes, the ORM gives real types
  under pyright strict, where Core's are `Any`; both get Alembic's autogenerated migrations.
- Alternatives considered: SQLAlchemy Core now or later (one set of queries for SQLite and PostgreSQL and no
  session to learn, but columns are typed `Any`). The SQLAlchemy ORM now (best typed, but more to learn for no
  current gain). SQLModel (still 0.0.x, needs type workarounds, and invites joining the domain model to the table).
  The full comparison is in `docs/tasks/0018-database-library.md`.
- Decided by: human (Jake, 2026-11-14, in chat), on Claude's proposal in task 0018.

## 2026-11-14: A T3 reason is saved only while T3 asks (task 0006 review)

- Decision: The phone's draft keeps what the worker wrote for T3, but the rated `Hazard`, and so the saved
  Take 5, keeps it only while the question still applies. Adding a strong control or lowering the before rating
  below 11 drops it from what is saved. This replaces part 2's "the answer remains saved".
- Why: A saved Take 5 is a record. Showing "Why stronger controls weren't possible" beside an isolation control
  the worker did add contradicts itself.
- Alternatives considered: Save every answer ever written (keeps a reason that no longer explains anything), or
  clear the box when the question goes (throws away the worker's words if they undo).
- Decided by: Claude in review of PR #28; Jake confirms it by merging that PR, or asks for it to be undone.

## 2026-11-14: Thinking questions come from the draft check (task 0006)

- Decision: `POST /api/take5s/check` adds `thinking_questions`, each with a field `path` and `message`.
  A T3 question remains present when answered, so the phone keeps showing the answer without deciding whether
  the rule applies. `HazardDraft` and `Hazard` gain `weak_controls_reason`, defaulting to an empty string for
  older drafts and saved documents. A missing required answer is also a normal field error. The short-job
  message is "Describe the job in at least four words." No dependencies are added.
- Why: The back end owns when the question applies; a field error alone would disappear when answered and
  take the answer box with it. Defaults keep existing records readable and unfinished drafts usable.
- Alternatives considered: Calculating the rule in TypeScript (duplicates a safety rule), or using only an
  error (cannot represent an answered question that still applies).
- Decided by: human (Jake, 2026-11-14), approving these additions and the message before implementation.

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
