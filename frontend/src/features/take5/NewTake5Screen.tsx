import { useState } from "react";
import { useTemplate } from "../../api/take5";
import { Button } from "../../components/Button";
import { Screen } from "../../components/Screen";
import type { Take5FormProps } from "./Take5Form";
import { Take5Form } from "./Take5Form";

/**
 * A new Take 5: load the card from the back end, then show the form, which draws its
 * own screen and top bar.
 */
export function NewTake5Screen(
  props: Omit<Take5FormProps, "template" | "onStartAfresh">,
) {
  const template = useTemplate();
  // A new key opens a new, empty form after a draft runs out.
  const [formKey, setFormKey] = useState(0);
  if (template.isSuccess)
    return (
      <Take5Form
        key={formKey}
        template={template.data}
        {...props}
        onStartAfresh={() => {
          setFormKey((key) => key + 1);
        }}
      />
    );
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
    </Screen>
  );
}
