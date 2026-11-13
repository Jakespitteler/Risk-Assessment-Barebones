import type { ControlDraft, TemplateResponse } from "../api/take5";
import { Field } from "./Field";

/** A reusable control editor, populated entirely from the API's control kinds. */
export function ControlEditor({
  control,
  kinds,
  path,
  errorFor,
  onChange,
  onRemove,
}: {
  control: ControlDraft;
  kinds: TemplateResponse["control_kinds"];
  path: string;
  errorFor: (path: string) => string | undefined;
  onChange: (control: ControlDraft) => void;
  onRemove: () => void;
}) {
  return (
    <section className="control-card">
      <Field
        name={`${path}.description`}
        label="What will you do?"
        error={errorFor(`${path}.description`)}
      >
        <textarea
          id={`${path}.description`}
          aria-invalid={Boolean(errorFor(`${path}.description`))}
          aria-describedby={
            errorFor(`${path}.description`)
              ? `${path}.description-error`
              : undefined
          }
          value={control.description}
          onChange={(event) => {
            onChange({ ...control, description: event.target.value });
          }}
        />
      </Field>
      <Field
        name={`${path}.kind`}
        label="Kind of control"
        error={errorFor(`${path}.kind`)}
      >
        <select
          id={`${path}.kind`}
          value={control.kind ?? ""}
          aria-invalid={Boolean(errorFor(`${path}.kind`))}
          aria-describedby={
            errorFor(`${path}.kind`) ? `${path}.kind-error` : undefined
          }
          onChange={(event) => {
            onChange({
              ...control,
              kind: kinds.find((kind) => kind === event.target.value) ?? null,
            });
          }}
        >
          <option value="" disabled>
            Choose a control kind
          </option>
          {kinds.map((kind) => (
            <option key={kind} value={kind}>
              {kind}
            </option>
          ))}
        </select>
      </Field>
      <button type="button" className="text-button" onClick={onRemove}>
        Remove control
      </button>
    </section>
  );
}
