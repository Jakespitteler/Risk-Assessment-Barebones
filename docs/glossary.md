# Glossary

One name for one thing. Each row is a term from `docs/spec.md`: what it means, what the code calls it, and the
spec rules about it. Use these names in code, tests and docs. Where the code's name differs from the spec's word,
both stay: Jake chose that on 2026-11-19, and task 0013's file lists the differences.

Rule numbers (R1, V2, T3, C4, K1 and so on) are the bold definitions in the spec. Every one must be in a back-end
test's docstring or a front-end test's name: `backend/tests/test_spec_rules.py` fails with the numbers that aren't,
or with any rule number a test names that the spec no longer has. `backend/tests/test_spec_examples.py` does the
same for the worked examples: each needs a test named by its number, and a test named for a run of them must list
each one as a case id, such as `test_example_3`. `backend/tests/test_glossary_names.py` fails when a code name
below no longer exists in the code. The front-end column holds components (files in `frontend/src/`), hooks and
helpers, and API types, which come from `src/api/schema.d.ts` through `src/api/take5.ts`.

## The Take 5

| Term | Meaning | Back end | Front end | Rules |
| --- | --- | --- | --- | --- |
| Take 5 | The short personal risk assessment a worker does just before starting a task. | `Take5`; saved as `SavedTake5` | `Take5Form`, `Take5ResultScreen`; types `Take5Draft`, `SavedTake5` | R5, V1 to V3 |
| Worker | The person filling in the Take 5. They type their name; there is no sign-in. | `SavedTake5.worker_name` | `worker_name` | C1, T6 (never sent to an AI) |
| Job | What the task is, in the worker's words. | `SavedTake5.job`; `job_wording_error` | `JobPage` | T4 |
| Where it is | Where the job is, in the worker's words. | `SavedTake5.location` | `location` | C1, T6 |
| Template | One company's Take 5: its questions, matrix, guidance and limits. The booklet is the first. | `Take5Template`; `BOOKLET_TEMPLATE` | `TemplateResponse`; `useTemplate` | K2, T6 |
| Think-through question | One of the card's seven questions; No means sort it out first. | `Question` with `QuestionRole.STOP` | `ThinkPage` | V1 |
| Hazard question | One of the card's questions about a kind of hazard; Yes needs a hazard linked to it. | `Question` with `QuestionRole.HAZARD`; `Question.example` | `HazardCheckPage` | T1, T5, T6 |
| Answer | Yes, No or N/A. Nothing is picked to begin with, and N/A never stops a job. | `Answer` (`Answer.YES`, `Answer.NO`, `Answer.NOT_APPLICABLE`) | `Answer`; `AnswerPicker` | V1, T5 |
| Hazard | Something on the job that could hurt the worker or someone else, in their words. | `Hazard.description`; `HazardDraft` while being filled in | `HazardListPage`; `HazardDraft` | T1, T5, T6, R4 to R6 |
| Link | A hazard on the list chosen as the one a Yes is about. One hazard can cover several questions. | `Hazard.covers` (question IDs); `unlinked_yes_answers` | `HazardLink` | T5 |

## Rating a hazard

| Term | Meaning | Back end | Front end | Rules |
| --- | --- | --- | --- | --- |
| Likelihood | How likely the hazard is to hurt someone, from Rare to Almost Certain. | `RiskRating.likelihood`; `RiskMatrix.likelihoods` | `RatingPicker`, `RatingGuidance` | R1 |
| Consequence | How bad the worst likely injury is, from Low to Critical. | `RiskRating.consequence`; `RiskMatrix.consequences` | `RatingPicker`, `RatingGuidance` | R1 |
| Matrix | The lookup table from likelihood and consequence to a score and band. Nothing is multiplied. | `RiskMatrix`, `RiskCell`; `BOOKLET_MATRIX` | `RiskMatrix` | R1, R2 |
| Rating (score) | A hazard's matrix cell: a score from 1 to 25 and its band. | `RiskRating`; `rate` | `RatingPage`, `RatingPicker`, `RiskBadge`; `RatingChoice` | R1 |
| Band | Low, Moderate, High or Extreme. | `RiskRating.band`, `RiskCell.band` | `RiskBadge` | R2 |
| Before rating | A hazard's rating with no controls. | `Hazard.before` | `before` | R6, T3, C3 |
| After rating | A hazard's rating with the worker's controls; the one that counts. | `Hazard.after` | `after` | R4, R5, R6 |
| The Take 5's rating | The highest after rating of its hazards. | `Take5.rating` | `VerdictPanel` | R5 |
| JHA | Job Hazard Analysis: the fuller assessment a rating of 11 or more needs. The app doesn't write one. | `RiskMatrix.needs_jha`, `Take5.needs_jha` | `VerdictPanel` | R3, V3 |
| JHA threshold | The rating that needs a JHA: 11 on the booklet. 10 is High but doesn't. | `RiskMatrix.jha_threshold` | none | R3, V3 |

