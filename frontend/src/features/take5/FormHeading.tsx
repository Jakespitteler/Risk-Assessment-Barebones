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
      </p>
      <h1
        ref={headingRef}
        tabIndex={-1}
        className="text-3xl leading-tight font-extrabold focus:outline-none"
      >
        {TITLES[stage.page]}
      </h1>
      {"hazard" in stage && (
        <HazardCard
          hazardNumber={stage.hazard + 1}
          hazardCount={hazardCount}
          hazardDescription={hazardDescription}
        />
      )}
    </header>
  );
}

/**
 * The hazard the worker is rating or controlling, in its own card with an amber edge, so
 * it stands out from the page's text at a glance (task 0047).
 */
function HazardCard({
  hazardNumber,
  hazardCount,
  hazardDescription,
}: {
  hazardNumber: number;
  hazardCount: number;
  hazardDescription: string;
}) {
  const hazardLabel = `Hazard ${String(hazardNumber)} of ${String(hazardCount)}`;
  return (
    <div className="rounded-lg border-l-4 border-brand bg-surface px-4 py-3 shadow-sm">
      <p className="text-sm font-bold tracking-wide text-ink-muted uppercase">
        {hazardLabel}
      </p>
      <p className="text-lg font-semibold [overflow-wrap:anywhere]">
        {hazardDescription || `Hazard ${String(hazardNumber)}`}
      </p>
    </div>
  );
}
