<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T05:42:07Z" -->

# API Task Workflow Start Flow Refactor

## Files Changed

- `src/backend/agents/api.py`
- `src/backend/tests/test_request_models.py`
- `docs/refactor-logs/api-task-workflow-start-flow-before.md`
- `docs/refactor-logs/api-task-workflow-start-flow.md`

## Reason For Changes

- Reduced duplicated workflow step session-start logic across workflow advance, manual run, and resume endpoints.
- Made active-step lookup, skill config lookup, Claude session launch, workflow persistence, and monitor startup explicit helper boundaries.
- Added regression coverage for the manual `run_claude_for_task` path without starting a real process.

## Behavior Preservation Notes

- `run_claude_for_task` still returns `already_running` when the active step has a `session_id`.
- Missing active step and missing step agent still return HTTP 400.
- Resume still re-checks Token Factory, clears `token_factory_error`, starts the first resumable step, starts the monitor, writes `pipeline_resumed`, and returns the same response shape.
- Workflow state values and route contracts are unchanged.
- No database schema, public request/response format, or task-engine behavior changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_request_models.py src/backend/tests/test_task_engine.py`: passed, `42 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.

## Remaining Risks

- Other `_start_claude_session` call sites remain in longer-running monitor and pipeline paths. They should be handled in separate slices because they are tied to artifact collection and auto-advance behavior.
- `resume_blocked_task` still directly imports Token Factory; moving that behind the shared preflight helper could alter error behavior and was left unchanged.
