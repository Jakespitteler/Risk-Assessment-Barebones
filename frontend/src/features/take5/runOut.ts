import type { FieldError } from "../../api/take5";

// The back end puts its "this draft has run out" error on this field (spec K2).
const RUN_OUT_PATH = "started_at";

/** The back end's message saying a draft has run out, if these errors include it. */
export function runOutMessage(errors: FieldError[] | undefined): string | null {
  return errors?.find((error) => error.path === RUN_OUT_PATH)?.message ?? null;
}
