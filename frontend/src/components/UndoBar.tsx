import { Button } from "./Button";

/** Says what was just removed, with a way to put it back. */
export function UndoBar({
  message,
  onUndo,
  onDismiss,
}: {
  message: string;
  onUndo: () => void;
  onDismiss: () => void;
}) {
  return (
    <div
      role="status"
      className="flex items-center gap-2 rounded-xl bg-action p-3 text-on-action"
    >
      <p className="grow font-semibold">{message}</p>
      <Button variant="secondary" onClick={onUndo} className="shrink-0">
        Undo
      </Button>
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Close"
        className="min-h-12 min-w-12 shrink-0 rounded-lg text-2xl hover:bg-action-hover focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-focus"
      >
        ×
      </button>
    </div>
  );
}
