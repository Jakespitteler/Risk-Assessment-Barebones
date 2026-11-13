import { fireEvent, render, screen, within } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it } from "vitest";
import type { RatingChoice, RiskMatrix } from "../api/take5";
import { RatingPicker } from "./RatingPicker";

// A made-up two-by-two matrix, so the test proves nothing about the booklet is built in.
const SMALL_MATRIX: RiskMatrix = {
  likelihoods: ["Often", "Seldom"],
  consequences: ["Scratch", "Serious"],
  cells: [
    [
      { score: 2, band: "Medium" },
      { score: 4, band: "Severe" },
    ],
    [
      { score: 1, band: "Minimal" },
      { score: 3, band: "Medium" },
    ],
  ],
  jha_threshold: 4,
};

function PickerOnSmallMatrix() {
  const [rating, setRating] = useState<RatingChoice>({
    likelihood: null,
    consequence: null,
  });
  return (
    <RatingPicker matrix={SMALL_MATRIX} rating={rating} onChange={setRating} />
  );
}

function pick(question: string, level: string) {
  const group = screen.getByRole("group", { name: question });
  fireEvent.click(within(group).getByRole("radio", { name: level }));
}

describe("RatingPicker", () => {
  it("starts with nothing picked and no score", () => {
    render(<PickerOnSmallMatrix />);

    for (const radio of screen.getAllByRole("radio")) {
      expect((radio as HTMLInputElement).checked).toBe(false);
    }
    expect(screen.getByRole("status").textContent).toBe(
      "Pick both to see the score.",
    );
  });

  it("shows no score while only one part is picked", () => {
    render(<PickerOnSmallMatrix />);

    pick("How likely is it?", "Seldom");

    expect(screen.getByRole("status").textContent).toBe(
      "Pick both to see the score.",
    );
  });

  it("shows the matrix's score and band once both parts are picked", () => {
    render(<PickerOnSmallMatrix />);

    pick("How likely is it?", "Seldom");
    pick("How bad would it be?", "Serious");

    expect(screen.getByRole("status").textContent).toBe("3Medium");
  });

  it("shows each half's error beside its question", () => {
    render(
      <RatingPicker
        matrix={SMALL_MATRIX}
        rating={{ likelihood: "Often", consequence: null }}
        onChange={() => undefined}
        errors={{ consequence: "Pick a consequence." }}
      />,
    );

    const group = screen.getByRole("group", { name: "How bad would it be?" });
    expect(group.getAttribute("aria-invalid")).toBe("true");
    expect(within(group).getByText("Pick a consequence.")).toBeTruthy();
  });
});
