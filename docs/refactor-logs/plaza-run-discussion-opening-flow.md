<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:28:07Z" -->

# Plaza Run Discussion Opening Flow Refactor

## Files Changed

- `src/backend/agents/plaza_engine.py`
- `src/backend/tests/test_plaza_dispatch.py`
- `docs/refactor-logs/plaza-run-discussion-opening-flow-before.md`
- `docs/refactor-logs/plaza-run-discussion-opening-flow.md`

## Reason For Changes

- Clarified the LLM-backed opening boundary inside `run_discussion`.
- Moved opening prompt construction into `_build_discussion_opening_prompt`.
- Moved moderator opening execution into `_run_discussion_opening`.
- Added focused coverage for the moderator, prompt content, round number, and niche role.

## Behavior Preservation Notes

- `run_discussion` still enters the LLM-backed path only when `_chat_fn` is configured.
- Opening prompt text and required constraints are preserved.
- Opening still delegates to `_speak_with_lock`, so existing lock, message creation, shaping, and broadcast behavior are unchanged.
- Debate rounds, fallback abort, final summary, plan payload, closing, persistence, and auto-extract were not changed.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_run_discussion_opening_uses_moderator_prompt src/backend/tests/test_plaza_dispatch.py::TestDiscussionLifecycle::test_run_discussion_startup_uses_simulated_path_without_chat_fn`: passed, `2 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `git diff --check`: passed; only Git CRLF working-copy warnings were reported.

## Remaining Risks

- `run_discussion` still contains large debate round, fallback abort, final summary, plan, and closing flows.
- Moderator can still be absent in malformed plaza state; this slice preserved the existing runtime behavior instead of changing error handling.
