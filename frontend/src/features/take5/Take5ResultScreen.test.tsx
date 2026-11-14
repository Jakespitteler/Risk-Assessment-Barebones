import { fireEvent, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { Take5Response } from "../../api/take5";
import {
  SAVED,
  STOPPED,
  quickClient,
  renderWithApi,
  stubApi,
} from "../../test-utils";
import { Take5ResultScreen } from "./Take5ResultScreen";

afterEach(() => {
  vi.unstubAllGlobals();
});

it("shows a Take 5 already in the cache without asking the back end", () => {
  const calls = stubApi({});
  const client = quickClient();
  client.setQueryData(["take5", SAVED.take5.id], SAVED);
  renderWithApi(
    <Take5ResultScreen id={SAVED.take5.id} onFix={vi.fn()} />,
    client,
  );
  expect(screen.getByRole("heading", { name: "Good to go" })).toBeTruthy();
  expect(calls).toEqual([]);
});

it("shows the saved verdict, the overall rating and each hazard", async () => {
  stubApi({
    [`GET /api/take5s/${SAVED.take5.id}`]: { status: 200, body: SAVED },
  });
  renderWithApi(<Take5ResultScreen id={SAVED.take5.id} onFix={vi.fn()} />);
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

it("shows each of the card's questions with the worker's answer", async () => {
  stubApi({
    [`GET /api/take5s/${SAVED.take5.id}`]: { status: 200, body: SAVED },
  });
  renderWithApi(<Take5ResultScreen id={SAVED.take5.id} onFix={vi.fn()} />);
  expect(
    await screen.findByRole("heading", { name: "Thinking it through" }),
  ).toBeTruthy();
  expect(screen.getByText("Have you got the gate keys?")).toBeTruthy();
  expect(screen.getByText("Are there dogs on site?")).toBeTruthy();
});

it("still opens a Take 5 saved before the card had questions", async () => {
  const old: Take5Response = {
    ...SAVED,
    take5: {
      ...SAVED.take5,
      template: { ...SAVED.take5.template, questions: [] },
      answers: {},
    },
  };
  stubApi({
    [`GET /api/take5s/${SAVED.take5.id}`]: { status: 200, body: old },
  });
  renderWithApi(<Take5ResultScreen id={SAVED.take5.id} onFix={vi.fn()} />);
  expect(
    await screen.findByRole("heading", { name: "Good to go" }),
  ).toBeTruthy();
  expect(screen.getByRole("heading", { name: "Moving wheel" })).toBeTruthy();
  expect(
    screen.queryByRole("heading", { name: "Thinking it through" }),
  ).toBeNull();
});

it("says a Take 5 that doesn't exist can't be found, with no Try again", async () => {
  stubApi({
    [`GET /api/take5s/${SAVED.take5.id}`]: {
      status: 404,
      body: { detail: "This Take 5 could not be found." },
    },
  });
  renderWithApi(<Take5ResultScreen id={SAVED.take5.id} onFix={vi.fn()} />);
  expect(
    await screen.findByRole("heading", {
      name: "This Take 5 couldn’t be found",
    }),
  ).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Try again" })).toBeNull();
});

/** Draw the result screen for a Take 5 that is already in the cache. */
function showResult(saved: Take5Response, onFix = vi.fn()) {
  stubApi({});
  const client = quickClient();
  client.setQueryData(["take5", saved.take5.id], saved);
  renderWithApi(
    <Take5ResultScreen id={saved.take5.id} onFix={onFix} />,
    client,
  );
}

it("links to the list of saved Take 5s", () => {
  showResult(SAVED);
  expect(
    screen.getByRole("link", { name: "Saved Take 5s" }).getAttribute("href"),
  ).toBe("/take5s");
});

it("offers to fix a Don't start yet in a new Take 5", () => {
  const onFix = vi.fn();
  showResult(STOPPED, onFix);
  fireEvent.click(
    screen.getByRole("button", { name: "Fix this in a new Take 5" }),
  );
  expect(onFix).toHaveBeenCalledWith(STOPPED.take5);
});

it("doesn't offer a fix for a Good to go", () => {
  showResult(SAVED);
  expect(
    screen.queryByRole("button", { name: "Fix this in a new Take 5" }),
  ).toBeNull();
});

it("links a fixed Take 5 to its fix instead of offering another", () => {
  const fixId = SAVED.take5.id;
  showResult({ ...STOPPED, fixed_by: fixId, offers_fix: false });
  expect(
    screen
      .getByRole("link", { name: "Open the Take 5 that fixes it" })
      .getAttribute("href"),
  ).toBe(`/take5s/${fixId}`);
  expect(
    screen.queryByRole("button", { name: "Fix this in a new Take 5" }),
  ).toBeNull();
});

it("offers to fix a fix that is itself a Don't start yet, and links back", () => {
  const firstId = SAVED.take5.id;
  showResult({ ...STOPPED, take5: { ...STOPPED.take5, fixes: firstId } });
  expect(
    screen.getByRole("link", { name: "Open the Take 5 it fixes" }),
  ).toBeTruthy();
  expect(
    screen.getByRole("button", { name: "Fix this in a new Take 5" }),
  ).toBeTruthy();
});

it("links a fix back to the Take 5 it fixes", () => {
  showResult({ ...SAVED, take5: { ...SAVED.take5, fixes: STOPPED.take5.id } });
  expect(
    screen
      .getByRole("link", { name: "Open the Take 5 it fixes" })
      .getAttribute("href"),
  ).toBe(`/take5s/${STOPPED.take5.id}`);
});
