---
id: 0024
title: Dark mode
status: done
owner: claude
branch: claude/project-thread-ajrmy7
---

## Goal

Jake asked for a dark mode on 2026-11-18. Today every screen is dark text on a light page, whatever the phone is
set to. A dark mode gives the same screens as light text on a dark page, for a night shift or a worker whose phone
is set to dark. It must not cost readability in the bright sun the spec plans for ("Where and when it is used"),
and a risk band or a verdict must mean the same thing at a glance in either mode.

To be direct about where it sits: dark mode doesn't make anyone think harder about a risk, which is this
project's main aim. Its case is comfort, and the spec's own aim that the Take 5 "is not resented": a white
screen at 2 am is resented. That is why it is placed after the tasks that make the worker think (question 11).

## Decide first

The questions for Jake, each with Claude's recommended pick. Jake answers them when the task starts.

1. **Why dark mode, and for whom?** For example: crews on night shift, workers who keep their phone dark all day,
   or Jake's own preference. Recommended: say which, because it decides question 2's default. Claude assumed
   night shift and phones already set to dark. Write the answer under "Where and when it is used" in the spec.
2. **What decides the mode?** Options:
   - (a) The phone's own light or dark setting, with no switch in the app. The least to build, but a worker whose
     phone is dark all day gets dark screens in full sun, and can't change it without leaving the app.
   - (b) A switch in the app only, light to begin with. Ignores what the worker already chose for their phone.
   - (c) The phone's setting to begin with, and a switch in the app that overrides it.
   - Recommended: (c). Dark text on a light page reads best in direct sun, so the worker needs a way back to
     light without going into the phone's settings, standing at the job with gloves on.
3. **How long does a choice made with the switch last?** Options:
   - (a) Until the worker switches back. Then the app never follows the phone again unless it offers a third
     choice, "Same as my phone", which makes the switch a three-way control.
   - (b) Until the phone's own setting next changes. A phone set to go dark at sunset takes the app with it, and
     the switch stays a simple two-way button.
   - (c) For this Take 5 only.
   - Recommended: (b). It needs no third choice, and a phone that changes with the time of day keeps working.
     To notice a change made while the app was closed, the app keeps the phone's setting from the moment of the
     choice beside the choice itself.
4. **Where is the switch?** The app has no settings screen. The top bar on every screen holds the "5", the
   screen's name and, on some screens, one control at the right (the "Leave" button or the "Saved Take 5s"
   link). Options:
   - (a) A button in the top bar on every screen, the full 48 px of a tap target, with a sun or moon picture and a
     label a screen reader reads ("Switch to dark" or "Switch to light").
   - (b) Only on the first screen and the saved list.
   - (c) A new settings screen.
   - Recommended: (a). The moment it is needed, walking out of the crib room into the sun, is often halfway
     through a Take 5. Screenshots at 360 px must show it fits beside "Saved Take 5s", the longer of the two,
     without crowding.
5. **Where is the choice kept?** Recommended: on the phone (`localStorage`), as the worker's name is. It is not
   saved with a Take 5 and not sent to the back end, so the API and the data model don't change. The front end
   still holds no rules: this is how a screen looks, not a rule about the Take 5.
6. **The risk band colours.** Today `RiskBadge.tsx` fills each band with its own colour and text (Low green,
   Moderate yellow, High orange, Extreme red). Recommended: keep the same fill and text colours in both modes, so
   a band looks the same everywhere and a worker learns it once. On a dark page, add a thin light edge so the
   badge's shape still shows. The band's name is always written beside the score (spec F3), so the colour is
   never the only sign.
7. **The verdict, warning and problem colours.** "Good to go" is a green panel, "Don't start yet" a red one, a
   warning amber and a problem red on a pale fill. Recommended: the same colour for the same meaning in both
   modes, in darker fills or lighter text on the dark page as contrast needs. The page itself is near-black (a
   very dark slate), not pure black, because white text on pure black smears for many people's eyes. Two more
   need a dark value too, or they vanish on a dark page: the main button (a near-black fill today) and the blue
   focus outline (`outline-blue-700`, on about 10 controls), which must still stand out 3 to 1 from the page.
