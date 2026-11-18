// The boxes a worker types words into. Radio buttons and lists are picked, not typed in.
const TEXT_BOXES = "textarea, input:not([type]), input[type='text']";

/**
 * Whether the main pointer is a mouse or trackpad, so the device has a keyboard of its
 * own. On a phone, moving the cursor into a box pops the keyboard up over the page.
 */
export function hasFinePointer(): boolean {
  return (
    typeof window.matchMedia === "function" &&
    window.matchMedia("(pointer: fine)").matches
  );
}

/**
 * Put the cursor in the first empty text box on the page, so typing goes straight in.
 *
 * Returns:
 *     Whether a box took the focus. False when every box is filled in, or there are none.
 */
export function focusFirstEmptyBox(container: HTMLElement | null): boolean {
  const boxes = container?.querySelectorAll<
    HTMLInputElement | HTMLTextAreaElement
  >(TEXT_BOXES);
  const empty = Array.from(boxes ?? []).find((box) => box.value === "");
  empty?.focus();
  return empty !== undefined;
}
