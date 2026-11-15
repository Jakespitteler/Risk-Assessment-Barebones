// The app writes every date and time one way, the way Jake chose (2026-11-15), such as
// "14 Nov 2026, 6:52 pm". The time is the phone's own time zone.
const DATE_TIME = new Intl.DateTimeFormat("en-AU", {
  dateStyle: "medium",
  timeStyle: "short",
});

/** Write a date and time from the API, such as "14 Nov 2026, 6:52 pm". */
export function formatDateTime(isoDateTime: string): string {
  return DATE_TIME.format(new Date(isoDateTime));
}
