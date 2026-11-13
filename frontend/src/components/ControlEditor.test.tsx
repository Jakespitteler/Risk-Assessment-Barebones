import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { ControlDraft } from "../api/take5";
import { ControlEditor } from "./ControlEditor";

it("starts without a control kind selected and draws the API choices", () => {
  const onChange = vi.fn<(control: ControlDraft) => void>();
  render(
    <ControlEditor
      control={{ description: "", kind: null }}
      kinds={["Isolate the hazard", "Wear PPE"]}
      path="hazards.0.controls.0"
      errorFor={() => undefined}
      onChange={onChange}
      onRemove={vi.fn()}
    />,
  );
  expect(screen.getByRole<HTMLSelectElement>("combobox").value).toBe("");
  expect(
    screen.getAllByRole("option").map((option) => option.textContent),
  ).toEqual(["Choose a control kind", "Isolate the hazard", "Wear PPE"]);
  fireEvent.change(screen.getByRole("combobox"), {
    target: { value: "Wear PPE" },
  });
  expect(onChange).toHaveBeenLastCalledWith({
    description: "",
    kind: "Wear PPE",
  });
});

it("connects field errors to the control inputs", () => {
  render(
    <ControlEditor
      control={{ description: "", kind: null }}
      kinds={["Wear PPE"]}
      path="hazards.0.controls.0"
      errorFor={() => "Fill in this field."}
      onChange={vi.fn()}
      onRemove={vi.fn()}
    />,
  );
  expect(screen.getByRole("textbox").getAttribute("aria-describedby")).toBe(
    "hazards.0.controls.0.description-error",
  );
  expect(screen.getByRole("combobox").getAttribute("aria-invalid")).toBe(
    "true",
  );
});
