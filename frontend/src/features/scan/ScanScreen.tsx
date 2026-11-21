import { useEffect, useRef, useState } from "react";
import {
  ApiError,
  type ScannedCardResponse,
  type Take5Draft,
  useReadCard,
  useSavePaperTake5,
  useTemplate,
} from "../../api/take5";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { Screen } from "../../components/Screen";
import { SavedListLink } from "../take5/SavedListLink";
import { PaperCardForm, UNREADABLE_MARK } from "./PaperCardForm";
import { shrinkPhoto } from "./shrinkPhoto";

type CardStatus =
  "waiting" | "reading" | "unread" | "ready" | "saved" | "skipped";

/** One photographed card on its way from the photo to saved. Kept only in this page. */
interface ScanCard {
  /** Made once, and sent on every save, so a retry can't save it twice. */
  id: string;
  photo: Blob;
  photoUrl: string;
  status: CardStatus;
  problem?: string;
  draft: Take5Draft;
  filledInAt: string | null;
  unreadable: string[];
  fieldErrors: Record<string, string>;
}

const BLANK_DRAFT: Take5Draft = {
  worker_name: "",
  job: "",
  location: "",
  answers: {},
  hazards: [],
};

/**
 * Scan paper cards (spec F10): take many photos, have the AI read them all, then check
 * each card beside its photo and save it as written, or skip it. The photos never leave
 * this page except to be read, and the batch is lost if the page closes (D20).
 */
