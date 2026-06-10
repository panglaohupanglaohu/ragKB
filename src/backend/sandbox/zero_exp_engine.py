# -*- coding: utf-8 -*-
"""Zero-Exp Engine — AAS 认知进化循环层.

实现零经验启动的智能体自主学习:
- 经验–反思–优化 持续循环
- 无需预设经验，从试错中学习
- 自动提取协作 SOP
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import (
    CollaborationSOP,
    ExperienceEntry,
    ExperienceOutcome,
    ReflectionEntry,
    SimulationStep,
    StrategyStatus,
)
from .memory_system import AgentMemory, MemoryPool

logger = logging.getLogger(__name__)


class ZeroExpEngine:
    """Zero-Exp 演化引擎 — 驱动智能体零经验自主学习.

    核心循环: Experience → Reflect → Optimize
    """

    def __init__(self, memory_pool: MemoryPool):
        self._memory_pool = memory_pool
        # 提取的 SOP 库
        self._sop_library: List[CollaborationSOP] = []
        # 演化统计
        self._total_experiences: int = 0
        self._total_reflections: int = 0
        self._total_sops: int = 0

    # ── 经验收集 ────────────────────────────────────────────────

    def collect_experience_from_step(
        self, session_id: str, step: SimulationStep, agent_id: str, twin_id: str
    ) -> ExperienceEntry:
        """从仿真步骤中收集单个智能体的经验."""
        action = step.agent_actions.get(twin_id)
        # [fix] 防御: action 可能是 None 或非 dict（如混沌禁用 Agent 的 disabled 标记）
        if not isinstance(action, dict):
            action = {"action": "unknown"}
        reward = step.step_rewards.get(twin_id, 0.0)

        # 确定结果
        if reward > 0.2:
            outcome = ExperienceOutcome.SUCCESS
        elif reward > 0:
            outcome = ExperienceOutcome.PARTIAL
        else:
            outcome = ExperienceOutcome.FAILURE

        experience = ExperienceEntry(
            agent_id=agent_id,
            session_id=session_id,
            situation=f"step_{step.step_id}: {action.get('action', 'unknown')}",
            action_taken=str(action),
            outcome=outcome,
            reward=reward,
        )

        # 存入记忆
        memory = self._memory_pool.get_or_create(agent_id)
        memory.record_experience(experience)
        self._total_experiences += 1

        return experience

    def collect_experiences_from_simulation(
        self, session_id: str, steps: List[SimulationStep], agent_twin_map: Dict[str, str]
    ) -> int:
        """批量从仿真结果中收集所有经验.

        Args:
            session_id: 会话ID
            steps: 仿真步骤列表
            agent_twin_map: twin_id → source_agent_id 映射

        Returns:
            收集的经验总数
        """
        count = 0
        for step in steps:
            for twin_id in step.agent_actions:
                agent_id = agent_twin_map.get(twin_id, twin_id)
                self.collect_experience_from_step(session_id, step, agent_id, twin_id)
                count += 1
        return count

    # ── 反思模块 ────────────────────────────────────────────────

    def reflect(self, agent_id: str, window_size: int = 10) -> Optional[ReflectionEntry]:
        """触发智能体反思 — 从最近经验中提炼规律.

        分析最近 window_size 条经验，寻找模式并生成新的启发式规则。
        """
        memory = self._memory_pool.get_or_create(agent_id)
        recent_exp = memory._short_term[-window_size:]

        if len(recent_exp) < 3:
            return None  # 经验不足以反思

        # 分析模式
        success_actions = [e.action_taken for e in recent_exp if e.outcome == ExperienceOutcome.SUCCESS]
        failure_actions = [e.action_taken for e in recent_exp if e.outcome == ExperienceOutcome.FAILURE]
        avg_reward = sum(e.reward for e in recent_exp) / len(recent_exp)

        # 生成反思
        analysis_parts = []
        if success_actions:
            analysis_parts.append(f"成功动作模式: {len(success_actions)}/{len(recent_exp)}")
        if failure_actions:
            analysis_parts.append(f"失败动作模式: {len(failure_actions)}/{len(recent_exp)}")
        analysis_parts.append(f"平均奖励: {avg_reward:.3f}")

        # 提取启发式
        heuristic = ""
        if len(success_actions) > len(failure_actions):
            heuristic = f"偏好执行类动作 (成功率={len(success_actions)/len(recent_exp):.0%})"
        elif failure_actions:
            heuristic = f"避免空闲等待 (失败占比={len(failure_actions)/len(recent_exp):.0%})"

        reflection = ReflectionEntry(
            agent_id=agent_id,
            trigger=f"经验窗口分析 (n={len(recent_exp)})",
            analysis="; ".join(analysis_parts),
            conclusion=f"当前策略效能: {'高' if avg_reward > 0.15 else '低'}",
            new_heuristic=heuristic,
            source_experiences=[e.experience_id for e in recent_exp[:5]],
            confidence=min(0.9, avg_reward * 2 + 0.3),
        )

        memory.add_reflection(reflection)
        self._total_reflections += 1
        logger.info(f"🪞 {agent_id} 反思: {reflection.conclusion}")
        return reflection

    def reflect_all(self, agent_ids: List[str]) -> List[ReflectionEntry]:
        """批量触发所有智能体反思."""
        reflections = []
        for agent_id in agent_ids:
            r = self.reflect(agent_id)
            if r:
                reflections.append(r)
        return reflections

    # ── SOP 提取 ────────────────────────────────────────────────

    def extract_sop(
        self, session_id: str, steps: List[SimulationStep], agent_twin_map: Dict[str, str]
    ) -> Optional[CollaborationSOP]:
        """从仿真结果中提取协作 SOP.

        分析高奖励步骤序列，提取可复用的协作模式。
        """
        if not steps:
            return None

        # 筛选高奖励步骤
        high_reward_steps = [s for s in steps if s.global_reward > 0.15]
        if len(high_reward_steps) < 3:
            return None

        # 提取协作模式
        role_actions: Dict[str, List[str]] = {}
        comm_patterns: List[Dict[str, Any]] = []

        for step in high_reward_steps:
            for twin_id, action in step.agent_actions.items():
                # [fix] 防御: action 可能是 None 或非 dict
                if not isinstance(action, dict):
                    continue
                agent_id = agent_twin_map.get(twin_id, twin_id)
                if agent_id not in role_actions:
                    role_actions[agent_id] = []
                role_actions[agent_id].append(action.get("action", "unknown"))

            for msg in step.messages:
                comm_patterns.append({
                    "from_role": agent_twin_map.get(msg["from"], msg["from"]),
                    "to": msg.get("to", "broadcast"),
                    "type": msg.get("type", "info"),
                })

        # 构建 SOP
        sop_steps = []
        for agent_id, actions in role_actions.items():
            # 取最频繁的动作模式
            from collections import Counter
            action_counts = Counter(actions)
            dominant_action = action_counts.most_common(1)[0][0] if action_counts else "idle"
            sop_steps.append({
                "agent": agent_id,
                "action": dominant_action,
                "frequency": action_counts.get(dominant_action, 0),
            })

        avg_reward = sum(s.global_reward for s in high_reward_steps) / len(high_reward_steps)

        sop = CollaborationSOP(
            name=f"SOP-{session_id[:6]}-{len(self._sop_library)}",
            description=f"从 {len(high_reward_steps)} 个高奖励步骤中提取的协作模式",
            agent_roles=list(role_actions.keys()),
            steps=sop_steps,
            communication_protocol={
                "patterns": comm_patterns[:10],
                "total_messages": len(comm_patterns),
            },
            success_rate=len(high_reward_steps) / len(steps),
            avg_reward=avg_reward,
            validated_count=1,
            status=StrategyStatus.CANDIDATE,
        )

        self._sop_library.append(sop)
        self._total_sops += 1
        logger.info(f"📋 SOP 提取: {sop.name} reward={avg_reward:.3f}")
        return sop

    # ── 优化循环 ────────────────────────────────────────────────

    async def run_evolution_cycle(
        self,
        session_id: str,
        steps: List[SimulationStep],
        agent_twin_map: Dict[str, str],
    ) -> Dict[str, Any]:
        """执行完整的 Experience→Reflect→Optimize 循环.

        Returns:
            循环结果摘要
        """
        # 1. 收集经验
        exp_count = self.collect_experiences_from_simulation(session_id, steps, agent_twin_map)

        # 2. 反思
        agent_ids = list(set(agent_twin_map.values()))
        reflections = self.reflect_all(agent_ids)

        # 3. 提取 SOP
        sop = self.extract_sop(session_id, steps, agent_twin_map)

        # 4. 固化记忆
        self._memory_pool.consolidate_all()

        return {
            "experiences_collected": exp_count,
            "reflections_generated": len(reflections),
            "sop_extracted": sop.name if sop else None,
            "sop_avg_reward": sop.avg_reward if sop else 0,
        }

    # ── 查询 ────────────────────────────────────────────────────

    def get_best_sop(self) -> Optional[CollaborationSOP]:
        """获取当前最优 SOP."""
        if not self._sop_library:
            return None
        return max(self._sop_library, key=lambda s: s.avg_reward)

    def get_sop_library(self) -> List[Dict[str, Any]]:
        """获取 SOP 库列表."""
        return [
            {
                "sop_id": s.sop_id,
                "name": s.name,
                "success_rate": s.success_rate,
                "avg_reward": s.avg_reward,
                "status": s.status.value,
                "agent_roles": s.agent_roles,
            }
            for s in self._sop_library
        ]

    def get_stats(self) -> Dict[str, Any]:
        """获取引擎统计."""
        return {
            "total_experiences": self._total_experiences,
            "total_reflections": self._total_reflections,
            "total_sops": self._total_sops,
            "best_sop_reward": self.get_best_sop().avg_reward if self.get_best_sop() else 0,
        }
