# -*- coding: utf-8 -*-
"""轨迹分析器 — LLM分析会话 → 提取 skills_referenced / outcome / evidence.

对应 SkillClaw: Claw1-4 Trajectories → Aggregation → Attribution.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TrajectoryAnalysis:
    """单个会话的轨迹分析结果."""
    session_id: str = ""
    skills_referenced: List[str] = field(default_factory=list)
    outcome: str = ""  # success / partial / failure
    evidence_snippets: List[str] = field(default_factory=list)
    root_cause: str = ""
    suggested_skill_improvements: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "skills_referenced": self.skills_referenced,
            "outcome": self.outcome,
            "evidence_snippets": self.evidence_snippets,
            "root_cause": self.root_cause,
            "suggested_skill_improvements": self.suggested_skill_improvements,
        }


@dataclass
class AggregatedAnalysis:
    """多个会话的聚合分析."""
    total_sessions: int = 0
    success_count: int = 0
    partial_count: int = 0
    failure_count: int = 0
    skill_usage_freq: Dict[str, int] = field(default_factory=dict)
    common_failure_patterns: List[str] = field(default_factory=list)
    improvement_suggestions: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_sessions": self.total_sessions,
            "success_count": self.success_count,
            "partial_count": self.partial_count,
            "failure_count": self.failure_count,
            "skill_usage_freq": self.skill_usage_freq,
            "common_failure_patterns": self.common_failure_patterns,
            "improvement_suggestions": self.improvement_suggestions,
        }


class TrajectoryAnalyzer:
    """分析会话轨迹，提取技能使用模式和效果归因."""

    def __init__(self, session_store=None, chat_harness=None):
        self._session_store = session_store
        self._chat_harness = chat_harness

    async def analyze_session(self, session_id: str) -> TrajectoryAnalysis:
        """LLM分析单个会话 → 提取技能引用和结果."""
        analysis = TrajectoryAnalysis(session_id=session_id)

        if not self._session_store:
            return analysis

        # Load session transcript
        session = self._session_store.get_session(session_id) if hasattr(self._session_store, 'get_session') else None
        if not session:
            return analysis

        transcript = ""
        messages = session.get("messages", []) if isinstance(session, dict) else []
        for msg in messages[-20:]:  # Last 20 messages
            role = msg.get("role", "")
            content = msg.get("content", "")[:500]
            transcript += f"[{role}] {content}\n"

        if not transcript or not self._chat_harness:
            return analysis

        # LLM analysis
        try:
            result = await self._chat_harness.chat(
                prompt=f"分析以下会话轨迹:\n\n{transcript}",
                system_prompt=TRAJECTORY_ANALYSIS_PROMPT,
                agent_id="trajectory_analyzer",
            )
            if result and result.get("response"):
                import json
                try:
                    data = json.loads(result["response"])
                    analysis.skills_referenced = data.get("skills_referenced", [])
                    analysis.outcome = data.get("outcome", "unknown")
                    analysis.evidence_snippets = data.get("evidence_snippets", [])
                    analysis.root_cause = data.get("root_cause", "")
                    analysis.suggested_skill_improvements = data.get("suggested_skill_improvements", [])
                except json.JSONDecodeError:
                    analysis.outcome = "parse_error"
        except Exception as e:
            logger.error("Trajectory analysis failed: %s", e)

        return analysis

    async def analyze_batch(self, session_ids: List[str]) -> AggregatedAnalysis:
        """批量分析多个会话 → 聚合结果."""
        agg = AggregatedAnalysis()
        analyses = []

        for sid in session_ids:
            a = await self.analyze_session(sid)
            analyses.append(a)

        agg.total_sessions = len(analyses)
        for a in analyses:
            if a.outcome == "success":
                agg.success_count += 1
            elif a.outcome == "partial":
                agg.partial_count += 1
            elif a.outcome == "failure":
                agg.failure_count += 1

            for skill_id in a.skills_referenced:
                agg.skill_usage_freq[skill_id] = agg.skill_usage_freq.get(skill_id, 0) + 1

            if a.root_cause:
                agg.common_failure_patterns.append(a.root_cause)

            agg.improvement_suggestions.extend(a.suggested_skill_improvements)

        return agg


TRAJECTORY_ANALYSIS_PROMPT = """你是一个会话轨迹分析专家。分析提供的会话记录，提取以下信息并以JSON格式输出:

{
  "skills_referenced": ["识别到的技能名称列表"],
  "outcome": "success/partial/failure",
  "evidence_snippets": ["关键证据片段"],
  "root_cause": "如果失败或部分成功，根因分析",
  "suggested_skill_improvements": [{"skill": "技能名", "suggestion": "改进建议"}]
}

只输出JSON，不要其他文字。"""


# ── Singleton ────────────────────────────────────────────────────

_analyzer: Optional[TrajectoryAnalyzer] = None


def get_trajectory_analyzer() -> TrajectoryAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = TrajectoryAnalyzer()
    return _analyzer


def init_trajectory_analyzer(session_store=None, chat_harness=None) -> TrajectoryAnalyzer:
    global _analyzer
    _analyzer = TrajectoryAnalyzer(session_store=session_store, chat_harness=chat_harness)
    logger.info("TrajectoryAnalyzer initialized")
    return _analyzer
