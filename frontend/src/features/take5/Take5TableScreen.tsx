import type { InputHTMLAttributes, ReactNode } from "react";
import { useEffect, useRef, useState } from "react";
import type { Take5Row, Take5TablePage } from "../../api/take5";
import { ApiError, take5TableCsvUrl, useTake5Table } from "../../api/take5";
import { Button } from "../../components/Button";
import { Field } from "../../components/Field";
import { FIELD_STYLE } from "../../components/fieldStyle";
import { Screen } from "../../components/Screen";
import { ColumnFilter } from "./ColumnFilter";
import { formatAsWritten, formatDateTime } from "./formatDateTime";
import { SavedListLink } from "./SavedListLink";

const HEADING = "text-3xl font-extrabold focus:outline-none";
// Typing waits this long after the last key before the table is asked again.
const SEARCH_PAUSE_MS = 400;
// The filters in the folded box above the table; the rest are in its columns.
const FILTERS_ABOVE = [
  "search",
  "from",
  "to",
  "weekday",
  "time_of_day",
  "from_paper",
];
// Each column heading's filter: its name in the address, and its values to tick,
// as the back end sends them (E6). The started column has none; the dates above
// cover it.
const COLUMN_FILTERS: Partial<
  Record<string, { name: string; choices: (page: Take5TablePage) => string[] }>
> = {
  Importance: {
    name: "importance",
    choices: (page) => page.importances.map(String),
  },
  Job: { name: "job", choices: (page) => page.jobs },
  Verdict: { name: "verdict", choices: (page) => page.verdicts },
  "Highest risk": { name: "band", choices: (page) => page.bands },
  "Thought gaps": {
    name: "thought_gaps",
    choices: (page) => page.thought_gap_choices,
  },
  Worker: { name: "worker", choices: (page) => page.workers },
  Location: { name: "area", choices: (page) => page.areas },
};
const DOWNLOAD_LINK =
  "flex min-h-14 items-center justify-center rounded-xl bg-action px-5 text-lg font-bold text-on-action hover:bg-action-hover focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-focus";

/**
 * Every saved Take 5 in one table, the most important first, with filters kept in the
 * page's address and a CSV of the same rows (spec F11, E1 to E6). Some filters sit
 * above the table and the rest under its column headings. The back end does the
 * filtering and works out every value; this page only draws them.
 */
