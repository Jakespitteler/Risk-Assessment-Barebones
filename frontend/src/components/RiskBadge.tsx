// Colours for the booklet's bands. A band from another matrix gets the plain style.
const BAND_STYLES: Record<string, string> = {
  Low: "bg-green-700 text-white",
  Moderate: "bg-yellow-300 text-black",
  High: "bg-orange-500 text-black",
  Extreme: "bg-red-700 text-white",
};
const UNKNOWN_BAND_STYLE = "bg-slate-800 text-white";

/** A score with its band. The two are always shown together (spec F3). */
export function RiskBadge({ score, band }: { score: number; band: string }) {
  const style = BAND_STYLES[band] ?? UNKNOWN_BAND_STYLE;
  return (
    <p className={`flex items-baseline gap-3 rounded-xl px-5 py-4 ${style}`}>
      <span className="text-4xl font-bold">{score}</span>
      <span className="text-2xl font-semibold">{band}</span>
    </p>
  );
}
