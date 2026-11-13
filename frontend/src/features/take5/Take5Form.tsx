import { useEffect, useState } from "react";
import type { FieldError, TemplateResponse } from "../../api/take5";
import {
  ApiError,
  useCheckDraft,
  useDraftCheck,
  useSubmitTake5,
} from "../../api/take5";
import { Notice } from "../../components/Notice";
import { UndoBar } from "../../components/UndoBar";
import { FormHeading } from "./FormHeading";
import { FormNav } from "./FormNav";
import { FormPage } from "./FormPage";
import type { Problem } from "./SaveProblem";
import { SaveProblem } from "./SaveProblem";
import type { Stage } from "./stage";
import * as stages from "./stage";
import { usePageFocus } from "./usePageFocus";
import { useTake5Draft } from "./useTake5Draft";

export interface Take5FormProps {
  template: TemplateResponse;
  stage: Stage;
  onStageChange: (stage: Stage, options?: { replace: boolean }) => void;
  onBack: (fallback: Stage) => void;
  onSaved: (id: string) => void;
}

/** The form, one page at a time. Each Continue asks the back end what is missing. */
export function Take5Form(props: Take5FormProps) {
  const { template, onStageChange, onSaved } = props;
  const take5 = useTake5Draft();
  const { draft } = take5;
  const stage = stages.shownStage(props.stage, draft);
  const checkDraft = useCheckDraft();
  const review = useDraftCheck(draft, stage.page === "review");
  const submit = useSubmitTake5();
  const { heading, container, focusErrorsOn } = usePageFocus(stage);
  const [allErrors, setErrors] = useState<FieldError[]>([]);
  const [fixing, setFixing] = useState(false);
  const [checking, setChecking] = useState(false);
  const [problem, setProblem] = useState<Problem | null>(null);
  const isHere = (error: FieldError) =>
    stages.sameStage(stages.stageOfError(error.path), stage);
  // Only this page's errors show, so Back never shows a notice with nothing marked.
  const errors = allErrors.filter(isHere);

  useEffect(() => {
    if (!stages.sameStage(stage, props.stage))
      onStageChange(stage, { replace: true });
  });

  /** Open the first page that has a gap, with that page's errors marked. */
  function showGaps(found: FieldError[]) {
    const first = found[0];
    if (!first) return;
    const target = stages.stageOfError(first.path);
    setErrors(found);
    setFixing(true);
    onStageChange(target, { replace: true });
    focusErrorsOn(target);
  }

  async function next() {
    setProblem(null);
    take5.dismissRemoval();
    setChecking(true);
    // With no signal the worker carries on; the review checks everything again.
    const check = await checkDraft(draft).catch(() => null);
    setChecking(false);
    if (check?.errors.some(isHere)) {
      setErrors(check.errors);
      focusErrorsOn(stage);
      return;
    }
    setErrors([]);
    if (fixing && check && !check.can_submit) showGaps(check.errors);
    else if (fixing && check) {
      // Replace the page that was fixed, so Back from the review goes where it always does.
      setFixing(false);
      onStageChange({ page: "review" }, { replace: true });
    } else onStageChange(stages.nextStage(stage, draft));
  }

  function finish() {
    setProblem(null);
    submit.mutate(
      { id: take5.submissionId, draft },
      {
        onSuccess: (saved) => {
          take5.saved(saved.take5.worker_name);
          onSaved(saved.take5.id);
        },
        onError: (error) => {
          const status = error instanceof ApiError ? error.status : 0;
          if (status === 422 && error instanceof ApiError)
            showGaps(error.fieldErrors);
          else if (status === 409) {
            take5.discard();
            setProblem("conflict");
          } else setProblem("unsent");
        },
      },
    );
  }

  const hazard = "hazard" in stage ? draft.hazards[stage.hazard] : undefined;
  return (
    <div ref={container} className="flex flex-col gap-6">
      <FormHeading
        stage={stage}
        hazardCount={draft.hazards.length}
        hazardDescription={hazard?.description ?? ""}
        headingRef={heading}
      />
      {errors.length > 0 && (
        <Notice>
          <p>Fill in the highlighted answers to carry on.</p>
        </Notice>
      )}
      <FormPage
        stage={stage}
        take5={take5}
        template={template}
        errors={errors}
        onErrorsChange={setErrors}
        onGaps={showGaps}
      />
      {take5.removal && (
        <UndoBar
          message={take5.removal.message}
          onUndo={take5.undoRemoval}
          onDismiss={take5.dismissRemoval}
        />
      )}
      {problem && (
        <SaveProblem problem={problem} submissionId={take5.submissionId} />
      )}
      <FormNav
        stage={stage}
        busy={checking || submit.isPending}
        // Finish waits until the review has shown the back end's answer.
        canFinish={review.data?.can_submit === true}
        label={
          submit.isPending ? "Saving…" : checking ? "Checking…" : undefined
        }
        onBack={() => {
          props.onBack(stages.previousStage(stage, draft));
        }}
        onContinue={() => void next()}
        onFinish={finish}
      />
    </div>
  );
}
