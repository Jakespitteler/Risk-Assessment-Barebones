import type { KeyboardEvent } from "react";
import { useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Button } from "../../components/Button";
import { FIELD_STYLE } from "../../components/fieldStyle";

// A list longer than this gets a box to find a value in it.
const FIND_FROM = 8;
const FOCUSABLE = "button, input, [href], select, textarea";

/**
 * A column heading's filter, as a spreadsheet has: a button that opens the
 * column's values to tick (spec E6). A row with any ticked value is kept; none
 * ticked keeps every row. The list opens over the page, so a table that scrolls
 * sideways on a phone never cuts it off.
 */
export function ColumnFilter({
  title,
  choices,
  ticked,
  onApply,
}: {
  /** The column's heading, such as "Job". */
  title: string;
  /** Every value the column can be filtered by, as the back end sends them. */
  choices: string[];
  /** The values ticked now, as the page's address holds them. */
  ticked: string[];
  /** Called with the values ticked when the person presses Apply. */
  onApply: (ticked: string[]) => void;
}) {
  const [open, setOpen] = useState(false);
  const opener = useRef<HTMLButtonElement>(null);
  const close = () => {
    setOpen(false);
    opener.current?.focus();
  };
  return (
    <>
      <button
        ref={opener}
        type="button"
        aria-label={
          ticked.length > 0
            ? `Filter ${title}, ${String(ticked.length)} ticked`
            : `Filter ${title}`
        }
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={() => {
          setOpen(true);
        }}
        className={`-ml-3 inline-flex min-h-12 min-w-12 shrink-0 items-center justify-center gap-1 rounded-lg px-1 hover:bg-surface-hover focus-visible:outline-4 focus-visible:outline-focus ${ticked.length > 0 ? "bg-action text-on-action hover:bg-action-hover" : "text-ink"}`}
      >
        <FunnelPicture filled={ticked.length > 0} />
        {ticked.length > 0 && (
          <span className="text-sm font-bold">{ticked.length}</span>
        )}
      </button>
      {open &&
        createPortal(
          <TickList
            title={title}
            choices={choices}
            ticked={ticked}
            onClose={close}
            onApply={(chosen) => {
              onApply(chosen);
              close();
            }}
          />,
          document.body,
        )}
    </>
  );
}

/**
 * The open list of a column's values, each with a tick box. Ticks change only
 * when Apply is pressed; Cancel, Escape or a tap outside leave the filter as it was.
 */
function TickList({
  title,
  choices,
  ticked,
  onClose,
  onApply,
}: {
  title: string;
  choices: string[];
  ticked: string[];
  onClose: () => void;
  onApply: (ticked: string[]) => void;
}) {
  const headingId = useId();
  const panel = useRef<HTMLDivElement>(null);
  const [chosen, setChosen] = useState(ticked);
  const [found, setFound] = useState("");
  // A ticked value the back end no longer lists still shows, so it can be unticked.
  const values = [
    ...choices,
    ...ticked.filter((value) => !choices.includes(value)),
  ];
  const shown = values.filter((value) =>
    value.toLowerCase().includes(found.trim().toLowerCase()),
  );
  useEffect(() => {
    panel.current?.querySelector<HTMLElement>(FOCUSABLE)?.focus();
  }, []);
  // Escape closes, and Tab stays inside the list while it is open.
  const keepFocusInside = (event: KeyboardEvent) => {
    if (event.key === "Escape") {
      onClose();
      return;
    }
    if (event.key !== "Tab" || !panel.current) return;
    const stops = [
      ...panel.current.querySelectorAll<HTMLElement>(FOCUSABLE),
    ].filter((stop) => !stop.hasAttribute("disabled"));
    const first = stops[0];
    const last = stops[stops.length - 1];
    // A tap on the list's background gives the list itself the focus.
    const onList = document.activeElement === panel.current;
    if (event.shiftKey && (onList || document.activeElement === first)) {
      event.preventDefault();
      last?.focus();
    } else if (!event.shiftKey && (onList || document.activeElement === last)) {
      event.preventDefault();
      first?.focus();
    }
  };
  const toggle = (value: string) => {
    setChosen((current) =>
      current.includes(value)
        ? current.filter((each) => each !== value)
        : [...current, value],
    );
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 sm:items-center"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby={headingId}
        // Focusable by a tap, so the focus never falls to the page behind, where
        // Escape and the Tab trap would stop working.
        tabIndex={-1}
        onKeyDown={keepFocusInside}
        className="flex max-h-[85vh] w-full flex-col gap-3 rounded-t-2xl border border-line bg-surface p-4 text-ink shadow-xl focus:outline-none sm:max-w-md sm:rounded-2xl"
      >
        <h2 id={headingId} className="text-xl font-extrabold">
          Filter {title.toLowerCase()}
        </h2>
        {values.length > FIND_FROM && (
          <input
            type="search"
            aria-label={`Find a ${title.toLowerCase()}`}
            placeholder="Find"
            className={FIELD_STYLE}
            value={found}
            onChange={(event) => {
              setFound(event.target.value);
            }}
          />
        )}
        <fieldset className="min-h-0 overflow-y-auto">
          <legend className="sr-only">{title} values to tick</legend>
          {shown.length === 0 && (
            <p className="py-2 text-ink-muted">
              {values.length === 0 ? "Nothing to filter yet." : "None found."}
            </p>
          )}
          {shown.map((value) => (
            <label
              key={value}
              className="flex min-h-12 cursor-pointer items-center gap-3 rounded-lg px-2 text-lg hover:bg-surface-hover"
            >
              <input
                type="checkbox"
                className="size-6 shrink-0 accent-action"
                checked={chosen.includes(value)}
                onChange={() => {
                  toggle(value);
                }}
              />
              <span className="break-words">{value}</span>
            </label>
          ))}
        </fieldset>
        <div className="flex flex-wrap items-center gap-3 border-t border-line pt-3">
          <Button
            onClick={() => {
              onApply(chosen);
            }}
          >
            Apply
          </Button>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="quiet"
            className="ml-auto self-center"
            disabled={chosen.length === 0}
            onClick={() => {
              setChosen([]);
            }}
          >
            Untick all
          </Button>
        </div>
      </div>
    </div>
  );
}

/** A funnel, the usual mark of a filter; filled while the column is filtered. */
function FunnelPicture({ filled }: { filled: boolean }) {
  return (
    <svg
      aria-hidden
      viewBox="0 0 24 24"
      className="size-5"
      fill={filled ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth={2}
      strokeLinejoin="round"
    >
      <path d="M3 5h18l-7 8.5V19l-4 2v-7.5L3 5Z" />
    </svg>
  );
}
