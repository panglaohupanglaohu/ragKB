<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:36:41Z" -->

# Plaza Final Summary Fallback Flow - Before

## Scope

Deterministic final-summary fallback inside `PlazaEngine.run_discussion`.

## Current Flow

1. `run_discussion` asks the moderator LLM for the final summary.
2. It checks `_has_actionable_plan(disc.summary)`.
3. If the summary is not actionable, it builds a participant list from moderator plus speakers.
4. It overwrites `disc.summary` with `_build_deterministic_plan_content`.
5. It writes default `key_conclusions`.
6. Plan payload construction and broadcast happen afterward.

## Behavior To Preserve

- Fallback still runs only when `_has_actionable_plan` returns false.
- Deterministic content still uses moderator plus speakers.
- Fallback reason remains `LLM 不可用或未返回结构化计划`.
- Default key conclusions remain unchanged.
- Plan payload, closing, persistence, and auto-extract remain unchanged.

## Smallest Safe Slice

Extract deterministic final-summary fallback into a helper. Leave the LLM call, plan payload, closing message, and persistence in place.
