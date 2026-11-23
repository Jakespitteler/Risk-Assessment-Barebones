import { useEffect, useRef } from "react";
import type { Take5Row } from "../../api/take5";
import { take5TableCsvUrl, useTake5Table } from "../../api/take5";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { Field } from "../../components/Field";
import { FIELD_STYLE } from "../../components/fieldStyle";
import { Screen } from "../../components/Screen";
import { formatAsWritten, formatDateTime } from "./formatDateTime";
import { SavedListLink } from "./SavedListLink";

const HEADING = "text-3xl font-extrabold focus:outline-none";
const VERDICTS = ["Good to go", "Don't start yet", "Not finished"];
const WEEKDAYS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];
const TIMES_OF_DAY = [
  "Midnight to 6 am",
  "6 am to noon",
  "Noon to 6 pm",
  "6 pm to midnight",
];
const DOWNLOAD_LINK =
  "flex min-h-14 items-center justify-center rounded-xl bg-action px-5 text-lg font-bold text-on-action hover:bg-action-hover focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-focus";

/**
 * Every saved Take 5 in one table, the most important first, with filters kept in the
 * page's address and a CSV of the same rows (spec F11, E1 to E5). The back end does
 * the filtering and works out every value; this page only draws them.
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
      <Card>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Field name="search" label="Find words">
            <input
              id="search"
              type="search"
              className={FIELD_STYLE}
              value={filters.get("search") ?? ""}
              onChange={(event) => {
                set("search", event.target.value);
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
            name="verdict"
            label="Verdict"
            choices={VERDICTS}
            filters={filters}
            onChoose={set}
          />
          <Choice
            name="band"
            label="Risk band"
            choices={table.data?.bands ?? []}
            filters={filters}
            onChoose={set}
          />
          <Choice
            name="area"
            label="Area"
            choices={table.data?.areas ?? []}
            filters={filters}
            onChoose={set}
          />
          <Choice
            name="weekday"
            label="Weekday"
            choices={WEEKDAYS}
            filters={filters}
            onChoose={set}
          />
          <Choice
            name="time_of_day"
            label="Time of day"
            choices={TIMES_OF_DAY}
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
        {filters.size > 0 && (
          <Button
            variant="quiet"
            onClick={() => {
              onFilters(new URLSearchParams());
            }}
          >
            Clear the filters
          </Button>
        )}
      </Card>
      {table.isError && !table.data ? (
        <>
          <p>
            The Take 5s couldn’t be loaded. Check your signal and try again.
          </p>
          <Button onClick={() => void table.refetch()}>Try again</Button>
        </>
      ) : !table.data ? (
        <p role="status">Loading the Take 5s…</p>
      ) : (
        <>
          <p role="status" className="text-lg font-bold">
            {rows.length === 1
              ? "1 Take 5 matches."
              : `${String(rows.length)} Take 5s match.`}
          </p>
          {rows.length > 0 && (
            <>
              <a className={DOWNLOAD_LINK} href={take5TableCsvUrl(filters)}>
                Download CSV
              </a>
              <RowsTable rows={rows} />
            </>
          )}
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
        {choices.map((choice) => (
          <option key={choice} value={choice}>
            {choice}
          </option>
        ))}
      </select>
    </Field>
  );
}

/**
 * The rows as a table. On a phone it scrolls sideways in its own box, so the page
 * never does. The CSV holds every value; the table shows the ones to scan.
 */
function RowsTable({ rows }: { rows: Take5Row[] }) {
  return (
    <div
      className="overflow-x-auto rounded-2xl border border-line bg-surface"
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
              <th key={title} scope="col" className="px-3 py-2 font-bold">
                {title}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-t border-line align-top">
              <td className="px-3 py-2 text-lg font-extrabold">
                {row.importance}
              </td>
              <td className="px-3 py-2">
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
