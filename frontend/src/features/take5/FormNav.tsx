import { Button } from "../../components/Button";
import type { Stage } from "./stage";

/**
 * Back, and Continue or Submit, side by side at the bottom where a thumb reaches.
 * Continue submits the form around it, so Enter presses it too. Submit never does:
 * it saves the Take 5, which can't be changed after that.
 */
export function FormNav({
  stage,
  busy,
  canSubmit,
  label,
  onBack,
  onSubmit,
}: {
  stage: Stage;
  busy: boolean;
  canSubmit: boolean;
  label: string | undefined;
  onBack: () => void;
  onSubmit: () => void;
}) {
  const last = stage.page === "review";
  return (
    <nav aria-label="Form navigation" className="grid grid-cols-2 gap-3">
      {stage.page !== "job" && (
        <Button variant="secondary" disabled={busy} onClick={onBack}>
          Back
        </Button>
      )}
      <Button
        disabled={busy || (last && !canSubmit)}
        type={last ? "button" : "submit"}
        onClick={last ? onSubmit : undefined}
        className="col-start-2"
      >
        {label ?? (last ? "Submit Take 5" : "Continue")}
      </Button>
    </nav>
  );
}
