---
id: 0033
title: Photograph paper Take 5 cards into saved Take 5s, then rank the batch
status: todo
owner:
branch:
---

## Goal

The goal (spec, decision D66): a batch of paper cards can be photographed. The AI fills in each one as a normal
saved Take 5, marked "from paper". A person confirms it beside the photo before it is saved, and the batch is
then ranked worst first by task 0032's ranking. It needs the AI; no worker waits on it. Anyone can use it, with
no sign-in. It should be an efficient workflow for a pile of cards.

## Decide first

Questions for Jake, each with Claude's recommendation. Answered when the task starts.

1. **How are photos taken?** Recommended: one page that takes many photos in a row (the phone's camera, or files
   chosen on a desktop), then reads them all.
2. **What does the person check?** Recommended: one card at a time, the photo beside the filled-in Take 5 on the
   same form workers use, with anything the AI couldn't read left empty and marked. Save, then the next card.
3. **What happens to the rules a paper card skips?** A paper card may have no controls, ticked boxes only or a
   two-word job, which the app's rules refuse (T2, T4, T5). Recommended: a scanned card is saved as written, with
   its verdict, and the gaps count against it in the ranking. It must not be rewritten to pass.
4. **Are the photos kept?** Recommended: yes, beside the saved Take 5, so the check can be seen later. This is a
   data model change, so it needs Jake's approval; the alternative is to throw the photos away after saving.
5. **Which model reads the photos?** Recommended: the provider's main model, with a setting to change it, as
   task 0027 did for vague hazards.
6. **Worker's name on the card.** The card has a name, which the AI must read to fill it in. Recommended: allowed
   for reading only; the name is never sent anywhere else, and the ranking never gets it (task 0032).

## Acceptance criteria

These follow the recommendations; they change with Jake's answers.

- [ ] A page takes a batch of photos and reads each into a draft Take 5 marked "from paper".
- [ ] A person checks each draft beside its photo and saves it; nothing is saved unchecked.
- [ ] A scanned card is saved as written, with its verdict, never rewritten to pass a rule.
- [ ] Once the batch is saved, it is ranked worst first with task 0032's job.
- [ ] Tests cover reading (with a stand-in for the AI), the check, saving and the ranking of a batch.
- [ ] `docs/spec.md` gets the scanning rules and worked examples; `docs/architecture.md` the new job and data.
- [ ] All checks pass.

## Out of scope

- Reading a blank card to build a company's template (the spec's "Planned for later").
- Sign-in or a supervisor role.

## Notes / assumptions

Added by Claude on 2026-11-19 in task 0030, from the goal Jake agreed that day. Depends on task 0032.
