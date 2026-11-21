import type {
  Answer,
  HazardDraft,
  Take5Draft,
  TemplateResponse,
} from "../../api/take5";
import { AnswerPicker } from "../../components/AnswerPicker";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { ControlEditor } from "../../components/ControlEditor";
import { Field } from "../../components/Field";
import { FIELD_STYLE } from "../../components/fieldStyle";
import { RatingPicker } from "../../components/RatingPicker";

export const UNREADABLE_MARK = "Couldn’t read this. Check the photo.";

const NO_RATING = { likelihood: null, consequence: null };

const EMPTY_HAZARD: HazardDraft = {
  description: "",
  weak_controls_reason: "",
  before: NO_RATING,
  controls: [],
  after: NO_RATING,
  covers: [],
};

/**
 * One paper card as the AI read it, for a person to check against its photo and change
 * (spec F10). Each field the AI couldn't read is marked, and a blank stays blank: a
 * paper card is saved as written (P1).
 */
export function PaperCardForm({
  template,
  draft,
  filledInAt,
  errorFor,
  onChange,
  onRemoveHazard,
}: {
  template: TemplateResponse;
  draft: Take5Draft;
  filledInAt: string | null;
  /** The back end's error for a field, or the mark for one the AI couldn't read. */
  errorFor: (path: string) => string | undefined;
  onChange: (draft: Take5Draft, filledInAt: string | null) => void;
  /** Told which hazard was removed, so marks and errors can follow the rest. */
  onRemoveHazard: (index: number) => void;
}) {
  const answers: Record<string, Answer> = draft.answers;
  const hazards = draft.hazards;
  const change = (changed: Partial<Take5Draft>) => {
    onChange({ ...draft, ...changed }, filledInAt);
  };
  const changeHazard = (index: number, hazard: HazardDraft) => {
    change({
      hazards: hazards.map((each, at) => (at === index ? hazard : each)),
    });
  };
  const day = filledInAt?.slice(0, 10) ?? "";
  const time = filledInAt?.slice(11, 16) ?? "";
  const changeDate = (newDay: string, newTime: string) => {
    onChange(
      draft,
      newDay ? (newTime ? `${newDay}T${newTime}` : newDay) : null,
    );
  };
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <TextField
          name="worker_name"
          label="Name"
          value={draft.worker_name}
          error={errorFor("worker_name")}
          onChange={(worker_name) => {
            change({ worker_name });
          }}
        />
        <TextField
          name="job"
          label="Job"
          value={draft.job}
          error={errorFor("job")}
          onChange={(job) => {
            change({ job });
          }}
        />
        <TextField
          name="location"
          label="Where"
          value={draft.location}
          error={errorFor("location")}
          onChange={(location) => {
            change({ location });
          }}
        />
        <div className="grid grid-cols-1 gap-4 min-[400px]:grid-cols-2">
          <Field
            name="filled_in_at"
            label="Date on the card"
            error={errorFor("filled_in_at")}
          >
            <input
              id="filled_in_at"
              type="date"
              className={FIELD_STYLE}
              aria-invalid={Boolean(errorFor("filled_in_at"))}
              aria-describedby={
                errorFor("filled_in_at") ? "filled_in_at-error" : undefined
              }
              value={day}
              onChange={(event) => {
                changeDate(event.target.value, time);
              }}
            />
          </Field>
          <Field name="filled_in_time" label="Time on the card">
            <input
              id="filled_in_time"
              type="time"
              className={FIELD_STYLE}
              value={time}
              disabled={!day}
              onChange={(event) => {
                changeDate(day, event.target.value);
              }}
            />
          </Field>
        </div>
      </Card>
      {errorFor("answers") && (
        <p className="font-semibold text-danger">{errorFor("answers")}</p>
      )}
      {template.questions.map((question) => {
        const path = `answers.${question.id}`;
        return (
          <Card key={question.id}>
            <AnswerPicker
              name={path}
              question={question.text}
              choices={template.answer_choices}
              picked={answers[question.id]}
              error={errorFor(path)}
              onPick={(answer) => {
                change({ answers: { ...answers, [question.id]: answer } });
              }}
            />
            {answers[question.id] && (
              <Button
                variant="quiet"
                onClick={() => {
                  change({
                    answers: Object.fromEntries(
                      Object.entries(answers).filter(
                        ([id]) => id !== question.id,
                      ),
                    ),
                  });
                }}
              >
                Leave blank, as on the card
              </Button>
            )}
          </Card>
        );
      })}
      {hazards.map((hazard, index) => (
        <HazardCard
          key={index}
          template={template}
          hazard={hazard}
          number={index + 1}
          errorFor={errorFor}
          onChange={(changed) => {
            changeHazard(index, changed);
          }}
          onRemove={() => {
            change({ hazards: hazards.filter((_, at) => at !== index) });
            onRemoveHazard(index);
          }}
        />
      ))}
      {errorFor("hazards") && (
        <p className="font-semibold text-danger">{errorFor("hazards")}</p>
      )}
      <Button
        variant="secondary"
        onClick={() => {
          change({ hazards: [...hazards, EMPTY_HAZARD] });
        }}
      >
        Add a hazard
      </Button>
    </div>
  );
}

