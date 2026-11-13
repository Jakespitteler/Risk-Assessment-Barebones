import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { Guidance } from "./Guidance";

it("starts folded away", () => {
  render(
    <Guidance title="What do the ratings mean?">
      <p>Rare: could happen, but only rarely.</p>
    </Guidance>,
  );
  const details = screen
    .getByText("What do the ratings mean?")
    .closest("details");
  expect(details?.open).toBe(false);
});
