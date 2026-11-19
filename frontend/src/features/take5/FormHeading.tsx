import type { Ref } from "react";
import type { Stage } from "./stage";
import { STEP_COUNT, stepOf } from "./stage";
import { StepBar } from "./StepBar";

const TITLES: Record<Stage["page"], string> = {
  job: "The job in front of you",
  think: "Think it through",
  hazards: "What could hurt someone?",
  check: "Did you miss any?",
  before: "Before any controls",
  controls: "What will stop it?",
  after: "After your controls",
  review: "One last look",
};

/**
 * Where the worker is in the form, with the step bar to move around it, and the page's
 * heading, which takes the focus.
 */
export function FormHeading({
  stage,
  hazardCount,
  hazardDescription,
  headingRef,
  furthestStep,
  busy,
  onPickStep,
}: {
  stage: Stage;
  hazardCount: number;
  hazardDescription: string;
  headingRef: Ref<HTMLHeadingElement>;
  furthestStep: number;
  busy: boolean;
  onPickStep: (step: number) => void;
}) {
  const step = stepOf(stage);
  return (
    <header className="flex flex-col gap-3">
      <StepBar
        stage={stage}
        furthestStep={furthestStep}
        busy={busy}
        onPickStep={onPickStep}
      />
      <p className="text-sm font-bold tracking-wide text-ink-muted uppercase">
        Step {step} of {STEP_COUNT}
        {"hazard" in stage &&
          ` · Hazard ${String(stage.hazard + 1)} of ${String(hazardCount)}`}
      </p>
      <h1
        ref={headingRef}
        tabIndex={-1}
        className="text-3xl leading-tight font-extrabold focus:outline-none"
      >
        {TITLES[stage.page]}
      </h1>
      {"hazard" in stage && (
        <p className="text-lg font-semibold [overflow-wrap:anywhere]">
          {hazardDescription || `Hazard ${String(stage.hazard + 1)}`}
        </p>
      )}
    </header>
  );
}
