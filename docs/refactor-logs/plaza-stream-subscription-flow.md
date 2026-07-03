<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-30T11:31:00Z" -->

# Plaza Stream Subscription Flow Refactor

## Files Changed

- `src/backend/agents/plaza_routes.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-stream-subscription-flow-before.md`
- `docs/refactor-logs/plaza-stream-subscription-flow.md`

## Reason For Changes

- Moved stream subscription and cleanup delegation into small helpers.
- Added focused coverage that the helpers pass through the discussion id and queue object.

## Behavior Preservation Notes

- The `StreamingResponse` setup and headers are unchanged.
- The live queue loop still consumes the queue returned by `engine.subscribe`.
- Cleanup still runs from the existing `finally` block.

## Validation Result

- `.\.venv\Scripts\python.exe -m pytest src/backend/tests/test_plaza_dispatch.py -q` -> 55 passed.
- `.\.venv\Scripts\python.exe -m pytest src/backend/tests/test_plaza_dispatch.py src/backend/tests/test_plaza_evolution_bridge.py src/backend/tests/test_plaza_retry_escalation.py src/backend/tests/test_plaza_task_artifact_bridge.py -q` -> 88 passed.
- `git diff --check` -> passed with existing CRLF conversion warnings for touched Python files.

## Remaining Risks

- `stream_discussion` still defines `event_stream` inline.
- `api.py` trace helper section is larger than ideal and should be split in a later slice if the project accepts a new module boundary.
