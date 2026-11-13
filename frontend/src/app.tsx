import { createBrowserRouter, RouterProvider } from "react-router";
import { RateRiskScreen } from "./features/take5/RateRiskScreen";

// Every screen and its URL. The only place React Router is set up.
const router = createBrowserRouter([
  { path: "/", element: <RateRiskScreen /> },
]);

export function App() {
  return <RouterProvider router={router} />;
}
