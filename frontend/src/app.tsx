import {
  createBrowserRouter,
  RouterProvider,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router";
import { NewTake5Screen } from "./features/take5/NewTake5Screen";
import { RateRiskScreen } from "./features/take5/RateRiskScreen";
import { Take5ResultScreen } from "./features/take5/Take5ResultScreen";
import type { Stage } from "./features/take5/stage";
import { stageFromSearch, stageToSearch } from "./features/take5/stage";

/** Whether the previous history entry belongs to this visit to the app. */
function canGoBack(): boolean {
  const state: unknown = window.history.state;
  return (
    typeof state === "object" &&
    state !== null &&
    "idx" in state &&
    typeof state.idx === "number" &&
    state.idx > 0
  );
}

// The form's page is in the URL, so the phone's back gesture steps back a page.
function NewTake5Route() {
  const navigate = useNavigate();
  const [search, setSearch] = useSearchParams();
  const goTo = (stage: Stage, options?: { replace: boolean }) => {
    setSearch(stageToSearch(stage), options);
  };
  return (
    <NewTake5Screen
      stage={stageFromSearch(search)}
      onStageChange={goTo}
      onBack={(fallback) => {
        if (canGoBack()) void navigate(-1);
        else goTo(fallback, { replace: true });
      }}
      // Replace the form, so going back from the result doesn't reopen the saved answers.
      onSaved={(id) => void navigate(`/take5s/${id}`, { replace: true })}
    />
  );
}

function SavedTake5Route() {
  const { id } = useParams();
  return <Take5ResultScreen id={id ?? ""} />;
}

// Every screen and its URL. The only place React Router is set up.
const router = createBrowserRouter([
  { path: "/", element: <NewTake5Route /> },
  { path: "/take5s/:id", element: <SavedTake5Route /> },
  { path: "/rate-risk", element: <RateRiskScreen /> },
]);

export function App() {
  return <RouterProvider router={router} />;
}
