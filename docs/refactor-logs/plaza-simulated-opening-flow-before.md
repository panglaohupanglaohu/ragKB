<!-- docs-signoff: author="Codex" kind="llm" doc="plan" ts="2026-06-29T02:41:22Z" -->

# Plaza Simulated Opening Flow - Before

## Scope

Opening moderator message inside `PlazaEngine._run_simulated`.

## Current Flow

1. `_run_simulated` checks whether a moderator exists.
2. It constructs the simulated opening `PlazaMessage` inline.
3. It assigns `seq`, appends to `disc.messages`, and broadcasts a `message` event.
4. It continues into simulated discussion rounds.

## Behavior To Preserve

- Opening content remains `欢迎各位参与「{disc.topic}」的讨论。让我们开始吧。`.
- Message remains a moderator message at round `0`.
- Message `seq` still equals the previous message count.
- Broadcast payload remains `{"type": "message", "message": msg.to_dict()}`.

## Smallest Safe Slice

Extract only simulated opening message construction and broadcast.
