import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { expect, it, vi } from "vitest";
import type { ControlDraft } from "../../api/take5";
import { SMALL_TEMPLATE } from "../../test-utils";
import { ControlsPage } from "./ControlsPage";

it("opens control 1 empty when there are none, and adds it once typed in", () => {
  const onAdd = vi.fn<(control: ControlDraft) => void>();
  render(
    <ControlsPage
      path="hazards.0"
      controls={[]}
      template={SMALL_TEMPLATE}
      errorFor={() => undefined}
      onChange={vi.fn()}
      onAdd={onAdd}
      onRemove={vi.fn()}
    >
      <p>A question about these controls</p>
    </ControlsPage>,
  );
  expect(screen.getByRole("heading", { name: "Control 1" })).toBeTruthy();
  expect(screen.getByText("A question about these controls")).toBeTruthy();
  // Remove and Add would do nothing to a control that isn't on the list yet.
  expect(screen.queryByRole("button", { name: "Remove control 1" })).toBeNull();
  expect(screen.queryByRole("button", { name: "Add a control" })).toBeNull();
  fireEvent.change(screen.getByLabelText("What will you do?"), {
    target: { value: "Chock the wheel" },
  });
  expect(onAdd).toHaveBeenCalledWith({
    description: "Chock the wheel",
    kind: null,
  });
});

it("adds control 1 when its kind is picked first", () => {
  const onAdd = vi.fn<(control: ControlDraft) => void>();
  render(
    <ControlsPage
      path="hazards.0"
      controls={[]}
      template={SMALL_TEMPLATE}
      errorFor={() => undefined}
      onChange={vi.fn()}
      onAdd={onAdd}
      onRemove={vi.fn()}
    />,
  );
  fireEvent.change(screen.getByLabelText("Kind of control"), {
    target: { value: "Wear PPE" },
  });
  expect(onAdd).toHaveBeenCalledWith({ description: "", kind: "Wear PPE" });
});

it("keeps the cursor in control 1 as the first letter typed adds it", () => {
  function ControlsInState() {
    const [controls, setControls] = useState<ControlDraft[]>([]);
    return (
      <ControlsPage
        path="hazards.0"
        controls={controls}
        template={SMALL_TEMPLATE}
        errorFor={() => undefined}
        onChange={(index, control) => {
          setControls(
            controls.map((item, at) => (at === index ? control : item)),
          );
        }}
        onAdd={(control) => {
          setControls([...controls, control]);
        }}
        onRemove={vi.fn()}
      />
    );
  }
  render(<ControlsInState />);
  const box = screen.getByLabelText("What will you do?");
  box.focus();
  fireEvent.change(box, { target: { value: "C" } });
  // The same box stays on the page, now with a Remove button, so no typing is lost.
  expect(screen.getByLabelText("What will you do?")).toBe(box);
  expect(document.activeElement).toBe(box);
  expect(screen.getByRole("button", { name: "Remove control 1" })).toBeTruthy();
});

it("puts the cursor in a control added with Add a control", () => {
  function ControlsInState() {
    const [controls, setControls] = useState<ControlDraft[]>([
      { description: "Gloves", kind: "Wear PPE" },
    ]);
    return (
      <ControlsPage
        path="hazards.0"
        controls={controls}
        template={SMALL_TEMPLATE}
        errorFor={() => undefined}
        onChange={vi.fn()}
        onAdd={(control) => {
          setControls([...controls, control]);
        }}
        onRemove={vi.fn()}
      />
    );
  }
  render(<ControlsInState />);
  fireEvent.click(screen.getByRole("button", { name: "Add a control" }));
  expect(screen.getByRole("heading", { name: "Control 2" })).toBeTruthy();
  expect(document.activeElement).toBe(
    screen.getAllByLabelText("What will you do?")[1],
  );
});

it("offers the template's control kinds and removes a control by number", () => {
  const onRemove = vi.fn();
  render(
    <ControlsPage
      path="hazards.0"
      controls={[{ description: "Gloves", kind: "Wear PPE" }]}
      template={SMALL_TEMPLATE}
      errorFor={() => undefined}
      onChange={vi.fn()}
      onAdd={vi.fn()}
      onRemove={onRemove}
    />,
  );
  expect(
    screen.getAllByRole("option").map((option) => option.textContent),
  ).toEqual(["Choose a control kind", "Isolate the hazard", "Wear PPE"]);
  fireEvent.click(screen.getByRole("button", { name: "Remove control 1" }));
  expect(onRemove).toHaveBeenCalledWith(0);
});
