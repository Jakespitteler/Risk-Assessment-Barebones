import { useQuery } from "@tanstack/react-query";
import type { components } from "./schema";

/** The risk matrix as the back end sends it. The front end only looks things up in it. */
export type RiskMatrix = components["schemas"]["RiskMatrix"];
type TemplateResponse = components["schemas"]["TemplateResponse"];

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
