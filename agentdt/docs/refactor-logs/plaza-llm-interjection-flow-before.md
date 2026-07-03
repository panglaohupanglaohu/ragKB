<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:22:48Z" -->

# Plaza LLM Interjection Flow - Before

## Scope

LLM-backed branch inside `PlazaEngine.handle_live_interjection`.

## Current Flow

1. The branch chooses an interjection speaker and asks the moderator LLM for redirect text plus `NEXT`.
2. It parses and normalizes the moderator reply.
3. It publishes the moderator redirect message.
4. It optionally generates the nominated reply.
5. It generates up to two supplementary replies.
6. It generates the revised plan, publishes plan update, saves the plaza, and returns the message bundle.

## Behavior To Preserve

- Speaker selection, prompt construction, parsing, nomination prefix, and publication helpers remain unchanged.
- Nominated and supplementary reply metadata remain unchanged.
- Plan update helper and return shape remain unchanged.

## Smallest Safe Slice

Move the LLM-backed branch orchestration into `_handle_llm_interjection` after earlier prompt and publish helpers are already in place.
