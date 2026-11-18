import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import type { components } from "./schema";

type Schemas = components["schemas"];
export type RiskMatrix = Schemas["RiskMatrix"];
export type TemplateResponse = Schemas["TemplateResponse"];
export type Question = Schemas["Question"];
export type Answer = Schemas["Answer"];
export type Take5Draft = Schemas["Take5Draft"];
export type HazardDraft = Schemas["HazardDraft"];
export type ControlDraft = Schemas["ControlDraft"];
export type RatingChoice = Schemas["RatingChoice"];
export type DraftCheck = Schemas["DraftCheck"];
export type FieldError = Schemas["FieldError"];
export type FieldWarning = Schemas["FieldWarning"];
export type Hazard = Schemas["Hazard"];
export type Take5Response = Schemas["Take5Response"];
export type SavedTake5 = Schemas["SavedTake5"];
export type Take5Summary = Schemas["Take5Summary"];
type FormErrors = Schemas["FormErrors"];

// Long enough for one bar of signal, short enough that the worker isn't left waiting.
const TIMEOUT_MS = 10_000;
// A Continue waits for one short try only: with no signal the worker carries on.
const CONTINUE_TIMEOUT_MS = 5_000;
const NETWORK_RETRIES = 2;
// Always send the request, even when the phone says it is offline. TanStack's default
// pauses it until the phone is back online, which leaves the screen waiting for good.
const NETWORK_MODE = "always";

/** The API answered with an error. Only a 422 carries field errors. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
    readonly fieldErrors: FieldError[] = [],
  ) {
    super(message);
  }
}

async function request<T>(
  url: string,
  body?: unknown,
  timeoutMs = TIMEOUT_MS,
): Promise<T> {
  const response = await fetch(url, {
    signal: AbortSignal.timeout(timeoutMs),
    ...(body === undefined
      ? {}
      : {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }),
  });
  if (response.ok) return (await response.json()) as T;
  // Every error the API sends is declared in its OpenAPI description: 422 is FormErrors,
  // the others are ErrorMessage. Both have `detail`.
  const error = (await response
    .json()
    .catch(() => ({}))) as Partial<FormErrors>;
  throw new ApiError(
    response.status,
    error.detail ?? "Something went wrong.",
    error.errors ?? [],
  );
}

/** Retry when there was no answer, or the server failed; any other answer won't change. */
function retryOnNetworkError(failures: number, error: Error) {
  const answered = error instanceof ApiError && error.status < 500;
  return !answered && failures < NETWORK_RETRIES;
}

/** The card a new Take 5 is filled in on, fetched once and kept while the app is open. */
export function useTemplate() {
  return useQuery({
    queryKey: ["take5-template"],
    queryFn: () => request<TemplateResponse>("/api/take5/template"),
    staleTime: Infinity,
    retry: retryOnNetworkError,
    networkMode: NETWORK_MODE,
  });
}

function checkKey(draft: Take5Draft) {
  return ["take5-check", draft];
}

/**
 * What the back end says is missing from a draft, and its ratings. Saves nothing.
 * Only asks while `enabled`, so the review can share the answer with the Finish button.
 */
export function useDraftCheck(
  draft: Take5Draft,
  enabled = true,
  keepQuestion = false,
) {
  return useQuery({
    queryKey: checkKey(draft),
    queryFn: () => request<DraftCheck>("/api/take5s/check", draft),
    staleTime: Infinity,
    retry: retryOnNetworkError,
    networkMode: NETWORK_MODE,
    enabled,
    // Only the controls prompt retains old data during editing. Review and Finish
    // must wait for the check of the current draft, never a previous answer.
    placeholderData: keepQuestion ? keepPreviousData : undefined,
  });
}

/**
 * Check a kept draft once as it opens, to find out whether it has run out (spec K2).
 * One short try with its own cache entry, so it never holds up a Continue that checks the
 * same answers; if it can't get through, the next Continue or the review checks again.
 */
export function useOpeningCheck(draft: Take5Draft, enabled: boolean) {
  return useQuery({
    queryKey: ["take5-opening-check", draft],
    queryFn: () =>
      request<DraftCheck>("/api/take5s/check", draft, CONTINUE_TIMEOUT_MS),
    staleTime: Infinity,
    retry: false,
    networkMode: NETWORK_MODE,
    enabled,
  });
}

/**
 * Look up a saved Take 5 by ID, with one short try: the Take 5, or null when none is
 * saved with that ID or the back end can't be reached. A draft that has run out may
 * have been saved already, with the answer lost on its way back to the phone.
 */
export function useFindSaved() {
  const queryClient = useQueryClient();
  return (id: string) =>
    queryClient
      .query({
        queryKey: ["take5", id],
        queryFn: () =>
          request<Take5Response>(
            `/api/take5s/${encodeURIComponent(id)}`,
            undefined,
            CONTINUE_TIMEOUT_MS,
          ),
        staleTime: Infinity,
        retry: false,
        networkMode: NETWORK_MODE,
      })
      .catch(() => null);
}

/**
 * Check a draft now, for a Continue button: one short try, with no retry. The answer is
 * kept for `useDraftCheck`.
 */
export function useCheckDraft() {
  const queryClient = useQueryClient();
  return (draft: Take5Draft) =>
    queryClient.query({
      queryKey: checkKey(draft),
      queryFn: () =>
        request<DraftCheck>("/api/take5s/check", draft, CONTINUE_TIMEOUT_MS),
      staleTime: Infinity,
      retry: false,
      networkMode: NETWORK_MODE,
    });
}

/**
 * Save a Take 5. The ID stays the same on every retry, so a retry after a lost answer
 * can't save it twice. The saved Take 5 goes straight into the result screen's cache.
 * The Take 5 it fixes, if any, is read again when next opened, so it shows its fix.
 */
export function useSubmitTake5() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, draft }: { id: string; draft: Take5Draft }) =>
      request<Take5Response>("/api/take5s", { id, draft }),
    retry: retryOnNetworkError,
    networkMode: NETWORK_MODE,
    onSuccess: (saved) => {
      queryClient.setQueryData(["take5", saved.take5.id], saved);
      if (saved.take5.fixes)
        void queryClient.invalidateQueries({
          queryKey: ["take5", saved.take5.fixes],
        });
    },
  });
}

/** A saved Take 5, with the verdict the worker was given. */
export function useSavedTake5(id: string) {
  return useQuery({
    queryKey: ["take5", id],
    queryFn: () =>
      request<Take5Response>(`/api/take5s/${encodeURIComponent(id)}`),
    staleTime: Infinity,
    retry: retryOnNetworkError,
    networkMode: NETWORK_MODE,
  });
}

/**
 * Every saved Take 5, newest first. Asked for again each time the list opens, so a
 * Take 5 saved since then shows.
 */
export function useSavedTake5List() {
  return useQuery({
    queryKey: ["take5s"],
    queryFn: () => request<Take5Summary[]>("/api/take5s"),
    retry: retryOnNetworkError,
    networkMode: NETWORK_MODE,
  });
}
