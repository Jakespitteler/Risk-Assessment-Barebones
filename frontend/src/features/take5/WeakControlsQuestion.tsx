import type { Take5Draft } from "../../api/take5";
import { useDraftCheck } from "../../api/take5";
import { Button } from "../../components/Button";
import { Field } from "../../components/Field";
import { FIELD_STYLE } from "../../components/fieldStyle";
import { Notice } from "../../components/Notice";
import { fieldProps } from "./fieldProps";

/** Show the server's T3 question; keep its answer box mounted during a new check. */
export function WeakControlsQuestion({
  draft,
  index,
  errorFor,
  onChange,
}: {
  draft: Take5Draft;
  index: number;
  errorFor: (path: string) => string | undefined;
  onChange: (answer: string) => void;
}) {
  const check = useDraftCheck(draft, true, true);
  const path = `hazards.${String(index)}.weak_controls_reason`;
  const question = (check.data?.thinking_questions ?? []).find(
    (item) => item.path === path,
  );
  const answer = draft.hazards[index]?.weak_controls_reason ?? "";
  return (
    <>
      {check.isError && (
        <Notice>
          <p>Your controls couldn’t be checked. Your answers are kept.</p>
          <Button onClick={() => void check.refetch()}>Try again</Button>
        </Notice>
      )}
      {(question || answer) && (
        <div className="flex flex-col gap-3 rounded-xl border-2 border-amber-700 bg-amber-50 p-4">
          {question && <p className="text-lg font-bold">{question.message}</p>}
          <Field
            name={path}
            label="Why aren't stronger controls possible?"
            error={question ? errorFor(path) : undefined}
          >
            <textarea
              {...fieldProps(path, question ? errorFor : () => undefined)}
              className={FIELD_STYLE}
              rows={4}
              value={answer}
              onChange={(event) => {
                onChange(event.target.value);
              }}
            />
          </Field>
          <p>
            {question
              ? "You can add a stronger control instead of writing a reason."
              : "Your earlier answer is kept. You can still edit it."}
          </p>
        </div>
      )}
    </>
  );
}
