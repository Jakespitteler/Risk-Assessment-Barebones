import { useEffect, useState } from "react";
import type {
  FieldError,
  FieldWarning,
  TemplateResponse,
} from "../../api/take5";
import {
  ApiError,
  useCheckDraft,
  useDraftCheck,
  useFindSaved,
  useOpeningCheck,
  useSubmitTake5,
} from "../../api/take5";
import { Button } from "../../components/Button";
import { Notice } from "../../components/Notice";
import { Screen } from "../../components/Screen";
import { UndoBar } from "../../components/UndoBar";
import { TimeLeft } from "./TimeLeft";
import { UncheckedNotice } from "./UncheckedNotice";
import { FormHeading } from "./FormHeading";
import { FormNav } from "./FormNav";
import { FormPage } from "./FormPage";
import { LeavePanel } from "./LeavePanel";
import { RunOutPanel } from "./RunOutPanel";
import { runOutMessage } from "./runOut";
import type { Problem } from "./SaveProblem";
import { SaveProblem } from "./SaveProblem";
import { SavedListLink } from "./SavedListLink";
import type { Stage } from "./stage";
import * as stages from "./stage";
import { usePageFocus } from "./usePageFocus";
import type { StoredDraft } from "./useTake5Draft";
import { blankHazard, useTake5Draft } from "./useTake5Draft";

/** A draft the back end says has run out, and whether it was found to be saved already. */
interface RunOut {
  message: string;
  lookedForSave: boolean;
}

export interface Take5FormProps {
  template: TemplateResponse;
  stage: Stage;
  onStageChange: (stage: Stage, options?: { replace: boolean }) => void;
  onBack: (fallback: Stage) => void;
  onSaved: (id: string) => void;
  /** The worker left the form, keeping the draft, or throwing it away (with Undo). */
  onLeave: (thrownAway: StoredDraft | null) => void;
  /** Open a new, empty Take 5 in place of one that ran out. */
  onStartAfresh: () => void;
}

/**
 * The form, one page at a time, on its own screen. Each Continue asks the back end what
 * is missing. Each page is a real form, so Enter in a one-line box presses Continue.
 * Once anything is filled in, Leave in the top bar keeps or throws away the draft. A
 * draft the back end says has run out is thrown away and never shown again.
 */
