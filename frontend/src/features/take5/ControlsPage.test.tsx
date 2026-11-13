import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { SMALL_TEMPLATE } from "../../test-utils";
import { ControlsPage } from "./ControlsPage";

it("says when there are no controls yet, and adds one", () => {
  const onAdd = vi.fn();
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
  expect(screen.getByText("No controls listed yet.")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Add a control" }));
  expect(onAdd).toHaveBeenCalledOnce();
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
