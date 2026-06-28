<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T05:54:36Z" -->

# Agent Toolbox Dispatch Flow Refactor

## Files Changed

- `src/backend/agents/agent_toolbox.py`
- `src/backend/tests/test_agent_toolbox.py`
- `docs/refactor-logs/agent-toolbox-dispatch-flow-before.md`
- `docs/refactor-logs/agent-toolbox-dispatch-flow.md`

## Reason For Changes

- Clarified the dispatcher boundary by separating finish handling, argument parsing, error payload creation, and tool invocation.
- Kept all individual tool implementations unchanged.
- Tightened dispatcher tests around unknown tools, invalid JSON, and bad keyword arguments.

## Behavior Preservation Notes

- `finish` still returns `{"ok": True, "_finished": True}`.
- Unknown tools still return `ok=False`.
- Invalid JSON still returns an error prefixed with `bad arguments JSON:`.
- Bad keyword arguments still return an error prefixed with `bad arguments:`.
- Unexpected tool crashes are still logged and returned as `ok=False`.
- No tool schema, filesystem behavior, sandbox behavior, or role-tool mapping changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_agent_toolbox.py::TestDispatchToolCall src/backend/tests/test_agent_toolbox.py::TestGetToolsForRole`: passed, `9 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.

## Known Legacy Failures

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_agent_toolbox.py src/backend/tests/test_sandbox_security.py` currently reports `48 passed, 3 failed`.
- Failing tests are sandbox/Python-runner related, not dispatcher behavior:
  - `TestToolRunPython::test_simple_expression`
  - `TestToolRunPython::test_import_check`
  - `TestSandboxModeSelection::test_runtime_self_check_passes_in_lite_mode`

## Remaining Risks

- `tool_run_python` and sandbox execution need a separate sandbox-runtime slice.
- Tool implementations still contain broad exception handling; this pass only handled dispatcher structure.