export function ScanScreen() {
  const template = useTemplate();
  const readCard = useReadCard();
  const savePaper = useSavePaperTake5();
  const [cards, setCards] = useState<ScanCard[]>([]);
  // How many saves found the card already saved, as it was first sent.
  const [savedBefore, setSavedBefore] = useState(0);
  const heading = useRef<HTMLHeadingElement>(null);
  const problem = useRef<HTMLParagraphElement>(null);
  // The photos waiting to be read, in the order taken, and whether one is being read.
  const queue = useRef<ScanCard[]>([]);
  const busy = useRef(false);
  const update = (id: string, changed: Partial<ScanCard>) => {
    setCards((all) =>
      all.map((card) => (card.id === id ? { ...card, ...changed } : card)),
    );
  };

  // Read one photo at a time, shrinking each just before it is sent, so a pile of big
  // phone photos is never all held at full size at once.
  const readQueue = async () => {
    if (busy.current) return;
    busy.current = true;
    for (let card = queue.current.shift(); card; card = queue.current.shift()) {
      update(card.id, { status: "reading", problem: undefined });
      try {
        const scan: ScannedCardResponse = await readCard.mutateAsync(
          await shrinkPhoto(card.photo),
        );
        update(card.id, {
          status: "ready",
          draft: scan.draft,
          filledInAt: scan.filled_in_at ?? null,
          unreadable: [...scan.unreadable],
        });
      } catch (error) {
        const message =
          error instanceof ApiError
            ? error.message
            : "The photo couldn’t be sent. Check your signal and try again.";
        // With no AI set up, no other photo can be read either.
        const stopped =
          error instanceof ApiError && error.status === 503
            ? queue.current.splice(0)
            : [];
        for (const unread of [card, ...stopped])
          update(unread.id, { status: "unread", problem: message });
      }
    }
    busy.current = false;
  };

  const read = (toRead: ScanCard[]) => {
    queue.current.push(...toRead);
    void readQueue();
  };

  const checking = cards.find(
    (card) => card.status === "ready" || card.status === "unread",
  );
  const stillReading = cards.some(
    (card) => card.status === "waiting" || card.status === "reading",
  );
  const shown = stillReading ? undefined : checking?.id;
  useEffect(() => {
    heading.current?.focus();
  }, [shown]);

  const addPhotos = (files: FileList | null) => {
    if (!files?.length) return;
    const added: ScanCard[] = [...files].map((photo) => ({
      id: crypto.randomUUID(),
      photo,
      photoUrl: URL.createObjectURL(photo),
      status: "waiting",
      draft: BLANK_DRAFT,
      filledInAt: null,
      unreadable: [],
      fieldErrors: {},
    }));
    setCards((all) => [...all, ...added]);
    read(added);
  };

  const retake = (card: ScanCard, files: FileList | null) => {
    const photo = files?.[0];
    if (!photo) return;
    URL.revokeObjectURL(card.photoUrl);
    const retaken = { ...card, photo, photoUrl: URL.createObjectURL(photo) };
    update(card.id, { ...retaken, status: "waiting" });
    read([retaken]);
  };

  // The photo is thrown away once its card is saved or skipped (Jake, answer 4).
  const finish = (card: ScanCard, status: "saved" | "skipped") => {
    URL.revokeObjectURL(card.photoUrl);
    update(card.id, { status, photo: new Blob(), photoUrl: "" });
  };

  const save = (card: ScanCard) => {
    savePaper.mutate(
      {
        id: card.id,
        draft: card.draft,
        filled_in_at: card.filledInAt,
        time_zone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      },
      {
        onSuccess: () => {
          finish(card, "saved");
        },
        onError: (error) => {
          // A save whose reply was lost, sent again after an edit, finds the first
          // save: the card is saved as it was first sent, so it counts as saved.
          if (error instanceof ApiError && error.status === 409) {
            setSavedBefore((count) => count + 1);
            finish(card, "saved");
            return;
          }
          update(card.id, {
            fieldErrors: Object.fromEntries(
              error instanceof ApiError
                ? error.fieldErrors.map(({ path, message }) => [path, message])
                : [],
            ),
            problem:
              error instanceof ApiError
                ? error.message
                : "The card wasn’t saved. Check your signal and try again.",
          });
          // The message sits beside Save, and is read out there.
          setTimeout(() => problem.current?.focus());
        },
      },
    );
  };

  const toRead = cards.filter(
    (card) => card.status === "waiting" || card.status === "reading",
  ).length;

  return (
    <Screen
      subtitle="Scan paper cards"
      aside={<SavedListLink />}
      wide={!stillReading && Boolean(checking)}
    >
      <h1
        ref={heading}
        tabIndex={-1}
        className="text-3xl font-extrabold focus:outline-none"
      >
        {stillReading
          ? `Reading ${toRead === 1 ? "1 photo" : `${String(toRead)} photos`}`
          : checking
            ? `Check card ${String(cards.indexOf(checking) + 1)} of ${String(cards.length)}`
            : "Scan paper cards"}
      </h1>
      {stillReading && (
        <p>
          The AI reads each photo, which can take up to a minute. Keep taking
          photos meanwhile; you’ll check every card once they’re all read.
        </p>
      )}
      {cards.length === 0 && (
        <p>
          Take a photo of each paper Take 5, one after another, or choose the
          photos you have. The AI fills in each card, then you check it beside
          its photo and save it as written. The photos aren’t kept.
        </p>
      )}
      {/* Always in the same place, so a photo taken while the last read finishes
          still arrives: the picker is never swapped out from under the camera. */}
      {
        <PhotoPicker
          key="photos"
          label={cards.length === 0 ? "Choose photos" : "Add more photos"}
          multiple
          variant={cards.length === 0 ? "primary" : "secondary"}
          onChoose={addPhotos}
        />
      }
      {savedBefore > 0 && !stillReading && !checking && (
        <p>
          {savedBefore === 1
            ? "One card was already saved, as it was first sent; later changes to it weren’t kept."
            : `${String(savedBefore)} cards were already saved, as they were first sent; later changes to them weren’t kept.`}
        </p>
      )}
      {!stillReading && checking && !template.data && (
        <Card>
          {template.isError ? (
            <>
              <p>
                The card couldn’t be loaded. Check your signal and try again.
              </p>
              <Button onClick={() => void template.refetch()}>Try again</Button>
            </>
          ) : (
            <p role="status">Loading the card…</p>
          )}
        </Card>
      )}
      {!stillReading && checking && template.data && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Photo card={checking} />
          <div className="flex flex-col gap-4">
            {checking.status === "ready" && (
              <fieldset disabled={savePaper.isPending} className="contents">
                <PaperCardForm
                  template={template.data}
                  draft={checking.draft}
                  filledInAt={checking.filledInAt}
                  errorFor={(path) =>
                    checking.fieldErrors[path] ??
                    (checking.unreadable.includes(path)
                      ? UNREADABLE_MARK
                      : undefined)
                  }
                  onChange={(draft, filledInAt) => {
                    update(checking.id, { draft, filledInAt });
                  }}
                  onRemoveItem={(listPath, index) => {
                    update(checking.id, {
                      unreadable: checking.unreadable.flatMap((path) => {
                        const moved = withoutItem(path, listPath, index);
                        return moved === null ? [] : [moved];
                      }),
                      fieldErrors: Object.fromEntries(
                        Object.entries(checking.fieldErrors).flatMap(
                          ([path, message]) => {
                            const moved = withoutItem(path, listPath, index);
                            return moved === null ? [] : [[moved, message]];
                          },
                        ),
                      ),
                    });
                  }}
                />
              </fieldset>
            )}
            {checking.problem && (
              <p
                ref={problem}
                role="alert"
                tabIndex={-1}
                className="font-semibold text-danger focus:outline-none"
              >
                {checking.problem}
              </p>
            )}
            <div className="flex flex-col gap-3">
              {checking.status === "ready" ? (
                <Button
                  disabled={savePaper.isPending}
                  onClick={() => {
                    save(checking);
                  }}
                >
                  {savePaper.isPending ? "Saving…" : "Save as written"}
                </Button>
              ) : (
                <>
                  <Button
                    onClick={() => {
                      update(checking.id, { status: "waiting" });
                      read([checking]);
                    }}
                  >
                    Try again
                  </Button>
                  <PhotoPicker
                    label="Take this photo again"
                    multiple={false}
                    variant="secondary"
                    onChoose={(files) => {
                      retake(checking, files);
                    }}
                  />
                </>
              )}
              <Button
                variant="secondary"
                disabled={savePaper.isPending}
                onClick={() => {
                  finish(checking, "skipped");
                }}
              >
                Skip this card
              </Button>
            </div>
          </div>
        </div>
      )}
      {cards.length > 0 && !stillReading && !checking && (
        <Done
          saved={cards.filter((card) => card.status === "saved").length}
          skipped={cards.filter((card) => card.status === "skipped").length}
          onMore={() => {
            setCards([]);
            setSavedBefore(0);
          }}
        />
      )}
    </Screen>
  );
}

