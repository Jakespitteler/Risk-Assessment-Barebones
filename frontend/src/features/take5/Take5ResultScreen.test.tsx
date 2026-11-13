import { screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { SAVED, quickClient, renderWithApi, stubApi } from "../../test-utils";
import { Take5ResultScreen } from "./Take5ResultScreen";

afterEach(() => {
  vi.unstubAllGlobals();
});

it("shows a Take 5 already in the cache without asking the back end", () => {
  const calls = stubApi({});
  const client = quickClient();
  client.setQueryData(["take5", SAVED.take5.id], SAVED);
  renderWithApi(<Take5ResultScreen id={SAVED.take5.id} />, client);
  expect(screen.getByRole("heading", { name: "Good to go" })).toBeTruthy();
  expect(calls).toEqual([]);
});

it("shows the saved verdict, the overall rating and each hazard", async () => {
  stubApi({
    [`GET /api/take5s/${SAVED.take5.id}`]: { status: 200, body: SAVED },
  });
  renderWithApi(<Take5ResultScreen id={SAVED.take5.id} />);
  expect(
    await screen.findByRole("heading", { name: "Good to go" }),
  ).toBeTruthy();
  expect(screen.getByRole("heading", { name: "Moving wheel" })).toBeTruthy();
  expect(
    screen.getByText(
      "Filled in on the Example card. It is kept as it was saved.",
    ),
  ).toBeTruthy();
});

it("says a Take 5 that doesn't exist can't be found, with no Try again", async () => {
  stubApi({
    [`GET /api/take5s/${SAVED.take5.id}`]: {
      status: 404,
      body: { detail: "This Take 5 could not be found." },
    },
  });
  renderWithApi(<Take5ResultScreen id={SAVED.take5.id} />);
  expect(
    await screen.findByRole("heading", {
      name: "This Take 5 couldn’t be found",
    }),
  ).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Try again" })).toBeNull();
});
