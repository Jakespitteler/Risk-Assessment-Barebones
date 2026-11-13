import { useEffect, useRef, useState } from "react";
import {
  ApiError,
  checkDraft,
  submitTake5,
  useTemplate,
} from "../../api/take5";
import type {
  FieldError,
  HazardDraft,
  Take5Draft,
  TemplateResponse,
} from "../../api/take5";
import { ControlEditor } from "../../components/ControlEditor";
import { Field, Guidance } from "../../components/Field";
import { NOTHING_PICKED, RatingPicker } from "../../components/RatingPicker";
import { ReviewDraft } from "./ReviewDraft";

type Stage =
  | { page: "job" | "hazards" | "review" }
  | { page: "before" | "controls" | "after"; hazard: number };

function blankHazard(): HazardDraft {
  return {
    description: "",
    before: { ...NOTHING_PICKED },
    controls: [],
    after: { ...NOTHING_PICKED },
  };
}

function workerName(): string {
  try {
    return localStorage.getItem("take5-worker-name") ?? "";
  } catch {
    return "";
  }
}

/** Load the server's card before showing editable worker answers. */
export function NewTake5Screen({ onSaved }: { onSaved: (id: string) => void }) {
  const template = useTemplate();
  if (template.isPending)
    return (
      <main className="page">
        <h1>Loading your Take 5…</h1>
      </main>
    );
  if (template.isError)
    return (
      <main className="page">
        <h1>The card couldn’t be loaded</h1>
        <p>Check your signal and try again.</p>
        <button
          className="button primary"
          onClick={() => void template.refetch()}
        >
          Try again
        </button>
      </main>
    );
  return <Take5Form template={template.data} onSaved={onSaved} />;
}

