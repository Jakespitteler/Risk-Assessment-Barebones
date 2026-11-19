import { useState } from "react";
import type { SavedTake5, Take5Draft } from "../../api/take5";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";

const LINK =
  "flex min-h-14 items-center justify-center rounded-xl px-5 text-center text-lg font-bold focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-focus";
const PRIMARY_LINK = `${LINK} bg-action text-on-action`;
const SECONDARY_LINK = `${LINK} border-2 border-ink bg-surface text-ink`;

/**
 * How a saved Take 5 links to its fix, as the back end says. It may offer to copy the
 * answers into a new Take 5 to fix it, link to the newest fix, and link back to the
 * Take 5 it fixes. The saved Take 5 itself never changes. A fix takes the place of the
 * phone's unfinished Take 5, so when there is one it asks first (spec D24).
 */
export function FixPanel({
  take5,
  fixedBy,
  offersFix,
  unfinished,
  onFix,
}: {
  take5: SavedTake5;
  fixedBy: string | null;
  offersFix: boolean;
  unfinished: Take5Draft | null;
  onFix: () => void;
}) {
  const [asking, setAsking] = useState(false);
  if (!take5.fixes && !fixedBy && !offersFix) return null;
  const unfinishedJob = unfinished?.job.trim();
  return (
    <Card>
      {take5.fixes && (
        <>
          <p>This Take 5 fixes an earlier one that said Don’t start yet.</p>
          <a className={SECONDARY_LINK} href={`/take5s/${take5.fixes}`}>
            Open the Take 5 it fixes
          </a>
        </>
      )}
      {fixedBy && (
        <>
          <p>This Take 5 has been fixed in a newer one.</p>
          <a className={PRIMARY_LINK} href={`/take5s/${fixedBy}`}>
            Open the Take 5 that fixes it
          </a>
        </>
      )}
      {offersFix && !asking && (
        <>
          <p>
            Your answers are copied into a new Take 5, so you only change what
            needs fixing. This one stays saved as it is.
          </p>
          <Button
            onClick={() => {
              if (unfinished) setAsking(true);
              else onFix();
            }}
          >
            Fix this in a new Take 5
          </Button>
        </>
      )}
      {offersFix && asking && (
        <>
          <p className="font-semibold [overflow-wrap:anywhere]">
            You have an unfinished Take 5
            {unfinishedJob ? ` for “${unfinishedJob}”` : ""}. Fixing this one
            throws it away.
          </p>
          <Button onClick={onFix}>Throw it away and fix this</Button>
          <Button
            variant="secondary"
            onClick={() => {
              setAsking(false);
            }}
          >
            Keep my unfinished Take 5
          </Button>
        </>
      )}
    </Card>
  );
}
