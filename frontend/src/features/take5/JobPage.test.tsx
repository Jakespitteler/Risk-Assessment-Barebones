import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { COMPLETE_DRAFT } from "../../test-utils";
import { JobPage } from "./JobPage";

it("shows the three answers and reports each edit by its field", () => {
  const onEdit = vi.fn();
  render(
    <JobPage
      draft={COMPLETE_DRAFT}
      errorFor={() => undefined}
      onEdit={onEdit}
    />,
  );
  expect(screen.getByLabelText<HTMLInputElement>("Your name").value).toBe(
    "Sam Example",
  );
  fireEvent.change(screen.getByLabelText("Where will you do it?"), {
    target: { value: "Pit 3" },
  });
  expect(onEdit).toHaveBeenCalledWith("location", "Pit 3");
});

it("ties each error to its field", () => {
  render(
    <JobPage
      draft={{ ...COMPLETE_DRAFT, job: "" }}
      errorFor={(path) => (path === "job" ? "Fill in this field." : undefined)}
      onEdit={vi.fn()}
    />,
  );
  const job = screen.getByLabelText("What is the job?");
  expect(job.getAttribute("aria-invalid")).toBe("true");
  expect(job.getAttribute("aria-describedby")).toBe("job-error");
  expect(screen.getByLabelText("Your name").getAttribute("aria-invalid")).toBe(
    "false",
  );
});
