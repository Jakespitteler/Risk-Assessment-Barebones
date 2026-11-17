import { useState } from "react";
import type { HazardDraft } from "../../api/take5";
import { Button } from "../../components/Button";
import { Warning } from "../../components/Warning";

const CHOICE_STYLE =
  "flex min-h-14 cursor-pointer flex-col justify-center rounded-xl border-2 border-slate-400 bg-white px-4 py-2 text-lg has-focus-visible:outline-4 has-focus-visible:outline-blue-700";

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
  const linked = hazards
    .map((hazard, index) => ({ hazard, index }))
    .filter(({ hazard }) => hazard.covers.includes(questionId));

  if (linked.length)
    return (
      <div className="flex flex-col gap-2">
        {linked.map(({ hazard, index }) => (
          <div
            key={index}
            className="flex flex-wrap items-center justify-between gap-2"
          >
            <p className="font-semibold text-green-800">
              <span aria-hidden="true">✓ </span>On your list:{" "}
              {hazard.description.trim()}
            </p>
            <Button
              variant="quiet"
              onClick={() => {
                onUnlink(index);
              }}
            >
              Not this one
            </Button>
          </div>
        ))}
        <Button variant="quiet" onClick={onAddHazard}>
          Add another
        </Button>
      </div>
    );

  if (picking)
    return (
      <fieldset className="flex flex-col gap-2">
        <legend className="mb-2 text-lg font-bold">
          Which one on your list is it?
        </legend>
        {hazards.map((hazard, index) => {
          const note = alsoCovers(hazard, questionId);
          return (
            <label key={index} className={CHOICE_STYLE}>
              <input
                type="radio"
                name={`link.${questionId}`}
                checked={false}
                onChange={() => {
                  setPicking(false);
                  onLink(index);
                }}
                className="sr-only"
              />
              <span className="font-bold">{hazard.description.trim()}</span>
              {note && <span className="text-base">{note}</span>}
            </label>
          );
        })}
        <Button variant="secondary" onClick={onAddHazard}>
          It’s not there: add a hazard
        </Button>
      </fieldset>
    );

  return (
    <Warning>
      <p>Which hazard on your list is this?</p>
      <div className="flex flex-wrap gap-2">
        <Button
          variant="secondary"
          onClick={() => {
            setPicking(true);
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
