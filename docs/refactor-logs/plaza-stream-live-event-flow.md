<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-30T11:22:00Z" -->

# Plaza Stream Live Event Flow Refactor

## Files Changed

- `src/backend/agents/plaza_routes.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-stream-live-event-flow-before.md`
- `docs/refactor-logs/plaza-stream-live-event-flow.md`

## Reason For Changes

- Moved live SSE event formatting into `_format_live_stream_event`.
- Moved `discussion_end` detection into `_is_discussion_end_event`.
- Moved heartbeat frame generation into `_build_stream_heartbeat_event`.

## Behavior Preservation Notes

- Replay, status, closed-discussion, cleanup, and response headers are unchanged.
- Live message events still use non-negative message sequence ids.
- Heartbeats still emit id-less SSE frames.

## Validation Result

- `.\.venv\Scripts\python.exe -m pytest src/backend/tests/test_plaza_dispatch.py -q` -> 54 passed.
- `.\.venv\Scripts\python.exe -m pytest src/backend/tests/test_plaza_dispatch.py src/backend/tests/test_plaza_evolution_bridge.py src/backend/tests/test_plaza_retry_escalation.py src/backend/tests/test_plaza_task_artifact_bridge.py -q` -> 87 passed.

## Remaining Risks

- `stream_discussion` still owns subscription setup and cleanup inline.
- `api.py` trace helper section is larger than ideal and should be split in a later slice if the project accepts a new module boundary.
