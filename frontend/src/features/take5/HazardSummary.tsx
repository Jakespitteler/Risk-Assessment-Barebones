import type { ReactNode } from "react";
import type { Hazard } from "../../api/take5";
import { Card } from "../../components/Card";
import { RiskBadge } from "../../components/RiskBadge";

/**
 * One rated hazard as the back end returned it: its ratings and its controls. Anything
 * the back end says about it, such as a warning, goes in `children` at the end.
 */
export function HazardSummary({
  hazard,
  number,
  children,
}: {
  hazard: Hazard;
  number: number;
  children?: ReactNode;
}) {
  const ratings = [
    { title: "Before controls", rating: hazard.before },
    { title: "After controls", rating: hazard.after },
  ];
  return (
    <Card>
      <p className="text-sm font-bold tracking-wide text-slate-700 uppercase">
        Hazard {number}
      </p>
      <h2 className="text-xl font-bold">{hazard.description}</h2>
      <div className="grid grid-cols-1 gap-4 min-[400px]:grid-cols-2">
        {ratings.map(({ title, rating }) => (
          <div key={title} className="flex flex-col gap-2">
            <h3 className="font-bold">{title}</h3>
            <p className="text-slate-700">
              {rating.likelihood} · {rating.consequence}
            </p>
            <RiskBadge score={rating.score} band={rating.band} />
          </div>
        ))}
      </div>
      <h3 className="font-bold">Controls</h3>
      {hazard.controls.length ? (
        <ul className="flex flex-col gap-2">
          {hazard.controls.map((control, index) => (
            <li
              key={index}
              className="flex flex-col border-l-4 border-slate-400 pl-3"
            >
              <strong>{control.description}</strong>
              <span className="text-slate-700">{control.kind}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p>No controls listed.</p>
      )}
      {children}
    </Card>
  );
}
