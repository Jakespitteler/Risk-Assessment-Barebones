import type { Stage } from "./stage";
import { firstStageOf, sameStage, stepOf } from "./stage";

const STEP_NAMES = ["Job", "Think", "Hazards", "Assess", "Review"];

// Every step is at least 48 px high, for a gloved thumb. The bar above each name fills in
// dark once the worker has reached that step, like a progress bar. The current step's bar
// is the amber of the app's "5" badge.
const STEP_LOOK =
  "flex min-h-12 w-full items-start border-t-4 pt-2 text-left text-sm aria-[current=step]:border-brand aria-[current=step]:font-bold";
const REACHED_LOOK = `${STEP_LOOK} border-ink font-semibold text-ink focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-focus disabled:cursor-wait disabled:opacity-60`;
const SHOWING_LOOK = `${STEP_LOOK} border-ink text-ink`;
const NOT_REACHED_LOOK = `${STEP_LOOK} border-line text-ink-faint`;

/**
 * The five steps across the top of the form, which the worker can tap to move around it
 * (spec F2). A step already reached opens on its first page. A step not reached yet can't
 * be tapped, so the only way to it is Continue, which checks each page on the way.
 */
export function StepBar({
  stage,
  furthestStep,
  busy,
  onPickStep,
}: {
  stage: Stage;
  /** The furthest step this Take 5 has reached, counting from 1. */
  furthestStep: number;
  /** True while a check or a save is under way, when the steps wait, as Back does. */
  busy: boolean;
  onPickStep: (step: number) => void;
}) {
  const currentStep = stepOf(stage);
  const reachedStep = Math.max(furthestStep, currentStep);
  return (
    <nav aria-label="Take 5 steps">
      <ol className="grid grid-cols-5 gap-2">
        {STEP_NAMES.map((name, index) => {
          const step = index + 1;
          const current = step === currentStep ? "step" : undefined;
          // The step's first page is already showing, so a tap there would do nothing.
          const showing = sameStage(firstStageOf(step), stage);
          return (
            <li key={name}>
              {step > reachedStep ? (
                <span className={NOT_REACHED_LOOK}>
                  {name}
                  <span className="sr-only">, not reached yet</span>
                </span>
              ) : showing ? (
                <span aria-current={current} className={SHOWING_LOOK}>
                  {name}
                </span>
              ) : (
                <button
                  type="button"
                  aria-current={current}
                  disabled={busy}
                  className={REACHED_LOOK}
                  onClick={() => {
                    onPickStep(step);
                  }}
                >
                  {name}
                </button>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
