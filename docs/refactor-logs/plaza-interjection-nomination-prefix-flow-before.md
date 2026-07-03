<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:08:37Z" -->

# Plaza Interjection Nomination Prefix Flow - Before

## Scope

Moderator reply nomination-prefix handling in the LLM-backed interjection branch.

## Current Flow

1. The flow parses the LLM redirect decision into moderator reply text and chosen speaker.
2. If a speaker is chosen, it builds a `请 {agent_name} 先回应。` prefix inline.
3. It prepends that prefix unless the moderator reply already starts with it.
4. The moderator redirect message is published afterward.

## Behavior To Preserve

- No prefix is added when no speaker is chosen.
- Existing matching prefix is not duplicated.
- Missing prefix is prepended exactly as before.
- Moderator message publication remains unchanged.

## Smallest Safe Slice

Extract only nomination-prefix normalization. Leave parsing, publishing, replies, plan revision, broadcasts, and persistence unchanged.
