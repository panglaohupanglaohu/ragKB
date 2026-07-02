<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:11:20Z" -->

# Plaza Interjection Moderator Redirect Publish Flow - Before

## Scope

Moderator redirect message publication in simulated and LLM-backed interjection branches.

## Current Flow

1. Both branches call `publish_message` inline for the moderator redirect.
2. Both use `round_number=disc.current_round` and `niche_role="moderator"`.
3. Both reply to the user message ID.
4. Both set metadata `interjection_kind=moderator_redirect` and `nominated_agent_id`.

## Behavior To Preserve

- Message content remains supplied by the caller.
- Reply target remains the user message ID.
- Metadata shape and values remain unchanged.
- `publish_message` remains responsible for message append and broadcast.

## Smallest Safe Slice

Extract only moderator redirect publication. Leave redirect text construction, nomination parsing, replies, plan updates, broadcasts, save, and return behavior unchanged.
