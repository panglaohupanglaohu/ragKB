<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:56:30Z" -->

# Plaza Interjection Supplementary Reply Prompt Flow - Before

## Scope

LLM-backed supplementary speaker prompt construction inside `PlazaEngine.handle_live_interjection`.

## Current Flow

1. After the nominated speaker replies, the flow selects up to two remaining speakers.
2. It builds each supplementary prompt inline.
3. The prompt includes extra speaker identity, topic, user interjection, nominated speaker reply, recent discussion, and no-repeat requirement.
4. `_agent_speak` sends each supplementary reply.
5. Reply linkage and metadata are updated afterward.

## Behavior To Preserve

- Supplementary speakers still come from remaining sorted speakers after the chosen speaker.
- Prompt still uses `_format_recent(disc, limit=6)`.
- `_agent_speak`, reply linkage, metadata, and extra reply collection remain unchanged.

## Smallest Safe Slice

Extract only supplementary reply prompt construction. Leave speaker selection, `_agent_speak`, metadata, plan revision, broadcasts, save, and return behavior unchanged.
