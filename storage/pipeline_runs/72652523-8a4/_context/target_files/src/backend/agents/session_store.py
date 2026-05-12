# -*- coding: utf-8 -*-
"""AgentsGroup2026 Session Store — Persistent session storage.

Mirrors claw-code-parity session_store.py architecture:
- Save/load sessions to JSON files
- Cross-session search
- Session replay
- Transcript management with compaction
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional


# ── Transcript Store ──────────────────────────────────────────


@dataclass
class TranscriptStore:
    """Ordered transcript of conversation entries with flush/compact.

    Mirrors claw-code TranscriptStore for persistence and replay.
    """

    entries: List[str] = field(default_factory=list)
    flushed: bool = False

    def append(self, entry: str) -> None:
        self.entries.append(entry)

    def compact(self, keep_last: int = 20) -> None:
        """Keep only the last N entries."""
        if len(self.entries) > keep_last:
            self.entries = self.entries[-keep_last:]

    def flush(self) -> None:
        self.flushed = True

    def replay(self) -> tuple:
        return tuple(self.entries)

    def clear(self) -> None:
        self.entries.clear()
        self.flushed = False


# ── Stored Session ────────────────────────────────────────────


@dataclass
class StoredSession:
    """Serializable session snapshot for persistence."""

    session_id: str = ""
    agent_id: str = ""
    messages: List[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    turn_count: int = 0
    metadata: dict = field(default_factory=dict)


DEFAULT_SESSION_DIR = Path(".poseidon_sessions")


def save_session(
    session: StoredSession,
    directory: Optional[Path] = None,
) -> Path:
    """Persist a session to a JSON file."""
    target = directory or DEFAULT_SESSION_DIR
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"{session.session_id}.json"
    data = {
        "session_id": session.session_id,
        "agent_id": session.agent_id,
        "messages": session.messages,
        "input_tokens": session.input_tokens,
        "output_tokens": session.output_tokens,
        "turn_count": session.turn_count,
        "metadata": session.metadata,
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return path


def load_session(
    session_id: str,
    directory: Optional[Path] = None,
) -> StoredSession:
    """Load a previously persisted session."""
    target = directory or DEFAULT_SESSION_DIR
    path = target / f"{session_id}.json"
    data = json.loads(path.read_text())
    return StoredSession(
        session_id=data.get("session_id", session_id),
        agent_id=data.get("agent_id", ""),
        messages=data.get("messages", []),
        input_tokens=data.get("input_tokens", 0),
        output_tokens=data.get("output_tokens", 0),
        turn_count=data.get("turn_count", 0),
        metadata=data.get("metadata", {}),
    )


def list_sessions(directory: Optional[Path] = None) -> List[str]:
    """List all saved session IDs."""
    target = directory or DEFAULT_SESSION_DIR
    if not target.exists():
        return []
    return [
        p.stem for p in sorted(target.glob("*.json"))
    ]


def delete_session(
    session_id: str,
    directory: Optional[Path] = None,
) -> bool:
    """Delete a persisted session file."""
    target = directory or DEFAULT_SESSION_DIR
    path = target / f"{session_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False


def search_sessions(
    query: str,
    directory: Optional[Path] = None,
    max_results: int = 10,
) -> List[StoredSession]:
    """Search across all saved sessions for matching messages."""
    target = directory or DEFAULT_SESSION_DIR
    if not target.exists():
        return []

    results: List[StoredSession] = []
    needle = query.lower()

    for path in sorted(target.glob("*.json"), reverse=True):
        try:
            data = json.loads(path.read_text())
            messages = data.get("messages", [])
            if any(needle in msg.lower() for msg in messages):
                results.append(StoredSession(
                    session_id=data.get("session_id", path.stem),
                    agent_id=data.get("agent_id", ""),
                    messages=messages,
                    input_tokens=data.get("input_tokens", 0),
                    output_tokens=data.get("output_tokens", 0),
                    turn_count=data.get("turn_count", 0),
                    metadata=data.get("metadata", {}),
                ))
                if len(results) >= max_results:
                    break
        except (json.JSONDecodeError, OSError):
            continue

    return results
