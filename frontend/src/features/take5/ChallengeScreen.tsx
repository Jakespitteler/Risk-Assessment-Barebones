import { useEffect, useRef, useState } from "react";
import type { SavedTake5 } from "../../api/take5";
import { ApiError, useAnswerTake5 } from "../../api/take5";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { Field } from "../../components/Field";
import { FIELD_STYLE } from "../../components/fieldStyle";
import { Notice } from "../../components/Notice";
import { Screen } from "../../components/Screen";
import { fieldProps } from "./fieldProps";
import { focusFirstEmptyBox, hasFinePointer } from "./focusFirstEmptyBox";
import { SavedListLink } from "./SavedListLink";

const ANSWER = "answer";

/**
 * The one question before the result (spec C1 to C6). The Take 5 is already saved, so
 * there is no way back to the form: the worker answers, and the result follows. Only
 * the phone that submitted it can answer; anyone else sees the question, and that it
 * isn't finished.
 */
export function ChallengeScreen({
  take5,
  canAnswer,
  onOutOfDate,
}: {
  take5: SavedTake5;
  canAnswer: boolean;
  /** Open the Take 5 again: it was answered elsewhere, or can't be found. */
  onOutOfDate: () => void;
}) {
  const [answer, setAnswer] = useState("");
  const [answerError, setAnswerError] = useState<string>();
  const [unsent, setUnsent] = useState(false);
  const send = useAnswerTake5(take5.id);
  const page = useRef<HTMLDivElement>(null);
  useEffect(() => {
    // On a computer the cursor goes straight into the box; a phone keeps its keyboard
    // down until the worker taps the box, so the question isn't covered.
    if (canAnswer && hasFinePointer() && focusFirstEmptyBox(page.current))
      return;
    page.current?.querySelector("h1")?.focus();
  }, [canAnswer]);

  function finish() {
    setUnsent(false);
    // Once it is answered, the finished Take 5 replaces this screen with its result.
    send.mutate(answer, {
      onError: (error) => {
        const status = error instanceof ApiError ? error.status : 0;
        if (status === 422 && error instanceof ApiError)
          setAnswerError(
            error.fieldErrors.find(({ path }) => path === ANSWER)?.message ??
              error.message,
          );
        else if (status === 409 || status === 404) onOutOfDate();
        else setUnsent(true);
      },
    });
  }

  return (
    <Screen subtitle="Your Take 5" aside={<SavedListLink />}>
      <div ref={page} className="flex flex-col gap-6">
        <h1
          tabIndex={-1}
          className="text-3xl font-extrabold focus:outline-none"
        >
          {canAnswer ? "One question before you start" : "Not finished yet"}
        </h1>
        <p className="text-lg">
          {canAnswer
            ? "Your Take 5 is saved. Answer this in your own words to see your result."
            : "This Take 5 was saved, but its question hasn’t been answered. Only the phone it was done on can answer it."}
        </p>
        <Card>
          <p className="text-slate-700">
            <span className="font-bold">Job:</span> {take5.job}
          </p>
          {canAnswer ? (
            <Field
              name={ANSWER}
              label={take5.challenge?.question ?? ""}
              error={answerError}
            >
              <textarea
                {...fieldProps(ANSWER, () => answerError)}
                rows={4}
                className={FIELD_STYLE}
                value={answer}
                onChange={(event) => {
                  setAnswer(event.target.value);
                  setAnswerError(undefined);
                }}
              />
            </Field>
          ) : (
            <p className="text-lg font-bold">{take5.challenge?.question}</p>
          )}
        </Card>
        {unsent && (
          <Notice>
            Your answer wasn’t sent. Check your signal and press Finish again.
          </Notice>
        )}
        {canAnswer && (
          <Button disabled={send.isPending} onClick={finish}>
            {send.isPending ? "Finishing…" : "Finish Take 5"}
          </Button>
        )}
      </div>
    </Screen>
  );
}
