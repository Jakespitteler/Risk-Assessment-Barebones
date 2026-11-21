---
id: 0033
title: Photograph paper Take 5 cards into saved Take 5s, then rank the batch
status: in-progress
owner: claude
branch: claude/0033-photo-reading (#71), claude/0033-reading-the-reply (#72), claude/0033-scan-paper-cards (#68), claude/0033-paper-cards-rules (part 2a)
---

## Goal

The goal (spec, decision D66): a batch of paper cards can be photographed. The AI fills in each one as a normal
saved Take 5, marked "from paper". A person confirms it beside the photo before it is saved, and the batch is
then ranked worst first by task 0032's ranking. It needs the AI; no worker waits on it. Anyone can use it, with
no sign-in. It should be an efficient workflow for a pile of cards.

## Decide first

Questions for Jake, each with Claude's recommendation. Answered when the task starts.

**Jake's answers, 2026-11-20** (asked as eight combined questions when the task was claimed):

- 1, 2: one page takes many photos in a row (camera on a phone, files on a desktop); the AI reads them all; then
  the person checks one card at a time, the photo beside the filled-in form, anything unreadable left empty and
  marked; Save, next card; then the batch is ranked worst first with task 0032's ranking.
- 3, 7: a scanned card is saved exactly as written, never rewritten to pass a rule, finished at once with its
  verdict and no challenge question. The gaps count against it in the ranking. The spec gets these exceptions
  for scans only.
- 4: **not approved**: the photos are not kept; each is thrown away once its card is saved or dropped.
- 5, 11: the provider's main model reads photos, with its own setting. The AI reads the worker's name off the card
  to fill it in; the name is never sent to any other AI call, and the ranking never gets it.
- 6: the batch waits only in the page that took the photos, in memory; nothing is kept on the server until a card
  is checked and saved. No change to D20.
- 8: a separate field for the card's date is **not approved**. The date and time written on the card, as read and
  checked, goes in the existing `started_at`, so "worst of today" (0032) goes by it; the scan time is `created_at`.
- 9: **approved**: a "from paper" field on a saved Take 5 (a data model change).
- 10: **approved**: add `python-multipart`, so FastAPI can take photo uploads.
- The AI interface gets one new method for a photo, which the Claude adapter fills; other jobs don't change.

**Jake's answers, 2026-11-21** (asked when parts 2 and 3 started):

- Card gaps: **approved**, a data model change: on a paper card only, a question, a rating or a control's kind may
  be blank, and there may be no hazards. A blank rating or no hazards gives "Don't start yet", with the reason
  said, and each blank is a gap in the ranking.
- Card date: a date with no time is the start of that day where the checker is; no date leaves `started_at`
  empty, so the scan time is used. A paper card has no time taken: no "Took N minutes", left out of the typical
  time.
- Batch ranking: on the scan page, by a new endpoint that ranks just the saved cards, in Today's review's style.
- The page: "Scan paper cards" at `/scan`, linked beside Today's review and Risk by area; a "From paper" tag on
  the saved list and the saved Take 5's page.

Built as three stacked pull requests, one job each: (1) reading a photo into a filled-in card, saving nothing;
(2) saving a scanned card and ranking a batch; (3) the scan page.

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
8. **Which date does a scanned card get?** Recommended: the date and time written on the card, as read and checked,
   with the scan time kept too (a second time field, so a data model change, like questions 4 and 9). So "worst of
   today" (0032) doesn't count a pile of old cards as today's, and the draft time limit (K2) doesn't apply to a
   scan.
9. **How is the "from paper" mark stored?** D66 already says scanned cards are marked "from paper"; storing it
   is a new field on a saved Take 5, so a data model change, which needs Jake's approval like the photos in
   question 4. Recommended: approve it.
10. **Uploading photos needs a new package.** FastAPI reads uploaded files with `python-multipart`, which isn't a
    dependency yet. Recommended: approve adding it. The alternative is sending each photo as text inside JSON,
    which is a third bigger and needs no package.
11. **Worker's name on the card.** The card has a name, which the AI must read to fill it in. Recommended: allowed
   for reading only; the name is never sent anywhere else, and the ranking never gets it (task 0032).

## Acceptance criteria

Rewritten on 2026-11-20 to follow Jake's answers above.

Part 1, reading (this pull request):

- [x] `POST /api/scans` takes one photo (JPEG, PNG, WebP or GIF, at most 7 MB) and returns the card as the AI
  read it, with the fields it couldn't read marked; nothing is saved and the photo is not kept.
- [x] A word the card doesn't allow (an answer, a level or a control kind) is left empty and marked, and nothing
  is rewritten to pass a rule.
- [x] With no AI set up the reply says scanning needs one (503); a wrong type, a too-big photo, or a photo the AI
  couldn't read is a 422 beside the photo. Never an AI error, and the log never holds the worker's name.
- [x] The AI interface has one new method for a photo, filled by the Claude adapter; the provider's main model
  reads photos unless `TAKE5_AI_SCAN_MODEL` names another.
- [ ] `backend/.env.example` lists `TAKE5_AI_SCAN_MODEL`. Jake adds it: the guard hook keeps agents out of that
      file.
  Until then `test_the_settings_template_names_every_setting` fails on this branch.
- [x] Tests cover the adapter, the instructions, the reading, the scanner and the route.

Part 2, saving (next pull request):

- [ ] A checked card is saved as written, marked "from paper", finished at once with its verdict and no
  challenge question, with the card's date and time in `started_at`; the spec gets the exceptions to F2, C6 and
  K2 for scans, with worked examples, and anyone can scan in "Users and roles".
- [ ] `docs/architecture.md` says a scanned card's text, as the AI read it and the person checked it, goes on to
  the ranking.
- [ ] A saved batch is ranked worst first with task 0032's ranking.

Part 3, the page (last pull request):

- [ ] One page takes many photos, reads them, then shows each card beside its photo to check and save, then the
  batch ranked worst first; designed for a desktop as well as a phone.
- [ ] The page shrinks each photo before sending it (to about 2576 px on the long edge, the most Claude reads), so
  a big phone photo is neither refused by the 7 MB limit nor by Claude's 8000 px limit, and sends faster on a
  site's mobile signal.

## Out of scope

- Reading a blank card to build a company's template (the spec's "Planned for later").
- Sign-in or a supervisor role.

## Notes / assumptions

Noted by Claude on 2026-11-20 in part 1, not fixed (outside this task's scope): Starlette stores a whole upload in
a temporary file before the route reads it, so the 7 MB limit is checked only after a big upload is on the
server's disk. Fine for a proof of concept with no sign-in on a trusted network; worth a request-size limit in
front of the app before it is ever put on the internet.

Added by Claude on 2026-11-19 in task 0030, from the goal Jake agreed that day. Depends on task 0032.
