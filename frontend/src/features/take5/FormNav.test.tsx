import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { Stage } from "./stage";
import { FormNav } from "./FormNav";

function nav(stage: Stage, busy = false, canFinish = true, label?: string) {
  const handlers = { onBack: vi.fn(), onFinish: vi.fn() };
  const view = render(
    <FormNav
      stage={stage}
      busy={busy}
      canFinish={canFinish}
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

it("finishes on the review", () => {
  const { onFinish } = nav({ page: "review" });
  const finish = screen.getByRole<HTMLButtonElement>("button", {
    name: "Finish Take 5",
  });
  fireEvent.click(finish);
  expect(onFinish).toHaveBeenCalledOnce();
  // Saving can't be taken back, so Enter never presses Finish.
  expect(finish.type).toBe("button");
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

it("keeps Finish disabled until the review has been checked", () => {
  nav({ page: "review" }, false, false);
  expect(
    screen.getByRole<HTMLButtonElement>("button", { name: "Finish Take 5" })
      .disabled,
  ).toBe(true);
});
