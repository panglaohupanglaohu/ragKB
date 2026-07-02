<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:38:49Z" -->

# Plaza Closing Flow - Before

## Scope

Closing message and discussion-end state transition inside `PlazaEngine.run_discussion`.

## Current Flow

1. After final plan payload creation and `plan_updated` broadcast, `run_discussion` builds a closing moderator message inline.
2. It assigns `seq`, appends the message, and broadcasts it.
3. It marks the discussion closed and writes `ended_at`.
4. It broadcasts `discussion_end` with the final summary.
5. Persistence and auto-extract run afterward.

## Behavior To Preserve

- Closing message still uses moderator identity.
- Closing message content still comes from `_build_closing_brief(disc.summary)`.
- Closing message round number remains `disc.max_rounds + 1`.
- Message broadcast still precedes `discussion_end`.
- Persistence and auto-extract remain after closing.

## Smallest Safe Slice

Extract closing message construction and closing side effects. Leave final plan update, persistence, and auto-extract untouched.
