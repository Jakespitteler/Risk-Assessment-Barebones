import { fireEvent, screen, waitFor } from "@testing-library/react";
import { useState } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  COMPLETE_DRAFT,
  PASSING_CHECK,
  SAVED,
  SMALL_TEMPLATE,
  renderWithApi,
  stubApi,
} from "../../test-utils";
import type { Stage } from "./stage";
import { Take5Form } from "./Take5Form";

const onSaved = vi.fn<(id: string) => void>();

// Stands in for the router: the stage is kept in state instead of the URL.
function FormAt({ start }: { start: Stage }) {
  const [stage, setStage] = useState(start);
  return (
    <Take5Form
      template={SMALL_TEMPLATE}
      stage={stage}
      onStageChange={setStage}
      onBack={setStage}
      onSaved={onSaved}
    />
  );
}

function storeDraft() {
  sessionStorage.setItem(
    "take5-draft",
    JSON.stringify({ draft: COMPLETE_DRAFT, submissionId: SAVED.take5.id }),
  );
}

beforeEach(() => {
  sessionStorage.clear();
  localStorage.clear();
  onSaved.mockReset();
});
afterEach(() => {
  vi.unstubAllGlobals();
});

it("starts with nothing filled in but the remembered name, and the heading focused", () => {
  localStorage.setItem("take5-worker-name", "Sam Example");
  stubApi({});
  renderWithApi(<FormAt start={{ page: "job" }} />);
  expect(screen.getByLabelText<HTMLInputElement>("Your name").value).toBe(
    "Sam Example",
  );
  expect(
    screen.getByLabelText<HTMLTextAreaElement>("What is the job?").value,
  ).toBe("");
  expect(document.activeElement).toBe(
    screen.getByRole("heading", { level: 1 }),
  );
});

it("keeps the worker on a page with gaps, shows them, and focuses the first", async () => {
  stubApi({
    "POST /api/take5s/check": {
      status: 200,
      body: {
        errors: [
          { path: "job", message: "Fill in this field." },
          { path: "hazards.0.description", message: "Fill in this field." },
        ],
        assessment: null,
        can_submit: false,
      },
    },
  });
  renderWithApi(<FormAt start={{ page: "job" }} />);
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  const job = screen.getByLabelText("What is the job?");
  await waitFor(() => {
    expect(document.activeElement).toBe(job);
  });
  expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(
    "The job in front of you",
  );
  // Only this page's gaps are shown here.
  expect(screen.getAllByText("Fill in this field.")).toHaveLength(1);
});

it("moves on when the page has no gaps", async () => {
  storeDraft();
  stubApi({ "POST /api/take5s/check": { status: 200, body: PASSING_CHECK } });
  renderWithApi(<FormAt start={{ page: "job" }} />);
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  expect(
    await screen.findByRole("heading", { name: "What could hurt someone?" }),
  ).toBeTruthy();
});

it("puts a removed hazard back on Undo", () => {
  storeDraft();
  stubApi({});
  renderWithApi(<FormAt start={{ page: "hazards" }} />);
  fireEvent.click(screen.getByRole("button", { name: "Remove hazard 1" }));
  expect(screen.queryByLabelText("Hazard 1")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Undo" }));
  expect(screen.getByLabelText<HTMLTextAreaElement>("Hazard 1").value).toBe(
    "Moving wheel",
  );
});

it("saves, forgets the draft, remembers the name and opens the result", async () => {
  storeDraft();
  stubApi({
    "POST /api/take5s/check": { status: 200, body: PASSING_CHECK },
    "POST /api/take5s": { status: 200, body: SAVED },
  });
  renderWithApi(<FormAt start={{ page: "review" }} />);
  fireEvent.click(await screen.findByRole("button", { name: "Finish Take 5" }));
  await waitFor(() => {
    expect(onSaved).toHaveBeenCalledWith(SAVED.take5.id);
  });
  expect(sessionStorage.getItem("take5-draft")).toBeNull();
  expect(localStorage.getItem("take5-worker-name")).toBe("Sam Example");
});

it("sends the worker to the gap the back end found on Finish", async () => {
  storeDraft();
  stubApi({
    "POST /api/take5s/check": { status: 200, body: PASSING_CHECK },
    "POST /api/take5s": {
      status: 422,
      body: {
        detail: "Fill in the highlighted fields before you submit.",
        errors: [
          {
            path: "hazards.0.controls.0.kind",
            message: "Pick a control kind.",
          },
        ],
      },
    },
  });
  renderWithApi(<FormAt start={{ page: "review" }} />);
  fireEvent.click(await screen.findByRole("button", { name: "Finish Take 5" }));
  expect(
    await screen.findByRole("heading", { name: "What will stop it?" }),
  ).toBeTruthy();
  expect(screen.getByText("Pick a control kind.")).toBeTruthy();
});

it("offers the saved Take 5 when its ID was used for other answers", async () => {
  storeDraft();
  stubApi({
    "POST /api/take5s/check": { status: 200, body: PASSING_CHECK },
    "POST /api/take5s": {
      status: 409,
      body: { detail: "This Take 5 was already saved with different answers." },
    },
  });
  renderWithApi(<FormAt start={{ page: "review" }} />);
  fireEvent.click(await screen.findByRole("button", { name: "Finish Take 5" }));
  expect(
    await screen.findByRole("link", { name: "Open the saved Take 5" }),
  ).toBeTruthy();
});
