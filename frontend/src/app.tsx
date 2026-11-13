import {
  createBrowserRouter,
  RouterProvider,
  useNavigate,
  useParams,
} from "react-router";
import { RateRiskScreen } from "./features/take5/RateRiskScreen";
import { NewTake5Screen } from "./features/take5/NewTake5Screen";
import { Take5ResultScreen } from "./features/take5/Take5ResultScreen";

function NewTake5Route() {
  const navigate = useNavigate();
  return (
    <NewTake5Screen
      onSaved={(id) => {
        void navigate(`/take5s/${id}`);
      }}
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
