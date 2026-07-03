<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:19:49Z" -->

# Plaza Interjection Supplementary Reply Generate Flow - Before

## Scope

LLM-backed supplementary speaker reply generation and metadata attachment.

## Current Flow

1. The LLM-backed interjection branch builds a supplementary prompt for each remaining speaker.
2. It calls `_agent_speak` inline.
3. If a message is returned, it assigns `reply_to` to the nominated reply ID, or moderator redirect ID when no nominated reply exists.
4. It adds `interjection_kind=supplementary_reply` and `prompted_by=moderator.agent_id`.
5. It appends the message to `extra_replies`.

## Behavior To Preserve

- `_agent_speak` arguments remain unchanged.
- Reply target fallback remains unchanged.
- Metadata remains unchanged.
- `extra_replies` collection remains controlled by the caller.

## Smallest Safe Slice

Extract only supplementary reply generation plus reply metadata attachment.
