# -*- coding: utf-8 -*-
"""Memory System — AAS 双记忆系统.

为每个孪生智能体配置"经验库"和"知识库"，细分为短期和长期存储。
智能体在沙箱中每一次试错都会转化为经验，指导后续的协同决策。
"""

from __future__ import annotations

import json
import logging
import os
from collections import defaultdict
from typing import Any, Dict, List, Optional

from .models import (
    ExperienceEntry,
    ExperienceOutcome,
    MemoryType,
    ReflectionEntry,
)

logger = logging.getLogger(__name__)

# 存储路径
_STORAGE_BASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "storage", "sandbox", "experience_pool"
)


class AgentMemory:
    """单个智能体的双记忆系统."""

    def __init__(self, agent_id: str, max_short_term: int = 50, max_long_term: int = 500):
        self.agent_id = agent_id
        self._max_short_term = max_short_term
        self._max_long_term = max_long_term
        # 短期记忆（当前会话）
        self._short_term: List[ExperienceEntry] = []
        # 长期记忆（跨会话持久）
        self._long_term: List[ExperienceEntry] = []
        # 反思记录
        self._reflections: List[ReflectionEntry] = []
        # 启发式规则库（从反思中提炼）
        self._heuristics: List[str] = []

    # ── 经验管理 ────────────────────────────────────────────────

    def record_experience(self, experience: ExperienceEntry) -> None:
        """记录一条新经验."""
        experience.agent_id = self.agent_id
        self._short_term.append(experience)
        # LRU 管理短期记忆
        if len(self._short_term) > self._max_short_term:
            # 将溢出的短期记忆提升为长期（如果有价值）
            evicted = self._short_term.pop(0)
            if evicted.outcome == ExperienceOutcome.SUCCESS or evicted.reward > 0.5:
                self._promote_to_long_term(evicted)

    def _promote_to_long_term(self, exp: ExperienceEntry) -> None:
        """将有价值的短期经验提升为长期记忆."""
        exp.memory_type = MemoryType.LONG_TERM
        self._long_term.append(exp)
        if len(self._long_term) > self._max_long_term:
            # 淘汰访问次数最少的
            self._long_term.sort(key=lambda e: e.access_count)
            self._long_term.pop(0)

    def consolidate(self) -> int:
        """记忆固化：将所有有价值的短期记忆提升为长期.

        Returns:
            提升的记忆数量
        """
        promoted = 0
        remaining = []
        for exp in self._short_term:
            if exp.outcome == ExperienceOutcome.SUCCESS or exp.reward > 0.3:
                self._promote_to_long_term(exp)
                promoted += 1
            else:
                remaining.append(exp)
        self._short_term = remaining
        logger.info(f"🧠 {self.agent_id}: 固化 {promoted} 条经验至长期记忆")
        return promoted

    # ── 经验检索 ────────────────────────────────────────────────

    def recall_relevant(self, situation: str, top_k: int = 5) -> List[ExperienceEntry]:
        """根据情境检索相关经验.

        简单实现：关键词匹配 + 奖励排序。
        后续可升级为向量检索。
        """
        all_memories = self._short_term + self._long_term
        keywords = set(situation.lower().split())

        scored = []
        for exp in all_memories:
            # 简单相关性评分
            exp_words = set(exp.situation.lower().split())
            overlap = len(keywords & exp_words)
            score = overlap * 0.5 + exp.reward * 0.3 + (1.0 if exp.outcome == ExperienceOutcome.SUCCESS else 0.0) * 0.2
            if score > 0:
                scored.append((score, exp))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [exp for _, exp in scored[:top_k]]

        # 更新访问计数
        for exp in results:
            exp.access_count += 1

        return results

    def get_heuristics(self) -> List[str]:
        """获取当前所有启发式规则."""
        return self._heuristics

    # ── 反思 ────────────────────────────────────────────────────

    def add_reflection(self, reflection: ReflectionEntry) -> None:
        """添加反思记录."""
        reflection.agent_id = self.agent_id
        self._reflections.append(reflection)
        # 提取新的启发式规则
        if reflection.new_heuristic:
            self._heuristics.append(reflection.new_heuristic)

    def get_reflections(self, limit: int = 10) -> List[ReflectionEntry]:
        """获取最近的反思记录."""
        return self._reflections[-limit:]

    # ── 统计 ────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """获取记忆系统统计."""
        return {
            "agent_id": self.agent_id,
            "short_term_count": len(self._short_term),
            "long_term_count": len(self._long_term),
            "reflections_count": len(self._reflections),
            "heuristics_count": len(self._heuristics),
            "success_rate": self._calc_success_rate(),
        }

    def _calc_success_rate(self) -> float:
        """计算历史成功率."""
        all_exp = self._short_term + self._long_term
        if not all_exp:
            return 0.0
        successes = sum(1 for e in all_exp if e.outcome == ExperienceOutcome.SUCCESS)
        return successes / len(all_exp)

    # ── 持久化 ──────────────────────────────────────────────────

    def save(self) -> None:
        """持久化长期记忆到文件."""
        os.makedirs(_STORAGE_BASE, exist_ok=True)
        filepath = os.path.join(_STORAGE_BASE, f"{self.agent_id}.json")
        data = {
            "agent_id": self.agent_id,
            "long_term": [self._exp_to_dict(e) for e in self._long_term],
            "heuristics": self._heuristics,
            "reflections": [self._ref_to_dict(r) for r in self._reflections[-50:]],
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self) -> bool:
        """从文件加载长期记忆."""
        filepath = os.path.join(_STORAGE_BASE, f"{self.agent_id}.json")
        if not os.path.exists(filepath):
            return False
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._long_term = [self._dict_to_exp(d) for d in data.get("long_term", [])]
        self._heuristics = data.get("heuristics", [])
        self._reflections = [self._dict_to_ref(d) for d in data.get("reflections", [])]
        return True

    @staticmethod
    def _exp_to_dict(exp: ExperienceEntry) -> Dict[str, Any]:
        return {
            "experience_id": exp.experience_id,
            "agent_id": exp.agent_id,
            "session_id": exp.session_id,
            "timestamp": exp.timestamp,
            "situation": exp.situation,
            "action_taken": exp.action_taken,
            "outcome": exp.outcome.value,
            "reward": exp.reward,
            "reflection": exp.reflection,
            "lessons_learned": exp.lessons_learned,
            "applicable_conditions": exp.applicable_conditions,
            "memory_type": exp.memory_type.value,
            "access_count": exp.access_count,
        }

    @staticmethod
    def _dict_to_exp(d: Dict[str, Any]) -> ExperienceEntry:
        return ExperienceEntry(
            experience_id=d.get("experience_id", ""),
            agent_id=d.get("agent_id", ""),
            session_id=d.get("session_id", ""),
            timestamp=d.get("timestamp", ""),
            situation=d.get("situation", ""),
            action_taken=d.get("action_taken", ""),
            outcome=ExperienceOutcome(d.get("outcome", "failure")),
            reward=d.get("reward", 0.0),
            reflection=d.get("reflection", ""),
            lessons_learned=d.get("lessons_learned", []),
            applicable_conditions=d.get("applicable_conditions", []),
            memory_type=MemoryType(d.get("memory_type", "long_term")),
            access_count=d.get("access_count", 0),
        )

    @staticmethod
    def _ref_to_dict(ref: ReflectionEntry) -> Dict[str, Any]:
        return {
            "reflection_id": ref.reflection_id,
            "agent_id": ref.agent_id,
            "timestamp": ref.timestamp,
            "trigger": ref.trigger,
            "analysis": ref.analysis,
            "conclusion": ref.conclusion,
            "new_heuristic": ref.new_heuristic,
            "source_experiences": ref.source_experiences,
            "confidence": ref.confidence,
        }

    @staticmethod
    def _dict_to_ref(d: Dict[str, Any]) -> ReflectionEntry:
        return ReflectionEntry(
            reflection_id=d.get("reflection_id", ""),
            agent_id=d.get("agent_id", ""),
            timestamp=d.get("timestamp", ""),
            trigger=d.get("trigger", ""),
            analysis=d.get("analysis", ""),
            conclusion=d.get("conclusion", ""),
            new_heuristic=d.get("new_heuristic", ""),
            source_experiences=d.get("source_experiences", []),
            confidence=d.get("confidence", 0.5),
        )


class MemoryPool:
    """记忆池 — 管理所有智能体的记忆系统."""

    def __init__(self):
        self._memories: Dict[str, AgentMemory] = {}

    def get_or_create(self, agent_id: str) -> AgentMemory:
        """获取或创建智能体记忆."""
        if agent_id not in self._memories:
            mem = AgentMemory(agent_id)
            mem.load()  # 尝试加载持久化数据
            self._memories[agent_id] = mem
        return self._memories[agent_id]

    def consolidate_all(self) -> Dict[str, int]:
        """批量固化所有智能体记忆."""
        results = {}
        for agent_id, mem in self._memories.items():
            results[agent_id] = mem.consolidate()
        return results

    def save_all(self) -> None:
        """持久化所有智能体长期记忆."""
        for mem in self._memories.values():
            mem.save()

    def get_global_stats(self) -> Dict[str, Any]:
        """获取全局记忆池统计."""
        stats = {}
        for agent_id, mem in self._memories.items():
            stats[agent_id] = mem.get_stats()
        return stats
