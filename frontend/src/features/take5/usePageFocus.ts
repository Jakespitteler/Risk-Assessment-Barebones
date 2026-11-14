import { useEffect, useRef, useState } from "react";
import { focusFirstError } from "./focusFirstError";
import type { Stage } from "./stage";

/**
 * Move the focus when the page changes: to the new heading, so a screen reader starts
 * there, or to the first error when the page was opened to fix one.
 */
export function usePageFocus(stage: Stage) {
  const heading = useRef<HTMLHeadingElement>(null);
  const container = useRef<HTMLFormElement>(null);
  // The page whose first error takes the focus next. It is used once, then cleared.
  const errorsOn = useRef<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const stageKey = JSON.stringify(stage);

  useEffect(() => {
    if (errorsOn.current === stageKey) {
      errorsOn.current = null;
      focusFirstError(container.current);
    } else heading.current?.focus();
  }, [stageKey, attempt]);

  return {
    heading,
    container,
    focusErrorsOn: (on: Stage) => {
      errorsOn.current = JSON.stringify(on);
      setAttempt((count) => count + 1);
    },
  };
}
