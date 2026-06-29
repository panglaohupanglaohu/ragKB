<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:46:18Z" -->

# Plaza Simulated Completion Flow - Before

## Scope

Summary, plan, close status, and final broadcasts inside `PlazaEngine._run_simulated`.

## Current Flow

1. `_run_simulated` combines moderator and speakers for deterministic plan generation.
2. It writes `disc.summary`, `disc.key_conclusions`, and `disc.plan`.
3. It broadcasts `plan_updated`.
4. It marks the discussion closed, sets `ended_at`, and broadcasts `discussion_end`.

## Behavior To Preserve

- Participants for deterministic plan remain `[moderator] + speakers` when moderator exists.
- Summary reason remains `模拟模式`.
- Plan revision reason remains `模拟模式自动生成`.
- Broadcast order remains `plan_updated` before `discussion_end`.
- No save behavior is added or removed.

## Smallest Safe Slice

Extract only simulated completion state updates and broadcasts.
