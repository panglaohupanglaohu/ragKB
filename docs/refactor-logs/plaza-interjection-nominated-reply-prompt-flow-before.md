<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:54:11Z" -->

# Plaza Interjection Nominated Reply Prompt Flow - Before

## Scope

LLM-backed nominated speaker prompt construction inside `PlazaEngine.handle_live_interjection`.

## Current Flow

1. After the moderator redirect is published, the flow checks whether a speaker was chosen.
2. It builds the nominated speaker prompt inline.
3. The prompt includes speaker identity, topic, user interjection, moderator reply, recent discussion, and direct response requirements.
4. `_agent_speak` sends the reply.
5. Reply linkage and metadata are updated afterward.

## Behavior To Preserve

- Prompt still uses recent discussion from `_format_recent(disc, limit=8)`.
- `_agent_speak` call and metadata updates remain unchanged.
- Nominated reply still answers the user issue directly.

## Smallest Safe Slice

Extract only nominated speaker prompt construction. Leave speaking, reply linkage, metadata, supplementary replies, plan revision, broadcasts, and persistence unchanged.
