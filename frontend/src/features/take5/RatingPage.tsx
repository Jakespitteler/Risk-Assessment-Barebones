import type { RatingChoice, TemplateResponse } from "../../api/take5";
import { Card } from "../../components/Card";
import { RatingPicker } from "../../components/RatingPicker";
import { RatingGuidance } from "./RatingGuidance";

/** Step 3: rate one hazard, before or after its controls. */
export function RatingPage({
  when,
  path,
  rating,
  template,
  errorFor,
  onChange,
}: {
  when: "before" | "after";
  path: string;
  rating: RatingChoice;
  template: TemplateResponse;
  errorFor: (path: string) => string | undefined;
  onChange: (rating: RatingChoice) => void;
}) {
  // An error on the whole rating, such as controls raising the score (spec R6).
  const ratingError = errorFor(path);
  return (
    <Card>
      <p>
        {when === "before"
          ? "Think about this hazard with no controls in place."
          : "Think about what could still happen with your controls in place."}
      </p>
      {ratingError && (
        <p
          id={path}
          tabIndex={-1}
          aria-invalid="true"
          className="font-semibold text-danger"
        >
          {ratingError}
        </p>
      )}
      <RatingGuidance template={template} />
      <RatingPicker
        matrix={template.matrix}
        rating={rating}
        errors={{
          likelihood: errorFor(`${path}.likelihood`),
          consequence: errorFor(`${path}.consequence`),
        }}
        onChange={onChange}
      />
    </Card>
  );
}
