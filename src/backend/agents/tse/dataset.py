# -*- coding: utf-8 -*-
"""Plaza extraction dataset: (transcript, skills) silver/gold pairs.

JSONL schema (one sample per line):
{
  "discussion_id": "...",
  "transcript": {"topic": "...", "messages": [...]},
  "skills": [{name, description, category, instructions, required_tools, ...}],
  "source": "silver|gold|human",
  "verified": false
}
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple

import numpy as np

from .config import TSEConfig
from .encoder import UtteranceEncoder, hash_embed_text
from .heads import (
    CATEGORY_LABELS,
    DEFAULT_TOOL_VOCAB,
    category_to_id,
    tools_to_multihot,
)
from .schema import validate_skill_fields
from .transcript import PlazaTranscript, parse_transcript

logger = logging.getLogger(__name__)


@dataclass
class ExtractionExample:
    discussion_id: str
    transcript: PlazaTranscript
    skills: List[Dict[str, Any]]
    source: str = "silver"
    verified: bool = False
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "discussion_id": self.discussion_id,
            "transcript": self.transcript.to_dict(),
            "skills": self.skills,
            "source": self.source,
            "verified": self.verified,
            "meta": self.meta,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ExtractionExample":
        tr_raw = d.get("transcript") or {}
        if isinstance(tr_raw, dict) and tr_raw.get("messages"):
            tr = parse_transcript(
                "",
                source_title=str(tr_raw.get("topic") or d.get("topic") or ""),
                source_meta={
                    "messages": tr_raw.get("messages"),
                    "topic": tr_raw.get("topic"),
                    "source_discussion_id": d.get("discussion_id") or tr_raw.get("discussion_id"),
                },
            )
            if tr_raw.get("topic"):
                tr.topic = str(tr_raw["topic"])
        else:
            text = str(d.get("source_text") or d.get("text") or "")
            tr = parse_transcript(
                text,
                source_title=str(d.get("topic") or d.get("source_title") or ""),
                source_meta=d.get("source_meta") if isinstance(d.get("source_meta"), dict) else {},
            )
        skills = []
        for s in d.get("skills") or []:
            try:
                skills.append(validate_skill_fields(s, strict=False))
            except Exception:
                continue
        return cls(
            discussion_id=str(d.get("discussion_id") or tr.discussion_id or "unknown"),
            transcript=tr,
            skills=skills,
            source=str(d.get("source") or "silver"),
            verified=bool(d.get("verified", False)),
            meta=dict(d.get("meta") or {}),
        )


class PlazaExtractionDataset:
    """In-memory dataset of extraction examples + feature builders for training."""

    def __init__(
        self,
        examples: Optional[List[ExtractionExample]] = None,
        config: TSEConfig | None = None,
    ):
        self.examples: List[ExtractionExample] = list(examples or [])
        self.config = config or TSEConfig()
        self.encoder = UtteranceEncoder(self.config)

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> ExtractionExample:
        return self.examples[idx]

    def __iter__(self) -> Iterator[ExtractionExample]:
        return iter(self.examples)

    def append(self, ex: ExtractionExample) -> None:
        self.examples.append(ex)

    def extend(self, items: Sequence[ExtractionExample]) -> None:
        self.examples.extend(items)

    def split(self, val_ratio: float = 0.15, seed: int = 42) -> Tuple["PlazaExtractionDataset", "PlazaExtractionDataset"]:
        rng = np.random.RandomState(seed)
        idxs = np.arange(len(self.examples))
        rng.shuffle(idxs)
        n_val = max(1, int(len(idxs) * val_ratio)) if len(idxs) > 1 else 0
        val_idx = set(idxs[:n_val].tolist())
        train_ex = [self.examples[i] for i in range(len(self.examples)) if i not in val_idx]
        val_ex = [self.examples[i] for i in range(len(self.examples)) if i in val_idx]
        return (
            PlazaExtractionDataset(train_ex, self.config),
            PlazaExtractionDataset(val_ex, self.config),
        )

    # ── IO ────────────────────────────────────────────────────────────

    @classmethod
    def load_jsonl(cls, path: str | Path, config: TSEConfig | None = None) -> "PlazaExtractionDataset":
        path = Path(path)
        examples: List[ExtractionExample] = []
        if not path.exists():
            logger.warning("dataset path missing: %s", path)
            return cls([], config)
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    examples.append(ExtractionExample.from_dict(json.loads(line)))
                except Exception as e:
                    logger.warning("skip line %d in %s: %s", line_no, path, e)
        return cls(examples, config)

    def save_jsonl(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for ex in self.examples:
                f.write(json.dumps(ex.to_dict(), ensure_ascii=False) + "\n")

    # ── Features for multi-task training ──────────────────────────────

    def primary_skill(self, ex: ExtractionExample) -> Optional[Dict[str, Any]]:
        return ex.skills[0] if ex.skills else None

    def field_targets(self, skill: Dict[str, Any], hidden_dim: int, seed: int) -> Dict[str, np.ndarray]:
        """Hash-embed skill fields as AE reconstruction targets."""
        tools = skill.get("required_tools") or []
        tools_text = " ".join(str(t) for t in tools)
        texts = {
            "name": str(skill.get("name") or ""),
            "description": str(skill.get("description") or ""),
            "category": str(skill.get("category") or "general"),
            "tools": tools_text,
            "instructions": str(skill.get("instructions") or ""),
        }
        out = {}
        for k, t in texts.items():
            e = hash_embed_text(t, hidden_dim, seed)
            if e.shape[0] < hidden_dim:
                e = np.pad(e, (0, hidden_dim - e.shape[0]))
            else:
                e = e[:hidden_dim]
            nrm = float(np.linalg.norm(e)) + 1e-8
            out[k] = (e / nrm).astype(np.float32)
        return out

    def label_tensors(self, skill: Dict[str, Any]) -> Dict[str, np.ndarray]:
        cat_id = category_to_id(str(skill.get("category") or "general"))
        y_cat = np.zeros(len(CATEGORY_LABELS), dtype=np.float32)
        y_cat[cat_id] = 1.0
        y_tools = tools_to_multihot(skill.get("required_tools") or [], DEFAULT_TOOL_VOCAB)
        return {"category_onehot": y_cat, "category_id": np.array(cat_id, dtype=np.int64), "tools_multihot": y_tools}
