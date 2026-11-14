import type { ReactNode } from "react";
import type { ControlDraft, TemplateResponse } from "../../api/take5";
import { Button } from "../../components/Button";
import { ControlEditor } from "../../components/ControlEditor";
import { Guidance } from "../../components/Guidance";

/** Step 3: what the worker will do about one hazard. */
export function ControlsPage({
  path,
  controls,
  template,
  errorFor,
  onChange,
  onAdd,
  onRemove,
  children,
}: {
  path: string;
  controls: ControlDraft[];
  template: TemplateResponse;
  errorFor: (path: string) => string | undefined;
  onChange: (index: number, control: ControlDraft) => void;
  onAdd: () => void;
  onRemove: (index: number) => void;
  children?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-4">
      <p>
        Write what you will actually do about this hazard, then choose the kind
        of control.
      </p>
      <Guidance title="What do the control kinds mean?">
        <p>{template.control_guidance}</p>
      </Guidance>
      {controls.map((control, index) => (
        <ControlEditor
          key={index}
          control={control}
          number={index + 1}
          kinds={template.control_kinds}
          path={`${path}.controls.${String(index)}`}
          errorFor={errorFor}
          onChange={(updated) => {
            onChange(index, updated);
          }}
          onRemove={() => {
            onRemove(index);
          }}
        />
      ))}
      {!controls.length && (
        <p className="rounded-xl border-2 border-dashed border-slate-400 p-4">
          No controls listed yet.
        </p>
      )}
      <Button variant="secondary" onClick={onAdd}>
        Add a control
      </Button>
      {children}
    </div>
  );
}
