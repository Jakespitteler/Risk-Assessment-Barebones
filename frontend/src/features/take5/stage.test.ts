import { describe, expect, it } from "vitest";
import type { Take5Draft } from "../../api/take5";
import { COMPLETE_DRAFT, HAZARD_DRAFT } from "../../test-utils";
import type { Stage } from "./stage";
import {
  nextStage,
  previousStage,
  shownStage,
  stageFromSearch,
  stageOfError,
  stageToSearch,
} from "./stage";

const NO_CONTROLS: Take5Draft = {
  ...COMPLETE_DRAFT,
  hazards: [{ ...HAZARD_DRAFT, controls: [] }],
};

describe("stage", () => {
  it("reads back what it writes to the URL", () => {
    const stage = { page: "after", hazard: 2 } as const;
    expect(stageFromSearch(new URLSearchParams(stageToSearch(stage)))).toEqual(
      stage,
    );
  });

  it("starts at the job for an unknown or broken URL", () => {
    expect(stageFromSearch(new URLSearchParams("page=nope"))).toEqual({
      page: "job",
    });
    expect(
      stageFromSearch(new URLSearchParams("page=before&hazard=x")),
    ).toEqual({
      page: "job",
    });
  });

  it("goes through each page of a hazard with controls, then to the review", () => {
    let stage: Stage = nextStage({ page: "job" }, COMPLETE_DRAFT);
    const seen = [stage];
    while (stage.page !== "review") {
      stage = nextStage(stage, COMPLETE_DRAFT);
      seen.push(stage);
    }
    expect(seen).toEqual([
      { page: "hazards" },
      { page: "before", hazard: 0 },
      { page: "controls", hazard: 0 },
      { page: "after", hazard: 0 },
      { page: "review" },
    ]);
  });

  it("skips the after page of a hazard with no controls, both ways", () => {
    expect(nextStage({ page: "controls", hazard: 0 }, NO_CONTROLS)).toEqual({
      page: "review",
    });
    expect(previousStage({ page: "review" }, NO_CONTROLS)).toEqual({
      page: "controls",
      hazard: 0,
    });
  });

  it("puts each field error on its own page", () => {
    expect(stageOfError("location")).toEqual({ page: "job" });
    expect(stageOfError("hazards")).toEqual({ page: "hazards" });
    expect(stageOfError("hazards.1.description")).toEqual({ page: "hazards" });
    expect(stageOfError("hazards.1.before.likelihood")).toEqual({
      page: "before",
      hazard: 1,
    });
    expect(stageOfError("hazards.0.controls.2.kind")).toEqual({
      page: "controls",
      hazard: 0,
    });
    expect(stageOfError("hazards.0.after")).toEqual({
      page: "after",
      hazard: 0,
    });
  });

  it("sends a page for a removed hazard back to the list", () => {
    expect(shownStage({ page: "before", hazard: 3 }, COMPLETE_DRAFT)).toEqual({
      page: "hazards",
    });
    expect(shownStage({ page: "after", hazard: 0 }, NO_CONTROLS)).toEqual({
      page: "controls",
      hazard: 0,
    });
  });
});
