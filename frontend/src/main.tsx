import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ApiProvider } from "./api/ApiProvider";
import { App } from "./app";
import "./index.css";

const rootElement = document.getElementById("root");
if (rootElement === null) {
  throw new Error("index.html has no element with the id 'root'.");
}

createRoot(rootElement).render(
  <StrictMode>
    <ApiProvider>
      <App />
    </ApiProvider>
  </StrictMode>,
);
