---
id: 0022
title: "It's on my list" on the hazard check page
status: todo
owner:
branch:
---

## Goal

On the "Did you miss any of these?" page, a Yes only offers "Add a hazard", even when the worker already wrote
it. For example, "Get hit by a car" is on the list, and "Am I or others at risk from the operation of vehicles or
mobile equipment?" is Yes. Jake chose (2026-11-16) to add an "It's on my list" choice, where the worker must pick
which hazard on their list it is, so the question is linked to that hazard. If the picked hazard is vague, the
app nudges them to make it specific, for example "Hit by a haul truck at the crib hut crossing". It only nudges
when the hazard really is vague, never on a specific one.

A plain one-tap "It's already there" button was turned down: it lets the worker tap past the question without
looking at their list, which is what the app exists to stop.

## Decide first

Workshop these with Jake when the task starts, before any code. Each has Claude's recommended pick. Write his
answers in `docs/spec.md` (the Decisions made table and the rule wording) and below, under "Decided".

1. **How "vague" is judged.** Options:
   - (a) A fixed rule on length: a hazard of fewer than six words is vague, the same way T4 judges the job.
     Simple and exact to test, but it can nudge a short specific hazard ("Crusher dust") and miss a long vague one.
   - (b) A fixed list of generic words, judged like T2: vague when the hazard is only a category such as "vehicles",
     "traffic", "chemicals" or "heights". Never nags a specific hazard, but misses "Get hit by a car".
   - (c) An AI judges it, behind an interface any provider can fill, with (a) or (b) as the fallback. Best judge
     of meaning, but it needs signal, can't be tested exactly, and the spec allows AI for the challenge question
     only (decision D3 and "Out of scope"), so it would be a product change.
   - Recommended: (a), as a pure function in the shared `domain/wording.py` beside `is_vague()` and
     `word_count()`, with the word count as a template setting. Because of the next question it only nudges, so a
     wrong nudge costs one tap, and the threshold can be tuned on real Take 5s. Keep (c) for after task 0009, when
     the AI interface exists.
2. **Is rewording required, or can it be skipped?** Recommended: skippable. The nudge shows the hazard in an
   edit box with "Say what could hit you and where, for example: ..." and two buttons, "Save" and "Keep it as it
   is". It never blocks Continue. A fixed rule can't be sure a hazard is vague, so blocking would nag the specific
   ones Jake doesn't want nagged.
3. **Must every Yes be linked to a hazard before Continue?** Today a Yes asks "Make sure it's on your list" but
   lets the worker carry on without adding anything. Recommended: yes, a new thinking rule (T5): each hazard
   question answered Yes needs a hazard linked to it, either one added from that Yes or one picked with "It's on
   my list". Continue names the gap beside the question. This closes the last tap-past on the page.
4. **Can one hazard cover several questions?** Recommended: yes. "Hit by the forklift carrying acid drums" can
   answer both the vehicles and the hazardous materials questions. The picker shows which questions each hazard
   already covers, so the worker sees when one hazard is doing a lot of work.
5. **Can one question be linked to several hazards?** Recommended: one pick from the list, plus "Add another" as
   today. Picking several would make the picker a tick-box list, which is easy to tick without reading.
6. **Is the link saved and shown?** Today the "Added to your list" link lives only in the phone's draft and isn't
   saved. Recommended: save each link with the Take 5 and show it on the review and result ("Vehicles or mobile
   equipment: Hit by a haul truck at the crib hut crossing"). One link covers both a hazard added from a Yes and
   one picked from the list. It also gives the challenge question (task 0008) something to ask about later. This
   changes the data model and the API, so it needs Jake's approval and an entry in `docs/decisions.md`.
7. **The example in the nudge.** Recommended: one example per hazard question, kept in the template beside the
   question's wording, so the vehicles question's nudge shows a vehicle example. Jake approves the seven examples.
8. **What happens when a linked hazard is removed or reworded later?** Recommended: removing it removes the link,
   and the Yes goes back to asking; Undo puts both back. Rewording keeps the link, and the vague check runs again.
9. **Other ideas, for later and not this task:** the same vague check on the hazard list page itself, not only
   when a hazard is picked; and asking the worker, when one hazard covers three or more questions, whether they
   are really one hazard.

## Acceptance criteria

To be finished once the questions above are answered. With the recommended picks:

- [ ] A Yes on a hazard question offers "Add a hazard" and "It's on my list". "It's on my list" asks "Which one?"
  and shows the worker's hazards as big choices, with no hazard picked to begin with.
- [ ] Picking one links the question to that hazard, and the Yes shows the linked hazard.
- [ ] When the picked hazard is vague by the chosen rule, the nudge appears with the question's example. A
  specific hazard shows no nudge.
- [ ] Rewording from the nudge changes the hazard on the list; the rule then runs again on the new words.
- [ ] Each new rule is pure, in `domain/` with no web or database code, and the back end reports it through
  `POST /api/take5s/check`; the front end holds no copy of it.
- [ ] Each new rule has worked examples in `docs/spec.md`, each with a test named after its number. At least, for
  rule (a) with six words: "Get hit by a car" (five words) is vague; "Hit by a truck reversing nearby" (exactly
  six) is not; "Hit by a haul truck at the crib hut crossing" is not. For T5: a Yes with no linked hazard can't
  continue; a Yes linked by a pick can; a No or N/A needs no link.
- [ ] `docs/spec.md` (step 3 of the core workflow, the thinking rules, F4 and the decisions table) and, if the
  link is saved, `docs/architecture.md` are updated.
- [ ] Vitest covers the picker and the nudge; a Playwright test covers linking, rewording and keeping a hazard.
- [ ] Phone-width (360 px) screenshots of every new or changed screen are attached to the PR.
- [ ] All checks pass.

## Out of scope

- Any AI judging of the wording, unless Jake picks (c) in question 1 and changes decision D3.
- The vague check on the hazard list page (question 9).
- Changing the seven hazard questions themselves.

## Notes / assumptions

- Asked for by Jake on 2026-11-16, from the "Did you miss any of these?" page that task 0005 built (spec decisions
  D13 and D15).
- Today's page is `frontend/src/features/take5/HazardCheckPage.tsx`. The "Added to your list" link is `addedFor`
  in `useTake5Draft.ts`, kept only in the phone's draft. Saving links on the phone changes the draft's format, so
  bump `DRAFT_VERSION` as task 0019 did.
- `domain/wording.py` already has `is_vague()` (T2's phrases) and `word_count()` (T4 and C4), so rule (a) or (b)
  can reuse them.
- Written after task 0019 (PR 32), whose drafts and Leave button this page sits inside.
