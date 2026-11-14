import { fireEvent, render, screen, within } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it } from "vitest";
import type { Answer } from "../api/take5";
import { AnswerPicker } from "./AnswerPicker";

function Picker({ error }: { error?: string }) {
  const [picked, setPicked] = useState<Answer>();
  return (
    <AnswerPicker
      name="answers.keys"
      question="Have you got the gate keys?"
      choices={["Yes", "No", "N/A"]}
      picked={picked}
      onPick={setPicked}
      error={error}
    />
  );
}

function radio(name: string) {
  const group = screen.getByRole("group", {
    name: "Have you got the gate keys?",
  });
  return within(group).getByRole<HTMLInputElement>("radio", { name });
}

describe("AnswerPicker", () => {
  it("starts with no answer picked", () => {
    render(<Picker />);
    for (const answer of ["Yes", "No", "N/A"])
      expect(radio(answer).checked).toBe(false);
  });

  it("picks one answer at a time", () => {
    render(<Picker />);
    fireEvent.click(radio("No"));
    fireEvent.click(radio("N/A"));
    expect(radio("No").checked).toBe(false);
    expect(radio("N/A").checked).toBe(true);
  });

  it("shows its error and marks the group for a screen reader", () => {
    render(<Picker error="Pick Yes, No or N/A." />);
    const group = screen.getByRole("group", {
      name: "Have you got the gate keys?",
    });
    expect(group.getAttribute("aria-invalid")).toBe("true");
    expect(group.getAttribute("aria-describedby")).toBe("answers.keys-error");
    expect(screen.getByText("Pick Yes, No or N/A.")).toBeTruthy();
  });
});
