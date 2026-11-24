---
id: 0045
title: ChatGPT as a second AI provider
status: in-progress
owner: claude
branch: claude/0045-chatgpt
---

## Goal

Jake, 2026-11-24: "Add chatgpt compatibility and merge with main". The app's AI jobs (the challenge question,
vague hazards, the ranking and reading paper cards) can run on OpenAI's models with `TAKE5_AI_PROVIDER=chatgpt`
and an OpenAI API key. Claude stays the default.

## Decide first

**Jake's answers, 2026-11-24:** it means the app's own AI, not ChatGPT as a coding agent; the official `openai`
package may be added. An OpenAI API key is pay-as-you-go, billed apart from a ChatGPT subscription.

## Acceptance criteria

- [ ] `TAKE5_AI_PROVIDER=chatgpt` runs every AI job on OpenAI's models, through one new adapter file, its library
  and one line in `api/app.py`; no rule, screen or other setting changes (spec F6).
- [ ] The adapter sends what it should and turns refusals, cut-off replies, empty replies and failed calls into
  `LanguageModelError`, tested against a stand-in with no network.
- [ ] The real-AI test for each provider runs only with that provider chosen and a key set.
- [ ] Jake has tried it with an OpenAI key.

## Out of scope

- Gemini or other providers; a key per provider; ChatGPT or Codex as a coding agent.

## Notes / assumptions

Added by Claude on 2026-11-24 from Jake's request and answers.
