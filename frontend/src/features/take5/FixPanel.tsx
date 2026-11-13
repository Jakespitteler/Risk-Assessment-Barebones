import type { SavedTake5 } from "../../api/take5";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";

const LINK =
  "flex min-h-14 items-center justify-center rounded-xl px-5 text-center text-lg font-bold focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-blue-700";
const PRIMARY_LINK = `${LINK} bg-slate-900 text-white`;
const SECONDARY_LINK = `${LINK} border-2 border-slate-900 bg-white text-slate-900`;

/**
 * How a saved Take 5 links to its fix. A Don't start yet can be copied into a new
 * Take 5 to fix it, until it has a fix; then it links to the newest fix instead. A fix
 * links back to the Take 5 it fixes. The saved Take 5 itself never changes.
 */
export function FixPanel({
  take5,
  fixedBy,
  onFix,
}: {
  take5: SavedTake5;
  fixedBy: string | null;
  onFix: () => void;
}) {
  const canFix = !take5.verdict.can_start && !fixedBy;
  if (!take5.fixes && !fixedBy && !canFix) return null;
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
      {canFix && (
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