export function Take5Form(props: Take5FormProps) {
  const { template, onStageChange, onSaved } = props;
  const take5 = useTake5Draft();
  const { draft } = take5;
  const stage = stages.shownStage(props.stage, draft);
  const checkDraft = useCheckDraft();
  const review = useDraftCheck(draft, stage.page === "review");
  // A kept draft is checked once as it opens, so one that has run out is never reused.
  const [opened] = useState(() => (draft.started_at ? draft : null));
  const openedCheck = useOpeningCheck(opened ?? draft, opened !== null);
  // Whether a later check got through, so a failed opening check no longer matters.
  const [checkedSinceOpening, setCheckedSinceOpening] = useState(false);
  // When the draft runs out, as the latest Continue's check said.
  const [continueRunsOutAt, setContinueRunsOutAt] = useState<string | null>(
    null,
  );
  const [leaving, setLeaving] = useState(false);
  const [runOut, setRunOut] = useState<RunOut | null>(null);
  const findSaved = useFindSaved();
  const submit = useSubmitTake5();
  const { heading, container, focusErrorsOn, focusFieldOn, focusPageAgain } =
    usePageFocus(stage);
  const [allErrors, setErrors] = useState<FieldError[]>([]);
  const [fixing, setFixing] = useState(false);
  const [checking, setChecking] = useState(false);
  const [problem, setProblem] = useState<Problem | null>(null);
  const stageOf = (path: string) =>
    stages.stageOfError(path, template.questions);
  const isHere = (error: FieldError) =>
    stages.sameStage(stageOf(error.path), stage);
  // Only this page's errors show, so Back never shows a notice with nothing marked.
  const errors = allErrors.filter(isHere);

  useEffect(() => {
    if (!stages.sameStage(stage, props.stage))
      onStageChange(stage, { replace: true });
    take5.keepStage(stage);
  });

  const runOutFound =
    runOutMessage(openedCheck.data?.errors) ??
    runOutMessage(review.data?.errors);
  useEffect(() => {
    if (runOutFound && runOut === null) void endRunOut(runOutFound);
  });

  /**
   * Throw away a draft the back end says has run out, and say why (spec K2). If it was
   * saved already, and only the answer was lost on its way back, open what was saved
   * instead, so the worker isn't told to start again for nothing.
   */
  async function endRunOut(message: string) {
    take5.dismissRemoval();
    setRunOut({ message, lookedForSave: false });
    const saved = await findSaved(take5.submissionId);
    if (saved) {
      take5.saved(saved.take5.worker_name);
      onSaved(saved.take5.id);
      return;
    }
    take5.discard();
    setRunOut({ message, lookedForSave: true });
  }

  /** Open the first page that has a gap, with that page's errors marked. */
  function showGaps(found: FieldError[]) {
    const first = found[0];
    if (!first) return;
    const target = stageOf(first.path);
    setErrors(found);
    setFixing(true);
    onStageChange(target, { replace: true });
    focusErrorsOn(target);
  }

  /** Open the page a warning is about. Continue there comes back to the review. */
  function openWarning(warning: FieldWarning) {
    const target = stageOf(warning.path);
    setErrors([]);
    setFixing(true);
    onStageChange(target, { replace: true });
  }

  /**
   * While fixing, go to the next gap. A gap on the very next page, such as the after
   * rating a new control needs, opens as normal, without marking it as a mistake.
   */
  function nextGap(found: FieldError[]) {
    const following = stages.nextStage(stage, draft);
    const first = found[0];
    if (first && stages.sameStage(stageOf(first.path), following))
      onStageChange(following);
    else showGaps(found);
  }

  /**
   * A Yes to a hazard question: add an empty hazard linked to it, and open the list with
   * the cursor in it. Continue there comes back to the questions, with their answers kept.
   */
  function addHazard(questionId: string) {
    setErrors((current) =>
      current.filter((error) => error.path !== `answers.${questionId}`),
    );
    take5.change((current) => ({
      ...current,
      hazards: [...current.hazards, { ...blankHazard(), covers: [questionId] }],
    }));
    const hazards: Stage = { page: "hazards" };
    focusFieldOn(
      hazards,
      `hazards.${String(draft.hazards.length)}.description`,
    );
    onStageChange(hazards);
  }

  async function next() {
    setProblem(null);
    take5.dismissRemoval();
    setChecking(true);
    // With no signal the worker carries on; the review checks everything again.
    const check = await checkDraft(draft).catch(() => null);
    setChecking(false);
    if (check) {
      setCheckedSinceOpening(true);
      setContinueRunsOutAt(check.runs_out_at ?? null);
    }
    const ranOut = runOutMessage(check?.errors);
    if (ranOut) {
      void endRunOut(ranOut);
      return;
    }
    if (check?.errors.some(isHere)) {
      setErrors(check.errors);
      focusErrorsOn(stage);
      return;
    }
    // The questions check the list, so an empty hazard added from them (and left by
    // going Back) is sent back to the list before the worker moves on.
    const hazardList: Stage = { page: "hazards" };
    if (
      stage.page === "check" &&
      check?.errors.some((error) =>
        stages.sameStage(stageOf(error.path), hazardList),
      )
    ) {
      setErrors(check.errors);
      onStageChange(hazardList);
      focusErrorsOn(hazardList);
      return;
    }
    setErrors([]);
    if (fixing && check && !check.can_submit) nextGap(check.errors);
    else if (fixing && check) {
      // Replace the page that was fixed, so Back from the review steps back one page.
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
          const ranOut =
            error instanceof ApiError ? runOutMessage(error.fieldErrors) : null;
          if (ranOut) void endRunOut(ranOut);
          else if (status === 422 && error instanceof ApiError)
            showGaps(error.fieldErrors);
          else if (status === 409) {
            take5.discard();
            setProblem("conflict");
          } else setProblem("unsent");
        },
      },
    );
  }

  if (runOut && !runOut.lookedForSave)
    return (
      <Screen subtitle="Before you start">
        <h1 className="text-3xl font-extrabold">Checking your Take 5…</h1>
      </Screen>
    );
  if (runOut)
    return (
      <Screen subtitle="Before you start">
        <RunOutPanel
          message={runOut.message}
          startedAt={draft.started_at}
          onStartAfresh={() => {
            onStageChange(stages.FIRST_STAGE, { replace: true });
            props.onStartAfresh();
          }}
        />
      </Screen>
    );
  if (leaving)
    return (
      <Screen subtitle="Before you start">
        <LeavePanel
          onKeep={() => {
            props.onLeave(null);
          }}
          onThrowAway={() => {
            props.onLeave(take5.throwAway());
          }}
          // The panel's buttons go with it, so the focus goes back to the page.
          onKeepGoing={() => {
            setLeaving(false);
            focusPageAgain();
          }}
        />
      </Screen>
    );
  // The first page links to the saved Take 5s until anything is filled in. After that
  // every page offers Leave instead, so nothing pulls the worker away unasked. Leave
  // waits for a check or a save, as Back does: their answer would otherwise move the
  // page, or save the Take 5, after the worker had left.
  const busy = checking || submit.isPending;
  const aside = take5.started ? (
    <Button
      variant="quiet"
      disabled={busy}
      onClick={() => {
        take5.dismissRemoval();
        setLeaving(true);
      }}
    >
      Leave
    </Button>
  ) : (
    stage.page === "job" && <SavedListLink />
  );
  const hazard = "hazard" in stage ? draft.hazards[stage.hazard] : undefined;
  return (
    <Screen subtitle="Before you start" aside={aside}>
      <form
        ref={container}
        noValidate
        className="flex flex-col gap-6"
        onSubmit={(event) => {
          event.preventDefault();
          void next();
        }}
      >
        <FormHeading
          stage={stage}
          hazardCount={draft.hazards.length}
          hazardDescription={hazard?.description ?? ""}
          headingRef={heading}
        />
        <TimeLeft
          runsOutAt={
            review.data?.runs_out_at ??
            continueRunsOutAt ??
            openedCheck.data?.runs_out_at
          }
        />
        {openedCheck.isError && !checkedSinceOpening && !review.data && (
          <UncheckedNotice
            startedAt={draft.started_at}
            checking={openedCheck.isFetching}
            onTryAgain={() => void openedCheck.refetch()}
          />
        )}
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
          onOpenWarning={openWarning}
          onAddHazard={addHazard}
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
          busy={busy}
          // Finish waits until the review has shown the back end's answer.
          canFinish={review.data?.can_submit === true}
          label={
            submit.isPending ? "Saving…" : checking ? "Checking…" : undefined
          }
          onBack={() => {
            props.onBack(stages.previousStage(stage, draft));
          }}
          onFinish={finish}
        />
      </form>
    </Screen>
  );
}
