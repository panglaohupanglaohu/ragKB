<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:30:13Z" -->

# Plaza Fallback Abort Flow - Before

## Scope

Continuous LLM fallback abort branch inside `PlazaEngine.run_discussion`.

## Current Flow

1. After each speaker call, `run_discussion` checks `_last_call_was_fallback`.
2. Consecutive fallback count increments on fallback and resets on successful LLM response.
3. When count reaches `_FALLBACK_ABORT_THRESHOLD`, the loop logs a warning.
4. It builds an abort moderator message inline.
5. It appends the message, broadcasts it, truncates `disc.max_rounds` to the current round, and breaks into final summary handling.

## Behavior To Preserve

- Trigger threshold remains unchanged.
- Abort message content remains unchanged.
- Abort message still uses moderator identity when available and system fallback otherwise.
- Message `seq` still matches append position.
- `disc.max_rounds` is still set to the abort round so final summary uses the shortened round count.

## Smallest Safe Slice

Extract abort message construction and abort side effects. Leave fallback counter logic and loop break structure in place.
