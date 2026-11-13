import { fireEvent, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { SMALL_TEMPLATE, renderWithApi, stubApi } from "../../test-utils";
import { NewTake5Screen } from "./NewTake5Screen";

afterEach(() => {
  vi.unstubAllGlobals();
});

const props = {
  stage: { page: "job" } as const,
  onStageChange: vi.fn(),
  onBack: vi.fn(),
  onSaved: vi.fn(),
};

it("shows the form once the card has loaded", async () => {
  stubApi({ "GET /api/take5/template": { status: 200, body: SMALL_TEMPLATE } });
  renderWithApi(<NewTake5Screen {...props} />);
  expect(
    await screen.findByRole("heading", { name: "The job in front of you" }),
  ).toBeTruthy();
});

it("offers to try again when the card can't be loaded", async () => {
  const calls = stubApi({
    "GET /api/take5/template": [
      "offline",
      "offline",
      "offline",
      "offline",
      { status: 200, body: SMALL_TEMPLATE },
    ],
  });
  renderWithApi(<NewTake5Screen {...props} />);
  fireEvent.click(await screen.findByRole("button", { name: "Try again" }));
  expect(
    await screen.findByRole("heading", { name: "The job in front of you" }),
  ).toBeTruthy();
  expect(calls).toHaveLength(5);
});
