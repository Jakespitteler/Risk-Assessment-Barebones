import { cleanup } from "@testing-library/react";
import { afterEach, beforeEach } from "vitest";
import { fakeMatchMedia, resetPhoneScheme } from "./test-phone-scheme";

// jsdom can't say whether the phone is set to dark, so each test gets a stand-in on a light phone.
beforeEach(() => {
  resetPhoneScheme();
  window.matchMedia = fakeMatchMedia;
});

// Remove whatever the last test drew, so each test starts on an empty page.
afterEach(cleanup);
