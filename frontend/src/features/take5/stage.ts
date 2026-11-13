import type { Take5Draft } from "../../api/take5";

// Which page of the form is showing. It lives in the URL, so the phone's back gesture
// steps back through the form instead of leaving it.
export type HazardPage = "before" | "controls" | "after";
export type Stage =
  { page: "job" | "hazards" | "review" } | { page: HazardPage; hazard: number };

export const FIRST_STAGE: Stage = { page: "job" };

const HAZARD_PAGES: readonly string[] = ["before", "controls", "after"];
const OTHER_PAGES: readonly string[] = ["job", "hazards", "review"];

/** Read the stage from a URL query such as `?page=before&hazard=0`. */
export function stageFromSearch(search: URLSearchParams): Stage {
  const page = search.get("page") ?? "";
  const hazard = Number(search.get("hazard"));
  if (HAZARD_PAGES.includes(page) && Number.isInteger(hazard) && hazard >= 0)
    return { page: page as HazardPage, hazard };
  if (OTHER_PAGES.includes(page))
    return { page: page as "job" | "hazards" | "review" };
  return FIRST_STAGE;
}

/** Write the stage as a URL query. */
export function stageToSearch(stage: Stage): Record<string, string> {
  return "hazard" in stage
    ? { page: stage.page, hazard: String(stage.hazard) }
    : { page: stage.page };
}

export function sameStage(first: Stage, second: Stage): boolean {
  return (
    first.page === second.page &&
    ("hazard" in first ? first.hazard : -1) ===
      ("hazard" in second ? second.hazard : -1)
  );
}

/** A stage the draft can show: a hazard that was removed sends the worker to the list. */
export function shownStage(stage: Stage, draft: Take5Draft): Stage {
  if (!("hazard" in stage)) return stage;
  const hazard = draft.hazards[stage.hazard];
  if (!hazard) return { page: "hazards" };
  if (stage.page === "after" && !hazard.controls.length)
    return { page: "controls", hazard: stage.hazard };
  return stage;
}

/** The last page of a hazard: its after rating, or its controls when it has none. */
function lastPageOf(draft: Take5Draft, hazard: number): Stage {
  return {
    page: draft.hazards[hazard]?.controls.length ? "after" : "controls",
    hazard,
  };
}

/** The page after this one. A hazard with no controls has no after page. */
export function nextStage(stage: Stage, draft: Take5Draft): Stage {
  switch (stage.page) {
    case "job":
      return { page: "hazards" };
    case "hazards":
      return draft.hazards.length ? { page: "before", hazard: 0 } : stage;
    case "before":
      return { page: "controls", hazard: stage.hazard };
    case "controls":
    case "after":
      if (
        stage.page === "controls" &&
        draft.hazards[stage.hazard]?.controls.length
      )
        return { page: "after", hazard: stage.hazard };
      return stage.hazard + 1 < draft.hazards.length
        ? { page: "before", hazard: stage.hazard + 1 }
        : { page: "review" };
    case "review":
      return stage;
  }
}

/** The page before this one. */
export function previousStage(stage: Stage, draft: Take5Draft): Stage {
  switch (stage.page) {
    case "job":
    case "hazards":
      return FIRST_STAGE;
    case "before":
      return stage.hazard === 0
        ? { page: "hazards" }
        : lastPageOf(draft, stage.hazard - 1);
    case "controls":
      return { page: "before", hazard: stage.hazard };
    case "after":
      return { page: "controls", hazard: stage.hazard };
    case "review":
      return draft.hazards.length
        ? lastPageOf(draft, draft.hazards.length - 1)
        : { page: "hazards" };
  }
}

/** The page a field error belongs on, from its dotted path such as `hazards.0.after`. */
export function stageOfError(path: string): Stage {
  const [first, index, field] = path.split(".");
  if (first !== "hazards") return FIRST_STAGE;
  const hazard = Number(index);
  if (field === "before" || field === "controls" || field === "after")
    return { page: field, hazard };
  return { page: "hazards" };
}

/** Which of the four steps a stage is part of, counting from 1. */
export function stepOf(stage: Stage): number {
  if (stage.page === "job") return 1;
  if (stage.page === "hazards") return 2;
  return stage.page === "review" ? 4 : 3;
}
