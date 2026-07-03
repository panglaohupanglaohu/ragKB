<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:04:02Z" -->

# Plaza Interjection Pause State Flow - Before

## Scope

Paused-state broadcast at the start of `PlazaEngine.handle_live_interjection`.

## Current Flow

1. After context resolution, `handle_live_interjection` enters the discussion lock.
2. It broadcasts `interjection_state` with `state="paused"` and a fixed message.
3. The no-LLM or LLM-backed correction branch runs afterward.

## Behavior To Preserve

- Broadcast still happens after the discussion lock is acquired.
- Payload type, state, and message remain unchanged.
- No-LLM and LLM-backed branches remain unchanged.

## Smallest Safe Slice

Extract only the paused-state broadcast payload into a helper.
