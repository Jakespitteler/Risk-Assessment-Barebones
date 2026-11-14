---
id: 0015
title: Change the licence so nobody but the owner may copy or use the app
status: done
owner: claude
branch: claude/project-thread-nidbht
---

## Goal

`LICENSE` is the MIT licence with Jake as the copyright holder, which lets anyone who gets a copy use, change and
share the code. Jake said (2026-11-14) the app is the property of Talison Lithium and must not be copied or used by
anyone else, using a known licence template. After Claude asked who the legal owner is, Jake chose (2026-11-14)
to be named as the owner for now.

## Acceptance criteria

- [x] `LICENSE` holds the chosen template, with the owner's exact legal name and the year.
- [x] `README.md` says who owns the app and points to `LICENSE`.
- [x] Anything else Jake's answers call for (file headers, the `Risk-Assessment` repo) is done or has its own task.
  Done: `package.json` and `backend/pyproject.toml` say the code is not open source. The `Risk-Assessment` repo
  and file headers are not wanted for now.
- [x] `docs/decisions.md` records the choice and who approved it.

## Out of scope

- Legal advice. Claude and ChatGPT are not lawyers; a lawyer should confirm the wording before it is relied on.
- The licences of the libraries the app uses. They keep their own licences, and none of them stops this.

## Notes / assumptions

The file stays named `LICENSE`, because that is the name GitHub looks for; "licence" is the Australian spelling of
the word in prose. The repo is private, so few people have a copy under the MIT terms today.

Known templates that fit, best first:

1. **A proprietary "All rights reserved" notice** (recommended, and chosen). The usual notice for privately owned
   software: copyright to the owner, no rights granted, copying or use without written permission prohibited. It
   is the only common choice that stops everyone but the owner using it.
2. **PolyForm Strict 1.0.0.** A published licence that lets anyone use the code for non-commercial purposes but not
   change or share it. It does not stop all use, so it does not match what Jake asked for.
3. **Business Source License 1.1.** Allows non-production use and turns into an open source licence after a set
   date. Not a fit, because the app would become open later.

Jake's answers (2026-11-14, in chat):

1. Owner: Jake Spitteler (the name the old MIT licence used), for now, instead of Talison Lithium. If Talison is
   to own it later, change the name in `LICENSE` and `README.md`; whether that needs a signed assignment is a
   question for a lawyer.
2. Already Talison's? Not needed while Jake is the owner.
3. Who may use it: not answered. Assumed: nobody without the owner's written permission, which is what the
   notice says. Jake can still give anyone written permission.
4. The `Risk-Assessment` repo: not for now.
5. "Whatever you recommend". Claude offered three levels: `LICENSE` and the README only; those plus the package
   files; or all of that plus a copyright line in every source file. Recommended and done: the middle one, so
   `"license": "UNLICENSED"` in `frontend/package.json` (npm's word for "nobody may use this") and
   `license = "LicenseRef-Proprietary"` in `backend/pyproject.toml`.

Jake also asked for the branch rule in `AGENTS.md` to allow the branch a tool forces, because cloud threads can
only push to `claude/project-thread-<id>`, and for open pull requests to stack. Both are in step 3 of "How work
happens".
