import { render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { stubPointer } from "../../test-utils";
import { focusFirstEmptyBox, hasFinePointer } from "./focusFirstEmptyBox";

afterEach(() => {
  vi.unstubAllGlobals();
});

it("counts a mouse or trackpad as a computer, and a finger as a phone", () => {
  stubPointer("fine");
  expect(hasFinePointer()).toBe(true);
  stubPointer("coarse");
  expect(hasFinePointer()).toBe(false);
});

it("puts the cursor in the first empty text box, skipping filled boxes and picked answers", () => {
  const { container } = render(
    <form>
      <input type="radio" aria-label="Yes" />
      <input aria-label="Your name" defaultValue="Sam Example" />
      <textarea aria-label="What is the job?" />
      <input aria-label="Where will you do it?" />
    </form>,
  );
  expect(focusFirstEmptyBox(container)).toBe(true);
  expect(document.activeElement).toBe(
    screen.getByLabelText("What is the job?"),
  );
});

it("says so when every box is filled in", () => {
  const { container } = render(
    <form>
      <textarea aria-label="Hazard 1" defaultValue="Dust" />
    </form>,
  );
  expect(focusFirstEmptyBox(container)).toBe(false);
  expect(document.activeElement).toBe(document.body);
});
