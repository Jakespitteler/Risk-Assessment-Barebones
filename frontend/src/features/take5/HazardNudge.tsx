import { useState } from "react";
import type { Nudge } from "../../api/take5";
import { Button } from "../../components/Button";
import { Field } from "../../components/Field";
import { FIELD_STYLE } from "../../components/fieldStyle";
import { Warning } from "../../components/Warning";

/**
 * The back end's nudge on a vague, stock or unfit hazard linked to a Yes (T6, T7), under the
 * question the back end names. The worker rewords the hazard in the box, which changes
 * it on the list as they type, or keeps it as it is. It never blocks Continue. While
 * the worker is typing the box and its message stay, and the page asks nothing: an AI
 * may judge the words, so it is asked once they leave the box (decision D56).
 */
export function HazardNudge({
  nudge: sentNudge,
  description,
  index,
  kept,
  onTyping,
  onReword,
  onKeep,
}: {
  /** The back end's nudge for this hazard under this question, if it sent one. */
  nudge: Nudge | undefined;
  description: string;
  index: number;
  /** True when the worker chose to keep these exact words, so nothing is asked. */
  kept: boolean;
  /** Called with true as the worker goes into the box, and false as they leave it. */
  onTyping: (typing: boolean) => void;
  onReword: (description: string) => void;
  onKeep: () => void;
}) {
  const [typing, setTyping] = useState(false);
  // The box stays while the worker is in it, even if what they type matches words they
  // kept before.
  const nudge = kept ? undefined : sentNudge;
  if (!(nudge || typing)) return null;

  const path = `hazards.${String(index)}.description`;
  const fieldId = `nudge.${path}`;
  return (
    <Warning>
      {nudge && (
        <>
          <p>{nudge.message}</p>
          <p>If you keep it as it is, it shows in today’s review.</p>
        </>
      )}
      <Field name={fieldId} label={`Hazard ${String(index + 1)}`}>
        <textarea
          id={fieldId}
          className={FIELD_STYLE}
          rows={3}
          value={description}
          onFocus={() => {
            setTyping(true);
            onTyping(true);
          }}
          onBlur={() => {
            setTyping(false);
            onTyping(false);
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
