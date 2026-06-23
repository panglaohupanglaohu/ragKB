# -*- coding: utf-8 -*-
"""萃取管线状态机 — 数据模型 (Extraction Pipeline State Machine Models).

定义:
- PipelineStage:   四阶段枚举 (DRAFT → REVIEW → APPROVAL → PUBLISHED)
- StageTransition: 阶段迁移事件 (event sourcing)
- GateRequirement: 阶段门禁要求 (交叉复核人数/身份检查)
- GateCheckResult: 门禁检查结果
- ExtractionPipeline: 管线实体 (聚合根)
- TodoItem:        待办事项 (驱动状态迁移)
- ReviewerIdentity: 复核人身份

四阶段流转:
  DRAFT ──[gate:review]──► REVIEW ──[gate:approval]──► APPROVAL ──[gate:publish]──► PUBLISHED
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════

class PipelineStage(str, Enum):
    """萃取管线四阶段."""
    DRAFT = "draft"          # 草稿阶段：初始创建
    REVIEW = "review"        # 复核阶段：交叉复核
    APPROVAL = "approval"    # 审批阶段：最终审核
    PUBLISHED = "published"  # 已发布：生产就绪

    @property
    def order(self) -> int:
        """阶段顺序（用于比较）. """
        _map = {PipelineStage.DRAFT: 0, PipelineStage.REVIEW: 1,
                PipelineStage.APPROVAL: 2, PipelineStage.PUBLISHED: 3}
        return _map[self]

    def next_stage(self) -> Optional["PipelineStage"]:
        """获取下一个阶段. """
        _map = {
            PipelineStage.DRAFT: PipelineStage.REVIEW,
            PipelineStage.REVIEW: PipelineStage.APPROVAL,
            PipelineStage.APPROVAL: PipelineStage.PUBLISHED,
            PipelineStage.PUBLISHED: None,
        }
        return _map[self]

    def prev_stage(self) -> Optional["PipelineStage"]:
        """获取上一个阶段（用于回退）. """
        _map = {
            PipelineStage.DRAFT: None,
            PipelineStage.REVIEW: PipelineStage.DRAFT,
            PipelineStage.APPROVAL: PipelineStage.REVIEW,
            PipelineStage.PUBLISHED: PipelineStage.APPROVAL,
        }
        return _map[self]


class TransitionType(str, Enum):
    """阶段迁移类型."""
    ADVANCE = "advance"      # 前进到下一阶段
    REJECT = "reject"        # 打回（回退到前一阶段）
    RESET = "reset"          # 重置到草稿
    ARCHIVE = "archive"      # 归档


class ReviewerIdentity(str, Enum):
    """复核人身份类型."""
    AUTHOR = "author"            # 作者（不可复核自己）
    PEER = "peer"                # 同级同事
    SENIOR = "senior"            # 高级工程师
    LEAD = "lead"                # 团队负责人
    ARCHITECT = "architect"      # 架构师
    QA = "qa"                    # 质量工程师
    EXTERNAL = "external"        # 外部审核员


class TodoStatus(str, Enum):
    """待办事项状态."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ═══════════════════════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════════════════════

class GateRequirement(BaseModel):
    """单个阶段的门禁要求."""
    stage: PipelineStage = Field(..., description="目标阶段（即进入此阶段前的门禁）")
    min_reviewers: int = Field(default=2, ge=1, description="最少复核人数")
    required_identities: List[ReviewerIdentity] = Field(
        default_factory=lambda: [ReviewerIdentity.PEER, ReviewerIdentity.SENIOR],
        description="必须出现的复核人身份"
    )
    min_approvals: int = Field(default=1, ge=1, description="最少同意票数")
    max_rejections: int = Field(default=0, ge=0, description="最大否决票数")
    require_cross_team: bool = Field(default=False, description="是否需要跨团队复核")
    forbid_self_review: bool = Field(default=True, description="禁止自审")
    auto_advance: bool = Field(default=False, description="满足条件时自动推进")
    extra_rules: Dict[str, Any] = Field(default_factory=dict)


