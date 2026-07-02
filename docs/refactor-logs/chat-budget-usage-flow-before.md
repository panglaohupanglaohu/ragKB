<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T05:45:11Z" -->

# Chat Budget Usage Flow - Before

## Scope

Core flow: budget checks and usage recording in `src/backend/agents/chat_harness.py`.

## Entrypoints

- `ChatHarness.chat`
- `ChatHarness.stream_chat`

## Current Flow

Non-streaming chat:

1. Build session messages.
2. Estimate request tokens.
3. Call `get_budget_guard().check`.
4. If blocked, add fallback assistant message and return `TurnResult(stop_reason="budget_exceeded")`.
5. Call the provider.
6. Convert provider `usage` into `UsageSummary`.
7. Build and record `UsageRecord`.
8. Update session usage and harness total token count.
9. If tool calls exist, check follow-up budget.
10. If follow-up model call succeeds, repeat provider-usage extraction and usage recording.

Streaming chat:

1. Build session messages.
2. Call `get_budget_guard().check`.
3. If blocked, yield start/delta/stop events with `stop_reason="budget_exceeded"`.
4. Stream provider chunks.
5. Prefer provider usage payload when present.
6. Otherwise estimate prompt/completion tokens from messages/content.
7. Build and record `UsageRecord`.
8. Update session usage and harness total token count.

## Existing Boundaries

- `BudgetGuard` owns budget decisions and usage persistence.
- `ChatHarness` currently owns token estimation, blocked fallback wording, usage conversion, cost estimation, and session metric updates inline.

## Behavior To Preserve

- Blocked non-streaming chat still returns `stop_reason="budget_exceeded"` and does not call the LLM.
- Blocked streaming chat still yields `message_start`, `message_delta`, and `message_stop`.
- Provider usage payload still takes precedence over estimated stream usage.
- Usage attribution still uses `agent_id/team_id` arguments first, then token context fallback.
- Tool follow-up usage recording remains separate from primary model call usage.

## Smallest Safe Refactor Slice

Extract budget-check and usage-recording helpers inside `ChatHarness` without changing public methods, stop reasons, event order, or stored usage fields.
