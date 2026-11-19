import { useState } from "react";
import type { Take5Draft } from "../../api/take5";
import { useHazardNudges } from "../../api/take5";
import { Button } from "../../components/Button";
import { Field } from "../../components/Field";
import { FIELD_STYLE } from "../../components/fieldStyle";
import { Warning } from "../../components/Warning";

/**
 * The back end's nudge to make a hazard linked to a Yes specific (spec T6), under the
 * question the back end names. The worker rewords the hazard in the box, which changes
 * it on the list as they type, or keeps it as it is. It never blocks Continue. While
 * the worker is typing the box and its message stay, and nothing is asked: an AI may
 * judge the words, so it is asked once they leave the box (decision D56).
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
  // The draft as it was when the worker went into the box. Until they leave it, that is
  // what is judged, so typing sends nothing. Kept words are never asked about.
  const [draftBeforeTyping, setDraftBeforeTyping] = useState<Take5Draft>();
  const typing = draftBeforeTyping !== undefined;
  const judged = useHazardNudges(draftBeforeTyping ?? draft, !kept);
  const path = `hazards.${String(index)}.description`;
  // Kept words are never asked about, but the box stays while the worker is in it, even
  // if what they type matches words they kept before.
  const nudge = kept
    ? undefined
    : (judged.data ?? []).find(
        (item) => item.path === path && item.question_id === questionId,
      );
  if (!(nudge || typing)) return null;

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
            setDraftBeforeTyping(draft);
          }}
          onBlur={() => {
            setDraftBeforeTyping(undefined);
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
