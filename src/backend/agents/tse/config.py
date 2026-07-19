# -*- coding: utf-8 -*-
"""TSE (TCN-Skill-Extractor) hyperparameters.

Matches methodology.md defaults: Longformer-dim→hash embed, TCN d={1,2,4},
5 skill queries, multi-task loss weights for training (future).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple


# Categories accepted by methodology + product skill_extractor
VALID_CATEGORIES = frozenset({
    "automation",
    "research",
    "general",
    "analysis",
    "monitoring",
    "development",
    "domain_knowledge",
    "digital_twin",
})

# Map methodology labels → product SkillCategory-ish labels when needed
CATEGORY_ALIASES = {
    "analysis": "research",
    "monitoring": "automation",
    "development": "automation",
}

FIELD_NAMES: Tuple[str, ...] = (
    "name",
    "description",
    "category",
    "tools",
    "instructions",
)

# Field-biased token seeds for cold-start skill queries (pure encoder path)
FIELD_KEYWORD_SEEDS = {
    "name": (
        "技能", "能力", "方案", "流程", "策略", "skill", "capability",
        "playbook", "runbook", "SOP", "做法", "方法",
    ),
    "description": (
        "问题", "场景", "目的", "用于", "解决", "when", "because",
        "背景", "目标", "适用",
    ),
    "category": (
        "自动化", "监控", "研发", "分析", "运维", "研究", "automation",
        "monitoring", "research", "devops",
    ),
    "tools": (
        "工具", "命令", "cli", "api", "sdk", "脚本", "kubectl", "aws",
        "terraform", "python", "boto3", "curl", "tool",
    ),
    "instructions": (
        "步骤", "首先", "然后", "最后", "配置", "检查", "验证", "执行",
        "step", "1.", "2.", "3.", "should", "must", "需要",
    ),
}


@dataclass
class TSEConfig:
    """Runtime config for the TSE pipeline."""

    # Stage 1 — utterance embedding
    embed_dim: int = 256
    max_utterances: int = 64
    max_chars_per_utterance: int = 800
    hash_seed: int = 20260716

    # Stage 2 — TCN
    tcn_hidden_dim: int = 256
    tcn_num_layers: int = 3  # dilations 1,2,4 → RF ≈ 29 with k=3
    tcn_kernel_size: int = 3
    tcn_dropout: float = 0.0  # inference default

    # Stage 3 — skill query attention
    num_queries: int = 5
    num_heads: int = 4
    top_k_utterances: int = 8  # utterances fed to decoder per discussion

    # Stage 4 — constrained decoder (ChatHarness / optional local LLM)
    max_skills: int = 8
    min_skills: int = 1
    decoder_temperature: float = 0.2
    max_source_chars_in_prompt: int = 10000
    grammar_retry: int = 1

    # Multi-task loss weights (for training hooks / telemetry)
    loss_decoder: float = 1.0
    loss_category: float = 0.1
    loss_tools: float = 0.1

    # Backend: "pure" always; "torch" if torch+transformers installed and weights present
    prefer_torch: bool = False
    torch_checkpoint: str = ""

    dilations: List[int] = field(default_factory=lambda: [1, 2, 4])

    def __post_init__(self) -> None:
        if not self.dilations:
            self.dilations = [2 ** i for i in range(self.tcn_num_layers)]
        # Receptive field (kernel=3): 1 + 2 * sum(dilations)
        # [1,2,4] → 1+2*(1+2+4)=15 one-sided; full ≈ 29 as methodology states


DEFAULT_CONFIG = TSEConfig()
