/** A link to the list of saved Take 5s, for the top bar. */
export function SavedListLink() {
  return (
    <a
      href="/take5s"
      className="flex min-h-12 items-center rounded-lg px-2 font-semibold whitespace-nowrap text-ink underline underline-offset-4 hover:decoration-2 hover:bg-surface-hover focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-focus"
    >
      Saved Take 5s
    </a>
  );
}
