import { afterEach, expect, it, vi } from "vitest";
import {
  answersHere,
  forgetUnanswered,
  rememberUnanswered,
  unansweredToOpen,
} from "./unanswered";

afterEach(() => {
  vi.restoreAllMocks();
  localStorage.clear();
  sessionStorage.clear();
});

it("answers only the Take 5s this phone submitted, until each is answered", () => {
  rememberUnanswered("first");
  rememberUnanswered("second");
  expect(answersHere("first")).toBe(true);
  expect(answersHere("another-phones")).toBe(false);
  forgetUnanswered("first");
  expect(answersHere("first")).toBe(false);
  expect(answersHere("second")).toBe(true);
});

it("goes back to the newest unanswered question only as the app opens", () => {
  rememberUnanswered("first");
  rememberUnanswered("second");
  expect(unansweredToOpen()).toBe("second");
  expect(unansweredToOpen()).toBeNull();
});

it("has nothing to go back to when every question is answered", () => {
  rememberUnanswered("first");
  forgetUnanswered("first");
  expect(unansweredToOpen()).toBeNull();
});

it("still lets this phone answer when its storage is switched off", () => {
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
    throw new Error("Storage is switched off.");
  });
  rememberUnanswered("first");
  expect(answersHere("first")).toBe(true);
  forgetUnanswered("first");
  expect(answersHere("first")).toBe(false);
});
