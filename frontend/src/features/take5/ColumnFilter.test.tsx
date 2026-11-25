import { fireEvent, render, screen, within } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { ColumnFilter } from "./ColumnFilter";

function show(ticked: string[] = [], choices = ["Ann", "Bob", "Cy"]) {
  const onApply = vi.fn();
  render(
    <ColumnFilter
      title="Worker"
      choices={choices}
      ticked={ticked}
      onApply={onApply}
    />,
  );
  return onApply;
}

it("opens the column's values with the ticked ones ticked, and applies the change", () => {
  const onApply = show(["Bob"]);
  fireEvent.click(
    screen.getByRole("button", { name: "Filter Worker, 1 ticked" }),
  );
  const list = screen.getByRole("dialog", { name: "Filter worker" });
  expect(within(list).getByLabelText("Bob")).toHaveProperty("checked", true);
  // The first tick box has the focus, so a keyboard user starts in the list.
  expect(document.activeElement).toBe(within(list).getByLabelText("Ann"));
  fireEvent.click(within(list).getByLabelText("Ann"));
  fireEvent.click(within(list).getByRole("button", { name: "Apply" }));
  expect(onApply).toHaveBeenCalledWith(["Bob", "Ann"]);
  expect(screen.queryByRole("dialog")).toBeNull();
});

it("leaves the filter as it was on Cancel or Escape, and gives the focus back", () => {
  const onApply = show();
  const opener = screen.getByRole("button", { name: "Filter Worker" });
  fireEvent.click(opener);
  fireEvent.click(screen.getByLabelText("Cy"));
  fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
  fireEvent.click(opener);
  expect(screen.getByLabelText("Cy")).toHaveProperty("checked", false);
  fireEvent.keyDown(screen.getByRole("dialog"), { key: "Escape" });
  expect(screen.queryByRole("dialog")).toBeNull();
  expect(document.activeElement).toBe(opener);
  expect(onApply).not.toHaveBeenCalled();
});

it("unticks every value at once, which applies as no filter", () => {
  const onApply = show(["Ann", "Cy"]);
  fireEvent.click(
    screen.getByRole("button", { name: "Filter Worker, 2 ticked" }),
  );
  fireEvent.click(screen.getByRole("button", { name: "Untick all" }));
  fireEvent.click(screen.getByRole("button", { name: "Apply" }));
  expect(onApply).toHaveBeenCalledWith([]);
});

it("finds a value in a long list, ignoring capitals", () => {
  show([], ["Ann", "Bob", "Cy", "Di", "Ed", "Flo", "Gus", "Hal", "Ivy"]);
  fireEvent.click(screen.getByRole("button", { name: "Filter Worker" }));
  fireEvent.change(screen.getByLabelText("Find a worker"), {
    target: { value: "IV" },
  });
  expect(
    screen
      .getAllByRole("checkbox")
      .map((box) => box.closest("label")?.textContent),
  ).toEqual(["Ivy"]);
});

it("keeps showing a ticked value the back end no longer lists, so it can be unticked", () => {
  show(["Zed"]);
  fireEvent.click(
    screen.getByRole("button", { name: "Filter Worker, 1 ticked" }),
  );
  expect(screen.getByLabelText("Zed")).toHaveProperty("checked", true);
});

it("keeps the focus in the list after a tap on its background, so Tab and Escape still work", () => {
  show();
  fireEvent.click(screen.getByRole("button", { name: "Filter Worker" }));
  const list = screen.getByRole("dialog", { name: "Filter worker" });
  list.focus();
  expect(document.activeElement).toBe(list);
  fireEvent.keyDown(list, { key: "Tab", shiftKey: true });
  expect(document.activeElement).toBe(
    within(list).getByRole("button", { name: "Cancel" }),
  );
  list.focus();
  fireEvent.keyDown(list, { key: "Tab" });
  expect(document.activeElement).toBe(within(list).getByLabelText("Ann"));
});
