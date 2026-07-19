# -*- coding: utf-8 -*-
"""Plaza transcript normalization for TSE Stage 1 input.

Accepts structured transcripts (methodology format) or free-form source_text
from skill_extractor (chat logs, plaza exports, documents).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class Utterance:
    msg_id: str
    speaker_id: str
    speaker_name: str
    role: str
    niche_role: str
    ritual_signal: str
    round_number: int
    content: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "msg_id": self.msg_id,
            "speaker_id": self.speaker_id,
            "speaker_name": self.speaker_name,
            "role": self.role,
            "niche_role": self.niche_role,
            "ritual_signal": self.ritual_signal,
            "round_number": self.round_number,
            "content": self.content,
        }


@dataclass
class PlazaTranscript:
    discussion_id: str
    topic: str
    messages: List[Utterance] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "discussion_id": self.discussion_id,
            "topic": self.topic,
            "messages": [m.to_dict() for m in self.messages],
            "meta": dict(self.meta),
        }

    def format_for_prompt(self, indices: Optional[Sequence[int]] = None) -> str:
        """Human-readable transcript, optionally subset of utterance indices."""
        lines = [f"Topic: {self.topic}"]
        msgs = self.messages
        if indices is not None:
            ordered = [i for i in indices if 0 <= i < len(msgs)]
            msgs_iter = [(i, msgs[i]) for i in ordered]
        else:
            msgs_iter = list(enumerate(msgs))
        for i, msg in msgs_iter:
            lines.append(
                f"[#{i} Round {msg.round_number}] {msg.speaker_name} "
                f"({msg.role}, signal={msg.ritual_signal}): {msg.content}"
            )
        return "\n".join(lines)


# Patterns for free-form plaza / chat logs
_LINE_PATTERNS = [
    # [Round 1] 架构师Alpha (architect, signal=supplement): content
    re.compile(
        r"^\[?\s*(?:Round|轮次|R)\s*(?P<round>\d+)\s*\]?\s*"
        r"(?P<name>[^(:：\[{]+?)\s*"
        r"(?:\((?P<meta>[^)]*)\))?\s*[:：]\s*(?P<body>.+)$",
        re.IGNORECASE,
    ),
    # 架构师Alpha: content  /  @devops: content
    re.compile(
        r"^(?:@)?(?P<name>[A-Za-z0-9_\u4e00-\u9fff\-·]{1,40})\s*[:：]\s*(?P<body>.+)$"
    ),
    # **Name** content
    re.compile(
        r"^\*\*(?P<name>[^*]{1,40})\*\*\s*[:：]?\s*(?P<body>.+)$"
    ),
]


def _parse_meta_blob(meta: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not meta:
        return out
    # role=x, signal=y  or  role, signal=y
    for part in re.split(r"[,;|]", meta):
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip().lower()] = v.strip()
        elif ":" in part:
            k, v = part.split(":", 1)
            out[k.strip().lower()] = v.strip()
        else:
            # bare token — treat first as role, later as signal
            if "role" not in out:
                out["role"] = part
            elif "ritual_signal" not in out:
                out["ritual_signal"] = part
    return out


def _guess_role(name: str, meta: Dict[str, str]) -> str:
    if meta.get("role"):
        return meta["role"]
    n = (name or "").lower()
    mapping = [
        ("architect", "architect"), ("架构", "architect"),
        ("devops", "devops"), ("运维", "devops"), ("sre", "devops"),
        ("pm", "pm"), ("产品", "pm"), ("manager", "pm"),
        ("security", "security"), ("安全", "security"),
        ("data", "data"), ("数据", "data"),
        ("research", "research"), ("研究", "research"),
        ("coder", "developer"), ("开发", "developer"), ("dev", "developer"),
    ]
    for key, role in mapping:
        if key in n:
            return role
    return "participant"


def _split_paragraphs(text: str) -> List[str]:
    chunks = re.split(r"\n\s*\n+", text.strip())
    out: List[str] = []
    for c in chunks:
        c = c.strip()
        if not c:
            continue
        # further split very long paragraphs by sentence boundary
        if len(c) > 600:
            parts = re.split(r"(?<=[。！？.!?])\s+", c)
            buf = ""
            for p in parts:
                if len(buf) + len(p) < 500:
                    buf = f"{buf} {p}".strip()
                else:
                    if buf:
                        out.append(buf)
                    buf = p
            if buf:
                out.append(buf)
        else:
            out.append(c)
    return out


def parse_transcript(
    source_text: str,
    *,
    source_title: str = "",
    source_meta: Optional[Dict[str, Any]] = None,
    max_utterances: int = 64,
) -> PlazaTranscript:
    """Build a PlazaTranscript from structured meta or free-form text."""
    meta = dict(source_meta or {})
    discussion_id = str(
        meta.get("source_discussion_id")
        or meta.get("discussion_id")
        or meta.get("id")
        or "unknown"
    )
    topic = str(meta.get("topic") or source_title or "untitled discussion")

    # Structured messages already in meta
    raw_msgs = meta.get("messages") or meta.get("utterances") or meta.get("lines")
    messages: List[Utterance] = []
    if isinstance(raw_msgs, list) and raw_msgs:
        for i, m in enumerate(raw_msgs[:max_utterances]):
            if not isinstance(m, dict):
                content = str(m).strip()
                if not content:
                    continue
                messages.append(
                    Utterance(
                        msg_id=f"m{i}",
                        speaker_id=f"speaker_{i}",
                        speaker_name=f"Speaker{i}",
                        role="participant",
                        niche_role="analyst",
                        ritual_signal="supplement",
                        round_number=i // 4,
                        content=content[:2000],
                    )
                )
                continue
            content = str(m.get("content") or m.get("text") or m.get("body") or "").strip()
            if not content:
                continue
            messages.append(
                Utterance(
                    msg_id=str(m.get("msg_id") or m.get("id") or f"m{i}"),
                    speaker_id=str(m.get("speaker_id") or m.get("agent_id") or f"speaker_{i}"),
                    speaker_name=str(m.get("speaker_name") or m.get("name") or m.get("speaker") or f"Speaker{i}"),
                    role=str(m.get("role") or "participant"),
                    niche_role=str(m.get("niche_role") or m.get("niche") or "analyst"),
                    ritual_signal=str(m.get("ritual_signal") or m.get("signal") or "supplement"),
                    round_number=int(m.get("round_number") if m.get("round_number") is not None else m.get("round", i // 4) or 0),
                    content=content[:2000],
                )
            )
        if messages:
            return PlazaTranscript(
                discussion_id=discussion_id,
                topic=topic,
                messages=messages,
                meta=meta,
            )

    text = (source_text or "").strip()
    if not text:
        return PlazaTranscript(discussion_id=discussion_id, topic=topic, messages=[], meta=meta)

    # Line-oriented parse
    lines = text.splitlines()
    parsed_any = False
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or len(line) < 2:
            continue
        matched = None
        for pat in _LINE_PATTERNS:
            m = pat.match(line)
            if m:
                matched = m
                break
        if not matched:
            continue
        parsed_any = True
        gd = matched.groupdict()
        name = (gd.get("name") or f"Speaker{i}").strip()
        body = (gd.get("body") or "").strip()
        if not body:
            continue
        meta_blob = _parse_meta_blob(gd.get("meta") or "")
        rnd = gd.get("round")
        round_number = int(rnd) if rnd is not None and str(rnd).isdigit() else len(messages) // 4
        messages.append(
            Utterance(
                msg_id=f"m{len(messages)}",
                speaker_id=f"spk_{len(messages)}",
                speaker_name=name[:40],
                role=_guess_role(name, meta_blob),
                niche_role=meta_blob.get("niche_role") or meta_blob.get("niche") or "analyst",
                ritual_signal=meta_blob.get("ritual_signal") or meta_blob.get("signal") or "supplement",
                round_number=round_number,
                content=body[:2000],
            )
        )
        if len(messages) >= max_utterances:
            break

    if not parsed_any or len(messages) < 2:
        # Paragraph fallback — treat as multi-turn pseudo-discussion
        messages = []
        paras = _split_paragraphs(text)
        for i, para in enumerate(paras[:max_utterances]):
            messages.append(
                Utterance(
                    msg_id=f"p{i}",
                    speaker_id=f"para_{i}",
                    speaker_name=f"Segment{i + 1}",
                    role="document",
                    niche_role="analyst",
                    ritual_signal="supplement",
                    round_number=i // 3,
                    content=para[:2000],
                )
            )

    return PlazaTranscript(
        discussion_id=discussion_id,
        topic=topic,
        messages=messages[:max_utterances],
        meta=meta,
    )
