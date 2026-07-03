<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T03:02:16Z" -->

# Plaza Stream Status Event Flow - Before

## Scope

Current status SSE event inside `plaza_routes.stream_discussion`.

## Current Flow

1. `event_stream` computes `status_seq` after replaying historical messages.
2. If discussion messages exist, `status_seq` is `max(msg.seq + 1 for msg in disc.messages)`.
3. If no messages exist, `status_seq` is `0`.
4. It emits a `status` SSE event with `disc.status.value`.

## Behavior To Preserve

- Status event sequence calculation remains unchanged.
- Empty discussions still use status id `0`.
- Status payload remains `{"type": "status", "status": disc.status.value}`.
- Status event still emits after replay and before closed/live handling.

## Smallest Safe Slice

Extract only status event sequence calculation and formatting.
