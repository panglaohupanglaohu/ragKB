<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:28:50Z" -->

# Plaza Agent Content Flow - Before

## Scope

Core flow: `PlazaEngine._generate_agent_content` in `src/backend/agents/plaza_engine.py`.

## Current Flow

1. If the LLM degraded window is active and the call is not bypassed, return deterministic fallback content and mark the last call as fallback.
2. Build a plaza token attribution context from the discussion ID, participant team ID, and participant agent ID.
3. Retry the injected chat function up to `_MAX_RETRIES`.
4. Wrap each chat call in `asyncio.wait_for` with `_LLM_CALL_TIMEOUT`.
5. Pass the participant-specific system prompt into the chat function.
6. If the provider returns usable text, return it.
7. If the provider returns known unusable fallback text, mark the LLM degraded and return deterministic fallback content.
8. On timeout, mark the LLM degraded, escalate immediately, and return deterministic fallback content.
9. On non-timeout failures, retry with exponential backoff.
10. When all retries are exhausted, add an escalation entry and return the offline marker text.

## Behavior To Preserve

- Degraded-window short-circuit remains unchanged unless `bypass_degraded=True`.
- Plaza LLM calls still run under `phase="plaza"` token attribution.
- Retry count, timeout, and backoff remain unchanged.
- Provider fallback text still triggers deterministic content instead of becoming a message.
- Timeout still escalates immediately and returns fallback content.
- Exhausted non-timeout retries still return `"[{participant.agent_name} 暂时离线]"`.
- Escalation queue fields and route-facing behavior remain unchanged.

## Smallest Safe Refactor Slice

Extract helper functions for degraded-window handling, plaza run ID derivation, single chat attempt execution, successful response handling, timeout fallback handling, retry delay, and exhausted-retry fallback. Keep public behavior and method signature unchanged.
