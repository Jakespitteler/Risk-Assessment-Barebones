import type { TemplateResponse } from "../../api/take5";
import { Guidance } from "../../components/Guidance";

/** What each likelihood and consequence means, in the card's own words. */
export function RatingGuidance({ template }: { template: TemplateResponse }) {
  const scales = [
    { name: "Likelihood", levels: template.likelihood_guidance },
    { name: "Consequence", levels: template.consequence_guidance },
  ];
  return (
    <Guidance title="What do the ratings mean?">
      {scales.map(({ name, levels }) => (
        <div key={name} className="flex flex-col gap-2">
          <h3 className="font-bold">{name}</h3>
          <dl className="flex flex-col gap-2">
            {levels.map(({ level, meaning }) => (
              <div key={level}>
                <dt className="font-semibold">{level}</dt>
                <dd>{meaning}</dd>
              </div>
            ))}
          </dl>
        </div>
      ))}
    </Guidance>
  );
}
