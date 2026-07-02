<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:06:38Z" -->

# Plaza Simulated Interjection Flow - Before

## Scope

No-LLM branch inside `PlazaEngine.handle_live_interjection`.

## Current Flow

1. When `_chat_fn` is absent, the branch chooses the first speaker when available.
2. It publishes the moderator redirect message.
3. It optionally publishes the nominated speaker reply.
4. It builds simulated revised-plan content.
5. It publishes the plan update, resumes interjection state, saves the plaza, and returns the message bundle.

## Behavior To Preserve

- Chosen speaker remains the first sorted speaker.
- Moderator redirect and nominated reply message text remain unchanged.
- Metadata keys and reply links remain unchanged.
- Plan content, plan update, resumed broadcast, save, and return shape remain unchanged.

## Smallest Safe Slice

Extract the no-LLM branch into a helper without changing message publication or plan update behavior.
