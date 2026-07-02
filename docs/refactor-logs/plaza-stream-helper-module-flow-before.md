<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-07-01T00:00:00Z" -->

# Plaza Stream Helper Module Flow Before Refactor

## Current Flow

- `src/backend/agents/plaza_routes.py` owns both Plaza HTTP routes and the discussion SSE helper mechanics.
- Stream helper responsibilities include SSE formatting, `Last-Event-ID` parsing, replay message generation, closed discussion synthetic events, live event formatting, heartbeat formatting, and subscribe/unsubscribe delegation.
- Tests call the private helper names through `agents.plaza_routes`.

## Refactor Target

- Move the stream helper mechanics into a dedicated module.
- Keep `plaza_routes.py` as the compatibility import surface for existing tests and callers.
- Preserve `stream_discussion` behavior and response format.

## Existing Verification Surface

- `src/backend/tests/test_plaza_dispatch.py` covers stream formatting, replay, status, closed events, live events, heartbeat, and subscription delegation.
