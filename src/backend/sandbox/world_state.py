# -*- coding: utf-8 -*-
"""World State Manager — MADTwin 环境语义映射层.

负责完成数字世界的"二次映射"：
- 捕获智能体团队的实时状态
- 建模工作流拓扑与协作边界
- 生成可用于沙箱仿真的 WorldStateSnapshot
"""

from __future__ import annotations

import copy
import logging
from typing import Any, Dict, List, Optional

from .models import (
    EnvironmentConstraint,
    ResourceState,
    WorkflowEdge,
    WorldStateSnapshot,
)

logger = logging.getLogger(__name__)


class WorldStateManager:
    """环境语义映射管理器 — 维护数字世界的实时语义模型."""

    def __init__(self):
        # 当前活跃的世界状态
        self._agent_states: Dict[str, Dict[str, Any]] = {}
        self._resources: List[ResourceState] = []
        self._workflow_edges: List[WorkflowEdge] = []
        self._constraints: List[EnvironmentConstraint] = []
        self._pending_tasks: List[Dict[str, Any]] = []
        self._global_metrics: Dict[str, float] = {}
        # 快照历史（LRU，最多50个）
        self._snapshot_history: List[WorldStateSnapshot] = []
        self._max_snapshots = 50

    # ── 状态注入（从真实系统同步） ──────────────────────────────

    def sync_agent_state(self, agent_id: str, state: Dict[str, Any]) -> None:
        """同步单个智能体状态."""
        self._agent_states[agent_id] = state

    def sync_agents_from_team(self, team_config: Dict[str, Any], *, replace: bool = True) -> None:
        """从团队配置批量同步智能体状态.

        replace=True（默认）: 同步即全量镜像——本次团队就是孪生世界的全部成员。
        旧行为是逐个 update 从不清空，多次切换团队后世界累积出跨团队的幽灵成员，
        导致演练 twins/协作图数量与所选团队对不上（如 7 人团队出现 40 节点协作图）。
        """
        agents = team_config.get("agents", [])
        if replace and agents:
            self._agent_states = {}
        for agent in agents:
            agent_id = agent.get("id", agent.get("name", "unknown"))
            self._agent_states[agent_id] = {
                "role": agent.get("role", "general"),
                "state": agent.get("state", "idle"),
                "skills": agent.get("skills", []),
                "tools": agent.get("tools", []),
                "channels": agent.get("channels", []),
                "current_task": agent.get("current_task"),
            }

    def sync_resources(self, resources: List[Dict[str, Any]]) -> None:
        """同步资源状态."""
        self._resources = [
            ResourceState(
                resource_id=r.get("id", ""),
                resource_type=r.get("type", "general"),
                capacity=r.get("capacity", 1.0),
                utilization=r.get("utilization", 0.0),
                available=r.get("available", True),
                metadata=r.get("metadata", {}),
            )
            for r in resources
        ]

    def sync_workflow(self, edges: List[Dict[str, Any]]) -> None:
        """同步工作流拓扑."""
        self._workflow_edges = [
            WorkflowEdge(
                source_agent_id=e.get("source", ""),
                target_agent_id=e.get("target", ""),
                channel=e.get("channel", ""),
                message_type=e.get("message_type", "request"),
                weight=e.get("weight", 1.0),
            )
            for e in edges
        ]

    def sync_constraints(self, constraints: List[Dict[str, Any]]) -> None:
        """同步环境约束."""
        self._constraints = [
            EnvironmentConstraint(
                name=c.get("name", ""),
                constraint_type=c.get("type", "permission"),
                target_agents=c.get("target_agents", []),
                rule=c.get("rule", ""),
                active=c.get("active", True),
            )
            for c in constraints
        ]

    def sync_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        """同步待处理任务."""
        self._pending_tasks = tasks

    def update_metrics(self, metrics: Dict[str, float]) -> None:
        """更新全局指标."""
        self._global_metrics.update(metrics)

    # ── v4 C-4.1: 房间状态机（场景化后房间即业务阶段） ──────────

    def set_room_stages(self, room_stages: Dict[str, int]) -> None:
        """设置房间阶段映射 {room_id: stage}，由场景编译产出."""
        self._room_stages = dict(room_stages or {})

    def validate_move(self, from_room: str, to_room: str) -> Dict[str, Any]:
        """校验 Agent 房间迁移是否符合业务阶段顺序.

        规则: 只允许迁移到相邻阶段（前进一步/回退一步）或同阶段房间。
        未设置阶段映射时全部放行（兼容无场景模式）。
        """
        stages = getattr(self, "_room_stages", None)
        if not stages:
            return {"allowed": True, "reason": ""}
        if to_room not in stages:
            return {"allowed": False, "reason": f"目标房间 {to_room} 不在当前场景中"}
        if not from_room or from_room not in stages:
            return {"allowed": True, "reason": ""}  # 初次进入任意房间
        delta = stages[to_room] - stages[from_room]
        if abs(delta) <= 1:
            return {"allowed": True, "reason": ""}
        return {
            "allowed": False,
            "reason": f"违反业务阶段顺序: {from_room}(阶段{stages[from_room]}) → "
                      f"{to_room}(阶段{stages[to_room]})，只能迁移到相邻阶段",
        }

    # ── 快照生成 ────────────────────────────────────────────────

    def take_snapshot(self, incremental: bool = False) -> WorldStateSnapshot:
        """生成当前世界状态的完整快照（二次映射）.

        Args:
            incremental: 是否生成增量快照（仅记录变化部分）

        Returns:
            WorldStateSnapshot 实例
        """
        parent_id = None
        if incremental and self._snapshot_history:
            parent_id = self._snapshot_history[-1].snapshot_id

        snapshot = WorldStateSnapshot(
            agent_states=copy.deepcopy(self._agent_states),
            resources=copy.deepcopy(self._resources),
            workflow_edges=copy.deepcopy(self._workflow_edges),
            constraints=copy.deepcopy(self._constraints),
            pending_tasks=copy.deepcopy(self._pending_tasks),
            global_metrics=copy.deepcopy(self._global_metrics),
            parent_snapshot_id=parent_id,
            delta_only=incremental,
        )

        # LRU 管理
        self._snapshot_history.append(snapshot)
        if len(self._snapshot_history) > self._max_snapshots:
            self._snapshot_history.pop(0)

        logger.info(
            f"📸 世界快照生成: {snapshot.snapshot_id[:8]}... "
            f"agents={len(snapshot.agent_states)} "
            f"tasks={len(snapshot.pending_tasks)}"
        )
        return snapshot

    def get_snapshot(self, snapshot_id: str) -> Optional[WorldStateSnapshot]:
        """按ID获取历史快照."""
        for s in self._snapshot_history:
            if s.snapshot_id == snapshot_id:
                return s
        return None

    def get_latest_snapshot(self) -> Optional[WorldStateSnapshot]:
        """获取最新快照."""
        return self._snapshot_history[-1] if self._snapshot_history else None

    # ── 状态查询 ────────────────────────────────────────────────

    def get_agent_ids(self) -> List[str]:
        """获取所有已注册智能体ID."""
        return list(self._agent_states.keys())

    def get_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取单个智能体状态."""
        return self._agent_states.get(agent_id)

    def get_workflow_graph(self) -> Dict[str, List[str]]:
        """获取工作流邻接表."""
        graph: Dict[str, List[str]] = {}
        for edge in self._workflow_edges:
            if edge.source_agent_id not in graph:
                graph[edge.source_agent_id] = []
            graph[edge.source_agent_id].append(edge.target_agent_id)
        return graph

    def get_resource_utilization(self) -> float:
        """获取整体资源利用率."""
        if not self._resources:
            return 0.0
        total = sum(r.utilization for r in self._resources)
        return total / len(self._resources)

    def to_dict(self) -> Dict[str, Any]:
        """序列化当前状态为字典."""
        return {
            "agent_count": len(self._agent_states),
            "resource_count": len(self._resources),
            "workflow_edges": len(self._workflow_edges),
            # M2-4: 透出工作流边明细（源→目标 + 传递语义），供办公室 3D 按边顺序渲染递交
            "workflow_edges_detail": [
                {
                    "source": e.source_agent_id, "target": e.target_agent_id,
                    "channel": e.channel, "message_type": e.message_type,
                    "weight": e.weight,
                }
                for e in self._workflow_edges
            ],
            # M2-5: 透出房间业务阶段映射，供办公室 3D 按阶段分区
            "room_stages": dict(getattr(self, "_room_stages", {}) or {}),
            # M3-1: 透出工作流图节点（角色·技能·模型档），供办公室渲染显式工作流图
            "workflow_nodes": [
                {
                    "id": aid,
                    "role": s.get("role", ""),
                    "skills": list(s.get("skills", []) or []),
                    "model_tier": s.get("model_tier", ""),
                }
                for aid, s in self._agent_states.items()
            ],
            "constraints": len(self._constraints),
            "pending_tasks": len(self._pending_tasks),
            "global_metrics": self._global_metrics,
            "snapshot_count": len(self._snapshot_history),
        }
