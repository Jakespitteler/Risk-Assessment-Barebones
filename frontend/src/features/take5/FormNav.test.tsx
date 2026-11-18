import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { Stage } from "./stage";
import { FormNav } from "./FormNav";

function nav(stage: Stage, busy = false, canSubmit = true, label?: string) {
  const handlers = { onBack: vi.fn(), onSubmit: vi.fn() };
  const view = render(
    <FormNav
      stage={stage}
      busy={busy}
      canSubmit={canSubmit}
      label={label}
      {...handlers}
    />,
  );
  return { ...handlers, ...view };
}

it("has no Back on the first page", () => {
  nav({ page: "job" });
  expect(screen.queryByRole("button", { name: "Back" })).toBeNull();
});

it("submits the form with Continue, so Enter in a box presses it", () => {
  nav({ page: "job" });
  expect(
    screen.getByRole<HTMLButtonElement>("button", { name: "Continue" }).type,
  ).toBe("submit");
});

it("submits the Take 5 on the review", () => {
  const { onSubmit } = nav({ page: "review" });
  const submit = screen.getByRole<HTMLButtonElement>("button", {
    name: "Submit Take 5",
  });
  fireEvent.click(submit);
  expect(onSubmit).toHaveBeenCalledOnce();
  // Saving can't be taken back, so Enter never presses Submit.
  expect(submit.type).toBe("button");
});

it("is disabled while busy, with what it is doing", () => {
  nav({ page: "review" }, true, true, "Saving…");
  expect(
    screen.getByRole<HTMLButtonElement>("button", { name: "Saving…" }).disabled,
  ).toBe(true);
  expect(
    screen.getByRole<HTMLButtonElement>("button", { name: "Back" }).disabled,
  ).toBe(true);
});

it("keeps Submit disabled until the review has been checked", () => {
  nav({ page: "review" }, false, false);
  expect(
    screen.getByRole<HTMLButtonElement>("button", { name: "Submit Take 5" })
      .disabled,
  ).toBe(true);
});
