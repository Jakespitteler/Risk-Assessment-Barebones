/** Put the cursor in the first answer on the page that has an error. */
export function focusFirstError(container: HTMLElement | null) {
  const invalid = container?.querySelector<HTMLElement>(
    "[aria-invalid='true']",
  );
  // A group of radio buttons can't take the focus itself, so its first button does.
  const target =
    invalid instanceof HTMLFieldSetElement
      ? invalid.querySelector<HTMLElement>("input")
      : invalid;
  target?.focus();
}
