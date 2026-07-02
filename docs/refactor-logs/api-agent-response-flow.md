<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:39:52Z" -->

# API Agent Response Flow Refactor

## Files Changed

- `src/backend/agents/api.py`
- `docs/refactor-logs/api-agent-response-flow-before.md`
- `docs/refactor-logs/api-agent-response-flow.md`

## Reason For Changes

- Clarified `_generate_agent_response` by separating team model synchronization, tool schema construction, parameter type normalization, system prompt construction, skill instruction lookup, tool execution, and follow-up response generation.
- Restored the tested response-boundary behavior where team-local skill instructions and required tools are included.
- Restored tested permission filtering so blocked tools are not exposed to the LLM tool schema.

## Behavior Preservation Notes

- `_generate_agent_response` keeps the same signature and `(response_text, result_object)` return shape.
- Public session routes and request/response formats were not changed.
- Team default model synchronization remains scoped to calls with `team_id`.
- Initial chat still receives agent/team/session attribution, system prompt, and available tool schemas.
- Tool-result follow-up chat still keeps team/session attribution and the same system prompt.
- Tool invocation result mutation remains in place for downstream metrics/logging.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_agent_skill_binding.py::TestAgentSkillBinding::test_generate_agent_response_uses_team_local_skill_instructions_and_required_tools src/backend/tests/test_permissions_and_secrets.py::TestToolPermissions::test_generate_agent_response_filters_blocked_tools`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- `send_session_message` still mixes message persistence, metrics, token accounting, and tool metric attribution; that should be a separate route-level slice.
- Tool execution follow-up still relies on global `ToolExecutor` and does not pass permission context into execution; this was not changed to avoid altering runtime behavior.
- `src/backend/agents/api.py` remains very large and should continue to be reduced by route family.
