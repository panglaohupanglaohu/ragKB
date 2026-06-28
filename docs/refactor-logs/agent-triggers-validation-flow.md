<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:01:49Z" -->

# Agent Triggers Validation Flow Refactor

## Files Changed

- `src/backend/agents/agent_triggers.py`
- `src/backend/tests/test_agent_triggers.py`
- `docs/refactor-logs/agent-triggers-validation-flow-before.md`
- `docs/refactor-logs/agent-triggers-validation-flow.md`

## Reason For Changes

- Clarified trigger validation by separating type-specific config validation from task-focus validation.
- Clarified URL safety checks by separating scheme, host/IP blocking, and response payload formatting.
- Added focused tests for focus requirements, focus checker failures, private/local URL rejection, and public domain allowance.

## Behavior Preservation Notes

- Public function signatures are unchanged.
- Existing validation error text is unchanged.
- Unknown trigger types still return immediately.
- Focus checker exceptions are still debug-logged and ignored.
- Domain names are still allowed without DNS resolution.
- URL safety response shape remains `{"safe": bool, "reason": str}`.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_agent_triggers.py`: passed, `7 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.

## Remaining Risks

- Cron parsing and next-fire calculation are still separate flows and were not changed.
- Poll execution behavior is not implemented in this module; this pass only covers validation and URL safety.
