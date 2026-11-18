import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { expect, it, vi } from "vitest";
import type { HazardDraft } from "../../api/take5";
import { COMPLETE_DRAFT, HAZARD_DRAFT } from "../../test-utils";
import { blankHazard } from "./useTake5Draft";
import { HazardListPage } from "./HazardListPage";

it("lists, adds and removes hazards by number", () => {
  const onAdd = vi.fn();
  const onRemove = vi.fn();
  const onDescribe = vi.fn();
  render(
    <HazardListPage
      hazards={COMPLETE_DRAFT.hazards}
      errorFor={() => undefined}
      onDescribe={onDescribe}
      onAdd={onAdd}
      onRemove={onRemove}
    />,
  );
  fireEvent.change(screen.getByLabelText("Hazard 1"), {
    target: { value: "Dust" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Add another hazard" }));
  fireEvent.click(screen.getByRole("button", { name: "Remove hazard 1" }));
  expect(onDescribe).toHaveBeenCalledWith(0, "Dust");
  expect(onAdd).toHaveBeenCalledOnce();
  expect(onRemove).toHaveBeenCalledWith(0);
});

it("shows the error for having no hazards", () => {
  render(
    <HazardListPage
      hazards={[]}
      errorFor={(path) =>
        path === "hazards" ? "List at least one hazard." : undefined
      }
      onDescribe={vi.fn()}
      onAdd={vi.fn()}
      onRemove={vi.fn()}
    />,
  );
  expect(
    screen.getByText("List at least one hazard.").getAttribute("aria-invalid"),
  ).toBe("true");
});

it("puts the cursor in a hazard added with Add another hazard", () => {
  function HazardsInState() {
    const [hazards, setHazards] = useState<HazardDraft[]>([HAZARD_DRAFT]);
    return (
      <HazardListPage
        hazards={hazards}
        errorFor={() => undefined}
        onDescribe={vi.fn()}
        onAdd={() => {
          setHazards([...hazards, blankHazard()]);
        }}
        onRemove={vi.fn()}
      />
    );
  }
  render(<HazardsInState />);
  fireEvent.click(screen.getByRole("button", { name: "Add another hazard" }));
  expect(document.activeElement).toBe(screen.getByLabelText("Hazard 2"));
});
