<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:25:47Z" -->

# Plaza Agent Content Retry Flow - Before

## Scope

Retry loop inside `PlazaEngine._generate_agent_content`.

## Current Flow

1. `_generate_agent_content` first checks degraded-window fallback.
2. It opens `token_scope` for plaza attribution.
3. Inside that scope, it runs the retry loop inline.
4. The loop calls `_call_agent_chat`, accepts usable content, retries empty/error responses, handles timeout fallback immediately, and falls back offline after retries.

## Behavior To Preserve

- Degraded-window short-circuit remains before token scope.
- Retry loop still runs inside `token_scope`.
- Timeout fallback, provider fallback text, empty response retry, max retries, and offline escalation behavior remain unchanged.
- Token attribution for successful plaza speech remains unchanged.

## Smallest Safe Slice

Extract only the retry loop body into a helper called from inside `token_scope`.
