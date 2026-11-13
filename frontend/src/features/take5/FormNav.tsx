import { Button } from "../../components/Button";
import type { Stage } from "./stage";

/** Back, and Continue or Finish, side by side at the bottom where a thumb reaches. */
export function FormNav({
  stage,
  busy,
  label,
  onBack,
  onContinue,
  onFinish,
}: {
  stage: Stage;
  busy: boolean;
  label: string | undefined;
  onBack: () => void;
  onContinue: () => void;
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
        disabled={busy}
        onClick={last ? onFinish : onContinue}
        className="col-start-2"
      >
        {label ?? (last ? "Finish Take 5" : "Continue")}
      </Button>
    </nav>
  );
}
