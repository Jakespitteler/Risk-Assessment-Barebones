---
id: 0022
title: An "It's on my list" choice on the hazard check page
status: done
owner: claude
branch: claude/0022-on-my-list (part 1), claude/0022-nudge (part 2)
---

## Goal

On the "Did you miss any of these?" page, a Yes only offers "Add a hazard", even when the worker already wrote
it. For example, "Get hit by a car" is on the list, and "Am I or others at risk from the operation of vehicles or
mobile equipment?" is Yes. Jake chose (2026-11-16) to add an "It's on my list" choice, where the worker must pick
which hazard on their list it is, so the question is linked to that hazard. If the picked hazard is vague, the
app nudges them to make it specific, for example "Hit by a haul truck at the crib hut crossing". Jake asked that
it only nudges when the hazard really is vague, not on a specific one. No fixed rule can judge that perfectly
(question 1), so the choice of rule decides how close the app gets.

A plain one-tap "It's already there" button was turned down: it lets the worker tap past the question without
looking at their list, which is what the app exists to stop.

## Decided

Jake answered on 2026-11-18: "1. (A) for now but when we implement the ai it should use it for this when it
has access. All else do the recommended." So the vague check is the word rule for now; once an AI is set up
(task 0009), it judges vagueness when it can be reached, with the word rule as the fallback. One change from the
recommendations: question 9's hazard ID wasn't needed. The link is kept on the hazard itself (`covers`, the
questions it is linked to), so removing a hazard removes its links and nothing else can shift.

- Part 1 (links and T5): questions 3, 4, 5, 6, 8, 9, 11 and 12. Spec T5, examples 65 to 69, decisions D30 to
  D33.
- Part 2 (the vague nudge): questions 1, 2, 7 and 10.

## Decide first

The questions as they were put to Jake, each with Claude's recommended pick.

1. **How "vague" is judged.** Options:
   - (a) A fixed rule on length: a hazard of fewer than six words is vague, the same way T4 judges the job.
     Simple and exact to test, but it can nudge a short specific hazard ("Crusher dust", or the spec's own
     "Fall from the tray", which is four words) and miss a long vague one. T4's own count is four.
   - (b) A fixed list of generic words, judged like T2: vague when the hazard is only a category such as "vehicles",
     "traffic", "chemicals" or "heights". Never nags a specific hazard, but misses "Get hit by a car".
   - (c) An AI judges it, behind an interface any provider can fill, with (a) or (b) as the fallback. Best judge
     of meaning, but it needs signal, can't be tested exactly, and the spec allows AI for the challenge question
     only (decision D3 and "Out of scope"), so it would be a product change.
   - The tension: (a) will sometimes nudge a short specific hazard, which Jake doesn't want; (b) never does,
     but misses his own example. A mix, such as "short and names no place or equipment", needs a list of place
     and equipment words, which is (b)'s weakness again.
   - Recommended: (a), as a pure function in the shared `domain/wording.py` beside `is_vague()` and
     `word_count()`, with the word count as a template setting. That is a new field on `Take5Template`, so a data
     model change; T4's four words is a fixed number in `thinking.py`, not a setting. Because of the next question
     it only nudges, so a wrong nudge costs one tap, and the threshold can be tuned on real Take 5s. Keep (c) for
     after task 0009, when the AI interface exists.
2. **Is rewording required, or can it be skipped?** Recommended: skippable. The nudge shows the hazard in an
   edit box with "Say what could hurt you and where, for example: ..." and two buttons, "Save" and "Keep it as it
   is". It never blocks Continue. A fixed rule can't be sure a hazard is vague, so blocking would nag the specific
   ones Jake doesn't want nagged.
3. **Must every Yes be linked to a hazard before Continue?** Today a Yes asks "Make sure it's on your list" but
   lets the worker carry on without adding anything. Recommended: yes, a new thinking rule (T5): each hazard
   question answered Yes needs a hazard linked to it, either one added from that Yes or one picked with "It's on
   my list". Continue names the gap beside the question. This closes the last tap-past on the page. The front
   end holds no rules, so the back end checks T5, and the phone must send the links with the draft to
   `POST /api/take5s/check`: an API change whatever the answer to question 6.
