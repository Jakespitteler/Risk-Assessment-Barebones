import { useEffect, useRef } from "react";
import { Button } from "../../components/Button";

/**
 * Asked when the worker presses Leave: keep the Take 5 to carry on later, throw it
 * away, or go back to it. Three big buttons, one under the other, for a gloved thumb.
 */
export function LeavePanel({
  onKeep,
  onThrowAway,
  onKeepGoing,
}: {
  onKeep: () => void;
  onThrowAway: () => void;
  onKeepGoing: () => void;
}) {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    heading.current?.focus();
  }, []);
  return (
    <section className="flex flex-col gap-4">
      <h1
        ref={heading}
        tabIndex={-1}
        className="text-3xl font-extrabold focus:outline-none"
      >
        Leave this Take 5?
      </h1>
      <p>
        Keep it to finish later, at the job, or throw it away if you’re not
        doing this job.
      </p>
      <Button onClick={onKeep}>Keep it for later</Button>
      <Button variant="secondary" onClick={onThrowAway}>
        Throw it away
      </Button>
      <Button variant="secondary" onClick={onKeepGoing}>
        Keep going
      </Button>
    </section>
  );
}
