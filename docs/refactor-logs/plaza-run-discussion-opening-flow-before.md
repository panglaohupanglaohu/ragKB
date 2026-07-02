<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:26:01Z" -->

# Plaza Run Discussion Opening Flow - Before

## Scope

LLM-backed opening slice of `PlazaEngine.run_discussion` in `src/backend/agents/plaza_engine.py`.

## Current Flow

1. `run_discussion` prepares the discussion and skips simulated mode when `_chat_fn` is available.
2. The opening prompt is built inline from topic, description, goal, and speaker names.
3. The moderator speaks through `_speak_with_lock` with `round_number=0`.
4. The moderator message is appended and broadcast by the existing speak path.
5. Control then moves into the debate round loop.

## Behavior To Preserve

- Opening remains moderator-only.
- Opening still uses `round_number=0` and `niche_role="moderator"`.
- Topic, optional description, optional goal, and participant names remain in the prompt.
- Existing `_speak_with_lock` behavior continues to own message creation, locking, and broadcast.

## Smallest Safe Slice

Extract prompt construction and opening orchestration into helpers without touching round discussion, fallback abort, final summary, plan generation, persistence, or auto-extract.
