import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { components } from "./schema";

type Schemas = components["schemas"];
export type RiskMatrix = Schemas["RiskMatrix"];
export type TemplateResponse = Schemas["TemplateResponse"];
export type Take5Draft = Schemas["Take5Draft"];
export type HazardDraft = Schemas["HazardDraft"];
export type ControlDraft = Schemas["ControlDraft"];
export type RatingChoice = Schemas["RatingChoice"];
export type DraftCheck = Schemas["DraftCheck"];
export type FieldError = Schemas["FieldError"];
export type Hazard = Schemas["Hazard"];
export type Take5Response = Schemas["Take5Response"];
type FormErrors = Schemas["FormErrors"];

// Long enough for one bar of signal, short enough that the worker isn't left waiting.
const TIMEOUT_MS = 15_000;
const NETWORK_RETRIES = 3;

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

async function request<T>(url: string, body?: unknown): Promise<T> {
  const response = await fetch(url, {
    signal: AbortSignal.timeout(TIMEOUT_MS),
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
  });
}

function checkQuery(draft: Take5Draft) {
  return {
    queryKey: ["take5-check", draft],
    queryFn: () => request<DraftCheck>("/api/take5s/check", draft),
    staleTime: Infinity,
    retry: retryOnNetworkError,
  };
}

/** What the back end says is missing from a draft, and its ratings. Saves nothing. */
export function useDraftCheck(draft: Take5Draft) {
  return useQuery(checkQuery(draft));
}

/** Check a draft now, for a Continue button. The answer is kept for `useDraftCheck`. */
export function useCheckDraft() {
  const queryClient = useQueryClient();
  return (draft: Take5Draft) => queryClient.query(checkQuery(draft));
}

/**
 * Save a Take 5. The ID stays the same on every retry, so a retry after a lost answer
 * can't save it twice. The saved Take 5 goes straight into the result screen's cache.
 */
export function useSubmitTake5() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, draft }: { id: string; draft: Take5Draft }) =>
      request<Take5Response>("/api/take5s", { id, draft }),
    retry: retryOnNetworkError,
    onSuccess: (saved) => {
      queryClient.setQueryData(["take5", saved.take5.id], saved);
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
  });
}
