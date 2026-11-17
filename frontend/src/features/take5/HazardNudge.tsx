import { useState } from "react";
import type { Take5Draft } from "../../api/take5";
import { useDraftCheck } from "../../api/take5";
import { Button } from "../../components/Button";
import { Field } from "../../components/Field";
import { FIELD_STYLE } from "../../components/fieldStyle";
import { Warning } from "../../components/Warning";
import { useSettledValue } from "./useSettledValue";

// Ask about the wording once the worker pauses, not once per key (as the controls do).
const PAUSE_BEFORE_CHECK_MS = 400;

/**
 * The back end's nudge to make a hazard linked to a Yes specific (spec T6), under the
 * question the back end names. The worker rewords the hazard in the box, which changes
 * it on the list as they type, or keeps it as it is. It never blocks Continue. While
 * the worker is typing the box stays, even once the words are specific enough.
 */
export function HazardNudge({
  draft,
  index,
  questionId,
  kept,
  onReword,
  onKeep,
}: {
  draft: Take5Draft;
  index: number;
  questionId: string;
  /** True when the worker chose to keep these exact words, so nothing is asked. */
  kept: boolean;
  onReword: (description: string) => void;
  onKeep: () => void;
}) {
  const [typing, setTyping] = useState(false);
  // A check already made of this exact draft is used at once; otherwise wait a moment.
  // Kept words are never asked about, so they send no checks.
  const current = useDraftCheck(draft, false);
  const settled = useDraftCheck(
    useSettledValue(draft, PAUSE_BEFORE_CHECK_MS),
    !kept,
    true,
  );
  const check = current.data ? current : settled;
  const path = `hazards.${String(index)}.description`;
  const nudge = (check.data?.nudges ?? []).find(
    (item) => item.path === path && item.question_id === questionId,
  );
  if (kept || !(nudge || typing)) return null;

  const description = draft.hazards[index]?.description ?? "";
  const fieldId = `nudge.${path}`;
  return (
    <Warning>
      {nudge && <p>{nudge.message}</p>}
      <Field name={fieldId} label={`Hazard ${String(index + 1)}`}>
        <textarea
          id={fieldId}
          className={FIELD_STYLE}
          rows={3}
          value={description}
          onFocus={() => {
            setTyping(true);
          }}
          onBlur={() => {
            setTyping(false);
          }}
          onChange={(event) => {
            onReword(event.target.value);
          }}
        />
      </Field>
      {nudge && (
        <Button
          variant="quiet"
          aria-label={`Keep it as it is: hazard ${String(index + 1)}`}
          onClick={(event) => {
            // The box goes away, so the focus goes back to the hazard it was about.
            event.currentTarget
              .closest("[data-hazard-link]")
              ?.querySelector<HTMLElement>("[data-hazard-link-text]")
              ?.focus();
            onKeep();
          }}
        >
          Keep it as it is
        </Button>
      )}
    </Warning>
  );
}
