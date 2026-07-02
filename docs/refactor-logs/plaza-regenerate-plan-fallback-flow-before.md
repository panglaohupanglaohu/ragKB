<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:35:00Z" -->

# Plaza Regenerate Plan Fallback Flow - Before

## Scope

Deterministic fallback inside `PlazaEngine.regenerate_plan`.

## Current Flow

1. `regenerate_plan` calls `_generate_agent_content` for a refreshed plan.
2. It checks `_has_actionable_plan(plan_text)`.
3. If the LLM text is not actionable, it builds a participant list inline.
4. It calls `_build_deterministic_plan_content` with reason `刷新计划时 LLM 不可用或未返回结构化计划`.

## Behavior To Preserve

- Fallback still runs only when `_has_actionable_plan` returns false.
- Participants still come from the whole plaza.
- Fallback reason remains unchanged.
- Plan payload, message publication, broadcast, save, and return shape remain unchanged.

## Smallest Safe Slice

Extract only deterministic fallback construction.
