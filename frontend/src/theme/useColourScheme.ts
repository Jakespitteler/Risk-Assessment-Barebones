import { useCallback, useEffect, useState, useSyncExternalStore } from "react";
import {
  choiceAfterSwitch,
  phoneScheme,
  readFreshChoice,
  saveChoice,
  schemeToShow,
  showScheme,
  watchPhoneScheme,
  type ColourScheme,
  type SchemeChoice,
} from "./colourScheme";

/**
 * The scheme on screen, and a function that switches to the other one.
 *
 * It follows the phone's setting as it changes, and forgets a choice from the switch once
 * the phone has changed since it was made.
 */
export function useColourScheme(): {
  showing: ColourScheme;
  switchScheme: () => void;
} {
  const phone = useSyncExternalStore(watchPhoneScheme, phoneScheme);
  const [choice, setChoice] = useState<SchemeChoice | null>(() =>
    readFreshChoice(phoneScheme()),
  );
  const showing = schemeToShow(phone, choice);

  useEffect(() => {
    showScheme(showing);
  }, [showing]);

  // Once the phone changes, a choice from the switch has had its day.
  useEffect(
    () =>
      watchPhoneScheme(() => {
        saveChoice(null);
        setChoice(null);
      }),
    [],
  );

  const switchScheme = useCallback(() => {
    const nextChoice = choiceAfterSwitch(phone, showing);
    saveChoice(nextChoice);
    setChoice(nextChoice);
  }, [phone, showing]);

  return { showing, switchScheme };
}
