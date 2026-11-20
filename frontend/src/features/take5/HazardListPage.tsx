import type { HazardDraft } from "../../api/take5";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { Field } from "../../components/Field";
import { FIELD_STYLE } from "../../components/fieldStyle";
import { fieldProps } from "./fieldProps";
import { useFocusOnAdd } from "./useFocusOnAdd";

/** Step 2: the hazards, in the worker's own words. */
export function HazardListPage({
  hazards,
  errorFor,
  onDescribe,
  onAdd,
  onRemove,
}: {
  hazards: HazardDraft[];
  errorFor: (path: string) => string | undefined;
  onDescribe: (index: number, description: string) => void;
  onAdd: () => void;
  onRemove: (index: number) => void;
}) {
  const listError = errorFor("hazards");
  const markAdded = useFocusOnAdd(
    hazards.length,
    `hazards.${String(hazards.length - 1)}.description`,
  );
  return (
    <div className="flex flex-col gap-4">
      <p>
        Look around the job. List the things that could hurt you or someone else
        today.
      </p>
      {hazards.map((hazard, index) => {
        const path = `hazards.${String(index)}.description`;
        return (
          <Card key={index}>
            <Field
              name={path}
              label={`Hazard ${String(index + 1)}`}
              error={errorFor(path)}
            >
              <textarea
                {...fieldProps(path, errorFor)}
                rows={2}
                className={FIELD_STYLE}
                value={hazard.description}
                onChange={(event) => {
                  onDescribe(index, event.target.value);
                }}
              />
            </Field>
            <Button
              variant="quiet"
              onClick={() => {
                onRemove(index);
              }}
            >
              Remove hazard {index + 1}
            </Button>
          </Card>
        );
      })}
      {listError && (
        <p
          id="hazards"
          tabIndex={-1}
          aria-invalid="true"
          className="font-semibold text-danger"
        >
          {listError}
        </p>
      )}
      <Button
        variant="secondary"
        onClick={() => {
          markAdded();
          onAdd();
        }}
      >
        Add another hazard
      </Button>
    </div>
  );
}
