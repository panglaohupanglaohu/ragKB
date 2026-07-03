<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:13:56Z" -->

# Plaza Simulated Interjection Speaker Reply Flow - Before

## Scope

Nominated speaker reply publication inside the simulated interjection branch.

## Current Flow

1. If a chosen speaker exists, the simulated branch calls `publish_message` inline.
2. The message content quotes the first 60 characters of the user interjection.
3. It uses the chosen speaker's niche role and replies to the moderator redirect message.
4. It sets metadata `interjection_kind=nominated_reply` and `prompted_by=moderator.agent_id`.

## Behavior To Preserve

- Reply text and 60-character user-message truncation remain unchanged.
- Reply target remains the moderator redirect message ID.
- Metadata and round number remain unchanged.
- `publish_message` remains responsible for append and broadcast.

## Smallest Safe Slice

Extract only simulated nominated speaker reply publication. Leave speaker selection, moderator redirect, plan update, save, and return shape unchanged.
