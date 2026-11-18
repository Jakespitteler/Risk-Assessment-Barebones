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
    the AI doesn't judge the answer, and the spec lists follow-up questions as out of scope, so a conversation,
    or rewarding quality, would revisit both. Voice may also suit the field (gloves, bright sun).

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
- **Compare with past Take 5s and public incidents.** Compare against previous Take 5s in our system, and against
  publicly reported incidents, like those in the WA
  [Safety Regulation System publication search](https://srs.dmp.wa.gov.au/SRS/Public/PublicationSearch?publicationTypeEnum=SbAndSir).
  - Relates to: "the company's risk standards given to the AI" in Planned for later. Starting a Take 5 from an
    earlier one is out of scope (copying stops thinking), which is different from comparing with one.
- **Some Take 5s matter more than others.** Some Take 5s will be more important than others. We might want to be
  able to filter them.
  - Relates to: the saved list (F5, D16) and showing it 50 at a time (task 0021).

### Supervisors and scanning

- **Scan company paper Take 5s.** At some point we will need to add the ability to scan company-specific
  paper-based Take 5s. This should be a fast workflow, as this app could end up being supervisors scanning many
  Take 5s.
  - Relates to: scanning a filled-in paper card, and supervisors, are out of scope for now. Planned for later
    reads a photo of a *blank* card to build a template, which is a different job from scanning filled-in ones.
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
  break if the drive is longer than a given time, the app could suggest fun things to stop at, or good places to
  stop for food, even if it is a slightly different route. It could also suggest more scenic routes. The ETA
  should assume a break.
  - Relates to: journey plans are in the spec's Planned for later ("may or may not be added"). Traffic and maps
    would come from a third party, so they would sit behind a swappable connection like the AI does.
- **Stop-off suggestions.** Unclear: Jake noted this one but isn't sure what it means. It may be the journey plan
  stop-offs above.

### Strategy

- **If the app isn't worth using on its own.** If the app is proved not to be worth using, could it be better as
  a scanner that connects to existing systems, like isystain and beaken? (Product names as Jake wrote them; to be
  confirmed.)
  - Relates to: the rule that every third-party connection is general enough to swap for another system.
