import { useEffect, useRef, useState } from "react";
import {
  ApiError,
  type ScannedCardResponse,
  type Take5Draft,
  useRankedBatch,
  useReadCard,
  useSavePaperTake5,
  useTemplate,
} from "../../api/take5";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { Screen } from "../../components/Screen";
import { RankedList } from "../take5/RankedList";
import { SavedListLink } from "../take5/SavedListLink";
import { COULDNT_READ, PaperCardForm } from "./PaperCardForm";
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
  const update = (id: string, changed: Partial<ScanCard>) => {
    setCards((all) =>
      all.map((card) => (card.id === id ? { ...card, ...changed } : card)),
    );
  };

  // Read one photo at a time, in the order taken.
  const readAll = async (toRead: ScanCard[]) => {
    for (const card of toRead) {
      update(card.id, { status: "reading", problem: undefined });
      try {
        const scan: ScannedCardResponse = await readCard.mutateAsync(
          card.photo,
        );
        update(card.id, {
          status: "ready",
          draft: scan.draft,
          filledInAt: scan.filled_in_at ?? null,
          unreadable: [...scan.unreadable],
        });
      } catch (error) {
        update(card.id, {
          status: "unread",
          problem:
            error instanceof ApiError
              ? error.message
              : "The photo couldn’t be sent. Check your signal and try again.",
        });
      }
    }
  };

  const checking = cards.find(
    (card) => card.status === "ready" || card.status === "unread",
  );
  useEffect(() => {
    heading.current?.focus();
  }, [checking?.id]);

  const addPhotos = async (files: FileList | null) => {
    if (!files?.length) return;
    const added: ScanCard[] = await Promise.all(
      [...files].map(async (file) => {
        const photo = await shrinkPhoto(file);
        return {
          id: crypto.randomUUID(),
          photo,
          photoUrl: URL.createObjectURL(photo),
          status: "waiting",
          draft: BLANK_DRAFT,
          filledInAt: null,
          unreadable: [],
          fieldErrors: {},
        };
      }),
    );
    setCards((all) => [...all, ...added]);
    await readAll(added);
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
        },
      },
    );
  };

  const readCount = cards.filter(
    (card) => card.status !== "waiting" && card.status !== "reading",
  ).length;
  const stillReading = cards.some(
    (card) => card.status === "waiting" || card.status === "reading",
  );

  return (
    <Screen subtitle="Scan paper cards" aside={<SavedListLink />} wide>
      <h1
        ref={heading}
        tabIndex={-1}
        className="text-3xl font-extrabold focus:outline-none"
      >
        {stillReading
          ? `Reading card ${String(readCount + 1)} of ${String(cards.length)}`
          : checking
            ? `Check card ${String(cards.indexOf(checking) + 1)} of ${String(cards.length)}`
            : "Scan paper cards"}
      </h1>
      {cards.length === 0 && (
        <ChoosePhotos
          onChoose={(files) => {
            void addPhotos(files);
          }}
        />
      )}
      {stillReading && (
        <p role="status">
          The AI reads each photo, which can take up to a minute. You’ll check
          every card once they’re all read.
        </p>
      )}
      {!stillReading && checking && template.data && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Photo card={checking} />
          <div className="flex flex-col gap-4">
            {checking.problem && (
              <p role="alert" className="font-semibold text-danger">
                {checking.problem}
              </p>
            )}
            {checking.status === "ready" && (
              <PaperCardForm
                template={template.data}
                draft={checking.draft}
                filledInAt={checking.filledInAt}
                errorFor={(path) =>
                  checking.fieldErrors[path] ??
                  (checking.unreadable.includes(path)
                    ? COULDNT_READ
                    : undefined)
                }
                onChange={(draft, filledInAt) => {
                  update(checking.id, { draft, filledInAt });
                }}
              />
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
                <Button
                  onClick={() => {
                    void readAll([checking]);
                  }}
                >
                  Try again
                </Button>
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
          savedIds={cards
            .filter((card) => card.status === "saved")
            .map((card) => card.id)}
          skipped={cards.filter((card) => card.status === "skipped").length}
          onMore={() => {
            setCards([]);
          }}
        />
      )}
    </Screen>
  );
}

/** Pick the photos: the camera or the gallery on a phone, files on a desktop. */
function ChoosePhotos({
  onChoose,
}: {
  onChoose: (files: FileList | null) => void;
}) {
  return (
    <Card>
      <p>
        Take a photo of each paper Take 5, or choose the photos you have. The AI
        fills in each card, then you check it beside its photo and save it as
        written. The photos aren’t kept.
      </p>
      <label className="flex min-h-14 cursor-pointer items-center justify-center rounded-xl bg-action px-5 text-lg font-bold text-on-action hover:bg-action-hover has-focus-visible:outline-4 has-focus-visible:outline-offset-2 has-focus-visible:outline-focus">
        Choose photos
        <input
          type="file"
          accept="image/*"
          multiple
          className="sr-only"
          onChange={(event) => {
            onChoose(event.target.files);
          }}
        />
      </label>
    </Card>
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

/** What happened to the batch, and the saved cards worst first (F10). */
function Done({
  savedIds,
  skipped,
  onMore,
}: {
  savedIds: string[];
  skipped: number;
  onMore: () => void;
}) {
  const saved = savedIds.length;
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <p className="text-lg font-bold">
          {saved === 1 ? "1 card saved" : `${String(saved)} cards saved`}
          {skipped > 0 && `, ${String(skipped)} skipped`}.
        </p>
        <a
          className="font-semibold underline underline-offset-4"
          href="/take5s"
        >
          See them in the saved list
        </a>
        <Button variant="secondary" onClick={onMore}>
          Scan more cards
        </Button>
      </Card>
      {saved > 0 && <BatchRanking ids={savedIds} />}
    </div>
  );
}

/** The batch's saved cards worst first, each with why, as Today's review shows them. */
function BatchRanking({ ids }: { ids: string[] }) {
  const ranking = useRankedBatch(ids);
  const byAi = ranking.data?.take5s.some((take5) => take5.ranked_by_ai);
  return (
    <section aria-labelledby="batch-heading" className="flex flex-col gap-3">
      <h2 id="batch-heading" className="text-2xl font-extrabold">
        This batch, worst first
      </h2>
      {ranking.isPending && (
        <p role="status">
          Ranking the cards… This can take up to half a minute.
        </p>
      )}
      {ranking.isError && (
        <>
          <p>The cards couldn’t be ranked. Check your signal and try again.</p>
          <Button onClick={() => void ranking.refetch()}>Try again</Button>
        </>
      )}
      {ranking.data && (
        <>
          <p>
            The riskiest jobs with the least thought on the card first, blanks
            counted against them.
          </p>
          {byAi && (
            <p className="text-ink-muted">
              An AI helped choose these and wrote their reasons. Names aren’t
              sent to it.
            </p>
          )}
          <RankedList take5s={ranking.data.take5s} />
        </>
      )}
    </section>
  );
}
