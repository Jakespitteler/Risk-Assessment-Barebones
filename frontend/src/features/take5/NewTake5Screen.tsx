import { useTemplate } from "../../api/take5";
import { Button } from "../../components/Button";
import { Screen } from "../../components/Screen";
import { SavedListLink } from "./SavedListLink";
import type { Take5FormProps } from "./Take5Form";
import { Take5Form } from "./Take5Form";

/**
 * A new Take 5: load the card from the back end, then show the form. The first page
 * also links to the saved Take 5s; later pages don't, so nothing pulls the worker away
 * mid-way.
 */
export function NewTake5Screen(props: Omit<Take5FormProps, "template">) {
  const template = useTemplate();
  return (
    <Screen
      subtitle="Before you start"
      aside={props.stage.page === "job" && <SavedListLink />}
    >
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
