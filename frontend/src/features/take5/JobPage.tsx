import type { Take5Draft } from "../../api/take5";
import { Card } from "../../components/Card";
import { Field } from "../../components/Field";
import { FIELD_STYLE } from "../../components/fieldStyle";
import { fieldProps } from "./fieldProps";

type JobField = "worker_name" | "job" | "location";

const FIELDS: readonly { name: JobField; label: string }[] = [
  { name: "worker_name", label: "Your name" },
  { name: "job", label: "What is the job?" },
  { name: "location", label: "Where will you do it?" },
];

/** Step 1: who is doing the job, what it is and where. */
export function JobPage({
  draft,
  errorFor,
  onEdit,
}: {
  draft: Take5Draft;
  errorFor: (path: string) => string | undefined;
  onEdit: (field: JobField, value: string) => void;
}) {
  return (
    <Card>
      <p>Say who you are, what you’re doing and where. Use your own words.</p>
      {FIELDS.map(({ name, label }) => (
        <Field key={name} name={name} label={label} error={errorFor(name)}>
          {name === "job" ? (
            <textarea
              {...fieldProps(name, errorFor)}
              rows={3}
              className={FIELD_STYLE}
              value={draft[name]}
              onChange={(event) => {
                onEdit(name, event.target.value);
              }}
            />
          ) : (
            <input
              {...fieldProps(name, errorFor)}
              className={FIELD_STYLE}
              autoComplete={name === "worker_name" ? "name" : "off"}
              value={draft[name]}
              onChange={(event) => {
                onEdit(name, event.target.value);
              }}
            />
          )}
        </Field>
      ))}
    </Card>
  );
}