8. **How much contrast, and how it is checked.** The spec asks for high contrast. Options for the level:
   - WCAG 2.2 AA: 4.5 to 1 for text, 3 to 1 for large text and for the edges of buttons and boxes.
   - AAA for body text: 7 to 1. Stricter, and kinder in sun.
   - Recommended: AA everywhere and AAA for body text, in both modes.

   Options for the check:
   - (a) A small Vitest test that works out the contrast of each pair of named colours. No new dependency, but it
     only checks the pairs written into it, not the screens as drawn.
   - (b) `@axe-core/playwright`, Deque's accessibility checker, run on each screen in both modes in the Playwright
     tests. It checks the real pages, and finds other problems too, such as a button with no name. It is a new
     development dependency, so it needs Jake's approval and an entry in `docs/decisions.md`.
   - Recommended: (b). It is the mainstream tool for this, and it checks what the worker actually sees. Its usual
     contrast rule checks AA only. AAA is a separate rule (`color-contrast-enhanced`) that covers all text, not
     only body text, so the level picked above decides which rules the tests turn on. Anything else it finds that
     isn't about colour is noted in this file, not fixed in this task.
9. **How the colours are written.** Today about 60 lines in 29 files name a Tailwind colour directly
   (`bg-white`, `text-slate-700` and so on). Options:
   - (a) Add a `dark:` class beside each one. Tailwind's standard way, but every colour is written twice, and a
     new component can leave one out without anyone noticing.
   - (b) Name each colour by its job once (for example the page, the ink, a panel, a danger and a caution colour)
     in `frontend/src/index.css`, as Tailwind 4's theme variables with a light and a dark value, and have the
     components use those names. Every component is touched once, but after that a new component gets dark mode
     for free.
   - Recommended: (b), in two stacked PRs to stay near AGENTS.md's ~400-line guide. The first moves to the named
     colours and changes nothing on screen, so its screenshots match today's. The second adds dark mode and the
     switch.
10. **No flash of the wrong mode.** Recommended: a few lines in `index.html` set the mode before the app draws,
    so a dark phone never flashes a white screen at night. The page also tells the browser its mode
    (`color-scheme`), so the browser's own parts, such as scroll bars and the text boxes' default colours, match.
    A `theme-color` line does the same for the phone browser's address bar.
11. **Where it goes in the order of work.** Recommended: after 0013, before 0021 (which waits for hosting). It
    depends on no other task, so Jake can move it anywhere; it was not put ahead of 0008 without his say.

## Jake's answers (2026-11-19)

"Go with all your recommendations", with two additions: question 1, "that and just for looks"; question 6, "yes,
choose an accent that looks good on both". So: 1 night shift, phones set to dark, and looks (spec D64); 2 (c)
(D65); 3 (b) (D66); 4 (a) (D67); 5 on the phone (D68); 6 the same band colours, with one grey edge (slate-400)
that shows on a light page and a dark one (D69); 7 as recommended (D70); 8 7 to 1 for text, checked by
`@axe-core/playwright`, a new development dependency he approved (D71); 9 (b), in two stacked pull requests (D72);
10 as recommended (D73); 11 now (D74).

## Acceptance criteria

- [x] With no choice made, the app follows the phone's light or dark setting.
- [x] The switch (if Jake picks one) changes the mode at once, is reached by role and label in tests, and the
  choice lasts as question 3 decides, including after a reload.
- [x] Every screen and state is readable in both modes, at the contrast question 8 sets, checked as question 8
  decides.
- [x] Risk bands, verdicts, warnings and problems keep their meaning in both modes, as questions 6 and 7 decide.
- [x] No white flash when a dark phone opens the app.
- [x] Vitest covers the switch; Playwright covers following the phone (its `colorScheme` setting), the switch,
  and the choice surviving a reload.
