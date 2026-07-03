<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:28:25Z" -->

# Plaza Round Speaker Prompt Flow - Before

## Scope

Speaker prompt construction inside the debate round loop of `PlazaEngine.run_discussion`.

## Current Flow

1. For each exchange speaker, `run_discussion` formats the recent discussion context inline.
2. It builds optional description and goal blocks inline.
3. It builds the full speaker prompt inline with topic, speaker identity, round number, exchange number, recent context, and speaking requirements.
4. The prompt is passed to `_speak_with_lock`.
5. Fallback detection and abort handling run immediately after the speaker call.

## Behavior To Preserve

- Recent context still uses `_format_recent(disc, limit=5)`.
- Description and goal are included only when present.
- Exchange display number remains one-based.
- `_speak_with_lock` still receives the same prompt, round number, and participant niche role.

## Smallest Safe Slice

Extract only prompt construction. Leave speaker execution, fallback counter state, abort message creation, round summaries, and final summary unchanged.
