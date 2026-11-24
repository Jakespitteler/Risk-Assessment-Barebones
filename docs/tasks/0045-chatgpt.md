---
id: 0045
title: ChatGPT as a second AI provider
status: review
owner: claude
branch: claude/0045-chatgpt (#91)
---

## Goal

Jake, 2026-11-24: "Add chatgpt compatibility and merge with main". The app's AI jobs (the challenge question,
vague hazards, the ranking and reading paper cards) can run on OpenAI's models with `TAKE5_AI_PROVIDER=chatgpt`
and an OpenAI API key. Claude stays the default.

## Decide first

**Jake's answers, 2026-11-24:** it means the app's own AI, not ChatGPT as a coding agent; the official `openai`
package may be added. An OpenAI API key is pay-as-you-go, billed apart from a ChatGPT subscription.

## Acceptance criteria

- [x] `TAKE5_AI_PROVIDER=chatgpt` runs every AI job on OpenAI's models, through one new adapter file, its library
  and one line in `api/app.py`; no rule, screen or other setting changes (spec F6).
- [x] The adapter sends what it should and turns refusals, cut-off replies, empty replies and failed calls into
  `LanguageModelError`, tested against a stand-in with no network.
- [x] The real-AI test for each provider runs only with that provider chosen and a key set.
- [ ] Jake approves the models (spec D133): `gpt-6.2-astra`, and `gpt-6-luna` for vague hazards.
- [ ] Jake has tried it with an OpenAI key, which also confirms the model names.

## Out of scope

- Gemini or other providers; a key per provider; ChatGPT or Codex as a coding agent.

## Notes / assumptions

Added by Claude on 2026-11-24 from Jake's request and answers. OpenAI's models, API and the package's release
dates were read from OpenAI's docs and PyPI on 2026-11-24, not from memory (spec D133).

- Started with `TAKE5_AI_PROVIDER=chatgpt` and a made-up key: the log names `gpt-6.2-astra` for the question,
  ranking and cards, and `gpt-6-luna` for hazards; a call reached OpenAI, was refused for the key, and became a
  `LanguageModelError`, so the app falls back as it does for Claude. No real OpenAI key was available.
- To check with Jake: if the settings template's comment lists the provider values, add `chatgpt` there (agents
  may not edit that file).
- `scripts/try_challenge.py` and `scripts/try_vague_hazard.py` try Claude only; they now stop when another
  provider is chosen, so an OpenAI key never goes to Anthropic.

The review of `deba42a` found no high problems. Fixed from it: any status but `completed` is refused, not only
`incomplete`; `store=False`, so OpenAI keeps no calls; commentary before the answer is left out; no `httpx2`
import in the app (typed with `openai.DefaultHttpxClient`, as the Claude adapter does); the try scripts' guard;
a more faithful stand-in and the limits checked in tests. Left for Jake: `gpt-6.2-astra` is newer than the
pinned package's list of model names, which only a real key can confirm; `"detail": "high"` for card photos may
be worth comparing with `"original"` then. The branch starts from `main`, as Jake asked, not stacked on the
open pull requests #87, #88 and #90.
