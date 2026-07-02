<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:34:03Z" -->

# Plaza Final Summary Prompt Flow - Before

## Scope

Final summary prompt construction inside `PlazaEngine.run_discussion`.

## Current Flow

1. `run_discussion` switches the discussion to `summarizing`.
2. It broadcasts the summarizing event.
3. It builds the final summary prompt inline from topic, optional description, optional goal, and full discussion history.
4. It calls `_generate_agent_content` with `bypass_degraded=True`.
5. Actionable-plan fallback, plan payload, closing message, persistence, and auto-extract run after the prompt call.

## Behavior To Preserve

- Prompt still includes full history from `_format_history(disc)`.
- Prompt still requires weighted P0/P1/P2 conclusions and an execution plan table.
- Final summary LLM call still bypasses the degraded window.
- Plan fallback and closing behavior remain unchanged.

## Smallest Safe Slice

Extract only final summary prompt construction. Leave summary generation, fallback plan handling, closing, persistence, and auto-extract unchanged.
