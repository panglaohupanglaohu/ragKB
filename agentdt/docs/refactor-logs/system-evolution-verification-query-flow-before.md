<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T07:22:29Z" -->

# System Evolution Verification Query Flow - Before

## Scope

Core flow: `SystemEvolutionChannel.get_verification_alerts` and `get_verification_queue` in `src/backend/channels/system_evolution.py`.

## Current Flow

`get_verification_alerts`:

1. Iterate all evolution items.
2. Optionally filter by source plaza ID and source discussion ID.
3. Convert each matching item into an alert with `_build_verification_alert`.
4. Drop items without alert state.
5. Sort critical alerts first, then verification-pending alerts, then item ID.

`get_verification_queue`:

1. Iterate all evolution items.
2. Optionally filter by source plaza ID and source discussion ID.
3. Build a queue item payload with verification status, retry, source task, and escalation fields.
4. Sort manual verification items first, then verification-pending items, then item ID.

## Behavior To Preserve

- Source plaza and discussion filters remain unchanged.
- Alert payload fields and queue item fields remain unchanged.
- Alert sorting and queue sorting remain unchanged.
- Items without alert state remain excluded from alerts.
- Public route payloads that consume these methods remain unchanged.

## Smallest Safe Refactor Slice

Extract shared source filtering, queue item payload construction, and sort key helpers without changing payload fields or order.
