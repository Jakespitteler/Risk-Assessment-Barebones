import type { Ref } from "react";
import type { Stage } from "./stage";
import { stepOf } from "./stage";

const STEPS = ["Job", "Think", "Hazards", "Assess", "Review"];

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

/** Where the worker is in the form, and the page's heading, which takes the focus. */
export function FormHeading({
  stage,
  hazardCount,
  hazardDescription,
  headingRef,
}: {
  stage: Stage;
  hazardCount: number;
  hazardDescription: string;
  headingRef: Ref<HTMLHeadingElement>;
}) {
  const step = stepOf(stage);
  return (
    <header className="flex flex-col gap-3">
      <ol aria-label="Take 5 progress" className="grid grid-cols-5 gap-2">
        {STEPS.map((name, index) => (
          <li
            key={name}
            aria-current={step === index + 1 ? "step" : undefined}
            className="border-t-4 border-stone-300 pt-2 text-sm text-slate-700 aria-[current=step]:border-slate-900 aria-[current=step]:font-bold aria-[current=step]:text-slate-900"
          >
            {name}
          </li>
        ))}
      </ol>
      <p className="text-sm font-bold tracking-wide text-slate-700 uppercase">
        Step {step} of {STEPS.length}
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
