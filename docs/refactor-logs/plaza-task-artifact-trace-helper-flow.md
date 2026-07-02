<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-30T11:14:00Z" -->

# Plaza Task Artifact Trace Helper Flow Refactor

## Files Changed

- `src/backend/agents/api.py`
- `docs/refactor-logs/plaza-task-artifact-trace-helper-flow-before.md`
- `docs/refactor-logs/plaza-task-artifact-trace-helper-flow.md`

## Reason For Changes

- Restored missing plaza task artifact, terminal-state, and trace helper seams after earlier API refactors.
- Reused existing pipeline events and task engine state instead of adding a separate trace store.
- Persisted trace events to per-task and global JSONL logs for existing trace views and export.

## Behavior Preservation Notes

- `get_recent_trace_summaries`, `get_recent_trace_events`, and NDJSON exports remain backed by current task state.
- Evolution item sync still delegates to `SystemEvolutionChannel.sync_task_outcome`.
- Explicit verify tests keep items in `verify_pending`; passing artifacts without explicit verify tests auto-close linked items.

## Validation Result

- `.\.venv\Scripts\python.exe -m pytest src/backend/tests/test_plaza_task_artifact_bridge.py -q` -> 16 passed.
- `.\.venv\Scripts\python.exe -m pytest src/backend/tests/test_plaza_dispatch.py src/backend/tests/test_plaza_evolution_bridge.py src/backend/tests/test_plaza_retry_escalation.py src/backend/tests/test_plaza_task_artifact_bridge.py -q` -> 85 passed.
- `git diff --check` -> passed with existing CRLF conversion warnings for touched Python files.

## Remaining Risks

- `stream_discussion` still has inline live event and heartbeat handling.
- `api.py` trace helper section is larger than ideal and should be split in a later slice if the project accepts a new module boundary.
