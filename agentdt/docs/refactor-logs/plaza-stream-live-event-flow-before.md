<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-30T11:22:00Z" -->

# Plaza Stream Live Event Flow - Before

## Scope

Live queue event formatting and heartbeat emission inside `plaza_routes.stream_discussion`.

## Current Flow

1. `event_stream` waits up to 30 seconds for a queue event.
2. If the event contains a message with a non-negative `seq`, that sequence is used as the SSE id.
3. The event is formatted as an SSE data frame.
4. `discussion_end` breaks the live loop.
5. Timeout emits an id-less heartbeat frame.

## Behavior To Preserve

- Non-negative message sequence ids remain SSE ids.
- Negative or missing message sequence ids still produce id-less frames.
- `discussion_end` still ends the live event loop.
- Timeout heartbeat payload remains `{"type": "heartbeat"}`.

## Smallest Safe Slice

Extract live event formatting, end-event detection, and heartbeat frame generation.
