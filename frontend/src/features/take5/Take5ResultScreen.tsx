import { useSavedTake5 } from "../../api/take5";
import { RiskBadge } from "../../components/RiskBadge";

/** Show the exact saved verdict, ratings, controls and template after submission. */
export function Take5ResultScreen({ id }: { id: string }) {
  const result = useSavedTake5(id);
  if (result.isPending)
    return (
      <main className="page">
        <h1>Opening your Take 5…</h1>
      </main>
    );
  if (result.isError)
    return (
      <main className="page">
        <h1>This Take 5 could not be opened</h1>
        <p>Check the address and your signal, then try again.</p>
        <button
          className="button primary"
          onClick={() => void result.refetch()}
        >
          Try again
        </button>
        <a className="button secondary" href="/">
          Start a new Take 5
        </a>
      </main>
    );
  const { take5, rating } = result.data;
  return (
    <main className="page">
      <header className="brand">
        <span className="brand-mark">5</span>
        <div>
          <p className="eyebrow">TAKE 5</p>
          <strong>Assessment saved</strong>
        </div>
      </header>
      <section
        className={`verdict ${take5.verdict.can_start ? "can-start" : "do-not-start"}`}
      >
        <p className="eyebrow">YOUR RESULT</p>
        <h1>{take5.verdict.can_start ? "Good to go" : "Don’t start yet"}</h1>
        {take5.verdict.reasons.length > 0 ? (
          <ul className="answer-list">
            {take5.verdict.reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        ) : (
          <p>
            Keep these controls in place while you work. If the job changes, do
            a new Take 5.
          </p>
        )}
      </section>
      <section className="card stack">
        <h2>Overall risk after controls</h2>
        <RiskBadge {...rating} />
        <dl className="job-details">
          <dt>Worker</dt>
          <dd>{take5.worker_name}</dd>
          <dt>Job</dt>
          <dd>{take5.job}</dd>
          <dt>Location</dt>
          <dd>{take5.location}</dd>
          <dt>Completed</dt>
          <dd>
            <time dateTime={take5.finished_at}>
              {new Date(take5.finished_at).toLocaleString()}
            </time>
          </dd>
        </dl>
      </section>
      {take5.hazards.map((hazard, index) => (
        <section className="card stack" key={index}>
          <p className="eyebrow">HAZARD {index + 1}</p>
          <h2>{hazard.description}</h2>
          <div className="ratings-summary">
            <div>
              <h3>Before controls</h3>
              <p className="supporting">
                {hazard.before.likelihood} · {hazard.before.consequence}
              </p>
              <RiskBadge {...hazard.before} />
            </div>
            <div>
              <h3>After controls</h3>
              <p className="supporting">
                {hazard.after.likelihood} · {hazard.after.consequence}
              </p>
              <RiskBadge {...hazard.after} />
            </div>
          </div>
          <h3>Controls</h3>
          {hazard.controls.length ? (
            <ul className="answer-list">
              {hazard.controls.map((control, controlIndex) => (
                <li key={controlIndex}>
                  <strong>{control.description}</strong>
                  <span>{control.kind}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p>No controls listed.</p>
          )}
        </section>
      ))}
      <p className="supporting">
        Completed on {take5.template.name}. This saved assessment is kept as
        submitted.
      </p>
      <a className="button primary" href="/">
        Start a new Take 5
      </a>
    </main>
  );
}
