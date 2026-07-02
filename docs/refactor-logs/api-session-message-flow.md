<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:46:11Z" -->

# API Session Message Flow Refactor

## Files Changed

- `src/backend/agents/api.py`
- `src/backend/tests/test_api_session_message.py`
- `docs/refactor-logs/api-session-message-flow-before.md`
- `docs/refactor-logs/api-session-message-flow.md`

## Reason For Changes

- Clarified `send_session_message` by separating session lookup, message construction, assistant message construction, token metric accounting, and tool metric accounting.
- Added focused regression coverage for the route-level behavior: returning the user message, appending assistant reply, recording real token usage, and recording harness tool invocation metrics.

## Behavior Preservation Notes

- The public route path, request model, status code, and return shape are unchanged.
- Missing sessions still raise HTTP 404.
- The endpoint still returns the user message rather than the assistant message.
- Assistant message metadata fields remain `model`, `provider`, and `latency_ms`.
- Real usage totals still take precedence over estimated token counts.
- Harness tool invocations still take precedence over parsed text invocations.
- API contracts, database schema, and request/response formats were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_api_session_message.py src/backend/tests/test_agent_skill_binding.py::TestAgentSkillBinding::test_generate_agent_response_uses_team_local_skill_instructions_and_required_tools src/backend/tests/test_permissions_and_secrets.py::TestToolPermissions::test_generate_agent_response_filters_blocked_tools`: passed, `3 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- `_sessions`, `_agent_metrics`, and `_agent_logs` remain in-memory globals; persistence and concurrency semantics were intentionally left untouched.
- Parsed text tool invocation detection still depends on `_parse_tool_invocations`; that parser is outside this slice.
- `src/backend/agents/api.py` remains large and still needs route-family extraction in later rounds.
