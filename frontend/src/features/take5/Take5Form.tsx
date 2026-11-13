import { useEffect, useRef, useState } from "react";
import type { FieldError, TemplateResponse } from "../../api/take5";
import { ApiError, useCheckDraft, useSubmitTake5 } from "../../api/take5";
import { Notice } from "../../components/Notice";
import { UndoBar } from "../../components/UndoBar";
import { focusFirstError } from "./focusFirstError";
import { FormHeading } from "./FormHeading";
import { FormNav } from "./FormNav";
import { FormPage } from "./FormPage";
import type { Problem } from "./SaveProblem";
import { SaveProblem } from "./SaveProblem";
import type { Stage } from "./stage";
import {
  nextStage,
  previousStage,
  sameStage,
  shownStage,
  stageOfError,
} from "./stage";
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
  const checkDraft = useCheckDraft();
  const submit = useSubmitTake5();
  const [errors, setErrors] = useState<FieldError[]>([]);
  const [fixing, setFixing] = useState(false);
  const [checking, setChecking] = useState(false);
  const [problem, setProblem] = useState<Problem | null>(null);
  const [focusErrorsOn, setFocusErrorsOn] = useState<{
    stageKey: string;
    attempt: number;
  } | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const form = useRef<HTMLDivElement>(null);
  const stage = shownStage(props.stage, draft);
  const stageKey = JSON.stringify(stage);

  useEffect(() => {
    if (!sameStage(stage, props.stage)) onStageChange(stage, { replace: true });
  });
  // A new page puts the focus on its heading, or on its first error when there is one.
  useEffect(() => {
    if (focusErrorsOn?.stageKey === stageKey) focusFirstError(form.current);
    else heading.current?.focus();
  }, [stageKey, focusErrorsOn]);

  function focusErrors(on: Stage) {
    setFocusErrorsOn((last) => ({
      stageKey: JSON.stringify(on),
      attempt: (last?.attempt ?? 0) + 1,
    }));
  }

  /** Show the first page that has a gap, with that page's errors. */
  function showGaps(found: FieldError[]) {
    const first = found[0];
    if (!first) return;
    const target = stageOfError(first.path);
    setErrors(
      found.filter((error) => sameStage(stageOfError(error.path), target)),
    );
    setFixing(true);
    onStageChange(target, { replace: true });
    focusErrors(target);
  }

  async function next() {
    setProblem(null);
    setChecking(true);
    // With no signal the worker carries on; the review checks everything again.
    const check = await checkDraft(draft).catch(() => null);
    setChecking(false);
    const here = (check?.errors ?? []).filter((error) =>
      sameStage(stageOfError(error.path), stage),
    );
    if (here.length) {
      setErrors(here);
      focusErrors(stage);
      return;
    }
    setErrors([]);
    if (fixing && check && !check.can_submit) showGaps(check.errors);
    else if (fixing && check) {
      setFixing(false);
      onStageChange({ page: "review" });
    } else onStageChange(nextStage(stage, draft));
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
          if (error instanceof ApiError && error.status === 422)
            showGaps(error.fieldErrors);
          else
            setProblem(
              error instanceof ApiError && error.status === 409
                ? "conflict"
                : "unsent",
            );
        },
      },
    );
  }

  const hazard = "hazard" in stage ? draft.hazards[stage.hazard] : undefined;
  return (
    <div ref={form} className="flex flex-col gap-6">
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
        label={
          submit.isPending ? "Saving…" : checking ? "Checking…" : undefined
        }
        onBack={() => {
          props.onBack(previousStage(stage, draft));
        }}
        onContinue={() => void next()}
        onFinish={finish}
      />
    </div>
  );
}
