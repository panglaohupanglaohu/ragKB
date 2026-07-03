<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T05:48:07Z" -->

# Chat Budget Usage Flow Refactor

## Files Changed

- `src/backend/agents/chat_harness.py`
- `docs/refactor-logs/chat-budget-usage-flow-before.md`
- `docs/refactor-logs/chat-budget-usage-flow.md`

## Reason For Changes

- Clarified budget checks and usage recording in non-streaming and streaming chat flows.
- Removed repeated `UsageRecord` construction from primary chat, tool follow-up, and streaming usage paths.
- Kept budget, usage attribution, and session accounting as explicit `ChatHarness` helper boundaries.

## Behavior Preservation Notes

- Non-streaming budget blocks still return `TurnResult(stop_reason="budget_exceeded")` before any LLM call.
- Streaming budget blocks still yield `message_start`, `message_delta`, then `message_stop`.
- Provider stream usage still takes precedence over estimated token usage.
- Streaming still skips usage persistence only when total usage is zero.
- Non-streaming primary and tool follow-up usage records keep the same attribution fields from `get_token_ctx`.
- Tool follow-up budget handling and stop reasons are unchanged.

## Validation Result

- `node scripts/run-python.cjs -m pytest -q src/backend/tests/test_token_budget.py`: passed, `10 passed`.
- `npm run lint`: passed.
- `npm run typecheck`: passed.

## Remaining Risks

- Tool-call execution and follow-up summarization still live inside `ChatHarness.chat`; that should be a separate slice because it involves `agent_toolbox` behavior.
- Error fallback paths still do not record usage, matching existing behavior.
