import { useEffect, useRef, useState } from "react";
import {
  createBrowserRouter,
  RouterProvider,
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router";
import { NewTake5Screen } from "./features/take5/NewTake5Screen";
import { RateRiskScreen } from "./features/take5/RateRiskScreen";
import { SavedTake5sScreen } from "./features/take5/SavedTake5sScreen";
import { Take5ResultScreen } from "./features/take5/Take5ResultScreen";
import { ReviewTodayScreen } from "./features/take5/ReviewTodayScreen";
import { ScanScreen } from "./features/scan/ScanScreen";
import { RiskByAreaScreen } from "./features/take5/RiskByAreaScreen";
import { Take5TableScreen } from "./features/take5/Take5TableScreen";
import { PatternsScreen } from "./features/take5/PatternsScreen";
import type { StoredDraft } from "./features/take5/useTake5Draft";
import {
  keepFixDraft,
  keptDraft,
  putBackDraft,
} from "./features/take5/useTake5Draft";
import { unansweredToOpen } from "./features/take5/unanswered";
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

/** Where to open the form: the page a kept draft was left on, unless the URL names one. */
function pageToCarryOnFrom(search: URLSearchParams): Stage | null {
  return search.has("page") ? null : (keptDraft()?.stage ?? null);
}

/**
 * The Take 5 whose question to go back to as the app opens: the newest one this phone
 * submitted and hasn't answered, unless a draft is kept or the URL names a page.
 */
function questionToGoBackTo(search: URLSearchParams): string | null {
  return search.has("page") || keptDraft() ? null : unansweredToOpen();
}

// The form's page is in the URL, so the phone's back gesture steps back a page. Opening
// the app with a kept draft carries on from the page it was left on, and with an
// unanswered question goes back to it (spec C6).
function NewTake5Route() {
  const navigate = useNavigate();
  const [search, setSearch] = useSearchParams();
  const [carryOnFrom] = useState(() => pageToCarryOnFrom(search));
  const [unansweredId] = useState(() => questionToGoBackTo(search));
  useEffect(() => {
    if (unansweredId)
      void navigate(`/take5s/${unansweredId}`, { replace: true });
  }, [unansweredId, navigate]);
  const goTo = (stage: Stage, options?: { replace: boolean }) => {
    setSearch(stageToSearch(stage), options);
  };
  // Put the page in the URL once, so the back gesture works from there as usual.
  const carriedOn = useRef(false);
  useEffect(() => {
    if (!carryOnFrom || carriedOn.current) return;
    carriedOn.current = true;
    setSearch(stageToSearch(carryOnFrom), { replace: true });
  }, [carryOnFrom, setSearch]);
  if (unansweredId) return null;
  return (
    <NewTake5Screen
      stage={
        search.has("page")
          ? stageFromSearch(search)
          : (carryOnFrom ?? stageFromSearch(search))
      }
      onStageChange={goTo}
      onBack={(fallback) => {
        if (canGoBack()) void navigate(-1);
        else goTo(fallback, { replace: true });
      }}
      // Replace the form, so going back from the result doesn't reopen the saved answers.
      onSaved={(id) => void navigate(`/take5s/${id}`, { replace: true })}
      // A thrown-away draft replaces the form, so the back gesture can't reopen it empty.
      onLeave={(thrownAway) =>
        void navigate("/take5s", {
          state: thrownAway && { thrownAway },
          replace: thrownAway !== null,
        })
      }
    />
  );
}

/** The draft just thrown away, if the list was opened by throwing one away. */
function thrownAwayIn(state: unknown): StoredDraft | null {
  return typeof state === "object" && state !== null && "thrownAway" in state
    ? (state.thrownAway as StoredDraft)
    : null;
}

// Throwing a draft away opens the list with Undo, which keeps the draft again and
// opens it, unless a newer one has been started since.
function SavedTake5sRoute() {
  const navigate = useNavigate();
  const location = useLocation();
  return (
    <SavedTake5sScreen
      thrownAway={thrownAwayIn(location.state)}
      onUndoThrowAway={(draft) => {
        putBackDraft(draft);
        void navigate("/", { replace: true });
      }}
      onDismissUndo={() => void navigate("/take5s", { replace: true })}
    />
  );
}

function SavedTake5Route() {
  const { id } = useParams();
  const navigate = useNavigate();
  return (
    <Take5ResultScreen
      id={id ?? ""}
      // The copy opens on the review, where its warnings point at what to fix.
      onFix={(take5) => {
        keepFixDraft(take5);
        void navigate(
          `/?${new URLSearchParams(stageToSearch({ page: "review" })).toString()}`,
        );
      }}
    />
  );
}

// The table's filters are in the URL, so a link opens the same view (spec F11). Each
// change replaces the address, so the back gesture leaves the page.
function Take5TableRoute() {
  const [search, setSearch] = useSearchParams();
  return (
    <Take5TableScreen
      filters={search}
      onFilters={(filters) => {
        setSearch(filters, { replace: true });
      }}
    />
  );
}

// Every screen and its URL. The only place React Router is set up.
const router = createBrowserRouter([
  { path: "/", element: <NewTake5Route /> },
  { path: "/take5s", element: <SavedTake5sRoute /> },
  { path: "/take5s/:id", element: <SavedTake5Route /> },
  { path: "/review-today", element: <ReviewTodayScreen /> },
  { path: "/risk-by-area", element: <RiskByAreaScreen /> },
  { path: "/rate-risk", element: <RateRiskScreen /> },
  { path: "/scan", element: <ScanScreen /> },
  { path: "/take5-table", element: <Take5TableRoute /> },
  { path: "/patterns", element: <PatternsScreen /> },
]);

export function App() {
  return <RouterProvider router={router} />;
}
