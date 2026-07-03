<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:54:57Z" -->

# Plaza Stream SSE Format Flow - Before

## Scope

SSE frame string formatting inside `plaza_routes.stream_discussion`.

## Current Flow

1. `stream_discussion.event_stream` formats replayed messages inline.
2. It formats status, closed-plan, closed-end, live, and heartbeat events inline.
3. Each frame uses optional `id: ...` followed by `data: ...` and a blank line.
4. JSON serialization uses `ensure_ascii=False`.

## Behavior To Preserve

- SSE frame text remains `id: <id>\ndata: <json>\n\n` when an id exists.
- SSE frame text remains `data: <json>\n\n` when no id exists.
- Unicode payloads remain unescaped.
- Event ids and event ordering remain unchanged.

## Smallest Safe Slice

Extract only SSE frame formatting.
