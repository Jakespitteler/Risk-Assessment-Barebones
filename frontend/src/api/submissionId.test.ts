import { afterEach, expect, it, vi } from "vitest";
import { newSubmissionId } from "./submissionId";

const UUID_V4 =
  /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

afterEach(() => {
  vi.unstubAllGlobals();
});

it("makes a version 4 UUID even where crypto.randomUUID is missing (plain HTTP)", () => {
  vi.stubGlobal("crypto", {
    getRandomValues: (bytes: Uint8Array) => bytes.fill(0xff),
  });
  expect(newSubmissionId()).toMatch(UUID_V4);
});

it("makes a different ID each time", () => {
  expect(newSubmissionId()).not.toBe(newSubmissionId());
});
