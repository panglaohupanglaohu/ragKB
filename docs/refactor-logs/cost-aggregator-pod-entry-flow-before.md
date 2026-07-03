<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:18:08Z" -->

# Cost Aggregator Pod Entry Flow - Before

## Scope

Core flow: `_pod_from_entry` in `src/backend/agents/cost_aggregator.py`.

## Current Flow

1. Read allocation `name` and `properties`.
2. Read labels from `properties.labels`, falling back to top-level `labels`.
3. Normalize Kubernetes labels.
4. Derive service/app/component/environment from namespace when service is missing.
5. Derive team from `agentsgroup-{team}-...` pod naming when team is missing or platform.
6. Extract cost fields from top-level entry, falling back to properties.
7. Sum component costs when `totalCost` is missing.
8. Convert `ramByteHours` to GB hours.
9. Resolve namespace, pod name, container, and window fields.
10. Return `PodCostItem`.

## Behavior To Preserve

- Top-level cost values still take precedence over properties.
- Missing `totalCost` still sums cost components.
- `ramByteHours` still converts using `1024 ** 3`.
- Namespace fallback labels remain unchanged.
- Team derivation from pod names remains unchanged.
- Window start/end extraction remains unchanged.

## Smallest Safe Refactor Slice

Extract helper functions for raw label lookup, namespace label fallback, team derivation, cost lookup, RAM conversion, and window lookup. Keep `PodCostItem` fields and rounding unchanged.
