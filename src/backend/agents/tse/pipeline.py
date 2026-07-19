# -*- coding: utf-8 -*-
"""TSE full pipeline: Longformer-hash → TCN → Skill Query Attn → Constrained JSON.

Public entrypoints used by skill_extractor._llm_prefill.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from .config import DEFAULT_CONFIG, TSEConfig
from .decoder import (
    ConstrainedSkillDecoder,
    heuristic_category_hint,
    heuristic_tools_hint,
)
from .encoder import UtteranceEncoder
from .heads import MultiTaskHeads
from .skill_attention import SkillQueryAttention, field_focus_summary, select_skill_moments
from .tcn import TCNTemporalModule
from .transcript import PlazaTranscript, parse_transcript

logger = logging.getLogger(__name__)


@dataclass
class TSEResult:
    skills: List[Dict[str, Any]] = field(default_factory=list)
    transcript: Optional[PlazaTranscript] = None
    focus_indices: List[int] = field(default_factory=list)
    field_focus: Dict[str, List[Dict]] = field(default_factory=dict)
    category_hint: str = ""
    tools_hint: List[str] = field(default_factory=list)
    raw_response: str = ""
    model: str = ""
    parse_error: Optional[str] = None
    latency_ms: float = 0.0
    stage_timings: Dict[str, float] = field(default_factory=dict)
    backend: str = "pure"
    prompt: str = ""
    skill_repr_norms: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skills": self.skills,
            "focus_indices": self.focus_indices,
            "field_focus": self.field_focus,
            "category_hint": self.category_hint,
            "tools_hint": self.tools_hint,
            "model": self.model,
            "parse_error": self.parse_error,
            "latency_ms": self.latency_ms,
            "stage_timings": self.stage_timings,
            "backend": self.backend,
            "skill_repr_norms": self.skill_repr_norms,
            "utterance_count": len(self.transcript.messages) if self.transcript else 0,
            "topic": self.transcript.topic if self.transcript else "",
        }


class TSEPipeline:
    """
    Longformer(token encoding) → TCN(temporal) → Skill Query Cross-Attention
    → Constrained JSON Decoder.

    Pure-numpy encoder stack always available; decoder uses ChatHarness.
    Optional MultiTaskHeads from training improve category/tools hints.
    """

    def __init__(self, config: TSEConfig | None = None, *, load_checkpoint: bool = False):
        self.config = config or DEFAULT_CONFIG
        self.encoder = UtteranceEncoder(self.config)
        self.tcn = TCNTemporalModule(self.config)
        self.attention = SkillQueryAttention(self.config)
        self.decoder = ConstrainedSkillDecoder(self.config)
        self.heads = MultiTaskHeads(
            hidden_dim=self.config.tcn_hidden_dim,
            seed=self.config.hash_seed + 3,
        )
        self.checkpoint_meta: Dict[str, Any] = {}
        if load_checkpoint:
            self.try_load_latest_checkpoint()

    def try_load_latest_checkpoint(self, path: str | None = None) -> bool:
        """Load trained weights if checkpoint exists. Returns True on success."""
        try:
            from .checkpoint import latest_checkpoint, load_checkpoint
            ckpt = path or latest_checkpoint()
            if not ckpt:
                return False
            self.checkpoint_meta = load_checkpoint(ckpt, self, self.heads) or {}
            self.checkpoint_meta["path"] = str(ckpt)
            logger.info("TSE pipeline loaded checkpoint %s", ckpt)
            return True
        except Exception as e:
            logger.warning("TSE checkpoint load skipped: %s", e)
            return False

    def encode_stages(
        self,
        transcript: PlazaTranscript,
    ) -> Dict[str, Any]:
        """Run Stage 1–3 (no LLM). Returns intermediate tensors + focus."""
        t0 = time.perf_counter()
        emb, mask = self.encoder.encode_transcript(transcript)
        t1 = time.perf_counter()
        temporal = self.tcn.forward(emb, mask)
        t2 = time.perf_counter()
        skill_repr, attn = self.attention.forward(temporal, mask)
        t3 = time.perf_counter()
        focus = select_skill_moments(attn, top_k=self.config.top_k_utterances)
        # If too few messages, use all
        if not focus and transcript.messages:
            focus = list(range(len(transcript.messages)))
        ff = field_focus_summary(transcript, attn)
        norms = {k: float(np.linalg.norm(v)) for k, v in skill_repr.items()}
        return {
            "embeddings": emb,
            "mask": mask,
            "temporal": temporal,
            "skill_repr": skill_repr,
            "attn_weights": attn,
            "focus_indices": focus,
            "field_focus": ff,
            "skill_repr_norms": norms,
            "timings": {
                "stage1_encoder_ms": (t1 - t0) * 1000,
                "stage2_tcn_ms": (t2 - t1) * 1000,
                "stage3_attention_ms": (t3 - t2) * 1000,
            },
        }

    async def extract(
        self,
        source_text: str,
        *,
        source_title: str = "",
        source_meta: Optional[Dict[str, Any]] = None,
        harness=None,
        chat_fn=None,
        transcript: Optional[PlazaTranscript] = None,
    ) -> TSEResult:
        """Full extract: parse → Stage1-3 → Stage4 constrained decode."""
        t_start = time.perf_counter()
        result = TSEResult(backend="pure")

        tr = transcript or parse_transcript(
            source_text,
            source_title=source_title,
            source_meta=source_meta,
            max_utterances=self.config.max_utterances,
        )
        result.transcript = tr

        if not tr.messages:
            result.parse_error = "empty transcript"
            result.latency_ms = (time.perf_counter() - t_start) * 1000
            return result

        stages = self.encode_stages(tr)
        result.focus_indices = list(stages["focus_indices"])
        result.field_focus = stages["field_focus"]
        result.skill_repr_norms = stages["skill_repr_norms"]
        result.stage_timings.update(stages["timings"])

        # Multi-task heads (trained) → decoder hints; fall back to heuristics
        try:
            head_pred = self.heads.predict(stages["skill_repr"])
            result.category_hint = str(head_pred.get("category") or heuristic_category_hint(tr))
            head_tools = list(head_pred.get("required_tools") or [])
            result.tools_hint = head_tools or heuristic_tools_hint(tr)
        except Exception:
            result.category_hint = heuristic_category_hint(tr)
            result.tools_hint = heuristic_tools_hint(tr)

        t_dec0 = time.perf_counter()
        dec = await self.decoder.generate(
            tr,
            focus_indices=result.focus_indices,
            field_focus=result.field_focus,
            category_hint=result.category_hint,
            tools_hint=result.tools_hint,
            harness=harness,
            chat_fn=chat_fn,
        )
        result.stage_timings["stage4_decoder_ms"] = (time.perf_counter() - t_dec0) * 1000
        result.skills = list(dec.get("skills") or [])
        result.raw_response = dec.get("raw_response") or ""
        result.model = dec.get("model") or ""
        result.parse_error = dec.get("parse_error")
        result.prompt = dec.get("prompt") or ""
        result.latency_ms = (time.perf_counter() - t_start) * 1000

        logger.info(
            "TSE extract discussion=%s utterances=%d focus=%s skills=%d latency=%.1fms model=%s",
            tr.discussion_id,
            len(tr.messages),
            result.focus_indices,
            len(result.skills),
            result.latency_ms,
            result.model,
        )
        return result


# Module-level singleton for reuse of random tables / trained weights
_PIPELINE: Optional[TSEPipeline] = None


def get_tse_pipeline(config: TSEConfig | None = None, *, reload: bool = False) -> TSEPipeline:
    global _PIPELINE
    if config is not None:
        pipe = TSEPipeline(config, load_checkpoint=True)
        return pipe
    if _PIPELINE is None or reload:
        _PIPELINE = TSEPipeline(load_checkpoint=True)
    return _PIPELINE


async def extract_skills(
    source_text: str,
    *,
    source_title: str = "",
    source_meta: Optional[Dict[str, Any]] = None,
    harness=None,
    chat_fn=None,
    config: TSEConfig | None = None,
) -> TSEResult:
    """Convenience async API for skill_extractor."""
    pipe = get_tse_pipeline(config)
    return await pipe.extract(
        source_text,
        source_title=source_title,
        source_meta=source_meta,
        harness=harness,
        chat_fn=chat_fn,
    )


def extract_skill_moments(
    source_text: str,
    *,
    source_title: str = "",
    source_meta: Optional[Dict[str, Any]] = None,
    config: TSEConfig | None = None,
) -> Dict[str, Any]:
    """Sync Stage 1–3 only (for tests / telemetry without LLM)."""
    pipe = get_tse_pipeline(config)
    tr = parse_transcript(
        source_text,
        source_title=source_title,
        source_meta=source_meta,
        max_utterances=pipe.config.max_utterances,
    )
    stages = pipe.encode_stages(tr)
    return {
        "topic": tr.topic,
        "utterance_count": len(tr.messages),
        "focus_indices": stages["focus_indices"],
        "field_focus": stages["field_focus"],
        "skill_repr_norms": stages["skill_repr_norms"],
        "timings": stages["timings"],
        "transcript_preview": tr.format_for_prompt(stages["focus_indices"])[:2000],
    }
