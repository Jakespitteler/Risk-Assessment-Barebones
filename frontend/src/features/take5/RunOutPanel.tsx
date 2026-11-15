import { useEffect, useRef } from "react";
import { Button } from "../../components/Button";
import { formatDateTime } from "./formatDateTime";

/**
 * Shown in place of the form when the back end says the draft has run out (spec K2).
 * The draft is already thrown away; the worker starts a new Take 5 at the job.
 */
export function RunOutPanel({
  message,
  startedAt,
  onStartAfresh,
}: {
  message: string;
  startedAt: string | null | undefined;
  onStartAfresh: () => void;
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
        This Take 5 has run out
      </h1>
      <p className="text-lg">{message}</p>
      {startedAt && (
        <p>
          Started{" "}
          <time dateTime={startedAt} className="font-semibold">
            {formatDateTime(startedAt)}
          </time>
        </p>
      )}
      <Button onClick={onStartAfresh}>Start a new Take 5</Button>
    </section>
  );
}
