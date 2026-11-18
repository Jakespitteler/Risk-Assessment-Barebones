import { Notice } from "../../components/Notice";

export type Problem = "unsent" | "conflict";

/** Why the Take 5 may not be saved, and what the worker can do about it. */
export function SaveProblem({
  problem,
  submissionId,
}: {
  problem: Problem;
  submissionId: string;
}) {
  return (
    <Notice>
      {problem === "conflict" ? (
        <>
          <p>This Take 5 was already saved with different answers.</p>
          <a
            className="flex min-h-12 items-center underline"
            href={`/take5s/${submissionId}`}
          >
            Open the saved Take 5
          </a>
        </>
      ) : (
        <p>
          Your answers are still here, but we couldn’t confirm your Take 5 was
          saved. Check your signal and press Submit again.
        </p>
      )}
    </Notice>
  );
}
