<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:16:13Z" -->

# Plaza Interjection Nominated Reply Generate Flow - Before

## Scope

LLM-backed nominated speaker reply generation and metadata attachment.

## Current Flow

1. The LLM-backed interjection branch builds the nominated speaker prompt.
2. It calls `_agent_speak` inline with the chosen participant.
3. If a message is returned, it assigns `reply_to` to the moderator redirect message ID.
4. It adds `interjection_kind=nominated_reply` and `prompted_by=moderator.agent_id`.

## Behavior To Preserve

- `_agent_speak` arguments remain unchanged.
- Missing speaker message still returns `None` without metadata mutation.
- Reply target and metadata remain unchanged.
- Supplementary replies and plan revision remain unchanged.

## Smallest Safe Slice

Extract only nominated reply generation plus reply metadata attachment.
