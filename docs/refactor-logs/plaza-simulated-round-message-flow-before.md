<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:44:02Z" -->

# Plaza Simulated Round Message Flow - Before

## Scope

Single speaker message creation inside `PlazaEngine._run_simulated`.

## Current Flow

1. `_run_simulated` builds fallback content for each speaker inline.
2. It constructs a `PlazaMessage` with speaker identity, niche role, content, and round number.
3. It assigns `seq`, appends the message, broadcasts a `message` event, then sleeps.

## Behavior To Preserve

- Fallback prompt remains `{topic}\n{description}\n{goal}`.
- Message identity and niche role still come from the speaker.
- Message `round_number`, `seq`, append, and broadcast behavior are unchanged.
- Sleep remains in `_run_simulated` after message publication.

## Smallest Safe Slice

Extract only one simulated speaker message publication.
