# -*- coding: utf-8 -*-
"""Plaza Consensus Measurement — 讨论收敛度量与分歧检测.

提供:
- ConsensusScore: 基于关键词重叠和立场分析的收敛度评分
- DissidentDetector: 检测明显的反方意见
- EarlyExitCheck: 判断是否可以提前结束讨论
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("plaza_consensus")

# 表达赞同的关键词
_AGREE_PATTERNS = re.compile(
    r"同意|赞同|没错|对的|确实|支持|认同|一致|正确|好主意|可行|"
    r"我也觉得|我也认为|agree|exactly|right|support",
    re.IGNORECASE,
)

# 表达反对的关键词
_DISAGREE_PATTERNS = re.compile(
    r"不同意|反对|但是|不过|然而|问题是|风险|需要注意|不可行|"
    r"不一定|不太|存疑|担忧|顾虑|disagree|however|but|risk|concern",
    re.IGNORECASE,
)


@dataclass
class ConsensusResult:
    """共识度量结果."""

    score: float  # 0.0 ~ 1.0, 1.0=完全共识
    agreement_count: int
    disagreement_count: int
    neutral_count: int
    dissenting_agents: List[str]  # 表达反对的agent_id
    convergence_trend: str  # "rising" | "stable" | "falling"
    can_early_exit: bool  # 是否可以提前结束

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 3),
            "agreement_count": self.agreement_count,
            "disagreement_count": self.disagreement_count,
            "neutral_count": self.neutral_count,
            "dissenting_agents": self.dissenting_agents,
            "convergence_trend": self.convergence_trend,
            "can_early_exit": self.can_early_exit,
        }


def measure_consensus(
    messages: List[Dict[str, Any]],
    round_number: Optional[int] = None,
    early_exit_threshold: float = 0.85,
) -> ConsensusResult:
    """Measure consensus from a list of messages.

    Parameters
    ----------
    messages : list of message dicts (must have 'content', 'agent_id', 'round_number')
    round_number : if provided, only consider messages from this round
    early_exit_threshold : score above which early exit is possible
    """
    filtered = messages
    if round_number is not None:
        filtered = [m for m in messages if m.get("round_number") == round_number]

    if not filtered:
        return ConsensusResult(
            score=0.5, agreement_count=0, disagreement_count=0,
            neutral_count=0, dissenting_agents=[], convergence_trend="stable",
            can_early_exit=False,
        )

    agreement_count = 0
    disagreement_count = 0
    neutral_count = 0
    dissenting_agents: List[str] = []

    for msg in filtered:
        content = msg.get("content", "")
        agent_id = msg.get("agent_id", "")

        agree_hits = len(_AGREE_PATTERNS.findall(content))
        disagree_hits = len(_DISAGREE_PATTERNS.findall(content))

        if disagree_hits > agree_hits:
            disagreement_count += 1
            if agent_id and agent_id not in dissenting_agents:
                dissenting_agents.append(agent_id)
        elif agree_hits > disagree_hits:
            agreement_count += 1
        else:
            neutral_count += 1

    total = agreement_count + disagreement_count + neutral_count
    if total == 0:
        score = 0.5
    else:
        # Score: agreement proportion, weighted with neutral as half-agree
        score = (agreement_count + neutral_count * 0.5) / total

    # Determine convergence trend by comparing current vs prior rounds
    trend = _compute_trend(messages, round_number)

    can_exit = score >= early_exit_threshold and disagreement_count == 0

    return ConsensusResult(
        score=score,
        agreement_count=agreement_count,
        disagreement_count=disagreement_count,
        neutral_count=neutral_count,
        dissenting_agents=dissenting_agents,
        convergence_trend=trend,
        can_early_exit=can_exit,
    )


def _compute_trend(
    messages: List[Dict[str, Any]], current_round: Optional[int]
) -> str:
    """Compare consensus between current and previous round."""
    if current_round is None or current_round <= 1:
        return "stable"

    prev_msgs = [m for m in messages if m.get("round_number") == current_round - 1]
    curr_msgs = [m for m in messages if m.get("round_number") == current_round]

    if not prev_msgs or not curr_msgs:
        return "stable"

    prev_score = _quick_score(prev_msgs)
    curr_score = _quick_score(curr_msgs)

    diff = curr_score - prev_score
    if diff > 0.1:
        return "rising"
    elif diff < -0.1:
        return "falling"
    return "stable"


def _quick_score(msgs: List[Dict[str, Any]]) -> float:
    """Lightweight score for trend comparison."""
    agree = 0
    disagree = 0
    for m in msgs:
        content = m.get("content", "")
        a = len(_AGREE_PATTERNS.findall(content))
        d = len(_DISAGREE_PATTERNS.findall(content))
        if a > d:
            agree += 1
        elif d > a:
            disagree += 1
    total = agree + disagree + (len(msgs) - agree - disagree)
    return (agree + (len(msgs) - agree - disagree) * 0.5) / total if total > 0 else 0.5


def highlight_dissent(
    messages: List[Dict[str, Any]],
    round_number: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Extract messages with clear dissenting opinions for UI highlighting.

    Returns list of {agent_id, agent_name, content_preview, round_number}
    """
    filtered = messages
    if round_number is not None:
        filtered = [m for m in messages if m.get("round_number") == round_number]

    dissents: List[Dict[str, Any]] = []
    for msg in filtered:
        content = msg.get("content", "")
        agree_hits = len(_AGREE_PATTERNS.findall(content))
        disagree_hits = len(_DISAGREE_PATTERNS.findall(content))

        if disagree_hits > agree_hits and disagree_hits >= 2:
            dissents.append({
                "agent_id": msg.get("agent_id", ""),
                "agent_name": msg.get("agent_name", ""),
                "content_preview": content[:150],
                "round_number": msg.get("round_number", 0),
            })

    return dissents
