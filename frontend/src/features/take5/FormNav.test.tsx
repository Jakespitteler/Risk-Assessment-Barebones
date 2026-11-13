import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { Stage } from "./stage";
import { FormNav } from "./FormNav";

function nav(stage: Stage, busy = false, canFinish = true, label?: string) {
  const handlers = { onBack: vi.fn(), onContinue: vi.fn(), onFinish: vi.fn() };
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

it("finishes on the review", () => {
  const { onFinish } = nav({ page: "review" });
  fireEvent.click(screen.getByRole("button", { name: "Finish Take 5" }));
  expect(onFinish).toHaveBeenCalledOnce();
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
