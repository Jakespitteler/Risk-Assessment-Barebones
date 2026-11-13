import { useTemplate } from "../../api/take5";
import { Button } from "../../components/Button";
import { Screen } from "../../components/Screen";
import type { Take5FormProps } from "./Take5Form";
import { Take5Form } from "./Take5Form";

/** A new Take 5: load the card from the back end, then show the form. */
export function NewTake5Screen(props: Omit<Take5FormProps, "template">) {
  const template = useTemplate();
  return (
    <Screen subtitle="Before you start">
      {template.isPending && (
        <h1 className="text-3xl font-extrabold">Loading your Take 5…</h1>
      )}
      {template.isError && (
        <>
          <h1 className="text-3xl font-extrabold">
            The card couldn’t be loaded
          </h1>
          <p>Check your signal and try again.</p>
          <Button onClick={() => void template.refetch()}>Try again</Button>
        </>
      )}
      {template.isSuccess && <Take5Form template={template.data} {...props} />}
    </Screen>
  );
}