- [x] Phone-width (360 px) screenshots of every screen in both modes are attached to the PR, with dark ones saved
  under the same names ending in `-dark`.
- [x] `docs/spec.md` is updated: "Where and when it is used", a feature entry for light and dark, and the
  decisions table. `docs/architecture.md` says where the colours and the switch live.
- [x] All checks pass.

## Out of scope

- Switching on the light around the phone. Browsers don't let a web page read the light sensor, except Chrome
  behind a setting.
- A choice of colour themes beyond light and dark, or a company's own colours.
- Changing the risk band colours themselves, or any wording.
- Saving the choice on the server, or with a worker's Take 5s.

## Notes / assumptions

- Asked for by Jake on 2026-11-18, as a task file only. Written after task 0022 (PRs 36 and 37), on top of them.
- Today: `frontend/src/index.css` is only `@import "tailwindcss";`, so it is Tailwind 4. Its `dark:` variant
  follows the phone by default; a switch needs a `@custom-variant dark` line keyed on a class or attribute on the
  page. Nothing new to install for the mode itself.
- `Screen.tsx` draws the page colour (`bg-stone-100`) and the top bar on every screen. `RiskBadge.tsx` holds the
  band colours. `VerdictPanel.tsx`, `Notice.tsx` and `Warning.tsx` hold the verdict, problem and warning colours.
- The worker's name is kept in `localStorage` by `useTake5Draft.ts` (`read()` and `write()`), which a stored
  mode can follow.
- `playwright.config.ts` runs at 360 px with no `colorScheme`, so today's screenshots are light whatever the
  computer is set to. Keep it that way for the existing tests.
- Vitest's pretend browser (jsdom) has no `window.matchMedia`, which is how the app reads the phone's setting,
  so the Vitest tests need a small stand-in for it.
- If task 0013 is done first, any rule this task adds to the spec needs a test named after it to pass 0013's
  check. With the recommended picks it adds a feature entry, not a scoring or thinking rule.
- Assumption: night shift and phones already set to dark are the reasons (question 1).
- Built 2026-11-19 in two stacked pull requests. The first (#53, branch `claude/project-thread-ajrmy7`) names
  every colour by its job and changes nothing on screen except one shade: a text box with a gap now has the same
  red edge as its message (red-800, was red-700). The second (branch `claude/0024-dark-mode`) adds dark mode.
- Based on `main`, not stacked on another agent's open #51 (0013) and #52 (0029): this task touches only the front
  end and its docs, so they don't overlap.
- To reach 7 to 1 in light, a step not yet reached in the step bar now uses the quieter ink, slate-700 (was
  slate-600, 6.95 to 1). With that, the quietest ink was the same as the quieter one in both modes, so it was
  dropped.
- The top bar at 360 px: the switch is 44 px wide and 48 px high, "Saved Take 5s" never wraps, and on the job
  page "Before you start" wraps onto two lines beside it. Every other screen's name fits on one line.
- Every browser test now runs twice, on a light phone and a dark one, and every screenshot is checked by axe. It
  takes about 2.7 minutes instead of 1.2. `@axe-core/playwright` 4.14.0 brings `axe-core` 4.14.1.
- The rate-a-risk screen (`/rate-risk`, from task 0002) has no top bar, so no switch; it follows the phone, or
  the last choice.
- A choice made before the phone changed, while the app was closed, is forgotten when the app opens. A phone whose
  setting changes twice while the app is closed (dark at sunset, light by morning) can't be told apart from one
  that never changed, so an old choice can come back then. Accepted: it needs the app closed all night.
- The focus outline in dark (blue-400) is about 7 to 1 on the page, checked by hand: axe has no rule for the
  contrast of an outline.
- Reviewed by a separate reviewer agent on 2026-11-19. Fixed from its findings: axe ran only its contrast rule
  (now every WCAG 2.2 AA rule as well), the no-flash test could not fail, `/rate-risk` didn't follow the phone
  while open, the start-up lines read a broken choice differently from the app, a stale choice was kept, and the
  saved list's hover didn't show in dark.
