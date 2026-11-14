import { fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import {
  COMPLETE_DRAFT,
  PASSING_CHECK,
  SAVED,
  renderWithApi,
  stubApi,
} from "../../test-utils";
import { ReviewPage } from "./ReviewPage";

afterEach(() => {
  vi.unstubAllGlobals();
});

it("draws the ratings from the back end's check, not its own", async () => {
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  renderWithApi(
    <ReviewPage
      draft={COMPLETE_DRAFT}
      onGaps={vi.fn()}
      onOpenWarning={vi.fn()}
    />,
  );
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
  renderWithApi(
    <ReviewPage
      draft={COMPLETE_DRAFT}
      onGaps={onGaps}
      onOpenWarning={vi.fn()}
    />,
  );
  await waitFor(() => {
    expect(onGaps).toHaveBeenCalledWith(errors);
  });
});

it("offers to try again when the answers can't be checked", async () => {
  stubApi({ "POST /api/take5s/check": "offline" });
  renderWithApi(
    <ReviewPage
      draft={COMPLETE_DRAFT}
      onGaps={vi.fn()}
      onOpenWarning={vi.fn()}
    />,
  );
  expect(await screen.findByRole("button", { name: "Try again" })).toBeTruthy();
});

const NO_CONTROLS = {
  path: "hazards.0.controls",
  message: "No controls: you'll be told not to start.",
};

it("shows each warning on its hazard, with a button to its controls", async () => {
  stubApi({
    "POST /api/take5s/check": {
      status: 200,
      body: { ...PASSING_CHECK, warnings: [NO_CONTROLS] },
    },
  });
  const onOpenWarning = vi.fn();
  renderWithApi(
    <ReviewPage
      draft={COMPLETE_DRAFT}
      onGaps={vi.fn()}
      onOpenWarning={onOpenWarning}
    />,
  );
  const warning = await screen.findByText(NO_CONTROLS.message);
  // The warning sits in its hazard's card, under the hazard's heading.
  const hazardCard = screen
    .getByRole("heading", { name: "Moving wheel" })
    .closest("section");
  expect(hazardCard?.contains(warning)).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "Add a control" }));
  expect(onOpenWarning).toHaveBeenCalledWith(NO_CONTROLS);
});

it("shows no warning when the back end sends none", async () => {
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  renderWithApi(
    <ReviewPage
      draft={COMPLETE_DRAFT}
      onGaps={vi.fn()}
      onOpenWarning={vi.fn()}
    />,
  );
  await screen.findByText("Minimal");
  expect(screen.queryByRole("button", { name: "Add a control" })).toBeNull();
});

it("says when the draft is a copy made to fix a Don't start yet", async () => {
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  renderWithApi(
    <ReviewPage
      draft={{ ...COMPLETE_DRAFT, fixes: SAVED.take5.id }}
      onGaps={vi.fn()}
      onOpenWarning={vi.fn()}
    />,
  );
  expect(
    await screen.findByText(
      /This is a copy of a Take 5 that said Don’t start yet/,
    ),
  ).toBeTruthy();
});

it("shows each answer, and a No's warning with a button to change it", async () => {
  const warning = {
    path: "answers.keys",
    message: "You answered No: you'll be told not to start.",
  };
  stubApi({
    "POST /api/take5s/check": {
      status: 200,
      body: {
        ...PASSING_CHECK,
        assessment: {
          ...PASSING_CHECK.assessment,
          answers: { keys: "No", dogs: "No" },
        },
        warnings: [warning],
      },
    },
  });
  const onOpenWarning = vi.fn();
  renderWithApi(
    <ReviewPage
      draft={COMPLETE_DRAFT}
      onGaps={vi.fn()}
      onOpenWarning={onOpenWarning}
    />,
  );
  expect(await screen.findByText(warning.message)).toBeTruthy();
  expect(screen.getByText("Have you got the gate keys?")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Change answer" }));
  expect(onOpenWarning).toHaveBeenCalledWith(warning);
});
