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
