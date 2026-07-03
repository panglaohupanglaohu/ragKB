<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:28:36Z" -->

# Plaza Regenerate Plan Prompt Flow - Before

## Scope

Prompt construction inside `PlazaEngine.regenerate_plan`.

## Current Flow

1. `regenerate_plan` resolves plaza, discussion, and moderator.
2. It formats the last 30 messages inline, truncating each message to 200 characters.
3. It builds the full plan-regeneration prompt inline.
4. It calls `_generate_agent_content` with `bypass_degraded=True`.
5. Fallback, plan payload, message publication, broadcast, save, and return happen afterward.

## Behavior To Preserve

- Recent context still uses the last 30 messages and 200-character content truncation.
- Existing plan JSON still uses `json.dumps(..., ensure_ascii=False)`.
- Prompt output contract remains unchanged.
- LLM call, fallback, publish, broadcast, save, and return shape remain unchanged.

## Smallest Safe Slice

Extract only recent-context formatting and prompt construction.
