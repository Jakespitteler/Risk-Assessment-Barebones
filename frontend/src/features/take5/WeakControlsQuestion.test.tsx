import { fireEvent, screen, waitFor } from "@testing-library/react";
import { useState } from "react";
import { afterEach, expect, it, vi } from "vitest";
import type { Take5Draft } from "../../api/take5";
import {
  COMPLETE_DRAFT,
  PASSING_CHECK,
  renderWithApi,
  stubApi,
} from "../../test-utils";
import { WeakControlsQuestion } from "./WeakControlsQuestion";

const path = "hazards.0.weak_controls_reason";
const label = "Why aren't stronger controls possible?";
const question = "The server's question for this hazard";
const checked = {
  ...PASSING_CHECK,
  thinking_questions: [{ path, message: question }],
};

function Answer() {
  const [draft, setDraft] = useState<Take5Draft>(COMPLETE_DRAFT);
  return (
    <WeakControlsQuestion
      draft={draft}
      index={0}
      errorFor={() => "Fill in this field."}
      onChange={(answer) => {
        setDraft({
          ...draft,
          hazards: draft.hazards.map((hazard) => ({
            ...hazard,
            weak_controls_reason: answer,
          })),
        });
      }}
    />
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

it("shows the server's wording and field error, and keeps focus while checking an edit", async () => {
  stubApi({ "POST /api/take5s/check": { status: 200, body: checked } });
  renderWithApi(<Answer />);
  const input = await screen.findByLabelText<HTMLTextAreaElement>(label);
  expect(screen.getByText(question)).toBeTruthy();
  expect(input.getAttribute("aria-describedby")).toBe(`${path}-error`);
  input.focus();
  fireEvent.change(input, { target: { value: "Live testing" } });
  expect(screen.getByLabelText(label)).toBe(input);
  expect(document.activeElement).toBe(input);
  await waitFor(() => {
    expect(input.value).toBe("Live testing");
  });
});

it("keeps a written answer visible when the next server reply removes the question", async () => {
  const calls = stubApi({
    "POST /api/take5s/check": [
      { status: 200, body: checked },
      { status: 200, body: PASSING_CHECK },
    ],
  });
  renderWithApi(<Answer />);
  fireEvent.change(await screen.findByLabelText(label), {
    target: { value: "Kept answer" },
  });
  await waitFor(() => {
    expect(calls).toHaveLength(2);
    expect(screen.queryByText(question)).toBeNull();
    expect(screen.getByLabelText<HTMLTextAreaElement>(label).value).toBe(
      "Kept answer",
    );
    expect(
      screen.getByText("Your earlier answer is kept. You can still edit it."),
    ).toBeTruthy();
  });
});

it("offers a retry when the controls cannot be checked", async () => {
  stubApi({
    "POST /api/take5s/check": [
      "offline",
      "offline",
      "offline",
      { status: 200, body: checked },
    ],
  });
  renderWithApi(<Answer />);
  fireEvent.click(await screen.findByRole("button", { name: "Try again" }));
  expect(await screen.findByLabelText(label)).toBeTruthy();
});