## Controls

| Term | Meaning | Back end | Front end | Rules |
| --- | --- | --- | --- | --- |
| Control | What the worker will do to stop a hazard hurting someone: a kind and their own words. | `Control` (`Control.description`, `Control.kind`); `ControlDraft` | `ControlEditor`, `ControlsPage` | V2, T2, T3 |
| Control kind | One of the card's six "Make the changes" options. | `ControlKind` | `ControlEditor` | T3 |
| Strong / weak control | Remove, isolate and barricade are strong; the other three rely on people getting it right. | `ControlKind.is_strong` | none | T3 |
| Vague phrase | A control that is only a phrase such as "be careful". It is not accepted. | `VAGUE_PHRASES`, `is_vague`; `control_wording_error` | `ControlEditor` | T2 |
| Weak-controls question | Asked when a serious hazard's controls are all weak; it must be answered. | `weak_controls_question`; `Hazard.weak_controls_reason` | `WeakControlsQuestion` | T3 |

## The result

| Term | Meaning | Back end | Front end | Rules |
| --- | --- | --- | --- | --- |
| Verdict | Good to go, or Don't start yet with every reason that applies. | `Verdict` (`Verdict.can_start`, `Verdict.reasons`); `verdict` | `VerdictPanel` | V1 to V3, C5 |
| Reason | One line saying why the job is stopped. | `Verdict.reasons` | `VerdictPanel` | V1 to V3 |
| Warning | On the review, something allowed that will stop the job. | `FieldWarning`; `DraftCheck.warnings` | `ReviewPage`, `Warning` | V1, V2 |
| Form error | Something missing or not allowed, so the page can't go on. Not a verdict. | `FieldError`, `FormErrors` | `Field`; `FieldError` | T2 to T5 |
| Nudge | A suggestion under a Yes to make a vague, stock or unfit hazard specific. It never stops Continue or Submit. | `Nudge`; `specific_hazard_nudges` | `HazardNudge`; `useHazardNudges` | T6, T7 |
| Stock or unfit hazard | A hazard an AI calls stock (wording that fits any job) or unfit (can't happen on this job). Nudged like a vague one. | `HazardVerdict`, `HazardFlag` | `flag` | T7 |
| Kept flag | What the hazard check still said about a hazard when it was submitted, so the worker kept it. Counts in today's review. | `Hazard.kept_flag`, `with_kept_flags` | none (the back end keeps it) | T7, W10 |
| Vague / specific hazard | Whether a hazard says what could hurt and where. The AI judges, or the word rule does. | `HazardVerdict`; `Take5Template.specific_hazard_words`; `HazardJudge` | none (the back end decides) | T6 |
| Fix | A new Take 5 started from a Don't start yet, with its answers copied. | `SavedTake5.fixes`; `fix.py` | `FixPanel`; `fixDraftOf` | (feature F3) |

## The challenge question

| Term | Meaning | Back end | Front end | Rules |
| --- | --- | --- | --- | --- |
| Challenge question | The one question asked after submitting, about the weakest part of this Take 5. | `Challenge`; `ChallengeAsker` | `ChallengeScreen`, `ChallengeSummary` | C1 to C6 |
| AI question | A challenge question an AI wrote, kept only if it passes the check. | `AiQuestion`; `checked_question`, `ai_challenge`; `AskedBy.AI` | none (the worker isn't told) | C1, C2, C5 |
| Fallback question | The fixed question about the hazard with the highest before rating. | `fallback_challenge`; `AskedBy.FALLBACK` | none (the worker isn't told) | C3 |
| Answer (to the challenge) | At least four words. It is saved and never changes the verdict. | `Challenge.answer`; `answer_error` | `ChallengeScreen`; `useAnswerTake5` | C4, C5 |
| Unfinished / finished | Saved but not yet answered, so it has no verdict; or answered, with its verdict. | `SavedTake5.finished_at`, `SavedTake5.verdict` | `Take5ResultScreen` | C6 |
| Language model | Any AI the app can ask. Claude is the first provider. | `LanguageModel`; `ai/providers/claude.py` | none | C1, T6 |

## Drafts

| Term | Meaning | Back end | Front end | Rules |
| --- | --- | --- | --- | --- |
| Draft | The Take 5 being filled in, kept on the phone until it is submitted or thrown away. | `Take5Draft` | `useTake5Draft`; type `Take5Draft` | K1 |
| Kept draft | A draft kept for later with Leave. It sits at the top of the saved list with "Carry on". | none (it lives on the phone) | `StoredDraft`, `keptDraft`, `KeptDraftCard`, `LeavePanel` | K1 |
| Time limit / run out | How long a draft lasts from the first change: 2 hours on the booklet. Past it, it has run out. | `Take5Template.draft_time_limit_minutes`; `time_limit_error`, `runs_out_at` | `TimeLeft`, `RunOutPanel` | K2 |
| Start time | When the worker made the draft's first change. | `SavedTake5.started_at` | `started_at` | K2, K3 |
| Submission ID | The ID the phone makes for a Take 5, so a retry gets the same saved Take 5 back. | `submission_id` | `useSubmitTake5` | K2 |
| Saved list | Every saved Take 5, newest first, 50 at a time with "Show more". Everyone using the app can see it. | `Take5Summary`, `Take5ListPage`, `SavedListPage`; `Take5Repository` | `SavedTake5sScreen` | K1 |

## Ranking worst first

| Term | Meaning | Back end | Front end | Rules |
| --- | --- | --- | --- | --- |
| Today's review | Today's best Take 5, then all of them ranked worst first, each with one line saying why. Anyone can open it from the saved list. | `Take5RankingService`, `BestAndWorst` | `ReviewTodayScreen`, `useRankedTake5s`; types `RankedTake5s`, `RankedTake5Line` | W1, W7 to W9 |
| Thought gap | A sign of little thought: a hazard under 6 words, controls that don't lower a risk, a missing or short answer, or under 2 minutes taken. | `thought_gaps` | none (the back end sends the line) | W2 to W5 |
| Worst score | The highest before-controls score, plus 5 for each thought gap. Higher is worse. | `worst_score`, `rank_by_rules` | none | W1 |
| Reason line | The one line saying why a Take 5 sits where it does: the AI's for the worst 10, else the rules'. | `RankedTake5.line`, `rule_line` | `line` | W1, W6 |
| Best of today | The best careful Take 5: finished and answered, controls on every hazard, no gap from W2 to W4 (rushed is allowed). The rules shortlist 5, the AI picks one and says what was good. | `BestTake5`, `is_careful`, `best_shortlist`, `best_by_rules`, `checked_ai_pick`, `with_ai_pick` | `ReviewTodayScreen`; type `BestTake5Line` | W8 |
| Typical time | The median minutes today's finished Take 5s took, shown beside the best's time. | `typical_minutes`, `minutes_taken` | `typical_minutes` | W9 |
| AI ranking | The AI reorders the worst 10 and writes their lines, never seeing a name. Its reply is checked, and the rules decide when it fails. | `Take5Ranker`, `AiTake5Ranker`, `checked_ai_order`, `with_ai_order`; `RankedBy` | `ranked_by_ai` | W6 |

## Risk by area

| Term | Meaning | Back end | Front end | Rules |
| --- | --- | --- | --- | --- |
| Risk by area | Every saved Take 5 (or, with the setting, the last 30 days) grouped by where the job is, hottest first. Opened from the saved list. | `AreaRiskService`, `risk_by_area`, `AreaRisk`, `area_since` | `RiskByAreaScreen`, `useRiskByArea`; types `RiskByArea`, `AreaRisk` | A2, A4 |
| Area | Where the job is, as typed, ignoring capitals, spaces and punctuation; named by the spelling typed most. | `area_key` | `name` | A1 |
| High risk | A Take 5 with a hazard whose before score needs a JHA on its card (11 or more on the booklet). | `is_high_risk` | `high_risk_count` | A3 |
| Common Yes | A hazard question answered Yes often in an area, with how many times; up to 3 per area. | `CommonYes` | `common_yes` | A5 |

## Paper cards

| Term | Meaning | Back end | Front end | Rules |
| --- | --- | --- | --- | --- |
| Paper card | A Take 5 filled in by hand, photographed, checked beside its photo and saved as written. | `Take5.from_paper`, `saved_paper_take5` | `from_paper` | P1 to P6 |
| Blank | A question, rating or control kind a paper card left empty; a reason and a thought gap. | `paper_gaps` | "Not rated" | P1, P3, P4 |
| Card's date | The date written on a paper card, saved as when it was started. | `paper_started_at` | `filled_in_at` | P5 |
