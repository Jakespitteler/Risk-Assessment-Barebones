import { fireEvent, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { Take5Response } from "../../api/take5";
import {
  SAVED,
  STOPPED,
  UNANSWERED,
  keepSampleDraft,
  quickClient,
  renderWithApi,
  stubApi,
} from "../../test-utils";
import { Take5ResultScreen } from "./Take5ResultScreen";
import { answersHere, rememberUnanswered } from "./unanswered";

afterEach(() => {
  localStorage.clear();
  vi.unstubAllGlobals();
});

const UNANSWERED_URL = `/api/take5s/${UNANSWERED.take5.id}`;
const ANSWER_URL = `POST ${UNANSWERED_URL}/answer`;
const FINISHED: Take5Response = {
  ...SAVED,
  take5: { ...SAVED.take5, id: UNANSWERED.take5.id },
};

function openUnanswered() {
  renderWithApi(<Take5ResultScreen id={UNANSWERED.take5.id} onFix={vi.fn()} />);
}

async function answerWith(answer: string) {
  fireEvent.change(
    await screen.findByLabelText(
      "What stops the wheel moving while you work on it?",
    ),
    { target: { value: answer } },
  );
  fireEvent.click(screen.getByRole("button", { name: "Finish Take 5" }));
}

it("asks the question of an unfinished Take 5 on the phone that saved it", async () => {
  rememberUnanswered(UNANSWERED.take5.id);
  stubApi({ [`GET ${UNANSWERED_URL}`]: { status: 200, body: UNANSWERED } });
  openUnanswered();
  expect(
    await screen.findByRole("heading", {
      name: "One question before you start",
    }),
  ).toBeTruthy();
  expect(screen.queryByRole("heading", { name: "Good to go" })).toBeNull();
  expect(screen.queryByRole("button", { name: "Back" })).toBeNull();
});

it("shows the result, with the question and answer, once it is answered", async () => {
  rememberUnanswered(UNANSWERED.take5.id);
  const calls = stubApi({
    [`GET ${UNANSWERED_URL}`]: { status: 200, body: UNANSWERED },
    [ANSWER_URL]: { status: 200, body: FINISHED },
  });
  openUnanswered();
  await answerWith("Wheels chocked both sides");
  expect(
    await screen.findByRole("heading", { name: "Good to go" }),
  ).toBeTruthy();
  expect(
    screen.getByRole("heading", { name: "The question before you started" }),
  ).toBeTruthy();
  expect(screen.getByText("Wheels chocked both sides")).toBeTruthy();
  // The result's heading takes the focus, so a screen reader starts there.
  expect(document.activeElement).toBe(
    screen.getByRole("heading", { name: "Good to go" }),
  );
  expect(calls).toContain(ANSWER_URL);
  expect(answersHere(UNANSWERED.take5.id)).toBe(false);
});

it("names a short answer's problem beside the box, and stays on the question", async () => {
  rememberUnanswered(UNANSWERED.take5.id);
  stubApi({
    [`GET ${UNANSWERED_URL}`]: { status: 200, body: UNANSWERED },
    [ANSWER_URL]: {
      status: 422,
      body: {
        detail: "Answer the question before you finish.",
        errors: [
          {
            path: "answer",
            message:
              "Answer in at least four words: say what you'll check or do.",
          },
        ],
      },
    },
  });
  openUnanswered();
  await answerWith("Chocked both sides");
  expect(
    await screen.findByText(
      "Answer in at least four words: say what you'll check or do.",
    ),
  ).toBeTruthy();
  expect(
    screen
      .getByLabelText("What stops the wheel moving while you work on it?")
      .getAttribute("aria-invalid"),
  ).toBe("true");
});

it("says when the answer wasn't sent, so it can be sent again", async () => {
  rememberUnanswered(UNANSWERED.take5.id);
  stubApi({
    [`GET ${UNANSWERED_URL}`]: { status: 200, body: UNANSWERED },
    [ANSWER_URL]: "offline",
  });
  openUnanswered();
  await answerWith("Wheels chocked both sides");
  expect(
    await screen.findByText(
      "Your answer wasn’t sent. Check your signal and press Finish again.",
    ),
  ).toBeTruthy();
});

it("opens the result when the Take 5 was already answered", async () => {
  rememberUnanswered(UNANSWERED.take5.id);
  stubApi({
    [`GET ${UNANSWERED_URL}`]: [
      { status: 200, body: UNANSWERED },
      { status: 200, body: FINISHED },
    ],
    [ANSWER_URL]: {
      status: 409,
      body: {
        detail:
          "This Take 5 is already finished, so it can't be answered again.",
      },
    },
  });
  openUnanswered();
  await answerWith("Wheels chocked both sides");
  expect(
    await screen.findByRole("heading", { name: "Good to go" }),
  ).toBeTruthy();
});

it("shows another phone's unfinished Take 5 without a way to answer it", async () => {
  stubApi({ [`GET ${UNANSWERED_URL}`]: { status: 200, body: UNANSWERED } });
  openUnanswered();
  expect(
    await screen.findByRole("heading", { name: "Not finished yet" }),
  ).toBeTruthy();
  expect(
    screen.getByText("What stops the wheel moving while you work on it?"),
  ).toBeTruthy();
  expect(screen.queryByRole("textbox")).toBeNull();
  expect(screen.queryByRole("button", { name: "Finish Take 5" })).toBeNull();
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

it("links to the list of saved Take 5s, beside the subtitle Your Take 5", () => {
  showResult(SAVED);
  expect(screen.getByText("Your Take 5")).toBeTruthy();
  expect(
    screen.getByRole("link", { name: "Saved Take 5s" }).getAttribute("href"),
  ).toBe("/take5s");
});

it("writes when it was finished as the list does", () => {
  showResult(SAVED);
  expect(screen.getByText(/^13 Nov 2026, \d{1,2}:30 [ap]m$/)).toBeTruthy();
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

it("asks before a fix takes the place of the phone's unfinished Take 5", () => {
  localStorage.clear();
  keepSampleDraft();
  const onFix = vi.fn();
  showResult(STOPPED, onFix);
  fireEvent.click(
    screen.getByRole("button", { name: "Fix this in a new Take 5" }),
  );
  expect(onFix).not.toHaveBeenCalled();
  expect(
    screen.getByText(
      "You have an unfinished Take 5 for “Change tyre”. Fixing this one throws it away.",
    ),
  ).toBeTruthy();

  fireEvent.click(
    screen.getByRole("button", { name: "Keep my unfinished Take 5" }),
  );
  expect(
    screen.getByRole("button", { name: "Fix this in a new Take 5" }),
  ).toBeTruthy();

  fireEvent.click(
    screen.getByRole("button", { name: "Fix this in a new Take 5" }),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Throw it away and fix this" }),
  );
  expect(onFix).toHaveBeenCalledWith(STOPPED.take5);
  localStorage.clear();
});

it("says Carry on your Take 5 when the phone keeps an unfinished one", () => {
  localStorage.clear();
  keepSampleDraft();
  showResult(SAVED);
  expect(
    screen
      .getByRole("link", { name: "Carry on your Take 5" })
      .getAttribute("href"),
  ).toBe("/");
  expect(screen.queryByRole("link", { name: "Start a new Take 5" })).toBeNull();
  localStorage.clear();
});
