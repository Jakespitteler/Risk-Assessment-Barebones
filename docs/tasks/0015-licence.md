---
id: 0015
title: Change the licence so the app belongs to Talison Lithium and nobody else may copy or use it
status: in-progress
owner: claude
branch: claude/project-thread-nidbht
---

## Goal

`LICENSE` is the MIT licence with Jake as the copyright holder, which lets anyone who gets a copy use, change and
share the code. Jake said (2026-11-14) the app is the property of Talison Lithium and must not be copied or used by
anyone else, using a known licence template.

## Acceptance criteria

- [ ] `LICENSE` holds the chosen template, with the owner's exact legal name and the year.
- [ ] `README.md` says who owns the app and points to `LICENSE`.
- [ ] Anything else Jake's answers call for (file headers, the `Risk-Assessment` repo) is done or has its own task.
- [ ] `docs/decisions.md` records the choice and who approved it.

## Out of scope

- Legal advice. Claude and ChatGPT are not lawyers; Talison's legal team should confirm the wording.
- The licences of the libraries the app uses. They keep their own licences, and none of them stops this.

## Notes / assumptions

The file stays named `LICENSE`, because that is the name GitHub looks for; "licence" is the Australian spelling of
the word in prose. The repo is private, so few people have a copy under the MIT terms today.

Known templates that fit, best first:

1. **A proprietary "All rights reserved" notice** (recommended). The usual notice for company-owned software:
   copyright to the company, no rights granted, copying or use without written permission prohibited. It is the
   only common choice that stops everyone outside the company using it.
2. **PolyForm Strict 1.0.0.** A published licence that lets anyone use the code for non-commercial purposes but not
   change or share it. It does not stop all use, so it does not match what Jake asked for.
3. **Business Source License 1.1.** Allows non-production use and turns into an open source licence after a set
   date. Not a fit, because the app would become open later.

Questions for Jake (he answers in chat, and the thread updates this file):

1. What is the owner's exact legal name, as it appears on Talison's documents (for example "Talison Lithium Pty
   Ltd")?
2. Does Talison own the work already, for example because you built it as part of your job, or are you giving it
   to them? Has anyone at Talison agreed to it, and should their legal team check the notice before it is merged?
3. Who may use it: Talison employees and contractors only, or also others with written permission?
4. Should the `Risk-Assessment` repo get the same licence?
5. A short copyright line at the top of each source file as well, or only `LICENSE` and the README?
