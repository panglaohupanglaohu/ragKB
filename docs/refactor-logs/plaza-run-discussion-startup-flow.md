<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T07:32:41Z" -->

# Plaza Run Discussion Startup Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-run-discussion-startup-flow-before.md`
- `docs/refactor-logs/plaza-run-discussion-startup-flow.md`

## Reason For Changes

- Clarified the first slice of `run_discussion` by separating runnable state loading, start-state mutation, start broadcast, role resolution, and no-LLM simulated execution.
- Added focused coverage for startup broadcast, `started_at`, simulated execution, plaza persistence, and the no-chat-function path.

## Behavior Preservation Notes

- Missing plaza and missing discussion still return `None`.
- Non-open discussions are still returned unchanged.
- Open discussions still move to `in_progress` and get `started_at` before discussion-start broadcast.
- `discussion_start` payload is unchanged.
- Moderator and speaker resolution still use existing helpers.
- No-LLM path still delegates to `_run_simulated`, saves the plaza, and returns the discussion.
- LLM-backed opening, round orchestration, final summary, plan extraction, closing, persistence, and auto-extract logic were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_run_discussion_startup_uses_simulated_path_without_chat_fn src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_start_discussion_resets_closed_discussion_before_scheduling`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- `run_discussion` still contains large LLM-backed opening, debate round, fallback abort, final summary, plan, and closing flows.
- The no-LLM simulated implementation remains separate and was not refactored in this slice.
