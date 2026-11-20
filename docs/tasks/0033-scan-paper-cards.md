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
   two-word job, which the app's rules refuse (T2, T4, T5), and F2 says a Take 5 with anything missing can't be
   submitted. Recommended: a scanned card is saved as written, with its verdict, and the gaps count against it in
   the ranking. It must not be rewritten to pass. The spec gets a scanning exception to F2 and those rules.
4. **Are the photos kept?** Recommended: yes, beside the saved Take 5, so the check can be seen later. This is a
   data model change, so it needs Jake's approval; the alternative is to throw the photos away after saving.
5. **Which model reads the photos?** Recommended: the provider's main model, with a setting to change it, as
   task 0027 did for vague hazards.
6. **Where do read-but-unchecked cards wait?** The spec allows one draft, kept on the phone (D20, D23), but a
   batch is several at once. Recommended: the batch waits only in the page that took the photos, in memory, and
   is lost if the page closes; nothing is kept on the server until each card is checked and saved. The
   alternative, keeping the batch on the server, changes D20 and the data model.
7. **Does a scanned card get a challenge question?** A saved Take 5 has no verdict until its challenge question
   is answered (C6), and the saved list shows it as "Not finished". Recommended: no question. A scanned card is
   finished as it is saved, with its verdict, since nobody is there to answer; the spec gets that exception.
8. **Which date does a scanned card get?** Recommended: the date and time written on the card, as read and
   checked, with the scan time kept too. So "worst of today" (0032) doesn't count a pile of old cards as today's,
   and the draft time limit (K2) doesn't apply to a scan.
9. **The "from paper" mark.** It is a new field on a saved Take 5, so a data model change, which needs Jake's
   approval like the photos in question 4. Recommended: approve it; without it a scanned card can't be told apart.
10. **Uploading photos needs a new package.** FastAPI reads uploaded files with `python-multipart`, which isn't a
    dependency yet. Recommended: approve adding it. The alternative is sending each photo as text inside JSON,
    which is a third bigger and needs no package.
11. **Worker's name on the card.** The card has a name, which the AI must read to fill it in. Recommended: allowed
   for reading only; the name is never sent anywhere else, and the ranking never gets it (task 0032).

## Acceptance criteria

These follow the recommendations; they change with Jake's answers.

- [ ] A page takes a batch of photos and reads each into a draft Take 5 marked "from paper".
- [ ] A person checks each draft beside its photo and saves it; nothing is saved unchecked.
- [ ] A scanned card is saved as written, with its verdict, never rewritten to pass a rule.
- [ ] Once the batch is saved, it is ranked worst first with task 0032's job.
- [ ] Tests cover reading (with a stand-in for the AI), the check, saving and the ranking of a batch.
- [ ] Its screens are designed for a desktop as well as a phone; the check puts the photo beside the card.
- [ ] `docs/spec.md` gets the scanning rules, worked examples, a feature section, the exceptions to F2, C6 and
  K2 that the answers need, and anyone can scan in "Users and roles". `docs/architecture.md` gets the new job
  and data, and its section on the AI's risks covers photos as a new way in for instructions to the AI, and the
  AI's text from a scan being sent on to the ranking.
- [ ] All checks pass.

## Out of scope

- Reading a blank card to build a company's template (the spec's "Planned for later").
- Sign-in or a supervisor role.

## Notes / assumptions

Added by Claude on 2026-11-19 in task 0030, from the goal Jake agreed that day. Depends on task 0032.
