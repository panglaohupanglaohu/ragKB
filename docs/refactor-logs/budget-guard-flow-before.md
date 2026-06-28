<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T04:51:33Z" -->

# Budget Guard Flow - Before

## Scope

Core flow: `BudgetGuard.check` in `src/backend/agents/budget/guard.py`.

## Entrypoint

`BudgetGuard.check(session_id, agent_id, team_id, estimated_tokens)` is called before model execution to decide whether the requested token estimate can proceed.

## Current Flow

1. Compute the current UTC date string with `datetime.now(timezone.utc).date().isoformat()`.
2. Read existing usage totals from `UsageStore`:
   - `get_session_total(session_id)`
   - `get_agent_daily_total(agent_id, today)`
   - `get_team_daily_total(team_id, today)`
3. Evaluate limits in fixed order:
   - session limit
   - agent daily limit
   - team daily limit
4. For each scope, `_check_limit` appends a `BudgetEvent` when:
   - projected usage exceeds the configured limit, or
   - projected usage reaches the configured alert threshold.
5. Persist every generated event with `store.record_event(event)`.
6. Block the request if any event has `level == "halt"`.
7. Return `BudgetCheckResult(allowed=not blocked, events=events)`.

## Existing Boundaries

- `BudgetGuard` owns both orchestration and per-scope limit evaluation.
- `UsageStore` owns usage aggregation and event persistence.
- `TokenBudget` owns configured limits and alert behavior.

## Behavior To Preserve

- Event order remains session, agent, team.
- Missing scope IDs and non-positive limits produce no events.
- `on_exceed == "halt"` blocks on overage; any other value records warning events.
- Threshold warnings do not block.
- Event messages, event levels, projected values, and limits stay unchanged.

## Smallest Safe Refactor Slice

Extract helper functions for date calculation, usage-total retrieval, event persistence, and block detection. Keep `_check_limit` intact as the per-scope decision point to avoid changing public or test-visible behavior.
