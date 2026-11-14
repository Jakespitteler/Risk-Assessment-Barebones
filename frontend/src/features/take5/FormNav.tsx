import { Button } from "../../components/Button";
import type { Stage } from "./stage";

/**
 * Back, and Continue or Finish, side by side at the bottom where a thumb reaches.
 * Continue submits the form around it, so Enter presses it too. Finish never does.
 */
export function FormNav({
  stage,
  busy,
  canFinish,
  label,
  onBack,
  onFinish,
}: {
  stage: Stage;
  busy: boolean;
  canFinish: boolean;
  label: string | undefined;
  onBack: () => void;
  onFinish: () => void;
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
        disabled={busy || (last && !canFinish)}
        type={last ? "button" : "submit"}
        onClick={last ? onFinish : undefined}
        className="col-start-2"
      >
        {label ?? (last ? "Finish Take 5" : "Continue")}
      </Button>
    </nav>
  );
}
