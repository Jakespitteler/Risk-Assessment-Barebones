import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { Screen } from "./Screen";

it("puts the page in one main landmark with the app's name", () => {
  render(
    <Screen subtitle="Before you start">
      <h1>The job</h1>
    </Screen>,
  );
  const main = screen.getByRole("main");
  expect(main.textContent).toContain("Take 5");
  expect(main.textContent).toContain("Before you start");
});
