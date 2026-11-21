import {
  keepPreviousData,
  useInfiniteQuery,
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
export type Nudge = Schemas["Nudge"];
export type Hazard = Schemas["Hazard"];
export type Take5Response = Schemas["Take5Response"];
export type SavedTake5 = Schemas["SavedTake5"];
export type Take5Summary = Schemas["Take5Summary"];
export type Take5ListPage = Schemas["Take5ListPage"];
export type RankedTake5s = Schemas["RankedTake5s"];
export type RankedTake5Line = Schemas["RankedTake5Line"];
export type Verdict = Schemas["Verdict"];
export type Challenge = Schemas["Challenge"];
type FormErrors = Schemas["FormErrors"];

// Long enough for one bar of signal, short enough that the worker isn't left waiting.
const TIMEOUT_MS = 10_000;
// A Continue waits for one short try only: with no signal the worker carries on.
const CONTINUE_TIMEOUT_MS = 5_000;
// Submitting waits for the challenge question, which the back end gives the AI up to
// 10 seconds to write before it asks the fixed one (spec C3).
const SUBMIT_TIMEOUT_MS = 20_000;
// The ranking waits for the AI, which the back end gives up to 20 seconds to order
// the worst Take 5s before the fixed rules decide (spec W6).
const RANKING_TIMEOUT_MS = 30_000;
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
 * The back end's nudges to make vague hazards specific (spec T6). An AI may take a few
 * seconds to judge new words, so the last answer stays on screen until the next one
 * comes. Only asks while `enabled`.
 */
export function useHazardNudges(draft: Take5Draft, enabled: boolean) {
  return useQuery({
    queryKey: ["take5-nudges", draft],
    queryFn: () => request<Nudge[]>("/api/take5s/nudges", draft),
    staleTime: Infinity,
    retry: retryOnNetworkError,
    networkMode: NETWORK_MODE,
    enabled,
    placeholderData: keepPreviousData,
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
      request<Take5Response>("/api/take5s", { id, draft }, SUBMIT_TIMEOUT_MS),
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

/**
 * Answer a saved Take 5's challenge question, which finishes it with its verdict. The
 * same answer sent again gets the finished Take 5 back, so a retry is safe.
 */
export function useAnswerTake5(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (answer: string) =>
      request<Take5Response>(`/api/take5s/${encodeURIComponent(id)}/answer`, {
        answer,
      }),
    retry: retryOnNetworkError,
    networkMode: NETWORK_MODE,
    onSuccess: (finished) => {
      queryClient.setQueryData(["take5", id], finished);
    },
  });
}

/** A saved Take 5, with the verdict the worker was given, or its question. */
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
 * The saved Take 5s, newest first, a page of 50 at a time (spec D18). Each page after
 * the first is asked for with the last one already shown, so a Take 5 saved meanwhile
 * can't shift it. Asked for again each time the list opens, so a Take 5 saved since
 * then shows, and the pages already loaded are kept for a few minutes (D86).
 */
export function useSavedTake5List() {
  return useInfiniteQuery({
    queryKey: ["take5s"],
    queryFn: ({ pageParam }) =>
      request<Take5ListPage>(
        pageParam === null
          ? "/api/take5s"
          : `/api/take5s?before=${encodeURIComponent(pageParam)}`,
      ),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next,
    retry: retryOnNetworkError,
    networkMode: NETWORK_MODE,
  });
}

/**
 * Every Take 5 started since a moment, worst first, each with why (spec W1 to W7). The
 * moment is sent with its time zone, so "today" starts at midnight where the phone is.
 */
export function useRankedTake5s(since: string) {
  return useQuery({
    queryKey: ["ranked-take5s", since],
    queryFn: () =>
      request<RankedTake5s>(
        `/api/ranked-take5s?since=${encodeURIComponent(since)}`,
        undefined,
        RANKING_TIMEOUT_MS,
      ),
    // The page says it can take half a minute, so it isn't asked again on its own:
    // a failure shows "Try again", and the list doesn't reorder while it is read.
    retry: false,
    refetchOnWindowFocus: false,
    networkMode: NETWORK_MODE,
  });
}
