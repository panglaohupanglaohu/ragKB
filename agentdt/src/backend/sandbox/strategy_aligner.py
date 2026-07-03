# -*- coding: utf-8 -*-
"""Strategy Aligner — 集体智慧对齐与协同优化.

在沙箱仿真完成后:
1. 使用全局评论家评估结果
2. 对齐多智能体间的通信与分工协议
3. 确保整体奖励最大化
4. 输出可注入的最优 SOP

解决多个智能体独立试错时可能产生的"协同悖论"。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .models import (
    AlignmentProtocol,
    CollaborationSOP,
    CriticEvaluation,
    SandboxSession,
    SandboxStatus,
    StrategyStatus,
)
from .global_critic import GlobalCritic
from .zero_exp_engine import ZeroExpEngine

logger = logging.getLogger(__name__)


class StrategyAligner:
    """策略对齐器 — 确保多智能体协同一致性.

    流程:
    1. 全局评论家评估仿真表现
    2. 识别协同冲突与低效模式
    3. 生成对齐协议（通信规则、角色分配、冲突解决）
    4. 验证对齐后的策略改进
    """

    def __init__(self, critic: GlobalCritic, zero_exp: ZeroExpEngine):
        self._critic = critic
        self._zero_exp = zero_exp
        # 对齐协议库
        self._protocols: List[AlignmentProtocol] = []
        # 对齐统计
        self._alignment_count: int = 0

    # ── 核心对齐流程 ────────────────────────────────────────────

    async def align_session(self, session: SandboxSession) -> Dict[str, Any]:
        """对一次仿真会话执行完整的对齐流程.

        Returns:
            对齐结果摘要
        """
        # 1. 全局评估
        evaluation = self._critic.evaluate(session)
        session.evaluation = evaluation

        # 2. 演化循环（收集经验 + 反思 + 提取 SOP）
        agent_twin_map = {t.twin_id: t.source_agent_id for t in session.twins}
        evolution_result = await self._zero_exp.run_evolution_cycle(
            session.session_id, session.steps, agent_twin_map
        )

        # 3. 获取最优 SOP
        best_sop = self._zero_exp.get_best_sop()
        if best_sop and evaluation.global_score > 0.4:
            best_sop.status = StrategyStatus.VALIDATED
            session.best_sop = best_sop

        # 4. 生成对齐协议
        protocol = self._generate_alignment_protocol(session, evaluation)
        if protocol:
            self._protocols.append(protocol)

        # 5. 更新会话状态
        session.status = SandboxStatus.COMPLETED
        self._alignment_count += 1

        result = {
            "evaluation": {
                "global_score": evaluation.global_score,
                "task_completion": evaluation.task_completion,
                "communication_efficiency": evaluation.communication_efficiency,
                "resource_utilization": evaluation.resource_utilization,
                "conflict_avoidance": evaluation.conflict_avoidance,
                "convergence_speed": evaluation.convergence_speed,
                "recommendations": evaluation.recommendations,
            },
            "evolution": evolution_result,
            "best_sop": {
                "name": best_sop.name,
                "avg_reward": best_sop.avg_reward,
                "status": best_sop.status.value,
            } if best_sop else None,
            "protocol": {
                "name": protocol.name,
                "conflict_resolution": protocol.conflict_resolution,
            } if protocol else None,
            "session_status": session.status.value,
        }

        logger.info(
            f"🔄 对齐完成: session={session.session_id[:8]} "
            f"score={evaluation.global_score:.3f} "
            f"sop={'✓' if best_sop else '✗'}"
        )
        return result

    # ── 协议生成 ────────────────────────────────────────────────

    def _generate_alignment_protocol(
        self, session: SandboxSession, evaluation: CriticEvaluation
    ) -> Optional[AlignmentProtocol]:
        """基于评估结果生成对齐协议."""
        if not session.twins:
            return None

        # 角色分配
        role_assignments: Dict[str, str] = {}
        for twin in session.twins:
            role_assignments[twin.source_agent_id] = twin.role

        # 通信规则（基于评估反馈）
        comm_rules: List[Dict[str, Any]] = []
        if evaluation.communication_efficiency < 0.5:
            comm_rules.append({
                "rule": "reduce_broadcast",
                "description": "减少广播消息，改为定向通信",
                "target": "all",
            })
        if evaluation.conflict_avoidance < 0.6:
            comm_rules.append({
                "rule": "claim_lock",
                "description": "任务认领前先广播意图，等待确认后再执行",
                "target": "all",
            })
        if evaluation.convergence_speed < 0.4:
            comm_rules.append({
                "rule": "progress_broadcast",
                "description": "每完成子任务后广播进度，帮助全局感知",
                "target": "all",
            })

        # 冲突解决策略
        if evaluation.conflict_avoidance < 0.5:
            conflict_resolution = "priority"  # 优先级仲裁
        elif len(session.twins) > 4:
            conflict_resolution = "delegation"  # 委托协调者
        else:
            conflict_resolution = "voting"  # 投票决议

        # 适用场景
        scenarios = []
        if session.trigger_drift:
            scenarios.append(session.trigger_drift.drift_type.value)
        if session.trigger_description:
            scenarios.append(session.trigger_description)

        protocol = AlignmentProtocol(
            name=f"Protocol-{session.session_id[:6]}",
            role_assignments=role_assignments,
            communication_rules=comm_rules,
            conflict_resolution=conflict_resolution,
            applicable_scenarios=scenarios,
        )

        return protocol

    # ── 协同悖论检测 ────────────────────────────────────────────

    def detect_paradox(self, session: SandboxSession) -> List[Dict[str, Any]]:
        """检测协同悖论 — 个体最优 ≠ 集体最优 的情况.

        当某智能体的个体奖励很高，但其行为降低了全局奖励时，
        存在协同悖论。
        """
        paradoxes = []
        if not session.evaluation:
            return paradoxes

        eval_result = session.evaluation
        global_score = eval_result.global_score

        for twin_id, agent_score in eval_result.agent_scores.items():
            # 个体得分远高于全局得分 = 潜在悖论
            if agent_score > global_score * 1.5 and global_score < 0.5:
                twin = next((t for t in session.twins if t.twin_id == twin_id), None)
                if twin:
                    paradoxes.append({
                        "agent_id": twin.source_agent_id,
                        "twin_id": twin_id,
                        "agent_score": agent_score,
                        "global_score": global_score,
                        "gap": agent_score - global_score,
                        "diagnosis": "个体行为可能损害集体效率",
                    })

        return paradoxes

    # ── 查询 ────────────────────────────────────────────────────

    def get_protocols(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取对齐协议列表."""
        return [
            {
                "protocol_id": p.protocol_id,
                "name": p.name,
                "conflict_resolution": p.conflict_resolution,
                "rules_count": len(p.communication_rules),
                "applicable_scenarios": p.applicable_scenarios,
            }
            for p in self._protocols[-limit:]
        ]

    def get_stats(self) -> Dict[str, Any]:
        """获取对齐器统计."""
        return {
            "total_alignments": self._alignment_count,
            "protocols_generated": len(self._protocols),
            "critic_stats": self._critic.get_stats(),
            "zero_exp_stats": self._zero_exp.get_stats(),
        }
