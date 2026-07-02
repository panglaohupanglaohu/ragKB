<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:27:24Z" -->

# Plaza Agent Content Retry Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `docs/refactor-logs/plaza-agent-content-retry-flow-before.md`
- `docs/refactor-logs/plaza-agent-content-retry-flow.md`

## Reason For Changes

- Moved retry-loop details out of `_generate_agent_content`.
- Added `_generate_agent_content_with_retries` so `_generate_agent_content` now reads as degraded check plus token attribution boundary.

## Behavior Preservation Notes

- `_generate_agent_content_with_retries` is called inside `token_scope`, preserving plaza token attribution.
- Retry count, retry sleep, timeout fallback, offline fallback, and escalation behavior are unchanged.
- No public API, response shape, database schema, or request format changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_retry_escalation.py src/backend/tests/test_plaza_token_attribution.py`: passed, `11 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- Timeout fallback and offline fallback helpers still own side effects and can be reviewed in later slices.