/** Keep the entire draft in memory until the worker chooses to finish it. */
function Take5Form({
  template,
  onSaved,
}: {
  template: TemplateResponse;
  onSaved: (id: string) => void;
}) {
  const [draft, setDraft] = useState<Take5Draft>(() => ({
    worker_name: workerName(),
    job: "",
    location: "",
    hazards: [blankHazard()],
  }));
  const [stage, setStage] = useState<Stage>({ page: "job" });
  const [errors, setErrors] = useState<FieldError[]>([]);
  const [pending, setPending] = useState(false);
  const [failure, setFailure] = useState("");
  const [conflict, setConflict] = useState(false);
  const [submissionId] = useState(() => crypto.randomUUID());
  const busy = useRef(false);
  const page = useRef<HTMLElement>(null);
  const errorFor = (path: string) =>
    errors.find((error) => error.path === path)?.message;
  const step =
    stage.page === "job"
      ? 1
      : stage.page === "hazards"
        ? 2
        : stage.page === "review"
          ? 4
          : 3;
  const currentIndex = "hazard" in stage ? stage.hazard : 0;
  const hazard = draft.hazards[currentIndex];
  const prefix = `hazards.${String(currentIndex)}`;

  useEffect(() => {
    window.scrollTo({ top: 0 });
    page.current
      ?.querySelector<HTMLElement>(
        "[aria-invalid='true'] input, input[aria-invalid='true'], textarea[aria-invalid='true'], select[aria-invalid='true']",
      )
      ?.focus();
  }, [stage]);

  function updateHazard(index: number, update: Partial<HazardDraft>) {
    setErrors((current) =>
      current.filter(
        (error) => !error.path.startsWith(`hazards.${String(index)}.`),
      ),
    );
    setDraft((current) => ({
      ...current,
      hazards: current.hazards.map((item, position) =>
        position === index ? { ...item, ...update } : item,
      ),
    }));
  }

  function nextHazard(index: number) {
    setStage(
      index + 1 < draft.hazards.length
        ? { page: "before", hazard: index + 1 }
        : { page: "review" },
    );
  }

  function next() {
    if (stage.page === "job") setStage({ page: "hazards" });
    else if (stage.page === "hazards")
      setStage(
        draft.hazards.length
          ? { page: "before", hazard: 0 }
          : { page: "review" },
      );
    else if (stage.page === "before")
      setStage({ page: "controls", hazard: currentIndex });
    else if (stage.page === "controls" && hazard?.controls.length)
      setStage({ page: "after", hazard: currentIndex });
    else nextHazard(currentIndex);
  }

  function previous() {
    if (stage.page === "hazards") setStage({ page: "job" });
    else if (stage.page === "before") {
      const previousIndex = currentIndex - 1;
      setStage(
        previousIndex < 0
          ? { page: "hazards" }
          : {
              page: draft.hazards[previousIndex]?.controls.length
                ? "after"
                : "controls",
              hazard: previousIndex,
            },
      );
    } else if (stage.page === "controls")
      setStage({ page: "before", hazard: currentIndex });
    else if (stage.page === "after")
      setStage({ page: "controls", hazard: currentIndex });
    else if (stage.page === "review") {
      const last = draft.hazards.length - 1;
      setStage(
        last < 0
          ? { page: "hazards" }
          : {
              page: draft.hazards[last]?.controls.length ? "after" : "controls",
              hazard: last,
            },
      );
    }
  }

  function showErrors(found: FieldError[]) {
    setErrors(found);
    const path = found[0]?.path ?? "";
    if (["worker_name", "job", "location"].includes(path))
      setStage({ page: "job" });
    else if (
      path === "hazards" ||
      (path.endsWith(".description") && !path.includes(".controls."))
    )
      setStage({ page: "hazards" });
    else {
      const index = Number(path.split(".")[1]);
      setStage({
        page: path.includes(".before")
          ? "before"
          : path.includes(".controls")
            ? "controls"
            : "after",
        hazard: index,
      });
    }
  }

  async function finish() {
    if (busy.current) return;
    busy.current = true;
    setPending(true);
    setFailure("");
    setConflict(false);
    try {
      const check = await checkDraft(draft);
      if (!check.can_submit) {
        showErrors(check.errors);
        return;
      }
      const result = await submitTake5(submissionId, draft);
      try {
        localStorage.setItem("take5-worker-name", result.take5.worker_name);
      } catch {
        /* Storage may be unavailable on a private phone. */
      }
      onSaved(result.take5.id);
    } catch (error) {
      const alreadySaved = error instanceof ApiError && error.status === 409;
      setFailure(
        alreadySaved
          ? "This Take 5 was already saved with different answers. Open the saved assessment to see the original record."
          : "Your answers are still here. We couldn’t confirm that your Take 5 was saved. Check your signal and try again.",
      );
      setConflict(alreadySaved);
    } finally {
      busy.current = false;
      setPending(false);
    }
  }

  const attributes = (path: string) => ({
    id: path,
    "aria-invalid": Boolean(errorFor(path)),
    "aria-describedby": errorFor(path) ? `${path}-error` : undefined,
  });
  const titles = {
    job: "The job in front of you",
    hazards: "What could hurt someone?",
    before: "Before any controls",
    controls: "What will stop it?",
    after: "After your controls",
    review: "One last look",
  };

  return (
    <main className="page" ref={page}>
      <header className="brand">
        <span className="brand-mark">5</span>
        <div>
          <p className="eyebrow">PERSONAL RISK ASSESSMENT</p>
          <strong>Take 5 · Before you start</strong>
        </div>
      </header>
      <ol className="progress" aria-label="Take 5 progress">
        {["Job", "Hazards", "Assess", "Review"].map((name, index) => (
          <li key={name} aria-current={step === index + 1 ? "step" : undefined}>
            <span>{index + 1}</span>
            {name}
          </li>
        ))}
      </ol>
      <header>
        <p className="eyebrow">
          STEP {step} OF 4
          {"hazard" in stage
            ? ` · HAZARD ${String(currentIndex + 1)} OF ${String(draft.hazards.length)}`
            : ""}
        </p>
        <h1>{titles[stage.page]}</h1>
        {hazard && "hazard" in stage && (
          <p className="hazard-context">
            {hazard.description || `Hazard ${String(currentIndex + 1)}`}
          </p>
        )}
      </header>
      {errors.length > 0 && (
        <p className="error-banner" role="alert">
          Check the highlighted answers before finishing.
        </p>
      )}
      {stage.page === "job" && (
        <section className="card stack">
          <p>
            Say who you are, what you’re doing and where. Use your own words.
          </p>
          {(
            [
              ["worker_name", "Your name"],
              ["job", "What is the job?"],
              ["location", "Where will you do it?"],
            ] as const
          ).map(([name, label]) => (
            <Field key={name} name={name} label={label} error={errorFor(name)}>
              {name === "job" ? (
                <textarea
                  {...attributes(name)}
                  value={draft[name]}
                  onChange={(event) => {
                    setDraft({ ...draft, [name]: event.target.value });
                    setErrors((current) =>
                      current.filter((error) => error.path !== name),
                    );
                  }}
                />
              ) : (
                <input
                  {...attributes(name)}
                  autoComplete={name === "worker_name" ? "name" : "off"}
                  value={draft[name]}
                  onChange={(event) => {
                    setDraft({ ...draft, [name]: event.target.value });
                    setErrors((current) =>
                      current.filter((error) => error.path !== name),
                    );
                  }}
                />
              )}
            </Field>
          ))}
        </section>
      )}
      {stage.page === "hazards" && (
        <section className="stack">
          <p>
            Look around the job. List the things that could hurt you or someone
            else today.
          </p>
          {draft.hazards.map((item, index) => (
            <section className="card stack" key={index}>
              <Field
                name={`hazards.${String(index)}.description`}
                label={`Hazard ${String(index + 1)}`}
                error={errorFor(`hazards.${String(index)}.description`)}
              >
                <textarea
                  {...attributes(`hazards.${String(index)}.description`)}
                  value={item.description}
                  onChange={(event) => {
                    updateHazard(index, { description: event.target.value });
                  }}
                />
              </Field>
              <button
                type="button"
                className="text-button"
                onClick={() => {
                  setDraft({
                    ...draft,
                    hazards: draft.hazards.filter(
                      (_, position) => position !== index,
                    ),
                  });
                }}
              >
                Remove hazard {index + 1}
              </button>
            </section>
          ))}
          {errorFor("hazards") && (
            <p className="field-error">{errorFor("hazards")}</p>
          )}
          <button
            className="button secondary"
            onClick={() => {
              setDraft({
                ...draft,
                hazards: [...draft.hazards, blankHazard()],
              });
            }}
          >
            Add another hazard
          </button>
        </section>
      )}
      {hazard && (stage.page === "before" || stage.page === "after") && (
        <section className="card stack">
          <p>
            {stage.page === "before"
              ? "Think about this hazard with no controls in place."
              : "Think about what could still happen with your controls in place."}
          </p>
          {errorFor(`${prefix}.${stage.page}`) && (
            <p className="field-error" role="alert">
              {errorFor(`${prefix}.${stage.page}`)}
            </p>
          )}
          <Guidance title="What do the ratings mean?">
            {[
              { name: "Likelihood", items: template.likelihood_guidance },
              { name: "Consequence", items: template.consequence_guidance },
            ].map(({ name, items }) => (
              <div key={name}>
                <h3>{name}</h3>
                <dl className="guidance-list">
                  {items.map(([label, text]) => (
                    <div key={label}>
                      <dt>{label}</dt>
                      <dd>{text}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            ))}
          </Guidance>
          <RatingPicker
            matrix={template.matrix}
            rating={hazard[stage.page] ?? NOTHING_PICKED}
            errors={{
              likelihood: errorFor(`${prefix}.${stage.page}.likelihood`),
              consequence: errorFor(`${prefix}.${stage.page}.consequence`),
            }}
            onChange={(rating) => {
              updateHazard(currentIndex, { [stage.page]: rating });
            }}
          />
        </section>
      )}
      {hazard && stage.page === "controls" && (
        <section className="stack">
          <p>
            Write what you will actually do about this hazard, then choose the
            kind of control.
          </p>
          <Guidance title="What do the control kinds mean?">
            <p>{template.control_guidance}</p>
          </Guidance>
          {hazard.controls.map((control, index) => (
            <ControlEditor
              key={index}
              control={control}
              kinds={template.control_kinds}
              path={`${prefix}.controls.${String(index)}`}
              errorFor={errorFor}
              onChange={(updated) => {
                updateHazard(currentIndex, {
                  controls: hazard.controls.map((item, position) =>
                    position === index ? updated : item,
                  ),
                });
              }}
              onRemove={() => {
                updateHazard(currentIndex, {
                  controls: hazard.controls.filter(
                    (_, position) => position !== index,
                  ),
                });
              }}
            />
          ))}
          {!hazard.controls.length && (
            <p className="empty-state">No controls listed yet.</p>
          )}
          <button
            className="button secondary"
            onClick={() => {
              updateHazard(currentIndex, {
                controls: [...hazard.controls, { description: "", kind: null }],
              });
            }}
          >
            Add a control
          </button>
        </section>
      )}
      {stage.page === "review" && (
        <ReviewDraft draft={draft} matrix={template.matrix} />
      )}
      {failure && (
        <div className="error-banner" role="alert">
          <p>{failure}</p>
          {conflict && (
            <a href={`/take5s/${submissionId}`}>Open the saved Take 5</a>
          )}
        </div>
      )}
      <nav className="form-nav" aria-label="Form navigation">
        {stage.page !== "job" && (
          <button
            className="button secondary"
            disabled={pending}
            onClick={previous}
          >
            Back
          </button>
        )}
        {stage.page === "review" ? (
          <button
            className="button primary"
            disabled={pending}
            onClick={() => void finish()}
          >
            {pending ? "Saving…" : "Finish Take 5"}
          </button>
        ) : (
          <button className="button primary" disabled={pending} onClick={next}>
            Continue
          </button>
        )}
      </nav>
      <p className="privacy-note">
        Saved when you finish. Keep this page open while you fill it in.
      </p>
    </main>
  );
}
