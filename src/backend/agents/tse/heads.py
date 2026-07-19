# -*- coding: utf-8 -*-
"""Multi-task prediction heads (category CE + tools multi-label).

Used in training (methodology multi-task loss) and at inference for decoder hints.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

import numpy as np

from .config import TSEConfig

# Fixed label spaces (stable across train/infer)
CATEGORY_LABELS: Tuple[str, ...] = (
    "automation",
    "research",
    "general",
    "analysis",
    "monitoring",
    "development",
    "domain_knowledge",
    "digital_twin",
)

# Cap tool vocabulary; unknown tools ignored for multi-label head
DEFAULT_TOOL_VOCAB: Tuple[str, ...] = (
    "aws_cli", "python_boto3", "cloudwatch_api", "kubectl", "terraform",
    "docker", "python", "curl", "prometheus", "grafana", "git", "sql",
    "helm", "ansible", "nginx", "redis", "kafka", "elasticsearch",
    "lambda", "s3", "ec2", "rds", "jq", "bash", "httpx", "fastapi",
    "pytorch", "sklearn", "pandas", "numpy", "openai", "deepseek",
    "slack", "jira", "github", "gitlab", "vault", "consul",
    "istio", "argocd", "jenkins", "github_actions", "cloudformation",
    "pulumi", "datadog", "newrelic", "elk", "loki", "tempo",
)


def category_to_id(cat: str) -> int:
    c = (cat or "general").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "ops": "automation", "devops": "automation", "sre": "monitoring",
        "coding": "development", "domain": "domain_knowledge", "twin": "digital_twin",
        "data": "analysis", "infra": "automation",
    }
    c = aliases.get(c, c)
    try:
        return CATEGORY_LABELS.index(c)
    except ValueError:
        return CATEGORY_LABELS.index("general")


def id_to_category(i: int) -> str:
    if 0 <= i < len(CATEGORY_LABELS):
        return CATEGORY_LABELS[i]
    return "general"


def tools_to_multihot(tools: Sequence[str], vocab: Sequence[str] | None = None) -> np.ndarray:
    vocab = list(vocab or DEFAULT_TOOL_VOCAB)
    y = np.zeros(len(vocab), dtype=np.float32)
    index = {t: i for i, t in enumerate(vocab)}
    for t in tools or []:
        key = str(t).strip().lower().replace("-", "_").replace(" ", "_")
        # soft match
        if key in index:
            y[index[key]] = 1.0
            continue
        for v, i in index.items():
            if key in v or v in key:
                y[i] = 1.0
                break
    return y


def multihot_to_tools(vec: np.ndarray, vocab: Sequence[str] | None = None, thr: float = 0.5) -> List[str]:
    vocab = list(vocab or DEFAULT_TOOL_VOCAB)
    out = []
    for i, p in enumerate(vec):
        if float(p) >= thr and i < len(vocab):
            out.append(vocab[i])
    return out


class MultiTaskHeads:
    """category_head + tools_head on skill field representations."""

    def __init__(
        self,
        hidden_dim: int = 256,
        n_categories: int = len(CATEGORY_LABELS),
        n_tools: int = len(DEFAULT_TOOL_VOCAB),
        seed: int = 42,
    ):
        rng = np.random.RandomState(seed)
        scale = (2.0 / hidden_dim) ** 0.5 * 0.5
        self.hidden_dim = hidden_dim
        self.n_categories = n_categories
        self.n_tools = n_tools
        self.tool_vocab = list(DEFAULT_TOOL_VOCAB[:n_tools])
        self.W_cat = rng.normal(0, scale, size=(hidden_dim, n_categories)).astype(np.float32)
        self.b_cat = np.zeros(n_categories, dtype=np.float32)
        self.W_tools = rng.normal(0, scale, size=(hidden_dim, n_tools)).astype(np.float32)
        self.b_tools = np.zeros(n_tools, dtype=np.float32)

    def category_logits(self, h: np.ndarray) -> np.ndarray:
        return h @ self.W_cat + self.b_cat

    def tools_logits(self, h: np.ndarray) -> np.ndarray:
        return h @ self.W_tools + self.b_tools

    def predict(self, skill_repr: Dict[str, np.ndarray]) -> Dict[str, object]:
        cat_h = skill_repr.get("category")
        tools_h = skill_repr.get("tools")
        if cat_h is None or tools_h is None:
            return {"category": "general", "required_tools": [], "category_probs": None}
        cat_logits = self.category_logits(cat_h)
        cat_probs = _softmax(cat_logits)
        tools_logits = self.tools_logits(tools_h)
        tools_prob = 1.0 / (1.0 + np.exp(-tools_logits))
        return {
            "category": id_to_category(int(np.argmax(cat_probs))),
            "category_probs": cat_probs,
            "required_tools": multihot_to_tools(tools_prob, self.tool_vocab, thr=0.45),
            "tools_probs": tools_prob,
        }

    def state_dict(self) -> Dict[str, np.ndarray]:
        return {
            "W_cat": self.W_cat,
            "b_cat": self.b_cat,
            "W_tools": self.W_tools,
            "b_tools": self.b_tools,
        }

    def load_state_dict(self, state: Dict[str, np.ndarray]) -> None:
        for k in ("W_cat", "b_cat", "W_tools", "b_tools"):
            if k in state:
                setattr(self, k, np.asarray(state[k], dtype=np.float32))


def _softmax(x: np.ndarray) -> np.ndarray:
    x = x - np.max(x)
    e = np.exp(x)
    return e / (e.sum() + 1e-9)
