import { useState } from "react";
import type {
  Answer,
  FieldError,
  FieldWarning,
  HazardDraft,
  Question,
  Take5Draft,
  TemplateResponse,
} from "../../api/take5";
import { useHazardNudges } from "../../api/take5";
import { ControlsPage } from "./ControlsPage";
import { HazardCheckPage } from "./HazardCheckPage";
import { HazardListPage } from "./HazardListPage";
import { HazardNudge } from "./HazardNudge";
import { JobPage } from "./JobPage";
import { RatingPage } from "./RatingPage";
import { ReviewPage } from "./ReviewPage";
import type { Stage } from "./stage";
import { ThinkPage } from "./ThinkPage";
import type { Take5DraftState } from "./useTake5Draft";
import { blankHazard } from "./useTake5Draft";
import { WeakControlsQuestion } from "./WeakControlsQuestion";

/** The page for a stage, wired to the draft. An edit clears that field's errors. */
export function FormPage({
  stage,
  take5,
  template,
  errors,
  onErrorsChange,
  onGaps,
  onOpenWarning,
  onAddHazard,
}: {
  stage: Stage;
  take5: Take5DraftState;
  template: TemplateResponse;
  errors: FieldError[];
  onErrorsChange: (errors: FieldError[]) => void;
  onGaps: (errors: FieldError[]) => void;
  onOpenWarning: (warning: FieldWarning) => void;
  onAddHazard: (questionId: string) => void;
}) {
  const { draft, change, remove } = take5;
  // The draft as it was when the worker went into a nudge's box. While they type there,
  // that is what is judged, so typing asks nothing (decision D56). One ask covers the
  // whole page, however many hazards are linked.
  const [draftBeforeTyping, setDraftBeforeTyping] = useState<Take5Draft>();
  const nudges = useHazardNudges(
    withoutKeptLinks(draftBeforeTyping ?? draft, take5.keptAsIs),
    stage.page === "check",
  );
  const errorFor = (path: string) =>
    errors.find((error) => error.path === path)?.message;

  function edit(path: string, update: (current: Take5Draft) => Take5Draft) {
    onErrorsChange(errors.filter((error) => !error.path.startsWith(path)));
    change(update);
  }
  function editHazard(
    index: number,
    field: string,
    update: Partial<HazardDraft>,
  ) {
    edit(`hazards.${String(index)}.${field}`, (current) => ({
      ...current,
      hazards: current.hazards.map((hazard, position) =>
        position === index ? { ...hazard, ...update } : hazard,
      ),
    }));
  }
  function answer(questionId: string, picked: Answer) {
    edit(`answers.${questionId}`, (current) => ({
      ...current,
      answers: { ...current.answers, [questionId]: picked },
    }));
  }
  /** Link a hazard question's Yes to one hazard on the list, or unlink it (T5). */
  function link(questionId: string, hazardIndex: number, linked: boolean) {
    edit(`answers.${questionId}`, (current) => ({
      ...current,
      hazards: current.hazards.map((hazard, position) => {
        if (position !== hazardIndex) return hazard;
        const others = hazard.covers.filter((id) => id !== questionId);
        return { ...hazard, covers: linked ? [...others, questionId] : others };
      }),
    }));
  }
  /** The back end's nudge to make a linked hazard specific (T6), if it has one here. */
  function nudgeFor(questionId: string, hazardIndex: number) {
    const hazard = draft.hazards[hazardIndex];
    if (!hazard) return null;
    const path = `hazards.${String(hazardIndex)}.description`;
    return (
      <HazardNudge
        key={`${questionId}:${String(hazardIndex)}`}
        nudge={nudges.data?.find(
          (item) => item.path === path && item.question_id === questionId,
        )}
        description={hazard.description}
        index={hazardIndex}
        kept={take5.keptAsIs(hazard.description)}
        onTyping={(typing) => {
          setDraftBeforeTyping(typing ? draft : undefined);
        }}
        onReword={(description) => {
          editHazard(hazardIndex, "description", { description });
        }}
        onKeep={() => {
          take5.keepWording(hazard.description);
        }}
      />
    );
  }
  const questionsFor = (role: Question["role"]) =>
    template.questions.filter((question) => question.role === role);
  // Removing shifts the numbers of the items after it, so every error is cleared.
  function removeItem(
    message: string,
    update: (current: Take5Draft) => Take5Draft,
  ) {
    onErrorsChange([]);
    remove(message, update);
  }

  if (stage.page === "job")
    return (
      <JobPage
        draft={draft}
        errorFor={errorFor}
        onEdit={(field, value) => {
          edit(field, (current) => ({ ...current, [field]: value }));
        }}
      />
    );
  if (stage.page === "think")
    return (
      <ThinkPage
        questions={questionsFor("stop")}
        choices={template.answer_choices}
        answers={draft.answers}
        errorFor={errorFor}
        onAnswer={answer}
      />
    );
  if (stage.page === "check")
    return (
      <HazardCheckPage
        hazards={draft.hazards}
        questions={questionsFor("hazard")}
        choices={template.answer_choices}
        answers={draft.answers}
        errorFor={errorFor}
        onAnswer={answer}
        onLink={(questionId, hazardIndex) => {
          link(questionId, hazardIndex, true);
        }}
        onUnlink={(questionId, hazardIndex) => {
          link(questionId, hazardIndex, false);
        }}
        onAddHazard={onAddHazard}
        nudgeFor={nudgeFor}
        aiNotice={template.hazard_ai_notice}
      />
    );
  if (stage.page === "hazards")
    return (
      <HazardListPage
        hazards={draft.hazards}
        errorFor={errorFor}
        onDescribe={(index, description) => {
          editHazard(index, "description", { description });
        }}
        onAdd={() => {
          edit("hazards", (current) => ({
            ...current,
            hazards: [...current.hazards, blankHazard()],
          }));
        }}
        onRemove={(index) => {
          removeItem(`Hazard ${String(index + 1)} removed.`, (current) => ({
            ...current,
            hazards: current.hazards.filter(
              (_, position) => position !== index,
            ),
          }));
        }}
      />
    );
  if (!("hazard" in stage))
    return (
      <ReviewPage
        draft={draft}
        aiNotice={template.ai_notice}
        onGaps={onGaps}
        onOpenWarning={onOpenWarning}
      />
    );

  const index = stage.hazard;
  const hazard = draft.hazards[index];
  if (!hazard) return null;
  const path = `hazards.${String(index)}`;
  if (stage.page === "controls")
    return (
      <ControlsPage
        path={path}
        controls={hazard.controls}
        template={template}
        errorFor={errorFor}
        onChange={(position, control) => {
          editHazard(index, `controls.${String(position)}`, {
            controls: hazard.controls.map((item, at) =>
              at === position ? control : item,
            ),
          });
        }}
        onAdd={(control) => {
          editHazard(index, "controls", {
            controls: [...hazard.controls, control],
          });
        }}
        onRemove={(position) => {
          removeItem(`Control ${String(position + 1)} removed.`, (current) => ({
            ...current,
            hazards: current.hazards.map((item, at) =>
              at === index
                ? {
                    ...item,
                    controls: item.controls.filter((_, c) => c !== position),
                  }
                : item,
            ),
          }));
        }}
      >
        <WeakControlsQuestion
          draft={draft}
          index={index}
          errorFor={errorFor}
          onChange={(weakControlsReason) => {
            editHazard(index, "weak_controls_reason", {
              weak_controls_reason: weakControlsReason,
            });
          }}
        />
      </ControlsPage>
    );
  const when = stage.page;
  return (
    <RatingPage
      key={when}
      when={when}
      path={`${path}.${when}`}
      rating={hazard[when] ?? { likelihood: null, consequence: null }}
      template={template}
      errorFor={errorFor}
      onChange={(rating) => {
        editHazard(index, when, { [when]: rating });
      }}
    />
  );
}

/**
 * The draft without the links of hazards whose words the worker chose to keep, so the
 * back end never judges them or sends them to an AI (decisions D37 and D56).
 */
function withoutKeptLinks(
  draft: Take5Draft,
  keptAsIs: (description: string) => boolean,
): Take5Draft {
  return {
    ...draft,
    hazards: draft.hazards.map((hazard) =>
      keptAsIs(hazard.description) ? { ...hazard, covers: [] } : hazard,
    ),
  };
}
