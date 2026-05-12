# -*- coding: utf-8 -*-
"""操作事件 & 情境切片数据模型 — OperationEvent & ContextSlice.

设计目标:
  - OperationEvent: 记录每次系统操作 (Agent 调用/工具使用/任务执行),
    仅追加 (append-only), 禁止修改与删除
  - ContextSlice: 记录操作发生时的上下文快照 (会话状态/环境配置/Agent 配置),
    与 OperationEvent 建立追溯关联 (1:N), 保证审计完整
  - 不可变保证: OperationEvent 无 update/delete 方法, 只在创建时生成 hash,
    提供 verify_integrity() 检测事后篡改
  - 追溯链: ContextSlice → OperationEvent (via operation_id),
    OperationEvent 之间可选 parent_operation_id 形成因果链

对标 DDD Domain Events + Event Sourcing 模式.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════


class OperationType(str, Enum):
    """操作类型枚举 — 覆盖所有系统操作类别."""
    # Agent 生命周期
    AGENT_CREATED = "agent_created"
    AGENT_UPDATED = "agent_updated"
    AGENT_DELETED = "agent_deleted"
    AGENT_STATE_CHANGE = "agent_state_change"

    # 工具调用
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"

    # 任务执行
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

    # 团队管理
    TEAM_CREATED = "team_created"
    TEAM_UPDATED = "team_updated"
    TEAM_DELETED = "team_deleted"

    # 演进周期
    EVOLUTION_AUDIT = "evolution_audit"
    EVOLUTION_DISPATCH = "evolution_dispatch"
    EVOLUTION_VERIFY = "evolution_verify"
    EVOLUTION_CLOSE = "evolution_close"

    # 会话操作
    SESSION_CREATED = "session_created"
    SESSION_UPDATED = "session_updated"

    # 门禁 / 审核
    GATE_EVALUATION = "gate_evaluation"
    REVIEW_ACTION = "review_action"

    # 技能操作
    SKILL_EXTRACTED = "skill_extracted"
    SKILL_VERIFIED = "skill_verified"

    # 其他
    SYSTEM_EVENT = "system_event"
    UNKNOWN = "unknown"


class ContextType(str, Enum):
    """情境切片类型 — 记录快照的类别."""
    SESSION_STATE = "session_state"         # 会话状态快照
    AGENT_CONFIG = "agent_config"           # Agent 配置快照
    TEAM_CONFIG = "team_config"             # 团队配置快照
    ENVIRONMENT = "environment"             # 环境变量/配置快照
    TOOL_CALL_DETAIL = "tool_call_detail"   # 工具调用详情快照
    SYSTEM_STATE = "system_state"           # 系统整体状态快照
    USER_REQUEST = "user_request"           # 用户请求快照
    CUSTOM = "custom"                       # 自定义快照


# ═══════════════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class OperationEvent:
    """操作事件 — 不可变 (frozen dataclass), append-only.

    记录系统中每一次有意义的操作。创建后不可修改。
    operation_hash 用于事后完整性校验。
    parent_operation_id 形成操作因果链。
    """
    operation_id: str
    operation_type: OperationType
    agent_id: str
    team_id: str
    timestamp: str
    # 操作内容
    summary: str                           # 人类可读摘要
    detail: Dict[str, Any]                 # 操作详细数据 (序列化为 JSON)
    # 调用链
    parent_operation_id: Optional[str] = None    # 父操作 ID (因果链)
    session_id: Optional[str] = None             # 所属会话 ID
    task_id: Optional[str] = None                # 所属任务 ID
    # 不可变验证
    operation_hash: str = ""                # 内容哈希 (创建时自动计算)
    schema_version: int = 1                 # schema 版本 (未来兼容)
    # 服务端元数据 (不可变)
    idempotency_key: Optional[str] = None   # 幂等键 (相同 key 不重复写入)

    def __post_init__(self):
        """冻结后计算哈希."""
        if not self.operation_hash:
            object.__setattr__(
                self, "operation_hash", self._compute_hash()
            )

    def _compute_hash(self) -> str:
        """计算操作内容的 SHA256 哈希."""
        payload = {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type.value,
            "agent_id": self.agent_id,
            "team_id": self.team_id,
            "timestamp": self.timestamp,
            "summary": self.summary,
            "detail": self.detail,
            "parent_operation_id": self.parent_operation_id,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "schema_version": self.schema_version,
        }
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def verify_integrity(self) -> bool:
        """验证事件未被篡改."""
        return self.operation_hash == self._compute_hash()

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典."""
        return {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type.value,
            "agent_id": self.agent_id,
            "team_id": self.team_id,
            "timestamp": self.timestamp,
            "summary": self.summary,
            "detail": self.detail,
            "parent_operation_id": self.parent_operation_id,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "operation_hash": self.operation_hash,
            "schema_version": self.schema_version,
            "idempotency_key": self.idempotency_key,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OperationEvent":
        """从字典反序列化 (恢复后自动验证哈希)."""
        op_type = data.get("operation_type", "unknown")
        try:
            op_type = OperationType(op_type)
        except ValueError:
            op_type = OperationType.UNKNOWN

        return cls(
            operation_id=data.get("operation_id", ""),
            operation_type=op_type,
            agent_id=data.get("agent_id", ""),
            team_id=data.get("team_id", ""),
            timestamp=data.get("timestamp", ""),
            summary=data.get("summary", ""),
            detail=data.get("detail", {}),
            parent_operation_id=data.get("parent_operation_id"),
            session_id=data.get("session_id"),
            task_id=data.get("task_id"),
            operation_hash=data.get("operation_hash", ""),
            schema_version=data.get("schema_version", 1),
            idempotency_key=data.get("idempotency_key"),
        )

    @classmethod
    def create(
        cls,
        operation_type: OperationType,
        agent_id: str = "system",
        team_id: str = "default",
        summary: str = "",
        detail: Optional[Dict[str, Any]] = None,
        parent_operation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> "OperationEvent":
        """工厂方法 — 创建带自动 ID 和时间戳的操作事件."""
        return cls(
            operation_id=f"OP-{uuid.uuid4().hex[:8]}",
            operation_type=operation_type,
            agent_id=agent_id,
            team_id=team_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            summary=summary,
            detail=detail or {},
            parent_operation_id=parent_operation_id,
            session_id=session_id,
            task_id=task_id,
            idempotency_key=idempotency_key,
        )


@dataclass(frozen=True)
class ContextSlice:
    """情境切片 — 记录操作发生时的上下文快照，不可变。

    与 OperationEvent 通过 operation_id 建立 N:1 追溯关联。
    一个操作可以关联多个情境切片 (如同时记录会话状态和环境配置)。
    context_hash 用于事后完整性校验。
    """
    slice_id: str
    operation_id: str                      # 关联的操作事件 ID
    context_type: ContextType
    timestamp: str
    # 快照内容
    payload: Dict[str, Any]                # 上下文快照数据
    summary: str = ""                      # 快照摘要
    # 不可变验证
    context_hash: str = ""                 # 内容哈希 (创建时自动计算)
    schema_version: int = 1
    # 额外索引键
    entity_id: Optional[str] = None        # 关联实体 ID (Agent/Team/Task)
    entity_type: Optional[str] = None      # 关联实体类型

    def __post_init__(self):
        """冻结后计算哈希."""
        if not self.context_hash:
            object.__setattr__(
                self, "context_hash", self._compute_hash()
            )

    def _compute_hash(self) -> str:
        """计算上下文内容的 SHA256 哈希."""
        payload = {
            "slice_id": self.slice_id,
            "operation_id": self.operation_id,
            "context_type": self.context_type.value,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "summary": self.summary,
            "schema_version": self.schema_version,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
        }
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def verify_integrity(self) -> bool:
        """验证切片未被篡改."""
        return self.context_hash == self._compute_hash()

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典."""
        return {
            "slice_id": self.slice_id,
            "operation_id": self.operation_id,
            "context_type": self.context_type.value,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "summary": self.summary,
            "context_hash": self.context_hash,
            "schema_version": self.schema_version,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextSlice":
        """从字典反序列化."""
        ctx_type = data.get("context_type", "custom")
        try:
            ctx_type = ContextType(ctx_type)
        except ValueError:
            ctx_type = ContextType.CUSTOM

        return cls(
            slice_id=data.get("slice_id", ""),
            operation_id=data.get("operation_id", ""),
            context_type=ctx_type,
            timestamp=data.get("timestamp", ""),
            payload=data.get("payload", {}),
            summary=data.get("summary", ""),
            context_hash=data.get("context_hash", ""),
            schema_version=data.get("schema_version", 1),
            entity_id=data.get("entity_id"),
            entity_type=data.get("entity_type"),
        )

    @classmethod
    def create(
        cls,
        operation_id: str,
        context_type: ContextType,
        payload: Dict[str, Any],
        summary: str = "",
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
    ) -> "ContextSlice":
        """工厂方法 — 创建带自动 ID 和时间戳的情境切片."""
        return cls(
            slice_id=f"CS-{uuid.uuid4().hex[:8]}",
            operation_id=operation_id,
            context_type=context_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload=payload,
            summary=summary,
            entity_id=entity_id,
            entity_type=entity_type,
        )


# ═══════════════════════════════════════════════════════════════
# Trace Record — 关联 OperationEvent + ContextSlices 的查询视图
# ═══════════════════════════════════════════════════════════════


@dataclass
class OperationTrace:
    """操作追溯视图 — 聚合 OperationEvent 及其关联的所有 ContextSlice.

    用于审计查询: 给定 operation_id, 返回完整的事发上下文.
    """
    operation: OperationEvent
    context_slices: List[ContextSlice] = field(default_factory=list)

    @property
    def is_integrity_ok(self) -> bool:
        """验证操作事件及所有切片的完整性."""
        if not self.operation.verify_integrity():
            return False
        return all(s.verify_integrity() for s in self.context_slices)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation.to_dict(),
            "context_slices": [s.to_dict() for s in self.context_slices],
            "integrity_ok": self.is_integrity_ok,
        }


# ═══════════════════════════════════════════════════════════════
# Query Filters
# ═══════════════════════════════════════════════════════════════


@dataclass
class OperationQuery:
    """操作事件查询过滤器."""
    operation_type: Optional[OperationType] = None
    agent_id: Optional[str] = None
    team_id: Optional[str] = None
    session_id: Optional[str] = None
    task_id: Optional[str] = None
    parent_operation_id: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    limit: int = 100
    offset: int = 0

    def matches(self, op: OperationEvent) -> bool:
        """检查操作事件是否匹配过滤器."""
        if self.operation_type and op.operation_type != self.operation_type:
            return False
        if self.agent_id and op.agent_id != self.agent_id:
            return False
        if self.team_id and op.team_id != self.team_id:
            return False
        if self.session_id and op.session_id != self.session_id:
            return False
        if self.task_id and op.task_id != self.task_id:
            return False
        if self.parent_operation_id and op.parent_operation_id != self.parent_operation_id:
            return False
        if self.start_time and op.timestamp < self.start_time:
            return False
        if self.end_time and op.timestamp > self.end_time:
            return False
        return True


@dataclass
class ContextQuery:
    """情境切片查询过滤器."""
    operation_id: Optional[str] = None
    context_type: Optional[ContextType] = None
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    limit: int = 100
    offset: int = 0

    def matches(self, cs: ContextSlice) -> bool:
        """检查情境切片是否匹配过滤器."""
        if self.operation_id and cs.operation_id != self.operation_id:
            return False
        if self.context_type and cs.context_type != self.context_type:
            return False
        if self.entity_id and cs.entity_id != self.entity_id:
            return False
        if self.entity_type and cs.entity_type != self.entity_type:
            return False
        if self.start_time and cs.timestamp < self.start_time:
            return False
        if self.end_time and cs.timestamp > self.end_time:
            return False
        return True
