# Tool Loop Flow Before Refactor

Last updated: 2026-06-28

## Scope

Core flow: `agents.runtime.tool_loop.run_tool_loop`.

Files traced:

| File | Role |
| --- | --- |
| `src/backend/agents/runtime/tool_loop.py` | Shared multi-turn runtime for model/tool loops. |
| `src/backend/agents/agent_toolbox.py` | Tool registry and `dispatch_tool_call(...)`. |
| `src/backend/agents/agent_loop.py` | Compatibility caller through `run_tool_loop_sync_with_provider(...)`. |
| `src/backend/channels/evolution_executor.py` | Evolution caller through the shared runtime. |
| `src/backend/agents/api.py` | API task/tool-loop caller, existing legacy tests cover delegation drift. |
| `src/backend/tests/test_unified_tool_loop.py` | Existing shared runtime regression tests. |

## Current Flow

1. Entrypoint setup
   - `run_tool_loop(...)` creates a runtime event emitter.
   - It filters role tools through `ToolPermissionContext`.
   - It creates system/user messages, an `LLMClient`, budget guard, usage accumulator, changed-file list, tool log, and summary.
   - Emits `loop_start`.

2. Per-iteration preparation
   - Injects a late-iteration nudge at `80%` of `max_iterations`.
   - Compacts old tool result messages if message content exceeds `_CONTEXT_BUDGET_CHARS`.
   - Estimates tokens and asks the budget guard for permission.
   - If budget blocks, emits `error` and `loop_end`, then returns partial `ToolLoopResult`.

3. Model turn
   - Calls `LLMClient.chat_completion(...)` with current messages and tools.
   - If provider returns `error`, emits `error` and `loop_end`, then returns partial `ToolLoopResult`.
   - Records provider usage through `_record_usage(...)`.
   - Extracts first choice, content, tool calls, and finish reason.
   - Emits `model_turn`.
   - Appends the assistant message, including `tool_calls` when present.

4. No tool-call output
   - If the model returns no tool calls, content becomes summary when summary is empty.
   - Emits `loop_end` with `no_tool_call`.
   - Returns successful `ToolLoopResult` with `final_message`.

5. Tool-call output
   - For each tool call:
     - Emits `tool_call`.
     - If `name == "finish"`, parses JSON args, updates summary and files changed, logs the finish call, appends an ack tool message, and marks the loop finished.
     - Otherwise, blocks unknown or denied tools with a runtime error result.
     - Otherwise dispatches through `dispatch_tool_call(name, args_raw)`.
     - Successful `write_file` and `patch_file` calls add `path` from args into `files_changed`.
     - Appends a compact entry to `tool_log`.
     - Emits `tool_result`.
     - Appends the JSON tool result to messages, capped at 32000 chars.
   - If finish was called, emits `loop_end` with `finish_called` and returns.

6. Iteration cap
   - If all iterations are consumed, emits `loop_end`.
   - Returns a partial or failed `ToolLoopResult` depending on whether summary/files changed exist.

7. Sync wrappers
   - `run_tool_loop_sync(...)` runs the async function directly or in a background thread if an event loop already exists.
   - `run_tool_loop_sync_with_provider(...)` builds `ProviderConfig` from raw provider fields and delegates to `run_tool_loop_sync(...)`.

## Existing Weaknesses

- Tool-call handling mixes finish parsing, permission checks, dispatch, changed-file tracking, tool log updates, event emission, and message mutation in one loop.
- Finish handling and regular tool handling have different message/log formats inline.
- Changed-file tracking is repeated and tied to JSON parsing inside the main loop.
- The main loop is harder to read because model-turn control flow and tool-call side effects are interleaved.

## Smallest Safe Refactor Slice

Extract only internal tool-call helpers:

- finish argument parsing
- changed-file registration
- tool dispatch permission gate
- tool log/message payload construction

Do not change:

- Public function signatures.
- Event names or payload fields.
- Tool dispatch names/arguments.
- `ToolLoopResult` output shape.
- Budget or usage recording.
- Sync wrapper behavior.
