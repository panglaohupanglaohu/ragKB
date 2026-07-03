<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-07-01T00:00:00Z" -->

# Task Trace Helper Module Flow Refactor

## Files Changed

- `src/backend/agents/task_trace.py`
- `src/backend/agents/api.py`
- `docs/refactor-logs/task-trace-helper-module-flow-before.md`
- `docs/refactor-logs/task-trace-helper-module-flow.md`

## Reason For Changes

- Moved pure task artifact and trace helper logic out of `api.py`.
- Kept existing private `api.py` helper names as compatibility wrappers for current tests and callers.
- Reduced route module ownership to orchestration and API-facing seams.
- Pointed task artifact helper tests at `task_trace.py` directly so the new module boundary has explicit coverage.
- Added direct coverage for trace summary filtering, trace event filtering, log tail parsing, and NDJSON export iterators.
- Added direct coverage for terminal sync state, evolution sync kwargs, and trace payload builders.
- Added direct coverage for trace event payload enrichment and pipeline/global JSONL persistence.

## Behavior Preservation Notes

- Trace context, changed files, test result, workflow summary, diff preview, JSONL persistence, and artifact payload shapes are unchanged.
- `api.py` still owns TaskEngine lookup, evolution sync, broadcasting, and route handlers.
- `api.py` still exposes compatibility wrappers for existing private helper names.

## Validation Result

- `.\.venv\Scripts\python.exe -m pytest src/backend/tests/test_plaza_task_artifact_bridge.py -q` -> 23 passed.
- `.\.venv\Scripts\python.exe -m pytest src/backend/tests/test_plaza_dispatch.py src/backend/tests/test_plaza_evolution_bridge.py src/backend/tests/test_plaza_retry_escalation.py src/backend/tests/test_plaza_task_artifact_bridge.py -q` -> 88 passed.

## Remaining Risks

- `api.py` still owns evolution sync and broadcast helper orchestration.
- Historical unsigned `docs/` plan/todos files still block strict docs signoff across the full docs tree.
