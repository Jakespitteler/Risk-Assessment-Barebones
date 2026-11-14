import type {
  Answer,
  FieldError,
  FieldWarning,
  HazardDraft,
  Take5Draft,
  TemplateResponse,
} from "../../api/take5";
import { ControlsPage } from "./ControlsPage";
import { HazardCheckPage } from "./HazardCheckPage";
import { HazardListPage } from "./HazardListPage";
import { JobPage } from "./JobPage";
import { RatingPage } from "./RatingPage";
import { ReviewPage } from "./ReviewPage";
import type { Stage } from "./stage";
import { ThinkPage } from "./ThinkPage";
import type { Take5DraftState } from "./useTake5Draft";
import { blankHazard } from "./useTake5Draft";

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
  onAddHazard: () => void;
}) {
  const { draft, change, remove } = take5;
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
  const questionsFor = (role: "stop" | "hazard") =>
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
        onAddHazard={onAddHazard}
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
      <ReviewPage draft={draft} onGaps={onGaps} onOpenWarning={onOpenWarning} />
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
        onAdd={() => {
          editHazard(index, "controls", {
            controls: [...hazard.controls, { description: "", kind: null }],
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
      />
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
