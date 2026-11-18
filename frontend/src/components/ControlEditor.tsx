import type { ControlDraft, TemplateResponse } from "../api/take5";
import { Button } from "./Button";
import { Field } from "./Field";
import { FIELD_STYLE } from "./fieldStyle";

/**
 * One control: what the worker will do, and its kind from the back end's list. A control
 * not yet on the list has no Remove button.
 */
export function ControlEditor({
  control,
  number,
  kinds,
  path,
  errorFor,
  onChange,
  onRemove,
}: {
  control: ControlDraft;
  number: number;
  kinds: TemplateResponse["control_kinds"];
  path: string;
  errorFor: (path: string) => string | undefined;
  onChange: (control: ControlDraft) => void;
  onRemove?: () => void;
}) {
  const description = `${path}.description`;
  const kind = `${path}.kind`;
  return (
    <section className="flex flex-col gap-4 rounded-2xl border border-stone-300 bg-white p-4">
      <h2 className="text-lg font-bold">Control {number}</h2>
      <Field
        name={description}
        label="What will you do?"
        error={errorFor(description)}
      >
        <textarea
          id={description}
          rows={3}
          className={FIELD_STYLE}
          aria-invalid={Boolean(errorFor(description))}
          aria-describedby={
            errorFor(description) ? `${description}-error` : undefined
          }
          value={control.description}
          onChange={(event) => {
            onChange({ ...control, description: event.target.value });
          }}
        />
      </Field>
      <Field name={kind} label="Kind of control" error={errorFor(kind)}>
        <select
          id={kind}
          className={FIELD_STYLE}
          value={control.kind ?? ""}
          aria-invalid={Boolean(errorFor(kind))}
          aria-describedby={errorFor(kind) ? `${kind}-error` : undefined}
          onChange={(event) => {
            onChange({
              ...control,
              kind: kinds.find((item) => item === event.target.value) ?? null,
            });
          }}
        >
          <option value="" disabled>
            Choose a control kind
          </option>
          {kinds.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </Field>
      {onRemove && (
        <Button variant="quiet" onClick={onRemove}>
          Remove control {number}
        </Button>
      )}
    </section>
  );
}
