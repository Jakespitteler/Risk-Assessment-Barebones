import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { Field } from "./Field";

it("labels its input and shows its error under it", () => {
  render(
    <Field name="job" label="What is the job?" error="Fill in this field.">
      <input id="job" aria-describedby="job-error" />
    </Field>,
  );
  expect(screen.getByLabelText("What is the job?")).toBeTruthy();
  expect(document.getElementById("job-error")?.textContent).toBe(
    "Fill in this field.",
  );
});

it("shows no error when there is none", () => {
  render(
    <Field name="job" label="What is the job?">
      <input id="job" />
    </Field>,
  );
  expect(document.getElementById("job-error")).toBeNull();
});
