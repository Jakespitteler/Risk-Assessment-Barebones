import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Remove whatever the last test drew, so each test starts on an empty page.
afterEach(cleanup);
