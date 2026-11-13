import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { UndoBar } from "./UndoBar";

it("says what was removed and puts it back on Undo", () => {
  const onUndo = vi.fn();
  const onDismiss = vi.fn();
  render(
    <UndoBar
      message="Hazard 2 removed."
      onUndo={onUndo}
      onDismiss={onDismiss}
    />,
  );
  expect(screen.getByRole("status").textContent).toContain("Hazard 2 removed.");
  fireEvent.click(screen.getByRole("button", { name: "Undo" }));
  fireEvent.click(screen.getByRole("button", { name: "Close" }));
  expect(onUndo).toHaveBeenCalledOnce();
  expect(onDismiss).toHaveBeenCalledOnce();
});
