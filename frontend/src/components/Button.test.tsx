import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { Button } from "./Button";

it("is a plain button that can't submit a form by accident", () => {
  const onClick = vi.fn();
  render(<Button onClick={onClick}>Continue</Button>);
  const button = screen.getByRole("button", { name: "Continue" });
  expect(button.getAttribute("type")).toBe("button");
  fireEvent.click(button);
  expect(onClick).toHaveBeenCalledOnce();
});

it("is at least 56 px high in every style but the quiet one", () => {
  render(
    <>
      <Button>One</Button>
      <Button variant="secondary">Two</Button>
      <Button variant="quiet">Three</Button>
    </>,
  );
  expect(screen.getByRole("button", { name: "One" }).className).toContain(
    "min-h-14",
  );
  expect(screen.getByRole("button", { name: "Two" }).className).toContain(
    "min-h-14",
  );
  expect(screen.getByRole("button", { name: "Three" }).className).toContain(
    "min-h-12",
  );
});
