import type { ReactNode } from "react";
import type { Hazard } from "../../api/take5";
import { Card } from "../../components/Card";
import { RiskBadge } from "../../components/RiskBadge";

/**
 * One rated hazard as the back end returned it: its ratings and its controls. Anything
 * the back end says about it, such as a warning, goes in `children` at the end. Only a
 * paper card can leave a rating or a control's kind blank (spec P1).
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
      <p className="text-sm font-bold tracking-wide text-ink-muted uppercase">
        Hazard {number}
      </p>
      <h2 className="text-xl font-bold">{hazard.description}</h2>
      <div className="grid grid-cols-1 gap-4 min-[400px]:grid-cols-2">
        {ratings.map(({ title, rating }) => (
          <div key={title} className="flex flex-col gap-2">
            <h3 className="font-bold">{title}</h3>
            {rating ? (
              <>
                <p className="text-ink-muted">
                  {rating.likelihood} · {rating.consequence}
                </p>
                <RiskBadge score={rating.score} band={rating.band} />
              </>
            ) : (
              <p className="text-ink-muted">Not rated</p>
            )}
          </div>
        ))}
      </div>
      <h3 className="font-bold">Controls</h3>
      {hazard.controls.length ? (
        <ul className="flex flex-col gap-2">
          {hazard.controls.map((control, index) => (
            <li
              key={index}
              className="flex flex-col border-l-4 border-line-strong pl-3"
            >
              <strong>{control.description}</strong>
              <span className="text-ink-muted">{control.kind}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p>No controls listed.</p>
      )}
      {hazard.weak_controls_reason && (
        <div>
          <h3 className="font-bold">Why stronger controls weren't possible</h3>
          <p className="whitespace-pre-wrap">{hazard.weak_controls_reason}</p>
        </div>
      )}
      {children}
    </Card>
  );
}
