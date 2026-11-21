// The app writes every date and time one way, the way Jake chose (2026-11-15), such as
// "14 Nov 2026, 6:52 pm". The time is the phone's own time zone.
const DATE_TIME = new Intl.DateTimeFormat("en-AU", {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

/** Write a date and time from the API, such as "14 Nov 2026, 6:52 pm". */
export function formatDateTime(isoDateTime: string): string {
  const parts = DATE_TIME.formatToParts(new Date(isoDateTime));
  const part = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((found) => found.type === type)?.value ?? "";
  // en-AU writes "June", "July" and "Sept"; every month is three letters here.
  const month = part("month").slice(0, 3);
  const dayPeriod = part("dayPeriod").toLowerCase();
  return `${part("day")} ${month} ${part("year")}, ${part("hour")}:${part("minute")} ${dayPeriod}`;
}

const AS_WRITTEN = new Intl.DateTimeFormat("en-AU", {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "numeric",
  minute: "2-digit",
  timeZone: "UTC",
});

/**
 * Write a date and time as the API wrote them, at their own offset, whatever the
 * phone's zone: the date written on a paper card, such as "3 Apr 2026", with its time,
 * such as "3 Apr 2026, 6:40 am", unless it is the start of the day, which is how a
 * card with no time is saved (spec P5).
 */
export function formatAsWritten(isoDateTime: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(isoDateTime);
  if (!match) return formatDateTime(isoDateTime);
  const [, year, month, day, hour, minute] = match.map(Number);
  const asWritten = new Date(
    Date.UTC(year ?? 0, (month ?? 1) - 1, day ?? 1, hour ?? 0, minute ?? 0),
  );
  const parts = AS_WRITTEN.formatToParts(asWritten);
  const part = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((found) => found.type === type)?.value ?? "";
  const date = `${part("day")} ${part("month").slice(0, 3)} ${part("year")}`;
  if (hour === 0 && minute === 0) return date;
  return `${date}, ${part("hour")}:${part("minute")} ${part("dayPeriod").toLowerCase()}`;
}
