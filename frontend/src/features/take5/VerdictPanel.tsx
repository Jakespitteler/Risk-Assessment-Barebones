import type { Take5Response } from "../../api/take5";

/** The verdict, in colours as strong as the risk badge, so it reads in bright sun. */
export function VerdictPanel({
  verdict,
}: {
  verdict: Take5Response["take5"]["verdict"];
}) {
  return (
    <section
      className={`flex flex-col gap-3 rounded-2xl p-5 text-white ${
        verdict.can_start ? "bg-green-800" : "bg-red-800"
      }`}
    >
      <p className="text-sm font-bold tracking-wide uppercase">Your result</p>
      <h1 tabIndex={-1} className="text-4xl font-extrabold focus:outline-none">
        {verdict.can_start ? "Good to go" : "Don’t start yet"}
      </h1>
      {verdict.reasons.length > 0 ? (
        <ul className="flex list-disc flex-col gap-2 pl-5 text-lg font-semibold">
          {verdict.reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      ) : (
        <p className="text-lg">
          Keep these controls in place while you work. If the job changes, do a
          new Take 5.
        </p>
      )}
    </section>
  );
}
