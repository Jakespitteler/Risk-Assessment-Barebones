import { useEffect, useState } from "react";

/**
 * The value once it has stopped changing for `delayMs`. Lets a page ask the back end
 * about a draft after the worker pauses typing, not once for every key pressed.
 */
export function useSettledValue<T>(value: T, delayMs: number): T {
  const [settled, setSettled] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => {
      setSettled(value);
    }, delayMs);
    return () => {
      clearTimeout(timer);
    };
  }, [value, delayMs]);
  return settled;
}
