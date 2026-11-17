import { useEffect, useRef, useState } from "react";
import type { HazardDraft } from "../../api/take5";
import { Button } from "../../components/Button";
import { Warning } from "../../components/Warning";

const CHOICE_STYLE =
  "flex min-h-14 flex-col items-start justify-center rounded-xl border-2 border-slate-400 bg-white px-4 py-2 text-left text-lg hover:bg-stone-100 focus-visible:outline-4 focus-visible:outline-blue-700";

/** How many other questions a hazard already answers, in words, or null for none. */
function alsoCovers(hazard: HazardDraft, questionId: string) {
  const others = hazard.covers.filter((id) => id !== questionId).length;
  if (!others) return null;
  return others === 1
    ? "Already on another question"
    : `Already on ${String(others)} other questions`;
}

/**
 * Under a Yes to a hazard question: which hazard on the worker's list it is (spec T5).
 * Until one is linked the worker either picks it from the list ("It's on my list") or
 * adds a new one. Picking means reading the list again, so there is no one-tap escape.
 * Each choice is a button, so moving through the list never picks one by accident, and
 * the focus follows each change, so a screen reader keeps its place.
 */
export function HazardLink({
  questionId,
  hazards,
  onLink,
  onUnlink,
  onAddHazard,
}: {
  questionId: string;
  hazards: HazardDraft[];
  onLink: (hazardIndex: number) => void;
  onUnlink: (hazardIndex: number) => void;
  onAddHazard: () => void;
}) {
  const [picking, setPicking] = useState(false);
  // After the worker changes the link, the focus goes to the start of what replaced it.
  const moveFocus = useRef(false);
  const focusTarget = useRef<HTMLParagraphElement>(null);
  useEffect(() => {
    if (!moveFocus.current) return;
    moveFocus.current = false;
    focusTarget.current?.focus();
  });

  // A blank hazard, such as one added and left empty, can't be picked or shown.
  const written = hazards
    .map((hazard, index) => ({ hazard, index }))
    .filter(({ hazard }) => hazard.description.trim());
  const linked = written.filter(({ hazard }) =>
    hazard.covers.includes(questionId),
  );

  if (linked.length)
    return (
      <div className="flex flex-col gap-2">
        {linked.map(({ hazard, index }, position) => {
          const description = hazard.description.trim();
          return (
            <div
              key={index}
              className="flex flex-wrap items-center justify-between gap-2"
            >
              <p
                ref={position === 0 ? focusTarget : undefined}
                tabIndex={-1}
                className="font-semibold text-green-800"
              >
                <span aria-hidden="true">✓ </span>On your list: {description}
              </p>
              <Button
                variant="quiet"
                aria-label={`Not this one: ${description}`}
                onClick={() => {
                  moveFocus.current = true;
                  onUnlink(index);
                }}
              >
                Not this one
              </Button>
            </div>
          );
        })}
        <Button variant="quiet" onClick={onAddHazard}>
          Add another
        </Button>
      </div>
    );

  if (picking)
    return (
      <div
        role="group"
        aria-labelledby={`link-${questionId}`}
        className="flex flex-col gap-2"
      >
        <p
          id={`link-${questionId}`}
          ref={focusTarget}
          tabIndex={-1}
          className="text-lg font-bold"
        >
          Which one on your list is it?
        </p>
        {written.map(({ hazard, index }) => {
          const note = alsoCovers(hazard, questionId);
          return (
            <button
              key={index}
              type="button"
              className={CHOICE_STYLE}
              onClick={() => {
                setPicking(false);
                moveFocus.current = true;
                onLink(index);
              }}
            >
              <span className="font-bold">{hazard.description.trim()}</span>
              {note && <span className="text-base">{note}</span>}
            </button>
          );
        })}
        <Button variant="secondary" onClick={onAddHazard}>
          It’s not there: add a hazard
        </Button>
      </div>
    );

  return (
    <Warning>
      <p ref={focusTarget} tabIndex={-1}>
        Which hazard on your list is this?
      </p>
      <div className="flex flex-wrap gap-2">
        <Button
          variant="secondary"
          onClick={() => {
            setPicking(true);
            moveFocus.current = true;
          }}
        >
          It’s on my list
        </Button>
        <Button variant="secondary" onClick={onAddHazard}>
          Add a hazard
        </Button>
      </div>
    </Warning>
  );
}
