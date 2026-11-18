// The Take 5s this phone submitted whose question isn't answered yet, newest last. Only
// the phone that submitted a Take 5 answers its question (decision D47).
const UNANSWERED_KEY = "take5-unanswered";
// Set once the app has been opened in this tab, so only opening the app goes back to an
// unanswered question, not every link to the start page (decision D46).
const OPENED_KEY = "take5-opened";

// Storage can be switched off on a phone, so every read and write may fail. Then the
// list is kept here instead, so the worker who just pressed Submit can still answer.
let idsWithoutStorage: string[] = [];

function readIds(): string[] {
  return [
    ...storedIds().filter((id) => !idsWithoutStorage.includes(id)),
    ...idsWithoutStorage,
  ];
}

function storedIds(): string[] {
  try {
    const stored: unknown = JSON.parse(
      localStorage.getItem(UNANSWERED_KEY) ?? "[]",
    );
    return Array.isArray(stored)
      ? stored.filter((id): id is string => typeof id === "string")
      : [];
  } catch {
    return [];
  }
}

function writeIds(ids: string[]) {
  idsWithoutStorage = idsWithoutStorage.filter((id) => ids.includes(id));
  try {
    if (ids.length === 0) localStorage.removeItem(UNANSWERED_KEY);
    else localStorage.setItem(UNANSWERED_KEY, JSON.stringify(ids));
  } catch {
    // The question can still be answered now; it just won't be found after a reload.
    idsWithoutStorage = ids;
  }
}

/** Remember that this phone submitted a Take 5 whose question isn't answered yet. */
export function rememberUnanswered(id: string) {
  writeIds([...readIds().filter((kept) => kept !== id), id]);
}

/** Forget a Take 5 once it is finished, here or anywhere else. */
export function forgetUnanswered(id: string) {
  writeIds(readIds().filter((kept) => kept !== id));
}

/** Whether this phone submitted this Take 5, so may answer its question. */
export function answersHere(id: string): boolean {
  return readIds().includes(id);
}

/**
 * The newest unanswered Take 5 to go back to as the app opens, or null. Only the first
 * call in a tab can return one, so a later link to the start page still starts a Take 5.
 */
export function unansweredToOpen(): string | null {
  try {
    if (sessionStorage.getItem(OPENED_KEY)) return null;
    sessionStorage.setItem(OPENED_KEY, "yes");
  } catch {
    return null;
  }
  return readIds().at(-1) ?? null;
}
