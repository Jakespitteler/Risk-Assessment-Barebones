// cspell:ignore mhttp
import { describe, expect, it, vi } from "vitest";
import { backendDownMessage, cliLogLevel, startLogger } from "./startLogger";

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

  it("reads the other ways Vite accepts the flag", () => {
    expect(cliLogLevel(["node", "vite", "--logLevel=error"])).toBe("error");
    expect(cliLogLevel(["node", "vite", "-l", "silent"])).toBe("silent");
  });

  it("is Vite's usual info when the command line gives none, or an unknown one", () => {
    expect(cliLogLevel(["node", "vite"])).toBe("info");
    expect(cliLogLevel(["node", "vite", "--logLevel", "loud"])).toBe("info");
  });
});

/** A stand-in console that records each line the logger prints. */
function recordingConsole() {
  const lines: string[] = [];
  const record = (...parts: unknown[]) => {
    lines.push(parts.map(String).join(" "));
  };
  const output = {
    ...console,
    log: vi.fn(record),
    warn: vi.fn(record),
    error: vi.fn(record),
  };
  return { output: output as Console, lines };
}

describe("startLogger", () => {
  it("prints the short line in place of Vite's proxy error and stack", () => {
    const { output, lines } = recordingConsole();

    startLogger(["node", "vite"], output).error(PROXY_ERROR, {
      error: Object.assign(new Error("connect"), { code: "ECONNREFUSED" }),
    });

    expect(lines).toHaveLength(1);
    expect(lines[0]).toContain(
      "The back end isn't answering /api/take5/template.",
    );
    expect(lines[0]).not.toContain("ECONNREFUSED 127.0.0.1");
  });

  it("passes every other error on in Vite's own words", () => {
    const { output, lines } = recordingConsole();

    startLogger(["node", "vite"], output).error(
      "[Unhandled error] SyntaxError: no such export",
    );

    expect(lines).toEqual(["[Unhandled error] SyntaxError: no such export"]);
  });

  it("never clears the screen, even for the same line twice on a terminal", () => {
    // Vite only clears on a real terminal outside CI, so act like one.
    const wasTerminal = process.stdout.isTTY;
    process.stdout.isTTY = true;
    vi.stubEnv("CI", "");
    const written = vi
      .spyOn(process.stdout, "write")
      .mockImplementation(() => true);
    try {
      const { output, lines } = recordingConsole();
      const logger = startLogger(["node", "vite"], output);
      const backendDown = {
        error: Object.assign(new Error("connect"), { code: "ECONNREFUSED" }),
      };

      logger.error(PROXY_ERROR, backendDown);
      logger.error(PROXY_ERROR, backendDown);

      expect(lines).toHaveLength(2);
      expect(lines.join("")).not.toContain("(x2)");
      expect(written).not.toHaveBeenCalled();
    } finally {
      written.mockRestore();
      vi.unstubAllEnvs();
      process.stdout.isTTY = wasTerminal;
    }
  });

  it("keeps the command line's level, so start.py's warn hides the address box", () => {
    const { output, lines } = recordingConsole();

    startLogger(["node", "vite", "--logLevel", "warn"], output).info(
      "  Local: http://localhost:5173/",
    );

    expect(lines).toEqual([]);
  });
});
