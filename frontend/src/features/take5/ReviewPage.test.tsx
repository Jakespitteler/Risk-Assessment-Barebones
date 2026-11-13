import { screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import {
  COMPLETE_DRAFT,
  PASSING_CHECK,
  renderWithApi,
  stubApi,
} from "../../test-utils";
import { ReviewPage } from "./ReviewPage";

afterEach(() => {
  vi.unstubAllGlobals();
});

it("draws the ratings from the back end's check, not its own", async () => {
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  renderWithApi(<ReviewPage draft={COMPLETE_DRAFT} onGaps={vi.fn()} />);
  expect(await screen.findByText("Minimal")).toBeTruthy();
  expect(screen.getByText("Minimal").parentElement?.textContent).toBe(
    "1Minimal",
  );
  expect(screen.getByText("Sam Example")).toBeTruthy();
});

it("hands any gaps back, so the worker is sent to them", async () => {
  const errors = [{ path: "job", message: "Fill in this field." }];
  stubApi({
    "POST /api/take5s/check": {
      status: 200,
      body: { errors, assessment: null, can_submit: false },
    },
  });
  const onGaps = vi.fn();
  renderWithApi(<ReviewPage draft={COMPLETE_DRAFT} onGaps={onGaps} />);
  await waitFor(() => {
    expect(onGaps).toHaveBeenCalledWith(errors);
  });
});

it("offers to try again when the answers can't be checked", async () => {
  stubApi({ "POST /api/take5s/check": "offline" });
  renderWithApi(<ReviewPage draft={COMPLETE_DRAFT} onGaps={vi.fn()} />);
  expect(await screen.findByRole("button", { name: "Try again" })).toBeTruthy();
});
