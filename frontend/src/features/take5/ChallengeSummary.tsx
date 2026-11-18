import type { Challenge } from "../../api/take5";
import { Card } from "../../components/Card";

/** The question asked before the result, and the worker's answer, as they were saved. */
export function ChallengeSummary({ challenge }: { challenge: Challenge }) {
  return (
    <Card>
      <h2 className="text-xl font-bold">The question before you started</h2>
      <p className="text-lg font-semibold">{challenge.question}</p>
      <div>
        <p className="font-bold">Your answer</p>
        <p className="whitespace-pre-line">{challenge.answer}</p>
      </div>
    </Card>
  );
}
