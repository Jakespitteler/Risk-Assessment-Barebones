import { act, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { afterEach, expect, it, vi } from "vitest";
import {
  COMPLETE_DRAFT,
  SAVED,
  STOPPED,
  quickClient,
  stubApi,
} from "../test-utils";
import {
  ApiError,
  useCheckDraft,
  useSavedTake5,
  useSubmitTake5,
} from "./take5";

afterEach(() => {
  vi.unstubAllGlobals();
});

function wrapper(client: QueryClient) {
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
}

it("puts the saved Take 5 straight into the result screen's cache", async () => {
  const calls = stubApi({ "POST /api/take5s": { status: 200, body: SAVED } });
  const client = quickClient();
  const { result } = renderHook(() => useSubmitTake5(), {
    wrapper: wrapper(client),
  });

  await act(() =>
    result.current.mutateAsync({ id: SAVED.take5.id, draft: COMPLETE_DRAFT }),
  );

  expect(client.getQueryData(["take5", SAVED.take5.id])).toEqual(SAVED);
  expect(calls).toEqual(["POST /api/take5s"]);
});

it("reads the fixed Take 5 again once its fix is saved, so it shows the link", async () => {
  const fix = {
    ...SAVED,
    take5: { ...SAVED.take5, fixes: STOPPED.take5.id },
  };
  const fixed = { ...STOPPED, fixed_by: fix.take5.id };
  const path = `GET /api/take5s/${STOPPED.take5.id}`;
  const calls = stubApi({
    "POST /api/take5s": { status: 200, body: fix },
    [path]: { status: 200, body: fixed },
  });
  const client = quickClient();
  // The first result was on screen before the fix, so it is kept without a fix.
  client.setQueryData(["take5", STOPPED.take5.id], STOPPED);
  const submit = renderHook(() => useSubmitTake5(), {
    wrapper: wrapper(client),
  });

  await act(() =>
    submit.result.current.mutateAsync({
      id: fix.take5.id,
      draft: { ...COMPLETE_DRAFT, fixes: STOPPED.take5.id },
    }),
  );
  const first = renderHook(() => useSavedTake5(STOPPED.take5.id), {
    wrapper: wrapper(client),
  });

  await waitFor(() => {
    expect(first.result.current.data).toEqual(fixed);
  });
  expect(calls).toEqual(["POST /api/take5s", path]);
});

it("retries a save that got no answer, with the same ID", async () => {
  const calls = stubApi({
    "POST /api/take5s": ["offline", { status: 200, body: SAVED }],
  });
  const { result } = renderHook(() => useSubmitTake5(), {
    wrapper: wrapper(quickClient()),
  });

  await act(() =>
    result.current.mutateAsync({ id: SAVED.take5.id, draft: COMPLETE_DRAFT }),
  );

  expect(calls).toEqual(["POST /api/take5s", "POST /api/take5s"]);
  const bodies = vi.mocked(fetch).mock.calls.map(
    ([, init]) =>
      JSON.parse(typeof init?.body === "string" ? init.body : "{}") as {
        id: string;
      },
  );
  expect(bodies.map((body) => body.id)).toEqual([
    SAVED.take5.id,
    SAVED.take5.id,
  ]);
});

it("doesn't retry an answer, and keeps a 422's field errors", async () => {
  const calls = stubApi({
    "POST /api/take5s": {
      status: 422,
      body: {
        detail: "Fill in.",
        errors: [{ path: "job", message: "Fill in this field." }],
      },
    },
  });
  const { result } = renderHook(() => useSubmitTake5(), {
    wrapper: wrapper(quickClient()),
  });

  const error = await result.current
    .mutateAsync({ id: SAVED.take5.id, draft: COMPLETE_DRAFT })
    .catch((caught: unknown) => caught);

  expect(calls).toHaveLength(1);
  expect(error).toBeInstanceOf(ApiError);
  expect((error as ApiError).fieldErrors).toEqual([
    { path: "job", message: "Fill in this field." },
  ]);
});

it("retries reading a saved Take 5 when there is no signal", async () => {
  const path = `GET /api/take5s/${SAVED.take5.id}`;
  const calls = stubApi({ [path]: ["offline", { status: 200, body: SAVED }] });
  const { result } = renderHook(() => useSavedTake5(SAVED.take5.id), {
    wrapper: wrapper(quickClient()),
  });

  await waitFor(() => {
    expect(result.current.data).toEqual(SAVED);
  });
  expect(calls).toEqual([path, path]);
});

it("tries a Continue's check once, so no signal never keeps the worker waiting", async () => {
  const calls = stubApi({ "POST /api/take5s/check": "offline" });
  const { result } = renderHook(() => useCheckDraft(), {
    wrapper: wrapper(quickClient()),
  });

  await expect(result.current(COMPLETE_DRAFT)).rejects.toThrow(
    "Failed to fetch",
  );
  expect(calls).toEqual(["POST /api/take5s/check"]);
});
