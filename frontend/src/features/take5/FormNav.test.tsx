import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { FormNav } from "./FormNav";

it("has no Back on the first page", () => {
  render(
    <FormNav
      stage={{ page: "job" }}
      busy={false}
      label={undefined}
      onBack={vi.fn()}
      onContinue={vi.fn()}
      onFinish={vi.fn()}
    />,
  );
  expect(screen.queryByRole("button", { name: "Back" })).toBeNull();
});

it("finishes on the review, and is disabled while busy", () => {
  const onFinish = vi.fn();
  const { rerender } = render(
    <FormNav
      stage={{ page: "review" }}
      busy={false}
      label={undefined}
      onBack={vi.fn()}
      onContinue={vi.fn()}
      onFinish={onFinish}
    />,
  );
  fireEvent.click(screen.getByRole("button", { name: "Finish Take 5" }));
  expect(onFinish).toHaveBeenCalledOnce();
  rerender(
    <FormNav
      stage={{ page: "review" }}
      busy
      label="Saving…"
      onBack={vi.fn()}
      onContinue={vi.fn()}
      onFinish={onFinish}
    />,
  );
  expect(
    screen.getByRole<HTMLButtonElement>("button", { name: "Saving…" }).disabled,
  ).toBe(true);
});
