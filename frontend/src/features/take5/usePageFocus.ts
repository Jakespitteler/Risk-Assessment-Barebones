import { useEffect, useRef, useState } from "react";
import { focusFirstError } from "./focusFirstError";
import type { Stage } from "./stage";

/**
 * Move the focus when the page changes: to the new heading, so a screen reader starts
 * there, to the first error when the page was opened to fix one, or to a field the page
 * was opened to fill in.
 */
export function usePageFocus(stage: Stage) {
  const heading = useRef<HTMLHeadingElement>(null);
  const container = useRef<HTMLFormElement>(null);
  // The page whose first error takes the focus next. It is used once, then cleared.
  const errorsOn = useRef<string | null>(null);
  // The page, and the ID of the field on it, that takes the focus next. Used once.
  const fieldOn = useRef<{ stage: string; field: string } | null>(null);
  const [attempt, setAttempt] = useState(0);
  const stageKey = JSON.stringify(stage);

  useEffect(() => {
    const field = fieldOn.current?.stage === stageKey && fieldOn.current.field;
    fieldOn.current = null;
    if (errorsOn.current === stageKey) {
      errorsOn.current = null;
      focusFirstError(container.current);
    } else if (field) document.getElementById(field)?.focus();
    else heading.current?.focus();
  }, [stageKey, attempt]);

  return {
    heading,
    container,
    focusErrorsOn: (on: Stage) => {
      errorsOn.current = JSON.stringify(on);
      setAttempt((count) => count + 1);
    },
    focusFieldOn: (on: Stage, field: string) => {
      fieldOn.current = { stage: JSON.stringify(on), field };
    },
  };
}