/** One hazard on the card: its words, its ratings and its controls. */
function HazardCard({
  template,
  hazard,
  number,
  errorFor,
  onChange,
  onRemove,
}: {
  template: TemplateResponse;
  hazard: HazardDraft;
  number: number;
  errorFor: (path: string) => string | undefined;
  onChange: (hazard: HazardDraft) => void;
  onRemove: () => void;
}) {
  const path = `hazards.${String(number - 1)}`;
  const controls = hazard.controls;
  const ratingErrors = (rating: string) => ({
    likelihood: errorFor(`${rating}.likelihood`) ?? errorFor(rating),
    consequence: errorFor(`${rating}.consequence`) ?? errorFor(rating),
  });
  return (
    <Card>
      <h2 className="text-xl font-bold">Hazard {number}</h2>
      {errorFor(path) && (
        <p className="font-semibold text-danger">{errorFor(path)}</p>
      )}
      <TextField
        name={`${path}.description`}
        label="The hazard"
        value={hazard.description}
        error={errorFor(`${path}.description`)}
        onChange={(description) => {
          onChange({ ...hazard, description });
        }}
      />
      <h3 className="text-lg font-bold">Before controls</h3>
      <RatingPicker
        matrix={template.matrix}
        rating={hazard.before ?? NO_RATING}
        errors={ratingErrors(`${path}.before`)}
        onChange={(before) => {
          onChange({ ...hazard, before });
        }}
      />
      <ClearRating
        rating={hazard.before}
        onClear={() => {
          onChange({ ...hazard, before: NO_RATING });
        }}
      />
      {errorFor(`${path}.controls`) && (
        <p className="font-semibold text-danger">
          {errorFor(`${path}.controls`)}
        </p>
      )}
      {controls.map((control, index) => (
        <ControlEditor
          key={index}
          control={control}
          number={index + 1}
          kinds={template.control_kinds}
          path={`${path}.controls.${String(index)}`}
          kindCanBeBlank
          errorFor={(controlPath) =>
            errorFor(controlPath) ??
            errorFor(`${path}.controls.${String(index)}`)
          }
          onChange={(changed) => {
            onChange({
              ...hazard,
              controls: controls.map((each, at) =>
                at === index ? changed : each,
              ),
            });
          }}
          onRemove={() => {
            onChange({
              ...hazard,
              controls: controls.filter((_, at) => at !== index),
            });
          }}
        />
      ))}
      <Button
        variant="quiet"
        onClick={() => {
          onChange({
            ...hazard,
            controls: [...controls, { description: "", kind: null }],
          });
        }}
      >
        Add a control
      </Button>
      <h3 className="text-lg font-bold">After controls</h3>
      <RatingPicker
        matrix={template.matrix}
        rating={hazard.after ?? NO_RATING}
        errors={ratingErrors(`${path}.after`)}
        onChange={(after) => {
          onChange({ ...hazard, after });
        }}
      />
      <ClearRating
        rating={hazard.after}
        onClear={() => {
          onChange({ ...hazard, after: NO_RATING });
        }}
      />
      <Button variant="quiet" onClick={onRemove}>
        Remove hazard {number}
      </Button>
    </Card>
  );
}

/** Set a rating back to blank, for a card that left it blank (P1). */
function ClearRating({
  rating,
  onClear,
}: {
  rating: HazardDraft["before"];
  onClear: () => void;
}) {
  if (!rating?.likelihood && !rating?.consequence) return null;
  return (
    <Button variant="quiet" onClick={onClear}>
      Leave this rating blank, as on the card
    </Button>
  );
}

/** A labelled box for writing, with its mark or error beneath. */
function TextField({
  name,
  label,
  value,
  error,
  onChange,
}: {
  name: string;
  label: string;
  value: string;
  error: string | undefined;
  onChange: (value: string) => void;
}) {
  return (
    <Field name={name} label={label} error={error}>
      <textarea
        id={name}
        rows={2}
        className={FIELD_STYLE}
        value={value}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${name}-error` : undefined}
        onChange={(event) => {
          onChange(event.target.value);
        }}
      />
    </Field>
  );
}
