<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T01:42:29Z" -->

# Plaza Auto Extract Flow - Before

## Scope

`PlazaEngine._auto_extract_on_consensus` configuration and payload preparation.

## Current Flow

1. `_auto_extract_on_consensus` reads `config/settings.json` inline.
2. It returns early when `auto_extract_on_consensus` is false.
3. It imports and resolves the extraction store.
4. It builds the extraction pipeline description inline from topic, summary, and plan content.
5. It creates the pipeline with plaza tags and logs the pipeline ID.

## Behavior To Preserve

- Missing or unreadable settings still default to enabled.
- `auto_extract_on_consensus=false` still disables the hook.
- Description still truncates summary and plan text to 1500 characters.
- Pipeline name, team ID fallback, created-by field, and tags remain unchanged.

## Smallest Safe Slice

Extract settings enablement and description construction. Leave store lookup, pipeline creation, and logging unchanged.
