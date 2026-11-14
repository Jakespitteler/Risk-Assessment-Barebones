import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactNode } from "react";
import { vi } from "vitest";
import type {
  DraftCheck,
  HazardDraft,
  Take5Draft,
  Take5Response,
  TemplateResponse,
} from "./api/take5";

// A made-up card with two questions and a two-by-two matrix, so a test proves nothing
// about the booklet is built in.
export const SMALL_TEMPLATE: TemplateResponse = {
  name: "Example card",
  questions: [
    { id: "keys", text: "Have you got the gate keys?", role: "stop" },
    { id: "dogs", text: "Are there dogs on site?", role: "hazard" },
  ],
  answer_choices: ["Yes", "No", "N/A"],
  matrix: {
    likelihoods: ["Often", "Seldom"],
    consequences: ["Scratch", "Serious"],
    cells: [
      [
        { score: 2, band: "Medium" },
        { score: 4, band: "Severe" },
      ],
      [
        { score: 1, band: "Minimal" },
        { score: 3, band: "Medium" },
      ],
    ],
    jha_threshold: 4,
  },
  control_kinds: ["Isolate the hazard", "Wear PPE"],
  likelihood_guidance: [{ level: "Often", meaning: "Every week." }],
  consequence_guidance: [{ level: "Serious", meaning: "Hospital." }],
  control_guidance: "Strong controls work without relying on people.",
};

export const HAZARD_DRAFT: HazardDraft = {
  description: "Moving wheel",
  before: { likelihood: "Often", consequence: "Serious" },
  controls: [{ description: "Chock the wheel", kind: "Isolate the hazard" }],
  after: { likelihood: "Seldom", consequence: "Scratch" },
};

export const ANSWERS: Take5Draft["answers"] = { keys: "Yes", dogs: "No" };

export const COMPLETE_DRAFT: Take5Draft = {
  worker_name: "Sam Example",
  job: "Change tyre",
  location: "Example workshop",
  answers: ANSWERS,
  hazards: [HAZARD_DRAFT],
};

export const RATED_HAZARD = {
  description: "Moving wheel",
  before: {
    likelihood: "Often",
    consequence: "Serious",
    score: 4,
    band: "Severe",
  },
  controls: [
    { description: "Chock the wheel", kind: "Isolate the hazard" as const },
  ],
  after: {
    likelihood: "Seldom",
    consequence: "Scratch",
    score: 1,
    band: "Minimal",
  },
};

export const PASSING_CHECK: DraftCheck = {
  errors: [],
  warnings: [],
  can_submit: true,
  assessment: {
    template: SMALL_TEMPLATE,
    answers: ANSWERS,
    hazards: [RATED_HAZARD],
  },
};

export const SAVED: Take5Response = {
  take5: {
    id: "11111111-1111-4111-8111-111111111111",
    created_at: "2026-11-13T07:30:00Z",
    finished_at: "2026-11-13T07:30:00Z",
    worker_name: "Sam Example",
    job: "Change tyre",
    location: "Example workshop",
    template: SMALL_TEMPLATE,
    answers: ANSWERS,
    hazards: [RATED_HAZARD],
    verdict: { can_start: true, reasons: [] },
  },
  rating: {
    likelihood: "Seldom",
    consequence: "Scratch",
    score: 1,
    band: "Minimal",
  },
  fixed_by: null,
  offers_fix: false,
};

// A saved Don't start yet: its one hazard has no controls, so it is rated once.
export const STOPPED: Take5Response = {
  take5: {
    ...SAVED.take5,
    id: "22222222-2222-4222-8222-222222222222",
    hazards: [
      { ...RATED_HAZARD, controls: [], after: { ...RATED_HAZARD.before } },
    ],
    verdict: {
      can_start: false,
      reasons: ["Say how you will control: Moving wheel"],
    },
  },
  rating: { ...RATED_HAZARD.before },
  fixed_by: null,
  offers_fix: true,
};

type Reply = { status: number; body: unknown } | "offline";

/**
 * Answer the app's API calls in a test. Each route is "METHOD /path"; an array of
 * replies is used one by one, and the last one is kept for any later call.
 */
export function stubApi(routes: Record<string, Reply | Reply[]>) {
  const calls: string[] = [];
  const fetchStub = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = input instanceof Request ? input.url : input.toString();
    const route = `${init?.method ?? "GET"} ${url}`;
    calls.push(route);
    const replies = routes[route];
    const queue = Array.isArray(replies) ? replies : replies ? [replies] : [];
    const reply = (queue.length > 1 ? queue.shift() : queue[0]) ?? {
      status: 404,
      body: { detail: "Not stubbed." },
    };
    if (reply === "offline")
      return Promise.reject(new TypeError("Failed to fetch"));
    return Promise.resolve(
      new Response(JSON.stringify(reply.body), { status: reply.status }),
    );
  });
  vi.stubGlobal("fetch", fetchStub);
  return calls;
}

/** An API cache whose retries don't wait, so tests stay quick. */
export function quickClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retryDelay: 0 },
      mutations: { retryDelay: 0 },
    },
  });
}

/** Draw a component with a fresh API cache, with retries that don't wait. */
export function renderWithApi(ui: ReactNode, client = quickClient()) {
  return {
    client,
    ...render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>),
  };
}
