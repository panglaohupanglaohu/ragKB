<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:49:02Z" -->

# Plaza Simulated Round Loop Flow - Before

## Scope

Round loop body inside `PlazaEngine._run_simulated`.

## Current Flow

1. `_run_simulated` sets `disc.current_round`.
2. It broadcasts `round_start` with the current round and `disc.max_rounds`.
3. It publishes one simulated round message for each speaker.
4. It sleeps `0.1` seconds after each speaker message.

## Behavior To Preserve

- Round numbers still come from `range(1, min(disc.max_rounds + 1, 3))`.
- `round_start` payload and broadcast order are unchanged.
- Speaker order is unchanged.
- Per-speaker sleep remains `0.1` seconds after publishing.

## Smallest Safe Slice

Extract only the body of one simulated round.
