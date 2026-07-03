<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:39:04Z" -->

# Plaza Regenerate Plan Publish Flow - Before

## Scope

Publish, broadcast, save, and return tail inside `PlazaEngine.regenerate_plan`.

## Current Flow

1. `regenerate_plan` assigns `disc.plan` with `_build_plan_payload`.
2. It publishes the revised plan as a moderator `PlazaMessage`.
3. It broadcasts `plan_updated`.
4. It saves the plaza.
5. It returns `status`, `plan`, and `message`.

## Behavior To Preserve

- Revision reason remains `用户请求刷新执行计划`.
- Published message remains a moderator message.
- Message metadata remains `{"interjection_kind": "revised_plan"}`.
- SSE event order remains message first, then `plan_updated`.
- Save and return shape remain unchanged.

## Smallest Safe Slice

Extract only the publish/broadcast/save tail after plan text has already been generated.
