import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { Card } from "./Card";

it("groups what is inside it in one section", () => {
  render(
    <Card>
      <h2>The job</h2>
    </Card>,
  );
  expect(
    screen.getByRole("heading", { name: "The job" }).closest("section"),
  ).not.toBeNull();
});
