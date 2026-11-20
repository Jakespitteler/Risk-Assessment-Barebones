// cspell:ignore mhttp
import { describe, expect, it } from "vitest";
import { backendDownMessage, cliLogLevel } from "./startLogger";

// Vite's own message, as it prints it, red, with the stack after it.
const PROXY_ERROR =
  "\u001b[31mhttp proxy error: /api/take5/template\u001b[39m\nError: connect ECONNREFUSED 127.0.0.1:8000\n    at ...";

describe("backendDownMessage", () => {
  it("turns the back end not answering into one line naming the path", () => {
    expect(backendDownMessage(PROXY_ERROR, { code: "ECONNREFUSED" })).toBe(
      "The back end isn't answering /api/take5/template. If it doesn't come back, look for its error above.",
    );
  });

  it("does the same when the back end drops the connection while restarting", () => {
    expect(
      backendDownMessage(PROXY_ERROR, { code: "ECONNRESET" }),
    ).not.toBeNull();
  });

  it("keeps Vite's own words for any other proxy error", () => {
    expect(backendDownMessage(PROXY_ERROR, { code: "ETIMEDOUT" })).toBeNull();
    expect(backendDownMessage(PROXY_ERROR, undefined)).toBeNull();
  });

  it("keeps Vite's own words for every error that isn't a proxy error", () => {
    expect(
      backendDownMessage("[Unhandled error] SyntaxError: no such export", {
        code: "ECONNREFUSED",
      }),
    ).toBeNull();
  });
});

describe("cliLogLevel", () => {
  it("reads start.py's --logLevel, which Vite ignores once a config gives a logger", () => {
    expect(cliLogLevel(["node", "vite", "--logLevel", "warn"])).toBe("warn");
  });

  it("is Vite's usual info when the command line gives none, or an unknown one", () => {
    expect(cliLogLevel(["node", "vite"])).toBe("info");
    expect(cliLogLevel(["node", "vite", "--logLevel", "loud"])).toBe("info");
  });
});
