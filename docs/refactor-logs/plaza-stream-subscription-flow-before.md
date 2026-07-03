<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-30T11:29:00Z" -->

# Plaza Stream Subscription Flow - Before

## Scope

SSE stream subscription setup and cleanup inside `plaza_routes.stream_discussion`.

## Current Flow

1. `stream_discussion` subscribes to the discussion queue with `engine.subscribe(disc_id)`.
2. The nested `event_stream` consumes the queue.
3. A `finally` block unsubscribes with `engine.unsubscribe(disc_id, q)`.

## Behavior To Preserve

- The queue returned from `engine.subscribe` remains the live event queue.
- Cleanup still unsubscribes the same discussion id and queue object.
- Replay, status, closed, live, heartbeat, and response headers are unchanged.

## Smallest Safe Slice

Extract only subscription and unsubscription delegation.
