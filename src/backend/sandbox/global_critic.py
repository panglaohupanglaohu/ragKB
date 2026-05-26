# -*- coding: utf-8 -*-
"""Global Critic — DT-MADDPG 全局评论家.

利用仿真辅助评论家机制，将沙箱仿真结果作为"中心化评论家"的输入。
评估多智能体群体在沙箱中的表现，指导协同优化。

评估维度:
- 任务完成率 (task_completion)
- 通信效率 (communication_efficiency)
- 资源利用率 (resource_utilization)
- 冲突避免度 (conflict_avoidance)
- 策略收敛速度 (convergence_speed)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .models import (
    AgentTwin,
    CriticEvaluation,
    SandboxSession,
    SimulationStep,
)

logger = logging.getLogger(__name__)


class GlobalCritic:
    """全局评论家 — DT-MADDPG 中心化评估器.

    基于仿真结果进行全局评分，输出改进建议。
    隐私保护：评论家只接收脱敏的统计数据，不访问智能体内部状态。
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        # 评估权重（可调）
        self._weights = weights or {
            "task_completion": 0.30,
            "communication_efficiency": 0.20,
            "resource_utilization": 0.15,
            "conflict_avoidance": 0.20,
            "convergence_speed": 0.15,
        }
        # 评估历史
        self._eval_history: List[CriticEvaluation] = []

    # ── 核心评估 ────────────────────────────────────────────────

    def evaluate(self, session: SandboxSession) -> CriticEvaluation:
        """对一次完整仿真进行全局评估.

        Args:
            session: 已完成仿真的沙箱会话

        Returns:
            CriticEvaluation 包含各维度得分与改进建议
        """
        steps = session.steps
        twins = session.twins

        # 各维度评分
        task_score = self._eval_task_completion(steps, twins)
        comm_score = self._eval_communication_efficiency(steps, twins)
        resource_score = self._eval_resource_utilization(steps, twins)
        conflict_score = self._eval_conflict_avoidance(steps, twins)
        convergence_score = self._eval_convergence_speed(steps)

        # 加权综合
        global_score = (
            task_score * self._weights["task_completion"]
            + comm_score * self._weights["communication_efficiency"]
            + resource_score * self._weights["resource_utilization"]
            + conflict_score * self._weights["conflict_avoidance"]
            + convergence_score * self._weights["convergence_speed"]
        )

        # 各智能体得分
        agent_scores = self._eval_individual_agents(steps, twins)

        # 生成建议
        recommendations = self._generate_recommendations(
            task_score, comm_score, resource_score, conflict_score, convergence_score
        )

        evaluation = CriticEvaluation(
            session_id=session.session_id,
            task_completion=task_score,
            communication_efficiency=comm_score,
            resource_utilization=resource_score,
            conflict_avoidance=conflict_score,
            convergence_speed=convergence_score,
            global_score=global_score,
            agent_scores=agent_scores,
            recommendations=recommendations,
        )

        self._eval_history.append(evaluation)
        logger.info(
            f"🎯 全局评估: score={global_score:.3f} "
            f"task={task_score:.2f} comm={comm_score:.2f} "
            f"resource={resource_score:.2f} conflict={conflict_score:.2f}"
        )

        return evaluation

    # ── 各维度评分实现 ──────────────────────────────────────────

    def _eval_task_completion(self, steps: List[SimulationStep], twins: List[AgentTwin]) -> float:
        """评估任务完成率."""
        if not steps:
            return 0.0

        # 统计有效工作步骤比例
        working_steps = 0
        total_agent_steps = 0

        for step in steps:
            for action in step.agent_actions.values():
                total_agent_steps += 1
                if action.get("action") in ("work_on_task", "claim_task"):
                    working_steps += 1

        if total_agent_steps == 0:
            return 0.0

        # 结合奖励信号
        avg_reward = sum(s.global_reward for s in steps) / len(steps)
        work_ratio = working_steps / total_agent_steps

        return min(1.0, work_ratio * 0.6 + avg_reward * 2.0 * 0.4)

    def _eval_communication_efficiency(
        self, steps: List[SimulationStep], twins: List[AgentTwin]
    ) -> float:
        """评估通信效率.

        高效通信 = 有效信息/总消息量 高
        """
        total_messages = 0
        effective_messages = 0  # 导致后续积极行为的消息

        for i, step in enumerate(steps):
            total_messages += len(step.messages)
            # 如果消息后续步骤奖励提升，认为是有效通信
            if i < len(steps) - 1 and step.messages:
                if steps[i + 1].global_reward > step.global_reward:
                    effective_messages += len(step.messages)

        if total_messages == 0:
            return 0.5  # 无通信，中性评分

        # 通信不能太多也不能太少
        msg_per_step = total_messages / max(len(steps), 1)
        twins_count = len(twins)

        # 理想通信量: 每步每对智能体约0.5条
        ideal_msg_rate = twins_count * 0.5
        rate_penalty = 1.0 - min(1.0, abs(msg_per_step - ideal_msg_rate) / ideal_msg_rate) if ideal_msg_rate > 0 else 0.5

        efficiency = effective_messages / total_messages if total_messages > 0 else 0.0

        return min(1.0, efficiency * 0.6 + rate_penalty * 0.4)

    def _eval_resource_utilization(
        self, steps: List[SimulationStep], twins: List[AgentTwin]
    ) -> float:
        """评估资源利用率.

        评估智能体是否充分利用了可用能力。
        """
        if not twins:
            return 0.0

        # 智能体利用率 = 非空闲步骤/总步骤
        total_steps = len(steps) * len(twins)
        active_steps = 0

        for step in steps:
            for action in step.agent_actions.values():
                if action.get("action") != "idle":
                    active_steps += 1

        if total_steps == 0:
            return 0.0

        utilization = active_steps / total_steps
        # 既不能太低（浪费）也不能100%（无弹性）
        if utilization > 0.95:
            return 0.9  # 过度利用有风险
        return min(1.0, utilization * 1.2)

    def _eval_conflict_avoidance(
        self, steps: List[SimulationStep], twins: List[AgentTwin]
    ) -> float:
        """评估冲突避免度.

        冲突: 多个智能体同时认领同一任务，或行动相互矛盾。
        """
        conflict_count = 0
        total_steps = len(steps)

        for step in steps:
            # 检测同一步骤内多个 claim_task 指向同一任务
            claimed_tasks: Dict[str, int] = {}
            for action in step.agent_actions.values():
                if action.get("action") == "claim_task":
                    task = action.get("task", "")
                    claimed_tasks[task] = claimed_tasks.get(task, 0) + 1

            # 超过1个认领同一任务 = 冲突
            for count in claimed_tasks.values():
                if count > 1:
                    conflict_count += 1

        if total_steps == 0:
            return 1.0

        conflict_rate = conflict_count / total_steps
        return max(0.0, 1.0 - conflict_rate * 2.0)

    def _eval_convergence_speed(self, steps: List[SimulationStep]) -> float:
        """评估策略收敛速度.

        越早达到高奖励 = 收敛越快。
        """
        if not steps:
            return 0.0

        # 找到第一次达到"高奖励"的步骤
        threshold = 0.2
        convergence_step = len(steps)  # 默认未收敛

        for i, step in enumerate(steps):
            if step.global_reward >= threshold:
                # 连续3步高于阈值才算收敛
                if i + 2 < len(steps):
                    if all(steps[i + j].global_reward >= threshold for j in range(3)):
                        convergence_step = i
                        break

        # 归一化: 越早收敛得分越高
        max_steps = len(steps)
        if convergence_step >= max_steps:
            return 0.1  # 未收敛

        return max(0.1, 1.0 - convergence_step / max_steps)

    # ── 个体评估 ────────────────────────────────────────────────

    def _eval_individual_agents(
        self, steps: List[SimulationStep], twins: List[AgentTwin]
    ) -> Dict[str, float]:
        """评估各智能体个体表现."""
        scores: Dict[str, float] = {}

        for twin in twins:
            # 基于累计奖励和动作数
            if twin.actions_taken == 0:
                scores[twin.twin_id] = 0.0
            else:
                avg_reward = twin.rewards_collected / twin.actions_taken
                # 归一化到 0~1
                scores[twin.twin_id] = min(1.0, max(0.0, avg_reward * 3.0))

        return scores

    # ── 建议生成 ────────────────────────────────────────────────

    def _generate_recommendations(
        self,
        task: float,
        comm: float,
        resource: float,
        conflict: float,
        convergence: float,
    ) -> List[str]:
        """基于评分生成改进建议."""
        recommendations = []

        if task < 0.5:
            recommendations.append("任务完成率低：建议优化任务分配策略，减少智能体空闲时间")
        if comm < 0.4:
            recommendations.append("通信效率低：建议减少冗余消息，增加结构化信息传递")
        if resource < 0.5:
            recommendations.append("资源利用不足：建议增加任务并行度或减少智能体数量")
        if conflict < 0.6:
            recommendations.append("冲突频发：建议引入任务锁定机制或优先级仲裁")
        if convergence < 0.3:
            recommendations.append("收敛缓慢：建议增加智能体间的协调通信频率")

        if not recommendations:
            recommendations.append("整体表现良好，可考虑提升仿真复杂度以进一步验证")

        return recommendations

    # ── 查询 ────────────────────────────────────────────────────

    def get_eval_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取评估历史."""
        return [
            {
                "eval_id": e.eval_id,
                "session_id": e.session_id,
                "global_score": e.global_score,
                "task_completion": e.task_completion,
                "communication_efficiency": e.communication_efficiency,
                "convergence_speed": e.convergence_speed,
                "timestamp": e.timestamp,
            }
            for e in self._eval_history[-limit:]
        ]

    def get_stats(self) -> Dict[str, Any]:
        """获取评论家统计."""
        if not self._eval_history:
            return {"total_evaluations": 0, "avg_score": 0}

        scores = [e.global_score for e in self._eval_history]
        return {
            "total_evaluations": len(self._eval_history),
            "avg_score": sum(scores) / len(scores),
            "max_score": max(scores),
            "min_score": min(scores),
        }
