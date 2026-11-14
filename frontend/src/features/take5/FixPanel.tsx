import type { SavedTake5 } from "../../api/take5";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";

const LINK =
  "flex min-h-14 items-center justify-center rounded-xl px-5 text-center text-lg font-bold focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-blue-700";
const PRIMARY_LINK = `${LINK} bg-slate-900 text-white`;
const SECONDARY_LINK = `${LINK} border-2 border-slate-900 bg-white text-slate-900`;

/**
 * How a saved Take 5 links to its fix, as the back end says. It may offer to copy the
 * answers into a new Take 5 to fix it, link to the newest fix, and link back to the
 * Take 5 it fixes. The saved Take 5 itself never changes.
 */
export function FixPanel({
  take5,
  fixedBy,
  offersFix,
  onFix,
}: {
  take5: SavedTake5;
  fixedBy: string | null;
  offersFix: boolean;
  onFix: () => void;
}) {
  if (!take5.fixes && !fixedBy && !offersFix) return null;
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
      {offersFix && (
        <>
          <p>
            Your answers are copied into a new Take 5, so you only change what
            needs fixing. This one stays saved as it is.
          </p>
          <Button onClick={onFix}>Fix this in a new Take 5</Button>
        </>
      )}
    </Card>
  );
}
