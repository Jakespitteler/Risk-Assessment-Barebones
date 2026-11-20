# Ideas for later

Jake's ideas, written down so they can be talked through later. **None of them is a task, a decision or part of
the spec.** Don't build from this page. When Jake picks an idea, it becomes a task file in `docs/tasks/`, and
anything he decides goes in `docs/spec.md` and `docs/decisions.md` as usual.

Each idea is in Jake's words, tidied lightly. A line starting **Relates to** is a note from Claude on how the idea
touches what is already built or decided. It only points at things; it decides nothing.

<!-- cspell:ignore isystain beaken -->

## Added 2026-11-18

### Principles

- **Everything outside the basic Take 5 can be turned off.** *(Jake's principle.)* Everything outside of the
  basic Take 5 functionality should be able to be toggled off.
  - Relates to: two settings already work this way. A template with no minimum word count turns off the vague
    hazard nudge (T6), and one with no time limit turns off the draft time limit (K2, D21).
- **Ask for as little as possible, and still get the most out of it.** Ideally, we minimise the detail required
  to fill out the form while still getting the most out of it. In the field, people will only use this if it is
  easier, faster and also produces better results that make the place safer. This may need a balance, and things
  will need to be adjustable. It should meet the obligation of being necessary while actually helping.
  - Relates to: the open question in the spec on whether three minutes is the right target for a typical job.

### Making it fun

- **The app should be fun for the people using it.**
  - The AI could respond like a given fictional character.
  - We want to reward good quality work.
  - **A conversation instead of a form.** *(Jake really likes this one.)* A feature where it is more of a
    discussion, or a voice conversation, where the AI asks the right questions to get the Take 5 filled out
    well.
  - Relates to: the challenge question (C1 to C6) is the only place the AI talks to the worker today. D11 says
    the AI doesn't judge the answer, and the spec lists marking the answer and follow-up questions as out of
    scope, so a conversation, or rewarding quality, would revisit those.

### AI help

- **Sorting things into kinds.** AI multiclass classification for classifying risks, control type and other
  things in the app that have several classes.
  - Relates to: the worker picks the control kind today (D7). The spec's open question notes that T3 can be
    gamed by picking "Barricade the hazard" for a control that isn't one.
- **Spot hazards and controls in photos.** Analyse images with AI to spot hazards and controls.
  - Relates to: photos of the job are out of scope for now. The spec also says the AI suggesting hazards would
    undo "own words first", so how the AI uses a photo would need thought.
- **Write at each person's reading level.** Set a Flesch-Kincaid reading level for each user by analysing what
  they have written, and reply at that level, as this app will be used by people at every reading level.
  - Relates to: there is no sign-in (D4); the worker types their name and the phone remembers it.

### Checking the work was really done

- **Too quick may mean rushed.** Someone filling out a Take 5 too quickly could be an indicator that they rushed
  it.
  - Relates to: a saved Take 5 already keeps when it was started (K3, D25), so the time it took is known.
- **Confirm the controls were put in place.** We want to confirm the application of controls, for example with a
  photo before and after.
  - Relates to: photos of the job are out of scope for now.

### Data and comparison

- **Company-specific risk calibration.** If the calibration changes, the app should try to see whether anything
  out in the field fell through the cracks under the previous calibration.
  - Relates to: the matrix is already data handed to the rating rules (F1), and every saved Take 5 keeps a copy
    of the template it was filled in on. "Each company's own Take 5" is in the spec's Planned for later.
  - Jake, 2026-11-20: older Take 5s could be judged again, for example by the hazard check that task 0037 adds,
    to see whether anything out in the field breaks a new safety standard.
- **Compare with past Take 5s and public incidents.** Compare against previous Take 5s in our system, and against
  publicly reported incidents, like those in the WA
  [Safety Regulation System publication search](https://srs.dmp.wa.gov.au/SRS/Public/PublicationSearch?publicationTypeEnum=SbAndSir).
  - Relates to: "the company's risk standards given to the AI" in Planned for later. Starting a Take 5 from an
    earlier one is out of scope (copying stops thinking), which is different from comparing with one.
- **Some Take 5s matter more than others.** Some Take 5s will be more important than others. We might want to be
  able to filter them.
  - Relates to: the saved list (F5, D16) and showing it 50 at a time (task 0021, which leaves search and filters
    out of scope).

### Supervisors and scanning

- **Scan company paper Take 5s.** At some point we will need to add the ability to scan company-specific
  paper-based Take 5s. This should be a fast workflow, as this app could end up being supervisors scanning many
  Take 5s.
  - Relates to: scanning a filled-in paper card, and supervisors, are out of scope for now. Planned for later
    reads a photo, Word file or PDF of a *blank* card to build a template, which is a different job from scanning
    filled-in ones.
- **If only supervisors use it, raise only the glaring issues.** If it does end up being just the supervisors that
  use the app, then it is probably best that only the glaring issues get raised.
  - Relates to: the "turn things off" principle above, and the thinking rules (T1 to T6).

### Looking the part

- **A more visual app.** A dynamic risk matrix that shows more information, like the size and direction of the
  points. The whole app could be a bit more visual. Could add Stanley diagrams, in place of a bowtie diagram since
  a Stanley diagram is prettier, to show the hazards and controls.
  - Relates to: rating a risk (F1). Worth confirming which diagram is meant, with an example picture, before
    anything is designed.

### Journey plans

- **Traffic, breaks and stop-offs.** If we ever add journey plans to this app, it should look at your route and
  tell you if there is a build-up of traffic, a crash and so on. Since it should require the driver to have a
  break if the drive is longer than a given time, the app should suggest fun things to stop at, or good places to
  stop for food, even if it is a slightly different route. It could also suggest more scenic routes. The ETA
  should assume a break.
  - Relates to: journey plans are in the spec's Planned for later ("may or may not be added"). Traffic and maps
    would come from an outside service; the architecture's aim is that no single tool is hard to replace, as with
    the AI provider (F6).
- **Stop-off suggestions.** Unclear: Jake noted this one but isn't sure what it means. It may be the journey plan
  stop-offs above.

### Strategy

- **If the app isn't worth using on its own.** If the app is proved not to be worth using, could it be better as
  a scanner that connects to existing systems, like isystain and beaken? (Product names as Jake wrote them; to be
  confirmed.)
  - Relates to: scanning a filled-in paper card is out of scope for now (see above). Nothing connects to another
    company's system today; the architecture's aim is only that no single tool is hard to replace.

## Added 2026-11-20: every good idea so far, in one place

Jake asked on 2026-11-20 for every good idea we have had to be noted here, including the ones in the original
[Risk-Assessment](https://github.com/Jakespitteler/Risk-Assessment) app, keeping the proof of concept simple for
now. Each is judged against the goal at the top of `docs/spec.md`: **make a mine site safer by making every
Take 5 count**, so the worker really thinks about today's job, and the weak ones are found. An idea that makes
the app easier to tick through without thinking works against it, however handy.

### Ideas from Jake's threads

- **Tell the worker when theirs was the best of the day.** Praise for a careful Take 5 could make the app worth
  using, and rewards good work (see "Making it fun" above).
  - Relates to: task 0036 shows the best of today to whoever looks, but tells no one (D103); there is no sign-in
    to reach the worker by (D4).
- **To investigate, each with its own task file:** refusing made-up hazards and stock wording (task 0037); a heat
  map of high-risk areas, and how area relates to the data (0038); how the time of year, week and day relate to
  hazards and incidents (0039); a photo of the job with the hazards circled, to train or test an AI later (0040).
- **Each company's own Take 5**, built from a photo, Word file or PDF of its blank card, then editable.
  - Relates to: "Planned for later" in the spec; the matrix and questions are already data (F1).
- **More than the Take 5:** JHAs, hazard report cards and journey plans, built from the same pieces where they
  can be.
- **The company's risk standards as the AI's context.** Whether they fit in the AI's context or need a search
  index first is still to weigh.
- **A private AI**, so a company's information stays in house.
  - Relates to: the AI provider is one adapter behind `LanguageModel` (F6), so another provider is one file.
- **Feedback on the AI's replies feeds back into it**, so its questions and lines get better.

### Ideas from the original Risk-Assessment app

The original app is a much bigger version of this one. These are the parts worth bringing over one day, roughly
from the closest fit to the goal.

Helping the worker think:

- **"Your hazards first", then the AI suggests.** Once the worker has written their own hazards, the AI suggests
  a few common to jobs like this, each with Add and Not here; the worker still rates and controls each one
  (its issue #75).
  - Relates to: "own words first" (D1). Suggesting hazards only after the worker's own keeps it.
- **A "Before you start" list with Done ticks**, and "I've done these: ready to start", recording when the worker
  ticked them all off.
- **Prompts up the hierarchy of controls as they type:** PPE-only controls get "could you remove, swap, guard or
  isolate it?", and "be careful" gets "say what you'll actually do".
  - Relates to: the thinking rules (T2 to T5) do some of this already.
- **"Has the job changed?"**: walks the booklet's Think Through Change flowchart and starts a new Take 5 linked to
  the first.
- **Similar incidents** on similar work at WA mines, from the regulator's reports, matched on the app's own
  computer and never sent to the AI.
- **A critical-risk floor in code:** the rules that matter are enforced by code, whatever the AI says.
  - Relates to: the verdict is already decided by the rules alone (R5, V1 to V3).

Finding the weak ones and acting on them:

- **A supervisor's "Today" page:** "Don't start yet" Take 5s, who in the crew has done one today, and what waits
  for their approval.
  - Relates to: "Today's review" (F8) is a first step that needs no sign-in.
- **Told when something needs you**, on the home page, by email or in a Teams channel.
- **An end-of-shift summary** (its issue #83).
- **Crew feedback on the AI ("Helpful?")**, grouped by the AI into the same problem, and turned into backlog
  items, with a "What's coming" page for the crew.
- **Testing the AI against known cases** before a change to its instructions or site notes goes live.

Working on site:

- **Works with no signal:** the form opens offline and the Take 5 sends itself once there is signal; later, an
  offline answer to the question and a PIN sign-in (its issue #83).
- **A PDF of each Take 5** to download or print, with a sign-off box.
- **Scanning:** remove a photo, several photos into one card, and scanning a JHA (its issue #74).
  - Relates to: task 0033 photographs paper cards.
- **Start from a job you've done, or one a supervisor starred**, with ratings left blank so they still think.
  - Relates to: the spec leaves this out on purpose, as copying stops thinking. It would need a way to keep the
    thought in.
- **Everything outside the core in its own folder**, so each can be turned off (its issue #79), and **AI where it
  helps, with a rules fallback for every AI job** (its issue #77).
  - Relates to: both match the principles above and how this app is already built.

Beyond the Take 5 (from its issues):

- A JHA the crew write themselves, with questions at each step and the AI listing what may be missing, never
  drafting it; signing on each phone.
- Journey plans with "I've left" and "I've arrived" taps and an alert when someone is overdue.
- Hazard and near-miss reports from the phone, reviewed by a supervisor and HSE.
- A company's own risk table (#62), and filling in its own PDF or Word form (#58); company questions on the JHA
  and journey plan (#73).
- Shift handover of open jobs and hazards (#57), fitness for work and fatigue at the start of a shift (#56),
  critical control checks in the field (#55), a warning when a task needs a ticket the person doesn't hold (#54),
  plant and vehicle pre-start checks (#53), isolating and locking out plant (#51), and permits linked to the Take 5 and
  JHA (#50).
