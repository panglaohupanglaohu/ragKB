<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:32:00Z" -->

# Plaza Agent Content Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_retry_escalation.py`
- `docs/refactor-logs/plaza-agent-content-flow-before.md`
- `docs/refactor-logs/plaza-agent-content-flow.md`

## Reason For Changes

- Clarified the LLM-backed plaza speech generation flow by separating degraded-window handling, plaza run ID derivation, chat invocation, usable response handling, timeout fallback, retry sleep, and exhausted-retry offline handling.
- Added focused regression coverage for degraded-window fallback and provider fallback text.

## Behavior Preservation Notes

- `_generate_agent_content` keeps the same signature and return shapes.
- Degraded-window calls still bypass chat and return deterministic fallback content unless `bypass_degraded=True`.
- Plaza LLM calls still use `phase="plaza"` token attribution.
- Retry count, timeout, and exponential backoff remain unchanged.
- Provider fallback/error text still returns deterministic content without adding an escalation entry.
- Timeout still marks LLM degraded, adds an escalation entry, and returns deterministic fallback content.
- Exhausted non-timeout failures still add an escalation entry and return the offline marker text.
- Public routes, API contracts, database schema, and request/response formats were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_retry_escalation.py src/backend/tests/test_plaza_token_attribution.py`: passed, `11 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- `PlazaEngine.run_discussion` remains a large orchestration flow and should be refactored separately.
- Live interjection and plan regeneration still share prompt assembly and message publishing concerns that were intentionally left untouched.
- The deterministic fallback content generator remains large and topic-specific; it should be a separate low-risk slice.
