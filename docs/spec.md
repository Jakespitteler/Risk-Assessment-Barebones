# Product spec

Status: **version 1** (task 0001). The human owns product decisions; agents propose, the human approves. Every
product decision in this version was made by Jake and is listed under [Decisions made](#decisions-made). Merging
task 0001's pull request is his sign-off of the wording.

## Purpose

A Take 5 is the short personal risk assessment a mine-site worker does before starting a task. On paper it is a
card of tick boxes, and tick boxes get ticked without thinking. This app is a Take 5 for a phone that cannot be
finished on autopilot: the worker has to say, in their own words, what could hurt someone on this job today and
what will stop it, the app pushes back when the answer is thin, and before the result it asks one question
about the weakest part of what they wrote.

This repo is a rebuild of the one core feature of the larger Risk-Assessment app. The rule of thumb for every
design choice: **if the app is boring and can be used without thinking, people will use it without thinking.**

## Users and roles

| Role | Who | What they can do |
| --- | --- | --- |
| Worker | Anyone on a mine-site crew about to start a task | Fill in a Take 5, see its verdict, look back at saved Take 5s |

There is one role for now. There is no sign-in: the worker types their name and the
phone remembers it.

Where and when it is used (confirmed by Jake for task 0004):

- On the worker's own phone, standing at the job, just before starting.
- Often with gloves on, in bright sun, with a weak signal. So: big tap targets, high contrast, and screens that
  load fast.
- It has to be quick enough that it is not resented. Target (to be confirmed, see Open questions): a job with two
  hazards takes under
  three minutes.

## Core workflow

The first four screens follow the Take 5 booklet's steps and are four parts of one form: nothing is sent or
saved until the worker submits it. Then the app asks its one question, and then shows the result.

1. **The job.** The worker types their name, what the job is and where it is, in their own words. All three
   are needed.
2. **Think through the task.** Seven questions from the card (below). Each is answered Yes, No or N/A. Nothing is
   selected to begin with and there is no "all Yes" button. A No means *sort this out first*.
3. **Spot the hazards.** The worker first writes at least one thing that could hurt them or someone else. Only
   then does the app show the card's seven hazard questions as a cross-check ("did you miss any of these?"), on
   their own page after the list, with the worker's list at the top (decision D13). Each Yes asks "Which hazard
   on your list is this?", and the worker links it to one (T5, decision D26). "It's on my list" shows the list
   to pick from, with nothing picked; "Add a hazard" opens the list with a new empty hazard, already linked, and
   Continue there comes back to the questions. Once linked, the Yes shows "On your list:" and the hazard, with
   "Not this one" to unlink it and "Add another". A short hazard picked for a Yes is nudged to say what and where
   (T6). Every Take 5 has at least one hazard: "no hazards" is not an
   answer on a mine site.
4. **Assess the risk and make the changes.** For each hazard the worker:
   1. rates how likely and how bad it is **before** any controls,
   2. writes each control and picks what kind of control it is,
   3. rates how likely and how bad it is **after** those controls. With no controls there is nothing to rate
      again.
   The app shows the score and band from the risk matrix as soon as both parts of a rating are picked.
5. **One question before you start.** The worker submits and the Take 5 is saved. The app then asks one
   question about the weakest part of what they wrote, for example "You're relying on a harness. What is it
   anchored to, and who checked the anchor?" An AI writes the question; when it can't, the app asks a fixed one
   instead. The worker answers in their own words. See [The challenge question](#the-challenge-question).
6. **Result.** The Take 5 is now finished. It is saved with its verdict and the worker sees it: *Don't start
   yet* or *Good to go*, with the reasons in plain words.

Saved Take 5s can be opened again from a list. A finished Take 5 is never changed; if the job changes the worker
does a new one.

Until it is submitted, a Take 5 is a *draft*. The worker can leave it part-way and carry on later, but only for a
short time after starting it: see [Drafts](#drafts).

### The card's questions

The questions below, together with the risk matrix and its JHA threshold, are the **template** a Take 5 is
filled in on. Version 1 has one template, the Take 5 booklet's. The rules in this spec never name a question:
they work from what kind of question it is (a *stop* question or a *hazard* question) and from the template's
matrix. Another company's card is then a different template, not different rules. Every saved Take 5 keeps a
copy of the template it was filled in on.

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

Each hazard question has an example of a specific hazard it could be about, shown by T6 below. The examples are
the app's, not the card's, in the same order: "Hand caught in the conveyor tail pulley with the guard off", "Hit by
a haul truck at the crib hut crossing", "Battery acid splashed in my eyes while topping up the cells", "Feeder
starts up while I am clearing the chute", "Fall from the trailer deck while strapping the load", "Struck by rock
from the excavator loading on the bench above" and "Heat stress from working all afternoon in full sun".

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
  worker's controls). The **after** rating is the one that counts for R3 and R5 (decision D6).
- **R5 The Take 5's rating.** The Take 5's rating is the highest *after* rating of its hazards. A Take 5 always
  has at least one hazard, so it always has a rating.
- **R6 Controls can't make it worse, and no controls can't make it better.** A hazard's *after* score must not be
  higher than its *before* score; the form asks the worker to fix it. A hazard with no controls is not rated
  again: its *after* rating is its *before* rating.

### Verdict rules

The verdict is *Don't start yet* if any of the reasons below apply, and *Good to go* if none do. Every reason
that applies is shown, in this order. The verdict is worked out once, when the Take 5 is finished (the challenge
question is answered), and saved with it, so a saved Take 5 always shows the verdict the worker was given.

- **V1** A think-through question is answered No. ("You answered No to: ... Sort this out first.") Each question
  answered No is its own reason, in the card's order.
- **V2** A hazard has no controls. ("Say how you will control: ...")
- **V3** The Take 5's rating is 11 or more. ("The risk is High (12). At 11 or more you need a JHA before you
  start. Talk to your supervisor.") The app does not write JHAs.

N/A never stops a job. A Take 5 with anything missing (the name, the job, where it is, an answer to a question,
a rating, a first hazard, the weak-controls question in T3 below, or a hazard linked to each hazard question
answered Yes in T5) can't be submitted at all, so "missing" is a form error, not a verdict.

### Thinking rules

These are the fixed rules that stop the app being used on autopilot. They are in code, with no AI, so they work
the same every time and can be tested exactly.

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
- **T5 Every Yes points to a hazard.** Each hazard question answered Yes needs a hazard on the worker's list
  linked to it: one picked from the list, or one added from that Yes. Until then the Yes asks "Which hazard on
  your list is this?", and Continue stops with "Pick the hazard on your list that this is, or add it." beside the
  question. One hazard can be linked to several questions (decision D28).
  A link to a question that is no longer Yes stays on the phone, so changing the answer back keeps it, but it is
  not saved. Each saved hazard keeps the questions it is linked to, and the review and the result show the
  hazard under each Yes (decision D29).
- **T6 Say what and where.** A hazard linked to a Yes with fewer words than the template's minimum (6 on the
  booklet) gets a nudge under the first such question, in the card's order: "Make it specific: say what could
  hurt you, and where. For example: "\<that question's example\>"" (decision D30). It shows the hazard in a box,
  and what the worker types there changes the hazard on the list as they type; the box stays while they type, and
  goes once they leave it with specific words. "Keep it as it is" leaves the words as they are. A nudge never
  stops Continue or Finish (decision D31). Keeping the words is remembered on the phone for those exact words, so
  the nudge doesn't come back (decision D33). A short hazard can still be specific ("Crusher dust"), which is why
  it only nudges. A template with no minimum never nudges. Once an AI is set up it judges this instead, when it
  can be reached (see Planned for later).

### The challenge question

The fixed rules above can be satisfied by someone who knows what the app wants to hear. The challenge question
is the part they can't see coming, because it is written for this job.

The safety rules stay in code. The AI only asks; it never decides whether anyone can start work.

- **C1 One question, about this Take 5.** After the worker submits, the app asks one question about the weakest
  part of what they wrote. The AI is given the job, where it is, the answers, and the hazards with their
  ratings and controls. It is never given the worker's name.
- **C2 Checked before it is shown.** Spaces and line breaks at the ends of the AI's text are removed first. What
  is left is used only if it is 300 characters or fewer and ends with a question mark. Anything else, such as an
  apology or a refusal, is thrown away and C3 applies.
- **C3 Fallback.** If the AI fails, takes longer than 10 seconds, is not set up, or C2 throws its question away,
  the app asks a fixed question about the hazard with the highest *before* rating (the first listed, if there is
  a tie): "What is the one thing that has to go right so that '\<hazard\>' doesn't hurt anyone, and how will you
  check it before you start?" A Take 5 can therefore always be finished, with or without signal to the AI.
- **C4 A real answer.** The answer must be at least four words. (Every vague phrase in T2 is shorter than that,
  so "be careful" can't be an answer.)
- **C5 Asking, not judging.** The AI does not mark the answer, and nothing about the question or the answer
  changes the verdict (decision D11). Both are saved with the Take 5, along with whether the AI or
  the fallback asked, and for an AI question which model asked and which version of its instructions it had.
- **C6 Unfinished until answered.** Until the question is answered the Take 5 is saved but *unfinished*: it has
  no verdict, and opening it shows the question. The question is asked once; an unfinished Take 5 keeps the
  question it was given. It is answered once: a second answer is refused. If a saved Take 5 has no question
  (the app stopped between saving it and asking), opening it gives it the fallback question.

### Drafts

A worker gets called away mid-way, but a Take 5 is meant to be done at the job, just before starting. These rules
keep a draft long enough for a radio call and no longer (decisions D19 to D25).

- **K1 One draft, on the phone.** From the worker's first change until it is submitted or thrown away, the phone
  keeps one draft, with the page it was left on. Every page of the form has Leave, which asks: "Keep it for
  later", "Throw it away" (with Undo) or "Keep going". Either way out goes to the saved list, where a kept draft
  sits at the top with "Carry on" in place of "Start a new Take 5". Opening the app carries on where it was left.
  "Fix this in a new Take 5" takes the draft's place, so with a draft kept it asks first: "You have an
  unfinished Take 5 for '\<job\>'. Fixing this one throws it away."
- **K2 A draft runs out.** A draft started more than the template's time limit ago (2 hours on the booklet)
  has run out. The time counts from the worker's first change, not the last, so tapping it now and then can't
  keep it alive. Exactly on the limit is still in time. The back end checks it as the draft opens, on a
  Continue with changed answers, and on Finish, and refuses to save it: "This Take 5 was started more than 2
  hours ago. Start a new one at the job." The phone then throws it away and says so, with when it was started.
  It is never reopened, even with its answers cleared. A template with no time limit turns the check off
  completely. A retry of a Take 5 that was saved in time is never refused.
- **K3 The start time is kept.** A saved Take 5 keeps when its draft was started, so the time a Take 5 takes can
  be measured.

### Worked examples

Each example becomes an automated test, named by its number. Add one for every rule and every boundary.

Rating a hazard (R1, R2, R3):

| # | Likelihood | Consequence | Expected | Why |
| --- | --- | --- | --- | --- |
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
| --- | --- | --- | --- |
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
| --- | --- | --- | --- |
| 18 | Nothing | Good to go | No reason applies |
| 19 | "Do you have the necessary permits?" is No | Don't start yet | V1 |
| 20 | "Do you have the necessary permits?" is N/A | Good to go | N/A never stops a job |
| 21 | "Will I be working at heights?" is Yes, and the hazard is linked to it | Good to go | A hazard question is a prompt, not a verdict rule |
| 22 | The hazard has no controls (so it is rated 8) | Don't start yet | V2 |
| 23 | The hazard is Likely / Minor (12) before and after | Don't start yet | V3: 11 or more |
| 24 | The hazard is Almost Certain / Low (11) before and after | Don't start yet | V3: exactly 11 |
| 25 | The hazard is Possible / Major (18), then Rare / Major (10) | Good to go | V3: 10 is below the threshold |
| 26 | "Do you have the correct PPE?" is No, and the hazard has no controls | Don't start yet, with the V1 reason then the V2 reason | Every reason is shown, in order |
| 27 | "Do you have the correct PPE?" is No, and the hazard is Likely / Minor (12) before and after | Don't start yet, with the V1 reason then the V3 reason | Every reason is shown, in order |

Thinking rules (T2, T3, T4). T1 is about what the screen shows, so it is tested through the screen (see F4).

| # | Input | Expected | Why |
| --- | --- | --- | --- |
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

Every Yes points to a hazard (T5). Unless the row says otherwise, the Take 5 is example 18.

| # | Input | Expected | Why |
| --- | --- | --- | --- |
| 65 | "Will I be working at heights?" is Yes, and no hazard is linked to it | Can't be submitted: "Pick the hazard on your list that this is, or add it." beside the question | T5 |
| 66 | Example 65, with the hazard "Fall from the tray" linked to it | Can be submitted; the hazard is saved linked to the question | T5 |
| 67 | "Am I or others at risk from the operation of vehicles or mobile equipment?" and "Does the task involve hazardous materials?" are Yes, and one hazard is linked to both | Can be submitted | T5: one hazard can cover several questions |
| 68 | "Will I be working at heights?" is No or N/A, and no hazard is linked to it | Can be submitted | T5 only asks about a Yes |
| 69 | A hazard is linked to "Will I be working at heights?", which is then answered No | Can be submitted; the hazard is saved without the link | T5: only a link to a Yes is saved |

Say what and where (T6). Unless the row says otherwise, the hazard is linked to "Am I or others at risk from the
operation of vehicles or mobile equipment?", answered Yes, on the booklet's minimum of 6 words.

| # | Input | Expected | Why |
| --- | --- | --- | --- |
| 70 | Hazard "Get hit by a car" | Nudged: "Make it specific: say what could hurt you, and where. For example: "Hit by a haul truck at the crib hut crossing"" | T6: five words, one short |
| 71 | Hazard "Hit by a truck reversing nearby" | Not nudged | T6: exactly six words |
| 72 | Hazard "Hit by a haul truck at the crib hut crossing" | Not nudged | T6: specific, ten words |
| 73 | Hazard "Get hit by a car", linked to no question | Not nudged | T6 is about a hazard picked for a Yes |
| 74 | A template with no minimum; hazard "Car" | Not nudged | T6: no minimum turns it off |
| 75 | Example 70, kept as it is | Can be submitted, with the same verdict | T6 only nudges |

The challenge question (C1 to C6). Tests use a stand-in for the AI that returns whatever the row says. Unless the
row says otherwise, the Take 5 is example 18 with the hazard described as "Fall from the tray".

| # | Situation | Expected | Why |
| --- | --- | --- | --- |
| 40 | The AI returns "What stops the tray moving while you're on it?" | That question is asked; recorded as asked by the AI | C1, C2 |
| 41 | The AI fails, takes longer than 10 seconds, or is not set up | The fallback is asked: "What is the one thing that has to go right so that 'Fall from the tray' doesn't hurt anyone, and how will you check it before you start?"; recorded as the fallback | C3 |
| 42 | The AI returns only spaces and line breaks | The fallback is asked | C2: nothing left once the ends are trimmed |
| 43 | The AI returns a question of exactly 300 characters ending in "?" | That question is asked | C2: on the limit |
| 44 | The AI returns a question of 301 characters ending in "?" | The fallback is asked | C2: one over the limit |
| 45 | The AI returns example 40's question with two spaces before it and a line break after | Example 40's question is asked, without the extra spaces | C2: the trimmed text is what is checked and shown |
| 46 | The AI returns "I can't help with that request." | The fallback is asked | C2: it does not end with a question mark |
| 47 | The AI fails. Hazards: "Dust" Possible / Minor (8), then the same (8); and "Fall from the tray" Possible / Major (18), then Unlikely / Minor (5) | The fallback names "Fall from the tray" | C3: the highest *before* rating, even though its *after* rating is the lower one |
| 48 | The AI fails. Hazards: "Dust" then "Noise", both Possible / Moderate (13) before | The fallback names "Dust" | C3: a tie goes to the first listed |
| 49 | Worker "Sam Example" submits | The text given to the AI does not contain "Sam Example" | C1 |
| 50 | The answer is "Yes" | Not accepted | C4: one word |
| 51 | The answer is "Chocked both sides" | Not accepted | C4: three words, one short |
| 52 | The answer is "Wheels chocked both sides" | Accepted; the Take 5 is finished with the verdict Good to go | C4: exactly four words. C5: the verdict is example 18's |
| 53 | Example 19 (permits is No), answered as in example 52 | Finished with the verdict Don't start yet | C5: a good answer does not change the verdict |
| 54 | The Take 5 is submitted and the question is not answered | Unfinished: no verdict, and opening it shows the same question | C6 |
| 55 | Example 52, then a second answer is sent | Refused; the first answer and the verdict are kept | C6: a finished Take 5 is never changed |
| 56 | A saved Take 5 has no question (the app stopped between saving it and asking) | Opening it gives it the fallback question | C6 |

Drafts (K2, K3). On the booklet's time limit of 2 hours, unless the row says otherwise, checked at 15 Nov 2026,
8:12 pm.

| # | Situation | Expected | Why |
| --- | --- | --- | --- |
| 57 | Started 1 hour 59 minutes before | Can be used | K2: inside the limit |
| 58 | Started exactly 2 hours before | Can be used | K2: on the limit |
| 59 | Started 2 hours and 1 second before | Run out: "This Take 5 was started more than 2 hours ago. Start a new one at the job." | K2: one second over |
| 60 | A template with no time limit; started 3 days before | Can be used | K2: no limit turns the check off |
| 61 | Started 5 minutes after the check (the phone's clock was changed) | Can be used | K2: a start in the future counts as just started |
| 62 | No start time is sent (a phone from before drafts were kept) | Not checked; saved with no start time | K2 |
| 63 | Started at 8:12 pm, submitted at 8:16 pm | Saved with the start time 8:12 pm | K3 |
| 64 | Saved at 8:16 pm, then the same submission is sent again at 1:12 am | The Take 5 saved at 8:16 pm comes back | K2: a retry of a Take 5 saved in time |

## Features

### F1: Rate a risk

The matrix, the bands and the JHA threshold, as one pure module with no web or database code.

- Acceptance: worked examples 1 to 17 pass as tests.
- Acceptance: every one of the 25 cells is checked against the matrix table above.
- Acceptance: the matrix is data handed to the rating function. A test rates a hazard on a second, made-up
  matrix to prove that nothing about the booklet's matrix is built into the code.

### F2: Fill in a Take 5

The first four screens of the core workflow, saved when the worker submits.

- Acceptance: a Take 5 can't be submitted with anything missing (the list is under Verdict rules); each gap is
  named beside its field.
- Acceptance: no answer is selected when a screen opens.
- Acceptance: the front end holds no copy of the matrix or the rules; it gets them from the back end.
- Acceptance: the score and band show as soon as a likelihood and a consequence are both picked.
- Acceptance: the Take 5 is saved before the challenge question is asked, so a slow or failed AI never loses it.
- Acceptance: the phone remembers the worker's name for next time.
- Acceptance: every screen is usable one-handed on a 360 px wide phone, with tap targets at least 48 px high.
- Acceptance: after listing hazards, the worker assesses one hazard at a time, before controls, then controls,
  then after controls when there are any. The Back button, the phone's back gesture and a reload all keep the
  unsaved answers.
- Acceptance: Continue asks the back end about that page and names its gaps there, before moving on. A gap found
  at the review sends the worker to it, and back to the review once it is filled in.
- Acceptance: Enter in a one-line box or on a picked rating does what Continue does. Enter in a bigger box, such
  as the job, a hazard or a control, starts a new line. Enter never presses Finish.
- Acceptance: removing a hazard or a control can be undone.
- Acceptance: once anything is filled in, every page has Leave in the top bar, to keep the draft for later or
  throw it away; throwing it away can be undone (K1). Closing the app keeps the draft, and opening it again
  carries on from the same page.
- Acceptance: worked examples 57 to 64 pass as tests, and a draft that has run out is never shown again (K2).
- Acceptance: likelihood, consequence and control choices offer expandable guidance from the back end, using
  the approved card wording. Guidance never supplies a hazard or control answer for the worker.

### F3: The verdict

- Acceptance: worked examples 18 to 27 pass as tests.
- Acceptance: the result screen shows the verdict, every reason, each of the card's questions with the worker's
  answer, each hazard with its controls and its before and after ratings, and the challenge question with the
  worker's answer.
- Acceptance: no screen ever shows a score without its band.
- Acceptance: before Finish, the review warns about each think-through question answered No and each hazard with
  no controls (either will mean Don't start yet), with a way to change it. A warning never blocks Finish.
- Acceptance: a Don't start yet result offers to copy its answers into a new Take 5. The saved one never changes,
  and the two link to each other.
- How the fix works (task 0010): the check returns *warnings* beside its errors: things that are allowed but
  will stop the job. There are two kinds. On each think-through question answered No (V1, task 0005): "You
  answered No: you'll be told not to start." The review shows it under that answer with a "Change answer"
  button that opens the think-through page; Continue there goes back to the review. On each hazard with no
  controls (V2): "No controls: you'll be told not to start." The review shows it on its hazard with an "Add a
  control" button that opens that hazard's controls page; Continue there goes on to rate the new control and
  then back to the review. "Fix this in a new Take 5" copies the name, job, location, the answer to every
  question (decision D14), and every hazard's description, ratings and controls into a new draft with a new ID,
  and opens it on the review. A hazard that had no controls was never rated after them, so its
  after rating starts unpicked. The new Take 5 records which one it fixes. Only a saved Don't start yet can be
  fixed, and once it has a fix it links to the newest one instead of offering another.

### F4: Thinking rules

- Acceptance: worked examples 28 to 39 and 65 to 75 pass as tests.
- Acceptance: the hazard questions can't be seen or answered until one hazard has been written (T1).
- Acceptance: the answer to a weak-controls question is saved and shown on the result screen.

### F5: Saved Take 5s

- Acceptance: a list of saved Take 5s, newest first, shows the date, worker, job and verdict of each, or "Not
  finished" for one whose question is unanswered. A Don't start yet that a newer Take 5 fixes is marked "Fixed",
  whatever the newer one's verdict, as its result screen says (decision D16).
- Acceptance: every date and time is written as "14 Nov 2026, 6:52 pm", in the phone's own time zone (decision
  D17).
- Acceptance: opening one shows the same result screen the worker saw, with the verdict saved at the time.
- Acceptance: a finished Take 5 can't be changed.

### F6: The challenge question

- Acceptance: worked examples 40 to 56 pass as tests, with a stand-in for the AI.
- Acceptance: the worker never sees an error from the AI, only a question.
- Acceptance: the AI provider is chosen in settings. Adding ChatGPT or Gemini means one new adapter file, its
  library, and one line where it is plugged in; no rule, screen or other file changes.
- Acceptance: the AI's key is read from the server's settings; it is never in the repo or sent to the phone.

## Out of scope (for now)

- Any other use of AI: marking the worker's answer, follow-up questions, suggesting hazards or controls, or an
  AI verdict. Suggesting hazards in particular would undo "own words first".
- Sign-in, supervisors, crews and approvals.
- Scanning a filled-in paper card, photos of the job, PDFs of a Take 5, and admin tools.
- Working with no signal.
- Drafts kept on the server, or more than one draft at a time (decisions D20 and D23).
- Starting a Take 5 from an earlier one, except to fix a Don't start yet (F3). Copying is the fastest way to stop
  thinking.

### Planned for later

Not in version 1, but Jake expects them, so version 1 is built not to block them. How is in `architecture.md`
under "Ready for later".

- **The AI judges vague hazards.** Jake (2026-11-18): once an AI is set up, it judges whether a hazard linked to
  a Yes is vague, whenever it can be reached, with task 0022's word rule as the fallback. Task 0009's notes say
  where it fits.

- **Each company's own Take 5.** Companies use different cards and different matrices. Later the app should
  read a photo, Word file or PDF of a company's blank card and build the matching template, which a person then
  checks and edits before anyone fills it in.
- **JHAs, hazard report cards and journey plans.** They may or may not be added. The Take 5's building blocks
  (the matrix, controls, Yes / No questions, the wording checks, the challenge question) are kept separate from
  the Take 5 itself so that they can be reused. Until then the app only says when a JHA is needed.
- **The company's risk standards given to the AI**, so its question can draw on them.
- **An AI the company keeps private**, so that company information stays in house.
- **Feedback on the AI's questions.** Workers rate a question as useful or not, and those ratings are used to
  improve the AI's instructions. Each new version of the instructions is tested against sample Take 5s before
  it goes live, and each question records which version asked it, so versions can be compared.

## Decisions made

Jake made each of these on 2026-11-13, except where the row gives another date. The reasons are in
`decisions.md`. Changing one means changing this spec and its worked examples in the same PR.

| # | Decision | Chosen | Not chosen |
| --- | --- | --- | --- |
| D1 | What makes people think | Own words first, fixed pushback rules (T1 to T4), and an AI challenge question (C1 to C6) | The card's ticks only |
| D2 | Rate each hazard once or twice | Twice, before and after controls | Once, as on paper |
| D3 | AI in the first version | Yes, for the challenge question only | Rules only |
| D4 | Sign-in | None; the worker types their name | Accounts from the start |
| D5 | Stack | A Python API with a separate JavaScript front end (see `architecture.md`) | Server-rendered pages |
| D6 | Which rating decides a JHA | The *after* rating, as the paper card's column order (hazard, controls, score) implies | The *before* rating: stricter, but almost any job with a fatal hazard would then need a JHA |
| D7 | The list of control kinds | The card's six "Make the changes" options, the first three counted as strong | The booklet's formal hierarchy of controls |
| D8 | Who can see saved Take 5s | Everyone using the app, since there is no sign-in | Only the phone that made them |
| D9 | Which AI provider is set up first | Claude. The others plug into the same interface | ChatGPT or Gemini first |
| D10 | What happens when the AI can't be reached | The fixed fallback question (C3), so a Take 5 can always be finished | Wait for the AI |
| D11 | Whether the AI judges the answer | No. It asks one question and the answer is saved (C5) | The AI marks the answer and can ask again |
| D12 | The front-end libraries | React, TypeScript, Vite, Tailwind CSS, TanStack Query, React Router (see `architecture.md`) | Svelte or Vue |
| D13 | Where the hazard questions go (2026-11-14) | Their own page after the hazard list, with the list at the top | Under the list on the same page |
| D14 | What a fix does with the answers (2026-11-14) | Copies them; the review warns on each No with a way to change it | Leave them blank, so all 14 are answered again |
| D15 | What a Yes shows after a hazard is added from it (2026-11-14) | A tick, "Added to your list", and an "Add another" link. Replaced by D26 | The same reminder without its button; or the reminder and button unchanged |
| D16 | What each saved Take 5 shows in the list (2026-11-15) | The date, worker, job and verdict, and "Fixed" on a Don't start yet that has been fixed | The location as well |
| D17 | How dates are written (2026-11-15) | "14 Nov 2026, 6:52 pm" everywhere | Each phone's own format |
| D18 | How the saved list grows (2026-11-15) | Once hosted for a crew, the newest 50 with "Show more" (task 0021). Until then, all of them | All of them, always |
| D19 | What backing out of a Take 5 does (2026-11-15) | Both: Leave keeps it for later or throws it away, with Undo (K1) | Throw away only; keep only |
| D20 | Where a draft is kept (2026-11-15) | On the phone, since there is no sign-in (D4) | On the server, where a supervisor could see it |
| D21 | How long a draft lasts (2026-11-15) | 2 hours from its start; the template's limit can be set to none, which turns the check off (K2) | 12 hours (a shift); no limit |
| D22 | What happens to a draft that has run out (2026-11-15) | It is thrown away, and the worker is told why (K2) | Reopened with its answers cleared; reopened with a "check everything" warning |
| D23 | How many drafts (2026-11-15) | One at a time (K1) | A list |
| D24 | A fix while a draft is kept (2026-11-15) | Ask first, then throw the draft away (K1) | Replace it without asking; refuse until the draft is dealt with |
| D25 | Save when a Take 5 was started (2026-11-15) | Yes (K3) | Not now |
| D26 | A Yes to a hazard that is already on the list (2026-11-16) | "It's on my list", where the worker picks which hazard it is (T5) | A one-tap "It's already there" button, which can be tapped without looking at the list |
| D27 | Must every Yes point to a hazard (2026-11-18) | Yes, before Continue (T5) | A reminder that can be passed by |
| D28 | Can one hazard cover several questions (2026-11-18) | Yes; the picker says when a hazard is already on another question | One question per hazard |
| D29 | Is the link saved (2026-11-18) | Yes, on each hazard, and shown under each Yes on the review and the result. A fix copies it | Kept only on the phone |
| D30 | How a vague hazard is judged (2026-11-18) | Fewer than the template's minimum words (6) for now; the AI once it exists (T6) | A list of category words; an AI now |
| D31 | Is rewording required (2026-11-18) | No: a nudge to reword in place, or "Keep it as it is" | Required before Continue |
| D32 | The nudge's example (2026-11-18) | One per hazard question, kept in the template | One example for every question |
| D33 | Does "Keep it as it is" last (2026-11-18) | Yes, for those exact words, on the phone | Asked again on every visit |

## Open questions

- How and where will this be hosted, and for how many people? It only runs on a developer's computer for now.
- Is the three minute target right for a typical job?
- T3 could be gamed by picking "Barricade the hazard" for a control that isn't one. Fixed rules can't catch
  that. The challenge question is the place it is most likely to be picked up.
- What does the AI cost per Take 5, and is there a monthly limit? Worth measuring in the provider task (0009).
- A job description can contain someone's name even though the worker's own name is never sent. Is that
  acceptable, or should the worker be told what is sent?
- Should the vague phrases in T2 be a longer list, and who maintains it?
