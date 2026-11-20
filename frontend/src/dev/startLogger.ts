// Vite's terminal output while developing (task 0028). Not part of the app: only
// vite.config.ts imports this.
import { createLogger, type LogLevel, type Logger } from "vite";

const LOG_LEVELS: readonly LogLevel[] = ["info", "warn", "error", "silent"];
// Vite's own line when the back end doesn't answer: "http proxy error: <path>".
const PROXY_ERROR = /http proxy error: (\/[\w\-./?=&%]*)/;
const BACKEND_DOWN_CODES: readonly string[] = ["ECONNREFUSED", "ECONNRESET"];

/**
 * The `--logLevel` given on the command line, such as start.py's `warn`. Vite ignores
 * it once a config gives its own logger, so the logger has to read it itself.
 */
export function cliLogLevel(argv: readonly string[]): LogLevel {
  const given = argv[argv.indexOf("--logLevel") + 1];
  return LOG_LEVELS.find((level) => level === given) ?? "info";
}

/**
 * One short line in place of Vite's proxy error and stack trace when the back end
 * isn't answering, for example while it restarts. Null for any other error, which
 * keeps Vite's own words.
 */
export function backendDownMessage(
  message: string,
  error: unknown,
): string | null {
  const path = PROXY_ERROR.exec(message)?.[1];
  const code =
    typeof error === "object" && error !== null && "code" in error
      ? error.code
      : null;
  if (
    path === undefined ||
    typeof code !== "string" ||
    !BACKEND_DOWN_CODES.includes(code)
  ) {
    return null;
  }
  return `The back end isn't answering ${path}. If it doesn't come back, look for its error above.`;
}

/** Vite's own logger, at the command line's level, with the one-line proxy error. */
export function startLogger(argv: readonly string[] = process.argv): Logger {
  const logger = createLogger(cliLogLevel(argv));
  const logError = logger.error.bind(logger);
  logger.error = (message, options) => {
    const short = backendDownMessage(message, options?.error);
    if (short === null) {
      logError(message, options);
    } else {
      logError(short, { timestamp: options?.timestamp ?? true });
    }
  };
  return logger;
}
