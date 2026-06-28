<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-28T06:00:00Z" -->

# Agent Triggers Validation Flow - Before

## Scope

Core flow: `validate_trigger` and `is_url_safe` in `src/backend/agents/agent_triggers.py`.

## Current Flow

`validate_trigger` currently performs all trigger validation inline:

1. Reject unknown trigger types.
2. Validate cron expression syntax.
3. Require `fire_at` for `once`.
4. Require `every_minutes >= 1` for `interval` and `poll`.
5. Validate poll URL safety through `is_url_safe`.
6. Require at least one message source for `on_message`.
7. For task trigger types, require `focus_item`.
8. Optionally check `focus_item` through `focus_checker`.

`is_url_safe` currently performs URL safety inline:

1. Parse URL.
2. Allow only `http` and `https`.
3. Require a host.
4. Reject `localhost`.
5. Reject private, loopback, link-local, reserved, and unspecified IP addresses.
6. Allow domain names without DNS resolution.

## Behavior To Preserve

- Error message text remains unchanged.
- Unknown trigger type returns immediately after the type error.
- Focus checker exceptions are still debug-logged and ignored.
- Domain names are still allowed without DNS resolution.
- Poll URL safety response shape remains `{"safe": bool, "reason": str}`.

## Smallest Safe Refactor Slice

Extract type-specific trigger validation, focus validation, and URL safety sub-checks into helpers while keeping public function signatures and messages unchanged.
