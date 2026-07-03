<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:52:03Z" -->

# Plaza Start Discussion Flow - Before

## Scope

`plaza_routes.start_discussion` route boundary.

## Current Flow

1. The route resolves the plaza engine.
2. It fetches the discussion and maps missing discussion to 404.
3. It resets closed discussions before restart.
4. It rejects non-open, non-closed discussions with 400.
5. It schedules `engine.run_discussion` in the background and returns `started`.

## Behavior To Preserve

- Missing discussion still returns 404.
- Closed discussions are still reset before scheduling.
- Non-open, non-closed discussions still return 400 with the same message shape.
- Background scheduling still uses `asyncio.create_task(engine.run_discussion(...))`.
- Response remains `{"status": "started", "discussion_id": disc_id}`.

## Smallest Safe Slice

Extract discussion state resolution and background scheduling helpers.