export function Take5TableScreen({
  filters,
  onFilters,
}: {
  /** The filters, as the page's address holds them. */
  filters: URLSearchParams;
  /** Change the address's filters, which reloads the table. */
  onFilters: (filters: URLSearchParams) => void;
}) {
  const table = useTake5Table(filters);
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    heading.current?.focus();
  }, []);
  const set = (name: string, value: string) => {
    const changed = new URLSearchParams(filters);
    if (value) changed.set(name, value);
    else changed.delete(name);
    onFilters(changed);
  };
  const rows = table.data?.rows ?? [];
  const tick = (name: string, ticked: string[]) => {
    const changed = new URLSearchParams(filters);
    changed.delete(name);
    for (const value of ticked) changed.append(name, value);
    onFilters(changed);
  };
  // Clearing starts the search box afresh, even with typing not yet sent.
  const [cleared, setCleared] = useState(0);
  const clear = () => {
    setCleared((count) => count + 1);
    onFilters(new URLSearchParams());
  };
  const filtersAboveOn = FILTERS_ABOVE.filter((name) => filters.has(name));
  // Filters fill a phone's first screen, so they start folded there.
  const [filtersOpen] = useState(
    () => window.matchMedia("(min-width: 1024px)").matches,
  );
  const unreadableLink =
    table.error instanceof ApiError && table.error.status < 500;

  return (
    <Screen subtitle="Look back" aside={<SavedListLink />} wide>
      <h1 ref={heading} tabIndex={-1} className={HEADING}>
        All Take 5s
      </h1>
      <p>
        Every saved Take 5, the most important first: the riskiest jobs with the
        least thought in the answers. Narrow them down, then download the same
        rows to open in a spreadsheet.
      </p>
      <details
        open={filtersOpen}
        className="rounded-2xl border border-line bg-surface p-4"
      >
        <summary className="flex min-h-12 cursor-pointer items-center text-lg font-bold focus-visible:outline-4 focus-visible:outline-focus">
          Filters
          {filtersAboveOn.length > 0
            ? ` (${String(filtersAboveOn.length)} on)`
            : ""}
        </summary>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Field name="search" label="Find words">
            <TypedFilter
              key={cleared}
              id="search"
              type="search"
              className={FIELD_STYLE}
              value={filters.get("search") ?? ""}
              onSettle={(value) => {
                set("search", value);
              }}
            />
          </Field>
          <Field name="from" label="From">
            <input
              id="from"
              type="date"
              className={FIELD_STYLE}
              value={filters.get("from") ?? ""}
              onChange={(event) => {
                set("from", event.target.value);
              }}
            />
          </Field>
          <Field name="to" label="To">
            <input
              id="to"
              type="date"
              className={FIELD_STYLE}
              value={filters.get("to") ?? ""}
              onChange={(event) => {
                set("to", event.target.value);
              }}
            />
          </Field>
          <Choice
            name="weekday"
            label="Weekday"
            choices={table.data?.weekdays ?? []}
            filters={filters}
            onChoose={set}
          />
          <Choice
            name="time_of_day"
            label="Time of day"
            choices={table.data?.times_of_day ?? []}
            filters={filters}
            onChoose={set}
          />
          <Field name="from_paper" label="From paper">
            <select
              id="from_paper"
              className={FIELD_STYLE}
              value={filters.get("from_paper") ?? ""}
              onChange={(event) => {
                set("from_paper", event.target.value);
              }}
            >
              <option value="">Any</option>
              <option value="true">Paper cards only</option>
              <option value="false">Not paper cards</option>
            </select>
          </Field>
        </div>
      </details>
      {table.isError && !table.data ? (
        unreadableLink ? (
          <>
            <p>
              A filter in this page’s address can’t be read. Clear the filters
              and choose them again.
            </p>
            <Button onClick={clear}>Clear filters</Button>
          </>
        ) : (
          <>
            <p>
              The Take 5s couldn’t be loaded. Check your signal and try again.
            </p>
            <Button onClick={() => void table.refetch()}>Try again</Button>
          </>
        )
      ) : !table.data ? (
        <p role="status">Loading the Take 5s…</p>
      ) : (
        <>
          <p role="status" className="text-lg font-bold">
            {rows.length === 1
              ? "1 Take 5 matches."
              : `${String(rows.length)} Take 5s match.`}
          </p>
          <div className="grid grid-cols-1 gap-3 sm:flex">
            {/* While a new filter loads, the old rows still show, so the
                download waits for the rows it would hold. */}
            {rows.length > 0 && !table.isPlaceholderData && (
              <a
                className={`${DOWNLOAD_LINK} grow`}
                href={take5TableCsvUrl(filters)}
              >
                Download CSV
              </a>
            )}
            <Button
              variant="secondary"
              disabled={filters.size === 0}
              onClick={clear}
            >
              Clear filters
            </Button>
          </div>
          <RowsTable
            rows={rows}
            filterOf={(title) => {
              const column = COLUMN_FILTERS[title];
              if (!column) return null;
              return (
                <ColumnFilter
                  title={title}
                  choices={column.choices(table.data)}
                  ticked={filters.getAll(column.name)}
                  onApply={(ticked) => {
                    tick(column.name, ticked);
                  }}
                />
              );
            }}
          />
        </>
      )}
    </Screen>
  );
}

/** A filter with a fixed list of choices, and "Any" for no filter. */
function Choice({
  name,
  label,
  choices,
  filters,
  onChoose,
}: {
  name: string;
  label: string;
  choices: string[];
  filters: URLSearchParams;
  onChoose: (name: string, value: string) => void;
}) {
  return (
    <Field name={name} label={label}>
      <select
        id={name}
        className={FIELD_STYLE}
        value={filters.get(name) ?? ""}
        onChange={(event) => {
          onChoose(name, event.target.value);
        }}
      >
        <option value="">Any</option>
        {[
          ...choices,
          ...(filters.get(name) && !choices.includes(filters.get(name) ?? "")
            ? [filters.get(name) ?? ""]
            : []),
        ].map((choice) => (
          <option key={choice} value={choice}>
            {choice}
          </option>
        ))}
      </select>
    </Field>
  );
}

