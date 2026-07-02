<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-30T10:51:00Z" -->

# Plaza Stream Closed Event Flow - Before

## Scope

Closed-discussion synthetic SSE events inside `plaza_routes.stream_discussion`.

## Current Flow

1. After replay and status emission, `event_stream` checks `disc.status`.
2. If closed and `disc.plan` exists, it emits `plan_updated` with `status_seq + 1`.
3. It emits `discussion_end` with the next sequence id.
4. It returns without waiting for live queue events.

## Behavior To Preserve

- Closed discussions still emit synthetic events after status.
- `plan_updated` is only emitted when `disc.plan` is truthy.
- `discussion_end` always follows with the next sequence id.
- Closed discussions still return before the live event loop.

## Smallest Safe Slice

Extract only closed-discussion synthetic event generation.
