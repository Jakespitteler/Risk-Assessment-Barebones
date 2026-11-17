import { useState } from "react";
import type { Take5Draft } from "../../api/take5";
import { useDraftCheck } from "../../api/take5";
import { Button } from "../../components/Button";
import { Field } from "../../components/Field";
import { FIELD_STYLE } from "../../components/fieldStyle";
import { Warning } from "../../components/Warning";
import { useSettledValue } from "./useSettledValue";

// Ask about the wording once the worker pauses, not once per change (as the controls do).
const PAUSE_BEFORE_CHECK_MS = 400;

/**
 * The back end's nudge to make a hazard linked to a Yes specific (spec T6). The worker
 * rewords it here and saves, or keeps it as it is; either way it never blocks Continue.
 * The rewording is kept in this box until saved, so the nudge can't vanish mid-word.
 */
export function HazardNudge({
  draft,
  index,
  kept,
  onReword,
  onKeep,
}: {
  draft: Take5Draft;
  index: number;
  /** True when the worker chose to keep these exact words, so nothing is asked. */
  kept: boolean;
  onReword: (description: string) => void;
  onKeep: () => void;
}) {
  const description = draft.hazards[index]?.description ?? "";
  const [wording, setWording] = useState(description);
  // A check already made of this exact draft is used at once; otherwise wait a moment.
  const current = useDraftCheck(draft, false);
  const settled = useDraftCheck(
    useSettledValue(draft, PAUSE_BEFORE_CHECK_MS),
    true,
    true,
  );
  const check = current.data ? current : settled;
  const path = `hazards.${String(index)}.description`;
  const nudge = (check.data?.nudges ?? []).find((item) => item.path === path);
  if (!nudge || kept) return null;

  const fieldId = `nudge.${path}`;
  const changed = wording.trim() !== description.trim();
  return (
    <Warning>
      <p>{nudge.message}</p>
      <Field name={fieldId} label="Your hazard">
        <textarea
          id={fieldId}
          className={FIELD_STYLE}
          rows={3}
          value={wording}
          onChange={(event) => {
            setWording(event.target.value);
          }}
        />
      </Field>
      <div className="flex flex-wrap gap-2">
        <Button
          variant="secondary"
          disabled={!changed || !wording.trim()}
          onClick={() => {
            onReword(wording);
          }}
        >
          Save
        </Button>
        <Button variant="quiet" onClick={onKeep}>
          Keep it as it is
        </Button>
      </div>
    </Warning>
  );
}
