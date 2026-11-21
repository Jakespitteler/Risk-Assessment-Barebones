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

  const finish = (card: ScanCard, status: "saved" | "skipped") => {
    URL.revokeObjectURL(card.photoUrl);
    update(card.id, { status });
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
    <Screen subtitle="Scan paper cards" aside={<SavedListLink />} wide>
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
      {(cards.length === 0 || stillReading) && (
        <ChoosePhotos
          label={cards.length === 0 ? "Choose photos" : "Add more photos"}
          onChoose={addPhotos}
        />
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
                  onRemoveHazard={(index) => {
                    update(checking.id, {
                      unreadable: withoutHazard(checking.unreadable, index),
                      fieldErrors: Object.fromEntries(
                        withoutHazard(
                          Object.keys(checking.fieldErrors),
                          index,
                        ).map((path, at) => [
                          path,
                          Object.values(checking.fieldErrors)[at] ?? "",
                        ]),
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
          }}
        />
      )}
    </Screen>
  );
}

/**
 * The paths marked on a card once a hazard is removed: the removed hazard's go, and
 * each later hazard's move up one, so a mark stays beside its own hazard.
 */
function withoutHazard(paths: string[], removed: number): string[] {
  return paths.flatMap((path) => {
    const match = /^hazards\.(\d+)(.*)$/.exec(path);
    if (!match) return [path];
    const index = Number(match[1]);
    if (index === removed) return [];
    return [
      index > removed ? `hazards.${String(index - 1)}${match[2] ?? ""}` : path,
    ];
  });
}

/** Pick the photos: the camera or the gallery on a phone, files on a desktop. */
function ChoosePhotos({
  label,
  onChoose,
}: {
  label: string;
  onChoose: (files: FileList | null) => void;
}) {
  return (
    <Card>
      <p>
        Take a photo of each paper Take 5, one after another, or choose the
        photos you have. The AI fills in each card, then you check it beside its
        photo and save it as written. The photos aren’t kept.
      </p>
      <PhotoPicker label={label} multiple onChoose={onChoose} />
    </Card>
  );
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
      className={`flex min-h-14 cursor-pointer items-center justify-center rounded-xl px-5 text-lg font-bold has-focus-visible:outline-4 has-focus-visible:outline-offset-2 has-focus-visible:outline-focus ${look}`}
    >
      {label}
      <input
        type="file"
        accept="image/*"
        multiple={multiple}
        className="sr-only"
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
      <a className="font-semibold underline underline-offset-4" href="/take5s">
        See them in the saved list
      </a>
      <Button variant="secondary" onClick={onMore}>
        Scan more cards
      </Button>
    </Card>
  );
}