4. **Can one hazard cover several questions?** Recommended: yes. "Hit by the forklift carrying acid drums" can
   answer both the vehicles and the hazardous materials questions. The picker shows which questions each hazard
   already covers, so the worker sees when one hazard is doing a lot of work.
5. **Can one question be linked to several hazards?** Recommended: one pick from the list, plus "Add another" as
   today. Picking several would make the picker a tick-box list, which is easy to tick without reading.
6. **Is the link saved and shown?** Today the "Added to your list" mark lives only in the phone's draft, isn't
   sent to the back end, and names the question but not the hazard. Recommended: save each link with the Take 5
   and show it on the review and result ("Vehicles or mobile equipment: Hit by a haul truck at the crib hut
   crossing"). One link covers both a hazard added from a Yes and one picked from the list. It also gives the
   challenge question (task 0008) something to ask about later. This changes the data model and the API, so it
   needs Jake's approval and an entry in `docs/decisions.md`.
7. **The example in the nudge.** Recommended: one example per hazard question, kept in the template beside the
   question's wording, so the vehicles question's nudge shows a vehicle example. Jake approves the seven examples.
   This also adds to the template's data and to what `GET /api/take5/template` sends.
8. **What happens when a linked hazard is removed or reworded later?** Recommended: removing it removes the link,
   and the Yes goes back to asking; Undo puts both back. Rewording keeps the link, and the vague check runs again.
9. **How is a hazard named in a link?** Today a hazard has no ID, only its place in the list, which moves when
   an earlier one is removed. Recommended: give each hazard in the draft an ID that the phone makes, so a link
   survives a removal and Undo. It decides what the saved data looks like (question 6).
10. **How does the nudge come back from the check?** It is not an error, and not a warning as the spec defines one
    ("allowed, but will stop the job"). Recommended: a new third kind beside errors and warnings, named for what
    it is (for example `nudges`), rather than bending `thinking_questions`, which must be answered. "Keep it as it
    is" is remembered in the draft for that hazard's words, so the nudge doesn't come back on every Continue or
    after a reload; it only comes back if the words change and are still vague.
11. **What does "Fix this in a new Take 5" do with links (D14)?** It copies every answer, including each Yes.
    Recommended: copy the links too. A saved Take 5 from before this task has no links, so under T5 each Yes in
    its fix asks for one at the review, with a way to pick it. That is one extra tap per Yes, and a fair moment to
    check the list again.
12. **Are the links given to the AI (C1)?** Recommended: not in this task. Task 0008 builds what the AI is given;
    add the links there if they are saved, and change C1's list in the same PR.
13. **Other ideas, for later and not this task:** the same vague check on the hazard list page itself, not only
   when a hazard is picked; and asking the worker, when one hazard covers three or more questions, whether they
   are really one hazard.

## Acceptance criteria

Part 1 ticked the boxes it finished; part 2 ticked the rest.

- [x] A Yes on a hazard question offers "Add a hazard" and "It's on my list". "It's on my list" asks "Which one
  on your list is it?" and shows the worker's hazards as big choices, with no hazard picked to begin with.
- [x] Picking one links the question to that hazard, and the Yes shows the linked hazard.
- [x] When the picked hazard is vague by the chosen rule, the nudge appears with the question's example. A
  specific hazard shows no nudge.
- [x] Rewording from the nudge changes the hazard on the list; the rule then runs again on the new words.
- [x] Each new rule is pure, in `domain/` with no web or database code, and the back end reports it through
  `POST /api/take5s/check`; the front end holds no copy of it.
- [x] Each new rule has worked examples in `docs/spec.md`, each with a test named after its number. At least, for
  rule (a) with six words: "Get hit by a car" (five words) is vague; "Hit by a truck reversing nearby" (exactly
  six) is not; "Hit by a haul truck at the crib hut crossing" is not. For T5: a Yes with no linked hazard can't
  continue; a Yes linked by a pick can; a No or N/A needs no link.
- [x] `docs/spec.md` is updated: step 3 of the core workflow, the thinking rules, the list of what counts as
  missing under "Verdict rules", worked example 21, F4 and the decisions table. So is `docs/architecture.md`: the
  API section, which lists what this page does on the phone, and the data model for each change to it.
- [x] Vitest covers the picker and the nudge; a Playwright test covers linking, rewording and keeping a hazard.
- [x] Phone-width (360 px) screenshots of every new or changed screen are attached to the PR.
- [x] All checks pass.

## Out of scope

- Any AI judging of the wording, unless Jake picks (c) in question 1 and changes decision D3.
- The vague check on the hazard list page (question 13).
- Giving the links to the AI (question 12).
- Changing the seven hazard questions themselves.

## Notes / assumptions

- Asked for by Jake on 2026-11-16, from the "Did you miss any of these?" page that task 0005 built (spec decisions
  D13 and D15).
- Today's page is `frontend/src/features/take5/HazardCheckPage.tsx`. The "Added to your list" mark is `addedFor`
  in `useTake5Draft.ts`, kept only in the phone's draft. It is a list of question IDs, set when "Add a hazard" is
  tapped, and it doesn't say which hazard: removing any hazard clears every mark. A hazard has no ID either, only
  its place in the list, which moves when an earlier hazard is removed. So a real link needs a way to name a
  hazard that survives a removal. Keeping links on the phone changes the draft's format, so bump `DRAFT_VERSION`
  as task 0019 did.
- Today no rule looks at a Yes to a hazard question: worked example 21 is a Yes with nothing tying it to the one
  hazard, and it is Good to go. Under T5 that example needs a linked hazard. The next free worked example number
  is 65.
- `domain/wording.py` already has `is_vague()` (T2's phrases) and `word_count()` (T4 and C4), so rule (a) or (b)
  can reuse them. `is_vague()` already means T2's phrases, so the new check needs its own name.
- Written after task 0019 (PR 32), whose drafts and Leave button this page sits inside.
- Built in two stacked pull requests on `claude/0022-on-my-list`, after PR 35 (task 0023). Jake allowed a branch
  other than the thread's own on 2026-11-18, because the thread's branch is PR 33's, under PR 35.
- Part 1 (2026-11-18): `covers` on `HazardDraft` and `Hazard`; T5 in `thinking.py` and `check_draft()`;
  `HazardLink.tsx` under each Yes; `AnswerSummary` shows the link on the review and result. The phone's draft
  format changed, so `DRAFT_VERSION` is 4 and a draft kept in the old shape starts afresh.
- Part 1 assumption: the picker lists every hazard, including one already linked to another question, and says
  so ("Already on another question"), rather than hiding it.
- Part 1 review (2026-11-18): the picker's choices are buttons, not radios, because a radio's arrow keys would
  link a hazard while the worker was only moving through the list. The focus moves to what replaces each part,
  and a blank hazard is never offered or shown. Noted, not changed: the check lists the answers' gaps (T5
  included) before the hazard list's, though the list's page comes first. That order was already there for a
  missing answer, and Continue on the check page already sends an empty hazard back to the list.
- Size: with the recommended picks this is a new rule, a data model and API change, a picker, a nudge, seven
  examples and their tests, likely over the ~400-line guide in AGENTS.md. Consider two stacked PRs: the link and
  T5 first, then the vague nudge.
- Part 2 (2026-11-18): `Question.example` and `Take5Template.specific_hazard_words` (6 on the booklet);
  `hazard_wording_nudge()` in `thinking.py` (T6); `DraftCheck.nudges`; `HazardNudge.tsx` under the first Yes a
  hazard is linked to. "Keep it as it is" is kept in the phone's draft (`keptWording`) for those exact words; it
  is an optional field, so the draft version stays 4. Spec examples 70 to 75, decisions D34 to D37. The rule is a
  plain function, so task 0009 can put an AI in front of it with this as the fallback, as Jake asked.
- Part 2 review (2026-11-18): the nudge names the question it shows under (`question_id`), so the phone draws it
  under that question and needs no rule of its own to choose one. The box changes the hazard as the worker
  types, rather than waiting for a "Save" button, so there is one way to change it; the box stays while they
  type and goes once they leave it with specific words. "Keep it as it is" sends the focus back to the hazard it
  was about. The check that decides whether to show the nudge waits for a 400 ms pause in typing.
- Part 2 assumption: the seven examples in the spec are Claude's wording, made up for the booklet; Jake can
  change any of them.
