<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:46:39Z" -->

# Plaza Interjection Simulated Plan Flow - Before

## Scope

No-LLM interjection plan content inside `PlazaEngine.handle_live_interjection`.

## Current Flow

1. When `_chat_fn` is absent, the interjection branch picks the first speaker when available.
2. It publishes a moderator redirect and optional nominated reply.
3. It builds a one-row revised plan inline from the user message and chosen speaker.
4. It stores the plan payload, publishes it, broadcasts `plan_updated`, resumes interjection state, saves the plaza, and returns messages.

## Behavior To Preserve

- User message in the simulated plan reason remains truncated to 40 characters.
- Responsible role remains the chosen agent name or `待定`.
- The generated plan still contains one P0 task for responding to the user issue.
- Plan payload, broadcasts, save, and return shape remain unchanged.

## Smallest Safe Slice

Extract only simulated plan content construction. Leave message publishing, plan payload, broadcasts, save, and return behavior unchanged.
