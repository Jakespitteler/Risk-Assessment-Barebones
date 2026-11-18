import type { ReactNode } from "react";
import type { ControlDraft, TemplateResponse } from "../../api/take5";
import { Button } from "../../components/Button";
import { ControlEditor } from "../../components/ControlEditor";
import { Guidance } from "../../components/Guidance";
import { useFocusOnAdd } from "./useFocusOnAdd";

const BLANK_CONTROL: ControlDraft = { description: "", kind: null };

/**
 * Step 3: what the worker will do about one hazard. With no controls yet, control 1 is
 * open and empty, and joins the list once anything is typed or picked in it.
 */
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
  onAdd: (control: ControlDraft) => void;
  onRemove: (index: number) => void;
  children?: ReactNode;
}) {
  const shownControls = controls.length ? controls : [BLANK_CONTROL];
  const markAdded = useFocusOnAdd(
    controls.length,
    `${path}.controls.${String(controls.length - 1)}.description`,
  );
  return (
    <div className="flex flex-col gap-4">
      <p>
        Write what you will actually do about this hazard, then choose the kind
        of control.
      </p>
      <Guidance title="What do the control kinds mean?">
        <p>{template.control_guidance}</p>
      </Guidance>
      {shownControls.map((control, index) => (
        <ControlEditor
          key={index}
          control={control}
          number={index + 1}
          kinds={template.control_kinds}
          path={`${path}.controls.${String(index)}`}
          errorFor={errorFor}
          onChange={(updated) => {
            if (controls.length) onChange(index, updated);
            else onAdd(updated);
          }}
          onRemove={
            controls.length
              ? () => {
                  onRemove(index);
                }
              : undefined
          }
        />
      ))}
      {controls.length > 0 && (
        <Button
          variant="secondary"
          onClick={() => {
            markAdded();
            onAdd(BLANK_CONTROL);
          }}
        >
          Add a control
        </Button>
      )}
      {children}
    </div>
  );
}
