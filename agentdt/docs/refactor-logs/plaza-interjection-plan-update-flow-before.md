<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:01:51Z" -->

# Plaza Interjection Plan Update Flow - Before

## Scope

Plan payload, revised-plan message, broadcasts, and save tail in `PlazaEngine.handle_live_interjection`.

## Current Flow

1. The no-LLM branch builds plan content, assigns `disc.plan`, publishes the revised-plan message, broadcasts `plan_updated`, broadcasts resumed state, saves the plaza, and returns.
2. The LLM-backed branch repeats the same tail after generating `plan_text`.
3. Both branches use the same metadata: `{"interjection_kind": "revised_plan"}`.
4. Both branches use `disc.current_round`, moderator role, and the selected reply target.

## Behavior To Preserve

- Plan payload still uses `_build_plan_payload`.
- Revised-plan message still uses `publish_message`.
- `plan_updated` broadcast still precedes resumed-state broadcast.
- Plaza save still happens before the response object is returned.
- Return shapes remain unchanged in both branches.

## Smallest Safe Slice

Extract the shared plan-update tail while preserving branch-specific plan text, revision reason, and reply target.
