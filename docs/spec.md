# Product spec

Status: **draft, waiting for Jake's approval** (task 0001). The human owns product decisions; agents propose,
the human approves. Anything marked *proposed* is Claude's recommendation and is listed again under
[Decisions waiting on Jake](#decisions-waiting-on-jake). Nothing here is final until that table is empty.

## Purpose

A Take 5 is the short personal risk assessment a mine-site worker does before starting a task. On paper it is a
card of tick boxes, and tick boxes get ticked without thinking. This app is a Take 5 for a phone that cannot be
finished on autopilot: the worker has to say, in their own words, what could hurt someone on this job today and
what will stop it, and the app pushes back when the answer is thin.

This repo is a rebuild of the one core feature of the larger Risk-Assessment app. The rule of thumb for every
design choice: **if the app is boring and can be used without thinking, people will use it without thinking.**

## Users and roles

| Role | Who | What they can do |
| --- | --- | --- |
| Worker | Anyone on a mine-site crew about to start a task | Fill in a Take 5, see its verdict, look back at saved Take 5s |

There is one role for now (*proposed*, decision D4). There is no sign-in: the worker types their name and the
phone remembers it.

Where and when it is used (carried over from the original app; Jake to confirm):

- On the worker's own phone, standing at the job, just before starting.
- Often with gloves on, in bright sun, with a weak signal. So: big tap targets, high contrast, small pages.
- It has to be quick enough that it is not resented. Target (*proposed*): a job with two hazards takes under
  three minutes.

## Core workflow

The five screens follow the five steps of the Take 5 booklet. They are five parts of one form: nothing is sent
or saved until the worker submits at the end.

1. **The job.** The worker types their name, what the job is and where it is, in their own words. All three
   are needed.
2. **Think through the task.** Seven questions from the card (below). Each is answered Yes, No or N/A. Nothing is
   selected to begin with and there is no "all Yes" button. A No means *sort this out first*.
3. **Spot the hazards.** The worker first writes at least one thing that could hurt them or someone else. Only
   then does the app show the card's seven hazard questions as a cross-check ("did you miss any of these?").
   A Yes shows "Make sure it's on your list" with a button to add a hazard. Every Take 5 has at least one
   hazard: "no hazards" is not an answer on a mine site.
4. **Assess the risk and make the changes.** For each hazard the worker:
   1. rates how likely and how bad it is **before** any controls,
   2. writes each control and picks what kind of control it is,
   3. rates how likely and how bad it is **after** those controls. With no controls there is nothing to rate
      again.
   The app shows the score and band from the risk matrix as soon as both parts of a rating are picked.
5. **Result.** The Take 5 is saved with its verdict and the worker sees it: *Don't start yet* or *Good to go*,
   with the reasons in plain words.

Saved Take 5s can be opened again from a list. A saved Take 5 is never edited; if the job changes the worker
does a new one.

### The card's questions

Think through the task (a **stop** question: No means don't start until it is sorted):

1. Do you understand the task scope?
2. Does a procedure exist?
3. Do you understand the steps required to do the task?
4. Are tools and equipment in good order?
5. Do you have the correct PPE?
6. Do you have the necessary permits?
7. Have you got a clear plan in mind?

Spot the hazards (a **hazard** question: Yes means there is a hazard to list and control):

1. Will I be operating equipment with the guards removed?
2. Am I or others at risk from the operation of vehicles or mobile equipment?
3. Does the task involve hazardous materials?
4. Will I be performing a task without a specific isolation procedure?
5. Will I be working at heights?
6. Will I be impacted by other activity in the vicinity?
7. Other environmental and/or H&S hazards?

### Kinds of control

The worker picks one for each control. They are the card's "Make the changes" list, strongest first.

| Kind | Strong or weak |
| --- | --- |
| Remove the hazard | Strong |
| Isolate the hazard | Strong |
| Barricade the hazard | Strong |
| Put systems in place (permits, safe work procedures) | Weak |
| Ensure correct behaviour | Weak |
| Wear PPE | Weak |

A strong control still works on a bad day. A weak control relies on every person getting it right every time.

## Risk model

Risk is rated on the booklet's 5x5 matrix. The worker picks a likelihood and a consequence, and the matrix gives
a **score** from 1 to 25 and a **band**. A higher score is always a higher risk.

Likelihood:

| Likelihood | Means | How often |
| --- | --- | --- |
| Almost Certain | Expected to happen | Once a week |
| Likely | May easily happen | Once a month |
| Possible | May happen | Once every year |
| Unlikely | May happen sometime | Once every 10 years |
| Rare | May happen in extreme circumstances | Once every 100 years |

Consequence (health and safety column of the booklet):

| Consequence | Means |
| --- | --- |
| Low | First aid treatment |
| Minor | Medical treatment |
| Moderate | Classified injury (lost time or restricted work) |
| Major | Fatality or severe permanent disability |
| Critical | Multiple fatalities, or health effects to more than 50 people |

The matrix (score and band for every pair):

| Likelihood \ Consequence | Low | Minor | Moderate | Major | Critical |
| --- | --- | --- | --- | --- | --- |
| **Almost Certain** | 11 High | 16 High | 20 Extreme | 23 Extreme | 25 Extreme |
| **Likely** | 7 Moderate | 12 High | 17 High | 21 Extreme | 24 Extreme |
| **Possible** | 4 Low | 8 Moderate | 13 High | 18 Extreme | 22 Extreme |
| **Unlikely** | 2 Low | 5 Low | 9 Moderate | 14 High | 19 Extreme |
| **Rare** | 1 Low | 3 Low | 6 Moderate | 10 High | 15 High |

The printed card shows Unlikely / Critical as 18, the same as Possible / Major, and never uses 19. Every other
cell is a unique rank, so the app records it as 19. Its band, Extreme, is the same either way.

### Scoring rules

- **R1 Rating.** A hazard's rating is the matrix cell for its likelihood and consequence. The matrix is a lookup
  table; nothing is multiplied.
- **R2 Bands.** Low is 1 to 5, Moderate is 6 to 9, High is 10 to 17, Extreme is 18 to 25.
- **R3 JHA threshold.** A rating of 11 or more needs a Job Hazard Analysis (JHA). Note that 10 is High but does
  not need one.
- **R4 Which rating counts.** A hazard has a *before* rating (no controls) and an *after* rating (with the
  worker's controls). The **after** rating is the one that counts for R3 and R5 (*proposed*, decision D6).
- **R5 The Take 5's rating.** The Take 5's rating is the highest *after* rating of its hazards. A Take 5 always
  has at least one hazard, so it always has a rating.
- **R6 Controls can't make it worse, and no controls can't make it better.** A hazard's *after* score must not be
  higher than its *before* score; the form asks the worker to fix it. A hazard with no controls is not rated
  again: its *after* rating is its *before* rating.

### Verdict rules

The verdict is *Don't start yet* if any of the reasons below apply, and *Good to go* if none do. Every reason
that applies is shown, in this order. The verdict is worked out once, when the Take 5 is submitted, and saved
with it, so a saved Take 5 always shows the verdict the worker was given.

- **V1** A think-through question is answered No. ("You answered No to: ... Sort this out first.")
- **V2** A hazard has no controls. ("Say how you will control: ...")
- **V3** The Take 5's rating is 11 or more. ("The risk is High (12). At 11 or more you need a JHA before you
  start. Talk to your supervisor.") The app does not write JHAs.

N/A never stops a job. A Take 5 with anything missing (the name, the job, where it is, an answer to a question,
a rating, a first hazard, or the weak-controls question in T3 below) can't be submitted at all, so "missing"
is a form error, not a verdict.

### Thinking rules

These are the rules that stop the app being used on autopilot (*proposed*, decision D1). They are fixed rules
in code, with no AI.

- **T1 Own words first.** The hazard questions stay hidden until the worker has written at least one hazard.
- **T2 Say what you'll do.** A control that is only a vague phrase is not accepted. The form says "Say what
  you'll actually do." The phrases, ignoring capitals and punctuation: *be careful*, *take care*, *take 5*,
  *watch out*, *stay alert*, *pay attention*, *use common sense*, *be aware*.
- **T3 Weak controls on a serious hazard.** When a hazard's *before* rating is 11 or more, it has at least one
  control, and every one of its controls is weak, the app asks: "Everything here relies on people getting it
  right. Could you remove, isolate or barricade it?" The worker must either add a strong control or write why
  none is possible before the Take 5 can be submitted. What they write is saved with the Take 5 and does not
  change the verdict. A hazard with no controls is not asked; V2 already covers it.
- **T4 A real job description.** The job must be at least four words. "Change tyre" is not enough; "Change the
  front left tyre on LV12" is.

### Worked examples

Each example becomes an automated test, named by its number. Add one for every rule and every boundary.

Rating a hazard (R1, R2, R3):

| # | Likelihood | Consequence | Expected | Why |
|---|---|---|---|---|
| 1 | Rare | Low | 1 Low, no JHA | Lowest cell of the matrix |
| 2 | Almost Certain | Critical | 25 Extreme, JHA | Highest cell |
| 3 | Unlikely | Minor | 5 Low, no JHA | Top of the Low band |
| 4 | Rare | Moderate | 6 Moderate, no JHA | Bottom of the Moderate band |
| 5 | Unlikely | Moderate | 9 Moderate, no JHA | Top of the Moderate band |
| 6 | Rare | Major | 10 High, no JHA | Bottom of the High band, and one below the JHA threshold |
| 7 | Almost Certain | Low | 11 High, JHA | Exactly on the JHA threshold |
| 8 | Likely | Moderate | 17 High, JHA | Top of the High band |
| 9 | Possible | Major | 18 Extreme, JHA | Bottom of the Extreme band |
| 10 | Unlikely | Critical | 19 Extreme, JHA | The cell the printed card misprints as 18 |

Rating a Take 5 (R4, R5, R6). Ratings are written likelihood / consequence. Each hazard has one control,
"Barricade the hazard", unless the row says otherwise.

| # | Hazards (before, then after) | Expected | Why |
|---|---|---|---|
| 11 | A: Possible / Minor (8), then Unlikely / Minor (5). B: Possible / Moderate (13), then Unlikely / Moderate (9) | Take 5 rating 9 Moderate, no JHA | R5: the highest *after* rating |
| 12 | A: Possible / Minor (8), then Unlikely / Minor (5). B: Likely / Minor (12), then Likely / Minor (12) | Take 5 rating 12 High, JHA | R5: one hazard at 11 or more is enough |
| 13 | A: Possible / Major (18), then Rare / Major (10) | Take 5 rating 10 High, no JHA | R4: the *after* rating counts, even though *before* was Extreme |
| 14 | No hazards | Can't be submitted | R5: every Take 5 has at least one hazard |
| 15 | A: Unlikely / Minor (5), then Possible / Minor (8) | Can't be submitted | R6: controls can't raise the score |
| 16 | A: Possible / Minor (8), then Possible / Minor (8) | Take 5 rating 8 Moderate, no JHA | R6: an unchanged score is allowed |
| 17 | A: Possible / Minor (8), with no controls | Take 5 rating 8 Moderate, no JHA | R6: with no controls the *after* rating is the *before* rating |

Verdict (V1 to V3). Unless the row says otherwise: every think-through question is Yes, every hazard question
is No, and there is one hazard rated Possible / Minor (8) then Unlikely / Minor (5) with one control, "Barricade
the hazard".

| # | What is different | Expected verdict | Why |
|---|---|---|---|
| 18 | Nothing | Good to go | No reason applies |
| 19 | "Do you have the necessary permits?" is No | Don't start yet | V1 |
| 20 | "Do you have the necessary permits?" is N/A | Good to go | N/A never stops a job |
| 21 | "Will I be working at heights?" is Yes | Good to go | A hazard question is a prompt, not a verdict rule |
| 22 | The hazard has no controls (so it is rated 8) | Don't start yet | V2 |
| 23 | The hazard is Likely / Minor (12) before and after | Don't start yet | V3: 11 or more |
| 24 | The hazard is Almost Certain / Low (11) before and after | Don't start yet | V3: exactly 11 |
| 25 | The hazard is Possible / Major (18), then Rare / Major (10) | Good to go | V3: 10 is below the threshold |
| 26 | "Do you have the correct PPE?" is No, and the hazard has no controls | Don't start yet, with the V1 reason then the V2 reason | Every reason is shown, in order |
| 27 | "Do you have the correct PPE?" is No, and the hazard is Likely / Minor (12) before and after | Don't start yet, with the V1 reason then the V3 reason | Every reason is shown, in order |

Thinking rules (T2, T3, T4). T1 is about what the page shows, so it is tested through the page (see F4).

| # | Input | Expected | Why |
|---|---|---|---|
| 28 | Control "Be careful." | Not accepted | T2, ignoring capitals and punctuation |
| 29 | Control "Be careful of the pinch point when lowering the tray" | Accepted | T2 only catches a control that is nothing but the phrase |
| 30 | Before Possible / Major (18); controls "Wear PPE" and "Ensure correct behaviour" | Weak-controls question asked | T3: 11 or more and all weak |
| 31 | Before Possible / Major (18); controls "Wear PPE" and "Isolate the hazard" | Not asked | T3: one strong control is enough |
| 32 | Before Rare / Major (10); control "Wear PPE" | Not asked | T3: 10 is below 11 |
| 33 | Before Almost Certain / Low (11); control "Put systems in place" | Asked | T3: exactly 11 |
| 34 | Before Possible / Major (18); no controls | Not asked | T3 needs at least one control; V2 covers this |
| 35 | Example 30, with the question left blank | Can't be submitted | T3: it must be answered |
| 36 | Example 30, answered "Live testing, so the panel can't be isolated" | Can be submitted; the answer is saved | T3: a reason is enough, and it does not change the verdict |
| 37 | Job "Change tyre" | Not accepted | T4: two words |
| 38 | Job "Change the tyre" | Not accepted | T4: three words, one short |
| 39 | Job "Change tyre on LV12" | Accepted | T4: exactly four words |

## Features

### F1: Rate a risk
The matrix, the bands and the JHA threshold, as one pure module with no web or database code.
- Acceptance: worked examples 1 to 17 pass as tests.
- Acceptance: every one of the 25 cells is checked against the matrix table above.

### F2: Fill in a Take 5
The five screens of the core workflow, saved when the worker submits.
- Acceptance: a Take 5 can't be submitted with anything missing (the list is under Verdict rules); each gap is
  named beside its field.
- Acceptance: no answer is selected when a screen opens.
- Acceptance: the score and band show as soon as a likelihood and a consequence are both picked.
- Acceptance: the Take 5 is saved before the result page is shown.
- Acceptance: the phone remembers the worker's name for next time.
- Acceptance: every screen is usable one-handed on a 360 px wide phone, with tap targets at least 48 px high.

### F3: The verdict
- Acceptance: worked examples 18 to 27 pass as tests.
- Acceptance: the result page shows the verdict, every reason, and each hazard with its controls and its before
  and after ratings.
- Acceptance: the page never shows a score without its band.

### F4: Thinking rules
- Acceptance: worked examples 28 to 39 pass as tests.
- Acceptance: the hazard questions can't be seen or answered until one hazard has been written (T1).
- Acceptance: the answer to a weak-controls question is saved and shown on the result page.

### F5: Saved Take 5s
- Acceptance: a list of saved Take 5s, newest first, shows the date, worker, job and verdict of each.
- Acceptance: opening one shows the same result page the worker saw, with the verdict saved at the time.
- Acceptance: a saved Take 5 can't be changed.

## Out of scope (for now)

- An AI check of the Take 5 (*proposed*, decision D3). When it comes it will be its own task and sit behind an
  interface that any provider (Claude, ChatGPT, Gemini) can fill.
- Sign-in, supervisors, crews and approvals.
- Writing or signing a JHA. The app only says one is needed.
- Journey plans, hazard report cards, scanning a paper card, photos, PDFs.
- Admin tools, and a different card per company.
- Working with no signal, and keeping a half-filled Take 5 if the page is closed.
- Starting a Take 5 from an earlier one. Copying is the fastest way to stop thinking.

## Decisions waiting on Jake

| # | Decision | Proposed | Main alternative and its tradeoff |
| --- | --- | --- | --- |
| D1 | What makes people think | Own words first, plus fixed pushback rules (T1 to T4) | Keep the card's ticks only: faster, but it is the habit the app exists to beat |
| D2 | Rate each hazard once or twice | Twice, before and after controls | Once, as on paper: two fewer taps per hazard, but nothing shows whether the controls do anything |
| D3 | AI in the first version | No, rules only | Yes: stronger challenge, but needs signal, costs money per Take 5 and is harder to test |
| D4 | Sign-in | None; the worker types their name | Accounts: needed for supervisors later, but a lot of work that isn't the Take 5 itself |
| D5 | Stack | Python, FastAPI, server-rendered pages, SQLite (see `architecture.md`) | Python API with a JavaScript front end: slicker, but two codebases |
| D6 | Which rating decides a JHA | The *after* rating, as the paper card's column order (hazard, controls, score) implies | The *before* rating: stricter and harder to talk down, but almost any job with a fatal hazard would then need a JHA |
| D7 | The list of control kinds | The card's six "Make the changes" options, the first three counted as strong | The booklet's formal hierarchy (eliminate, substitute, redesign, separate, administrative, PPE): more precise, less familiar wording |
| D8 | Who can see saved Take 5s | Everyone using the app, since there is no sign-in | Only on the phone that made them: more private, but a supervisor can never see them |

## Open questions

- How and where will this be hosted, and for how many people? It only runs on a developer's computer for now.
- Is the three minute target right for a typical job?
- T3 could be gamed by picking "Barricade the hazard" for a control that isn't one. Fixed rules can't catch
  that; an AI check could. Is that acceptable for the first version?
- Should the vague phrases in T2 be a longer list, and who maintains it?
