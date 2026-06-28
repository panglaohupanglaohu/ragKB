<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:43:24Z" -->

# API Session Message Flow - Before

## Scope

Core flow: `send_session_message` in `src/backend/agents/api.py`.

## Current Flow

1. Look up the in-memory session by `session_id`.
2. Return HTTP 404 when the session does not exist.
3. Create a user message with an eight-character UUID prefix and timestamp.
4. Append the user message to the session.
5. Resolve the target agent.
6. Increment `messages_sent` and log `message_received`.
7. Call `_generate_agent_response` with agent, content, session ID, and team ID.
8. If reply text exists, create and append an assistant message with model/provider/latency metadata.
9. If harness usage has positive total tokens, increment LLM call and token metrics from usage.
10. Otherwise estimate token metrics from request and reply text length.
11. If harness tool invocations exist, increment/log tool metrics from them.
12. Otherwise parse tool invocation markers from reply text and increment/log tool metrics from parsed text.
13. Return the original user message.

## Behavior To Preserve

- Missing sessions still return HTTP 404.
- The route still returns the user message, not the assistant reply.
- User message and assistant message shapes are unchanged.
- Metric names and increment rules are unchanged.
- Real usage totals take precedence over estimated token counts.
- Harness tool invocations take precedence over parsed text invocations.
- Public request/response formats remain unchanged.

## Smallest Safe Refactor Slice

Extract helpers for message construction, session lookup, assistant reply construction, response metric accounting, token metric accounting, and tool metric accounting without changing route contracts.
