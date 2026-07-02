<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T03:00:25Z" -->

# Plaza Stream Replay Message Flow - Before

## Scope

Historical message replay inside `plaza_routes.stream_discussion`.

## Current Flow

1. `event_stream` iterates over `disc.messages`.
2. It skips messages whose `seq` is non-negative and less than or equal to `last_seq`.
3. It emits all other messages as SSE `message` events.
4. Each replay event uses `msg.seq` as the SSE id.

## Behavior To Preserve

- Already received non-negative sequence numbers are still skipped.
- Negative sequence messages are still replayed.
- Replay payload remains `{"type": "message", "message": msg.to_dict()}`.
- Replay event id remains `str(msg.seq)`.

## Smallest Safe Slice

Extract only historical message replay event generation.