/**
 * Where a marked path is once an item of a list is removed, such as hazard 0 of
 * "hazards": the removed item's paths go (null), and each later item's move up one, so
 * a mark stays beside its own item.
 */
function withoutItem(
  path: string,
  listPath: string,
  removed: number,
): string | null {
  if (!path.startsWith(`${listPath}.`)) return path;
  const [index = "", ...rest] = path.slice(listPath.length + 1).split(".");
  if (!/^\d+$/.test(index)) return path;
  const at = Number(index);
  if (at === removed) return null;
  if (at < removed) return path;
  return [listPath, String(at - 1), ...rest].join(".");
}

/** A button that opens the camera or the photos. */
function PhotoPicker({
  label,
  multiple,
  variant = "primary",
  onChoose,
}: {
  label: string;
  multiple: boolean;
  variant?: "primary" | "secondary";
  onChoose: (files: FileList | null) => void;
}) {
  const look =
    variant === "primary"
      ? "bg-action text-on-action hover:bg-action-hover"
      : "border-2 border-ink bg-surface text-ink hover:bg-surface-hover";
  return (
    <label
      className={`relative flex min-h-14 cursor-pointer items-center justify-center rounded-xl px-5 text-lg font-bold has-focus-visible:outline-4 has-focus-visible:outline-offset-2 has-focus-visible:outline-focus ${look}`}
    >
      {label}
      <input
        type="file"
        accept="image/*"
        multiple={multiple}
        // Stretched over the whole button, unseen, so its tap area is the button's.
        className="absolute inset-0 cursor-pointer opacity-0"
        onChange={(event) => {
          onChoose(event.target.files);
          // The same photo can be chosen again after a problem.
          event.target.value = "";
        }}
      />
    </label>
  );
}

/** The photo of the card being checked. A tap opens it full size. */
function Photo({ card }: { card: ScanCard }) {
  return (
    <a
      href={card.photoUrl}
      target="_blank"
      rel="noreferrer"
      className="self-start lg:sticky lg:top-4"
    >
      <img
        src={card.photoUrl}
        alt="The paper card"
        className="max-h-[70dvh] w-full rounded-2xl border border-line object-contain"
      />
    </a>
  );
}

/** What happened to the batch. */
function Done({
  saved,
  skipped,
  onMore,
}: {
  saved: number;
  skipped: number;
  onMore: () => void;
}) {
  return (
    <Card>
      <p className="text-lg font-bold">
        {saved === 1 ? "1 card saved" : `${String(saved)} cards saved`}
        {skipped > 0 && `, ${String(skipped)} skipped`}.
      </p>
      <a
        className="flex min-h-12 items-center self-start font-semibold underline underline-offset-4 hover:decoration-2 focus-visible:outline-4 focus-visible:outline-focus"
        href="/take5s"
      >
        See them in the saved list
      </a>
      <Button variant="secondary" onClick={onMore}>
        Scan more cards
      </Button>
    </Card>
  );
}
