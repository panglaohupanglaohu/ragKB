# -*- coding: utf-8 -*-
"""门禁评估与审核数据模型 — Gate Evaluation & Review Data Models.

定义:
- GateEvaluationContext: evaluate(context) 的入参
- GateEvaluationResult: evaluate() 的返回值 {score, level, reasons}
- ReviewStatus: 审核条目生命周期状态
- ReviewAction: 审核操作类型 (approve/reject/request_changes)
- ReviewEntry: 一条审核队列条目（含版本号用于幂等）
- ReviewQueue: 审核队列聚合
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Gate Evaluation ─────────────────────────────────────────


class GateLevel(str, Enum):
    """门禁等级 — 对标 DNV CII A~E 五级评级."""
    A = "A"  # Major superior — 全面优秀
    B = "B"  # Minor superior — 良好
    C = "C"  # Moderate — 基本合规
    D = "D"  # Minor inferior — 不达标
    E = "E"  # Inferior — 严重不合规

    @staticmethod
    def from_score(score: float) -> "GateLevel":
        """0~100 分 → A~E 等级."""
        if score >= 85:
            return GateLevel.A
        if score >= 70:
            return GateLevel.B
        if score >= 55:
            return GateLevel.C
        if score >= 40:
            return GateLevel.D
        return GateLevel.E


class GateEvaluationContext(BaseModel):
    """门禁评估上下文 — evaluate(context) 的纯函数入参.

    包含评估所需的所有信息，无外部依赖。
    """
    # 被评估实体标识
    entity_id: str = Field(..., description="被评估实体ID（如 Channel/EvolutionItem）")
    entity_type: str = Field(default="evolution_item", description="实体类型")
    entity_name: str = Field(default="", description="实体名称")

    # 审查维度的量化数据
    compliance_score: float = Field(default=0.0, ge=0.0, le=100.0, description="合规评分 0-100")
    test_pass_rate: float = Field(default=100.0, ge=0.0, le=100.0, description="测试通过率 %")
    code_quality_score: float = Field(default=0.0, ge=0.0, le=100.0, description="代码质量评分")
    security_issues: int = Field(default=0, ge=0, description="安全问题数量")
    performance_impact: float = Field(default=0.0, ge=-100.0, le=100.0, description="性能影响评分 (-100~+100)")
    documentation_level: float = Field(default=0.0, ge=0.0, le=100.0, description="文档完善度")

    # 重大门槛条件（一票否决项）
    has_critical_security_issue: bool = Field(default=False, description="存在严重安全漏洞")
    has_breaking_change: bool = Field(default=False, description="存在破坏性变更")
    critical_test_failures: int = Field(default=0, ge=0, description="关键测试失败数")

    # 元数据
    domain: str = Field(default="general", description="所属领域")
    severity: str = Field(default="medium", description="严重程度")
    tags: Dict[str, str] = Field(default_factory=dict)
    extra: Dict[str, Any] = Field(default_factory=dict)


class GateEvaluationResult(BaseModel):
    """门禁评估结果 — evaluate(context) 的纯函数返回值."""
    score: float = Field(..., ge=0.0, le=100.0, description="综合评分 0-100")
    level: GateLevel = Field(..., description="门禁等级 A~E")
    passed: bool = Field(..., description="是否通过门禁")
    reasons: List[str] = Field(default_factory=list, description="评分依据/理由")
    warnings: List[str] = Field(default_factory=list, description="警告信息")
    blocked_by: List[str] = Field(default_factory=list, description="一票否决原因（空=无否决）")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ── Review Entry ────────────────────────────────────────────


class ReviewStatus(str, Enum):
    """审核条目生命周期状态."""
    PENDING = "pending"               # 待审核
    APPROVED = "approved"             # 已批准
    REJECTED = "rejected"             # 已拒绝
    CHANGES_REQUESTED = "changes_requested"  # 要求修改
    CLOSED = "closed"                 # 已关闭
    EXPIRED = "expired"               # 已过期


class ReviewAction(str, Enum):
    """审核操作类型."""
    APPROVE = "approve"               # 批准
    REJECT = "reject"                 # 拒绝
    REQUEST_CHANGES = "request_changes"  # 要求修改
    CLOSE = "close"                   # 关闭
    COMMENT = "comment"               # 添加评论（不改变状态）


class ReviewEntry(BaseModel):
    """一条审核队列条目 — 记录一次门禁评估及后续审核动作.

    幂等键: idempotency_key — 相同 key 的重复操作不产生新记录。
    版本号: version — 每次审核动作递增，用于乐观锁。
    """
    id: str = Field(default_factory=lambda: f"RVW-{uuid.uuid4().hex[:8]}")
    entity_id: str = Field(..., description="被审核实体ID")
    entity_type: str = Field(default="evolution_item")
    entity_name: str = Field(default="")

    # 评估快照 (evaluate() 的结果)
    evaluation_score: float = Field(default=0.0, ge=0.0, le=100.0)
    evaluation_level: GateLevel = Field(default=GateLevel.C)
    evaluation_passed: bool = Field(default=False)

    # 审核状态
    status: ReviewStatus = Field(default=ReviewStatus.PENDING)
    current_action: Optional[ReviewAction] = None

    # 幂等与版本控制
    idempotency_key: Optional[str] = Field(default=None, description="幂等键，防止重复处理")
    version: int = Field(default=1, ge=1, description="版本号，每次操作递增")
    entity_version: int = Field(default=1, ge=1, description="被审核实体的版本号")

    # 操作人与时间线
    reviewer: str = Field(default="system", description="审核人/系统")
    comment: str = Field(default="", description="审核评论")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: Optional[str] = None

    # 上下文
    domain: str = Field(default="general")
    severity: str = Field(default="medium")
    source_evaluation_context: Optional[Dict[str, Any]] = Field(default=None, description="原始评估上下文快照")
    tags: Dict[str, str] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_evaluation(
        cls,
        entity_id: str,
        result: GateEvaluationResult,
        context: Dict[str, Any],
        **kwargs,
    ) -> "ReviewEntry":
        """从评估结果创建审核条目."""
        return cls(
            entity_id=entity_id,
            evaluation_score=result.score,
            evaluation_level=result.level,
            evaluation_passed=result.passed,
            source_evaluation_context=context,
            **kwargs,
        )


class ReviewQueue(BaseModel):
    """审核队列聚合 — 包含所有待审核条目及统计."""
    entries: List[ReviewEntry] = Field(default_factory=list)
    total_pending: int = 0
    total_approved: int = 0
    total_rejected: int = 0
    last_updated: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def refresh_stats(self) -> None:
        """刷新队列统计."""
        self.total_pending = sum(1 for e in self.entries if e.status == ReviewStatus.PENDING)
        self.total_approved = sum(1 for e in self.entries if e.status == ReviewStatus.APPROVED)
        self.total_rejected = sum(1 for e in self.entries if e.status == ReviewStatus.REJECTED)
        self.last_updated = datetime.now(timezone.utc).isoformat()