class ReviewerRecord(BaseModel):
    """单条复核记录."""
    reviewer_id: str = Field(..., description="复核人ID")
    reviewer_name: str = Field(default="")
    identity: ReviewerIdentity = Field(default=ReviewerIdentity.PEER)
    team_id: str = Field(default="")
    action: str = Field(default="approve", description="approve | reject | request_changes")
    comment: str = Field(default="")
    reviewed_at: str = Field(default="")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class GateCheckResult(BaseModel):
    """门禁检查结果."""
    passed: bool = Field(default=False)
    stage: PipelineStage
    pipeline_id: str
    reason: str = Field(default="")
    details: Dict[str, Any] = Field(default_factory=dict)
    missing_identities: List[str] = Field(default_factory=list)
    current_reviewers: int = 0
    required_reviewers: int = 0
    current_approvals: int = 0
    required_approvals: int = 0
    checked_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class StageTransition(BaseModel):
    """阶段迁移记录 (Event Sourcing)."""
    transition_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    pipeline_id: str
    from_stage: PipelineStage
    to_stage: PipelineStage
    transition_type: TransitionType
    triggered_by: str = Field(default="system")
    gate_result: Optional[GateCheckResult] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    occurred_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    schema_version: int = Field(default=1)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class TodoItem(BaseModel):
    """待办事项."""
    todo_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    pipeline_id: str
    stage: PipelineStage
    title: str
    description: str = ""
    assignee_id: str = ""
    assignee_name: str = ""
    status: TodoStatus = Field(default=TodoStatus.PENDING)
    required_identity: Optional[ReviewerIdentity] = None
    due_by: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class PipelineConfig(BaseModel):
    """管线全局配置."""
    pipeline_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = Field(default="Untitled Pipeline")
    description: str = ""
    team_id: str = Field(default="")
    created_by: str = Field(default="")
    gate_requirements: Dict[PipelineStage, GateRequirement] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        d = self.model_dump()
        d["gate_requirements"] = {
            k.value if isinstance(k, PipelineStage) else k: v.model_dump()
            for k, v in self.gate_requirements.items()
        }
        return d


class ExtractionPipeline(BaseModel):
    """萃取管线实体 (聚合根)."""
    pipeline_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = Field(default="Untitled Pipeline")
    description: str = ""
    team_id: str = Field(default="")
    current_stage: PipelineStage = Field(default=PipelineStage.DRAFT)
    created_by: str = Field(default="")
    gate_requirements: Dict[PipelineStage, GateRequirement] = Field(default_factory=dict)
    reviewers: List[ReviewerRecord] = Field(default_factory=list)
    transitions: List[StageTransition] = Field(default_factory=list)
    todos: List[TodoItem] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    version: int = Field(default=1)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        d = self.model_dump()
        d["current_stage"] = self.current_stage.value
        d["gate_requirements"] = {
            k.value if isinstance(k, PipelineStage) else k: v.model_dump()
            for k, v in self.gate_requirements.items()
        }
        d["reviewers"] = [r.to_dict() for r in self.reviewers]
        d["transitions"] = [t.to_dict() for t in self.transitions]
        d["todos"] = [t.to_dict() for t in self.todos]
        return d


# ═══════════════════════════════════════════════════════
# Default Gate Requirements
# ═══════════════════════════════════════════════════════

def default_gate_requirements() -> Dict[PipelineStage, GateRequirement]:
    """返回默认的四阶段门禁配置.

    简化版: 单人即可推进，降低使用门槛。
    不强制特定复核身份（peer/senior），触发推进的本人即可作为唯一复核人同意。
    """
    return {
        PipelineStage.REVIEW: GateRequirement(
            stage=PipelineStage.REVIEW,
            min_reviewers=1,
            required_identities=[],
            min_approvals=1,
            max_rejections=1,
            require_cross_team=False,
            forbid_self_review=False,
            auto_advance=True,
        ),
        PipelineStage.APPROVAL: GateRequirement(
            stage=PipelineStage.APPROVAL,
            min_reviewers=1,
            required_identities=[],
            min_approvals=1,
            max_rejections=1,
            require_cross_team=False,
            forbid_self_review=False,
            auto_advance=True,
        ),
        PipelineStage.PUBLISHED: GateRequirement(
            stage=PipelineStage.PUBLISHED,
            min_reviewers=1,
            required_identities=[],
            min_approvals=1,
            max_rejections=1,
            require_cross_team=False,
            forbid_self_review=False,
            auto_advance=True,
        ),
    }
