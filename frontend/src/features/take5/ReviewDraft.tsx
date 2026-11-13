import type { RiskMatrix, Take5Draft } from "../../api/take5";
import { lookUpCell } from "../../components/RatingPicker";
import { RiskBadge } from "../../components/RiskBadge";

/** Review the worker's own answers; the API alone determines whether work can start. */
export function ReviewDraft({
  draft,
  matrix,
}: {
  draft: Take5Draft;
  matrix: RiskMatrix;
}) {
  return (
    <div className="stack">
      <section className="card">
        <h2>The job</h2>
        <dl className="job-details">
          <dt>Name</dt>
          <dd>{draft.worker_name || "Not filled in"}</dd>
          <dt>Job</dt>
          <dd>{draft.job || "Not filled in"}</dd>
          <dt>Location</dt>
          <dd>{draft.location || "Not filled in"}</dd>
        </dl>
      </section>
      {draft.hazards.map((hazard, index) => {
        const before = lookUpCell(matrix, hazard.before ?? {});
        const after = hazard.controls.length
          ? lookUpCell(matrix, hazard.after ?? {})
          : before;
        return (
          <section className="card stack" key={index}>
            <p className="eyebrow">Hazard {index + 1}</p>
            <h2>{hazard.description || "Not described"}</h2>
            <div className="ratings-summary">
              <div>
                <h3>Before controls</h3>
                {before ? <RiskBadge {...before} /> : <p>Not rated</p>}
              </div>
              <div>
                <h3>After controls</h3>
                {after ? <RiskBadge {...after} /> : <p>Not rated</p>}
              </div>
            </div>
            <h3>Controls</h3>
            {hazard.controls.length ? (
              <ul className="answer-list">
                {hazard.controls.map((control, controlIndex) => (
                  <li key={controlIndex}>
                    <strong>{control.description || "Not described"}</strong>
                    <span>{control.kind || "Kind not selected"}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p>No controls listed.</p>
            )}
          </section>
        );
      })}
      {!draft.hazards.length && <p>No hazards listed.</p>}
      <p className="supporting">
        Read your answers against the job in front of you. Go back if anything
        needs changing.
      </p>
    </div>
  );
}
