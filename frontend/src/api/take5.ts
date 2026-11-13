import { useQuery } from "@tanstack/react-query";
import type { components } from "./schema";

/** The risk matrix as the back end sends it. The front end only looks things up in it. */
export type RiskMatrix = components["schemas"]["RiskMatrix"];
export type TemplateResponse = components["schemas"]["TemplateResponse"];
export type Take5Draft = components["schemas"]["Take5Draft"];
export type HazardDraft = components["schemas"]["HazardDraft"];
export type ControlDraft = components["schemas"]["ControlDraft"];
export type RatingChoice = components["schemas"]["RatingChoice"];
export type DraftCheck = components["schemas"]["DraftCheck"];
export type FieldError = components["schemas"]["FieldError"];
export type Take5Response = components["schemas"]["Take5Response"];

/** Retains HTTP status so an ambiguous submission can be reopened safely. */
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(url: string, body?: unknown): Promise<T> {
  const response = await fetch(
    url,
    body === undefined
      ? undefined
      : {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
  );
  if (!response.ok)
    throw new ApiError(
      response.status,
      "The request could not be completed. Check your signal and try again.",
    );
  return (await response.json()) as T;
}

/** Check the completed draft without saving it. */
export function checkDraft(draft: Take5Draft) {
  return request<DraftCheck>("/api/take5s/check", draft);
}

/** Retry with the same ID so a lost response cannot duplicate an assessment. */
export function submitTake5(id: string, draft: Take5Draft) {
  return request<Take5Response>("/api/take5s", { id, draft });
}

/** Open the stored verdict instead of calculating a new one on the phone. */
export function useSavedTake5(id: string) {
  return useQuery({
    queryKey: ["take5", id],
    queryFn: () =>
      request<Take5Response>(`/api/take5s/${encodeURIComponent(id)}`),
    retry: false,
  });
}

async function fetchTemplate(): Promise<TemplateResponse> {
  const response = await fetch("/api/take5/template");
  if (!response.ok) {
    throw new Error(
      `The card could not be loaded (HTTP ${String(response.status)}).`,
    );
  }
  return (await response.json()) as TemplateResponse;
}

/** The card a new Take 5 is filled in on, fetched once and kept while the app is open. */
export function useTemplate() {
  return useQuery({
    queryKey: ["take5-template"],
    queryFn: fetchTemplate,
    staleTime: Infinity,
  });
}
