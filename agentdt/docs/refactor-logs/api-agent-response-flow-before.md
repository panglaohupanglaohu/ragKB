<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:35:44Z" -->

# API Agent Response Flow - Before

## Scope

Core flow: `_generate_agent_response` in `src/backend/agents/api.py`.

## Current Flow

1. Resolve the shared `ChatHarness`.
2. If a team ID is provided, load the team and sync its default model into the harness.
3. Build OpenAI-style function schemas from the agent's bound tools.
4. Build a base system prompt from the agent name, role, and skills.
5. Append instructions from bound skills when the skill registry has matching instruction text.
6. Call `harness.chat` with content, agent attribution, team attribution, session ID, system prompt, and tool schemas.
7. If the harness returns tool invocations, execute each tool through `ToolExecutor`.
8. Store execution output or error text back on the invocation object.
9. Send a follow-up chat prompt containing tool execution results.
10. Return either the first response/result or the follow-up response/result.

## Behavior To Preserve

- Team default model synchronization remains best-effort and only runs when `team_id` is provided.
- Tool schemas preserve name, description, parameters, required flags, and existing type normalization.
- Bound skill instructions remain appended to the system prompt.
- Initial chat still receives `tools=tools_for_llm`.
- Tool follow-up chat keeps team/session attribution and system prompt.
- Returned tuple shape remains `(response_text, result_object)`.
- Public session message route behavior is unchanged.

## Smallest Safe Refactor Slice

Extract helper functions for team model synchronization, tool schema construction, tool parameter schema construction, system prompt construction, skill instruction lookup, tool invocation execution, and follow-up response generation without changing public route contracts.
