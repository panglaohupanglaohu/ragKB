<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:31:49Z" -->

# Plaza Round Summary Prompt Flow - Before

## Scope

Moderator round-summary prompt construction inside `PlazaEngine.run_discussion`.

## Current Flow

1. After a round finishes, `run_discussion` checks whether it is not the final round.
2. It builds a moderator summary prompt inline.
3. The prompt includes `_format_round_messages(disc, round_num)`.
4. The moderator speaks through `_speak_with_lock` using the current round and `niche_role="moderator"`.

## Behavior To Preserve

- Summaries are still skipped for the final round.
- Prompt still includes the current round number and formatted round messages.
- `_speak_with_lock` still owns message creation and broadcast.

## Smallest Safe Slice

Extract only summary prompt construction. Leave round execution, fallback abort, final summary, plan generation, and persistence unchanged.