/**
 * A typed filter. It keeps its own text, so typing is never interrupted, and
 * passes it on once typing pauses. Only spaces is no filter, so it never rewrites
 * an address without one. When the address changes it by other means, such as
 * "Clear filters", the box shows the address's value.
 */
function TypedFilter({
  value,
  onSettle,
  ...box
}: {
  /** The filter as the address holds it. */
  value: string;
  /** Called with the text once typing pauses. */
  onSettle: (value: string) => void;
} & Omit<InputHTMLAttributes<HTMLInputElement>, "value" | "onChange">) {
  const [text, setText] = useState(value);
  // The address's value last seen, and the text last passed on, so the address
  // catching up with typing is told apart from a change made elsewhere.
  const [seen, setSeen] = useState(value);
  const [sent, setSent] = useState(value);
  if (value !== seen) {
    setSeen(value);
    if (value !== sent) setText(value);
  }
  useEffect(() => {
    const wanted = text.trim() ? text : "";
    if (wanted === value) return;
    const timer = setTimeout(() => {
      setSent(wanted);
      onSettle(wanted);
    }, SEARCH_PAUSE_MS);
    return () => {
      clearTimeout(timer);
    };
  });
  return (
    <input
      {...box}
      value={text}
      onChange={(event) => {
        setText(event.target.value);
      }}
    />
  );
}

/**
 * The rows as a table. On a phone it scrolls sideways in its own box, so the page
 * never does. The CSV holds every value; the table shows the ones to scan.
 */
function RowsTable({
  rows,
  filterOf,
}: {
  rows: Take5Row[];
  /** A column heading's filter button, or null for none. */
  filterOf: (title: string) => ReactNode;
}) {
  return (
    <div
      className="overflow-x-auto rounded-2xl border border-line bg-surface focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-focus"
      tabIndex={0}
      role="region"
      aria-label="Take 5s, the most important first"
    >
      <table className="w-full min-w-[56rem] border-collapse text-left">
        <thead className="bg-surface-subtle">
          <tr>
            {[
              "Importance",
              "Job",
              "Verdict",
              "Highest risk",
              "Thought gaps",
              "Worker",
              "Location",
              "Started",
            ].map((title) => (
              <th
                key={title}
                scope="col"
                className="px-3 py-2 align-bottom font-bold whitespace-nowrap"
              >
                <span className="flex items-center gap-1">
                  {title}
                  {filterOf(title)}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr className="border-t border-line">
              <td colSpan={8} className="px-3 py-4">
                No Take 5s match these filters.
              </td>
            </tr>
          )}
          {rows.map((row) => (
            <tr key={row.id} className="border-t border-line align-top">
              <td className="px-3 py-2 text-lg font-extrabold">
                {row.importance}
              </td>
              <td className="min-w-56 px-3 py-2">
                <a
                  href={`/take5s/${row.id}`}
                  className="inline-flex min-h-12 items-center font-semibold underline underline-offset-4 hover:decoration-2 focus-visible:outline-4 focus-visible:outline-focus"
                >
                  {row.job || "No job written"}
                </a>
                {row.from_paper && (
                  <span className="block text-sm text-ink-muted">
                    From paper
                  </span>
                )}
              </td>
              <td className="px-3 py-2">{row.verdict}</td>
              <td className="px-3 py-2">
                {row.highest_score === null
                  ? "Not rated"
                  : `${String(row.highest_score)} ${row.highest_band ?? ""}`}
                {row.needs_jha && (
                  <span className="block text-sm text-ink-muted">
                    Needs a JHA
                  </span>
                )}
              </td>
              <td className="px-3 py-2">
                {row.thought_gaps.length}
                {row.rushed && (
                  <span className="block text-sm text-ink-muted">Rushed</span>
                )}
              </td>
              <td className="px-3 py-2">{row.worker_name}</td>
              <td className="px-3 py-2">{row.location}</td>
              <td className="px-3 py-2 whitespace-nowrap">
                {row.started_at
                  ? row.from_paper
                    ? formatAsWritten(row.started_at)
                    : formatDateTime(row.started_at)
                  : formatDateTime(row.saved_at)}
                <span className="block text-sm text-ink-muted">
                  {row.weekday}
                  {row.time_of_day ? `, ${row.time_of_day.toLowerCase()}` : ""}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
