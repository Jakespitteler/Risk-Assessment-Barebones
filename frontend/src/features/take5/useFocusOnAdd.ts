import { useEffect, useRef } from "react";

/**
 * Put the cursor in a box the worker has just added with an Add button. Undo can make
 * the list longer too, but only an Add moves the focus.
 *
 * Args:
 *     count: How many items the list has.
 *     lastBoxId: The ID of the last item's text box.
 *
 * Returns:
 *     A function the Add button calls as it adds an item.
 */
export function useFocusOnAdd(count: number, lastBoxId: string): () => void {
  const added = useRef(false);
  useEffect(() => {
    if (!added.current) return;
    added.current = false;
    document.getElementById(lastBoxId)?.focus();
  }, [count, lastBoxId]);
  return () => {
    added.current = true;
  };
}
