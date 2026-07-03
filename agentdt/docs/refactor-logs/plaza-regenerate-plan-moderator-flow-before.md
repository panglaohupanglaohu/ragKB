<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:31:06Z" -->

# Plaza Regenerate Plan Moderator Flow - Before

## Scope

Moderator resolution inside `PlazaEngine.regenerate_plan`.

## Current Flow

1. `regenerate_plan` first checks `disc.moderator_agent_id`.
2. If present, it looks up that participant in the plaza.
3. If no explicit moderator is found, it falls back to the first participant whose niche role is `moderator`.
4. If still missing, it returns `{"error": "无议事长"}`.

## Behavior To Preserve

- Explicit discussion moderator remains preferred.
- Niche-role moderator fallback remains unchanged.
- Missing moderator error remains unchanged.

## Smallest Safe Slice

Extract moderator resolution only. Leave plaza/discussion lookup, prompt generation, fallback, publishing, broadcast, save, and return behavior unchanged.
