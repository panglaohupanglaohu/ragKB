<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:44:47Z" -->

# Plaza Interjection Context Flow - Before

## Scope

Initial context resolution in `PlazaEngine.handle_live_interjection`.

## Current Flow

1. `handle_live_interjection` looks up the plaza inline and raises `ValueError("广场不存在")` when missing.
2. It looks up the discussion inline and raises `ValueError("讨论不存在")` when missing.
3. It resolves participants, moderator, and sorted speakers inline.
4. It raises `ValueError("广场没有议事长")` when no moderator is available.
5. It then enters the discussion lock and handles simulated or LLM-backed interjection correction.

## Behavior To Preserve

- Error messages remain unchanged.
- Moderator resolution still uses `_resolve_moderator`.
- Speaker ordering still uses `_sort_speakers`.
- Locking, simulated branch, LLM branch, plan updates, store save, and broadcasts remain unchanged.

## Smallest Safe Slice

Extract only context preparation before the lock. Leave all interjection behavior branches untouched.
