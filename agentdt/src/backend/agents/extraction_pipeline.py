# -*- coding: utf-8 -*-
"""萃取管线状态机 — Pipeline State Machine + Gate Validation.

核心职责:
1. 四阶段流转控制 (DRAFT → REVIEW → APPROVAL → PUBLISHED)
2. 阶段门禁校验（交叉复核人数 + 身份检查）
3. 事件溯源集成（每次迁移生成 StageTransition 事件）
4. Todo 自动生成（根据门禁缺口生成待办）
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .extraction_models import (
    ExtractionPipeline,
    PipelineStage,
    StageTransition,
    TransitionType,
    GateRequirement,
    GateCheckResult,
    ReviewerRecord,
    ReviewerIdentity,
    TodoItem,
    TodoStatus,
    default_gate_requirements,
)
from .extraction_store import ExtractionStore, get_extraction_store

logger = logging.getLogger(__name__)


class GateValidationError(Exception):
    """门禁校验失败异常."""
    def __init__(self, result: GateCheckResult):
        self.result = result
        super().__init__(result.reason)


class ExtractionPipelineEngine:
    """萃取管线状态机引擎."""

    def __init__(self, store: Optional[ExtractionStore] = None):
        self._store = store or get_extraction_store()

    @property
    def store(self) -> ExtractionStore:
        return self._store

    # ── Gate Validation ─────────────────────────────────

    def check_gate(
        self,
        pipeline: ExtractionPipeline,
        target_stage: Optional[PipelineStage] = None,
    ) -> GateCheckResult:
        """检查当前阶段的门禁条件。

        Args:
            pipeline: 管线实体
            target_stage: 要进入的目标阶段（默认为当前阶段的 next）

        Returns:
            GateCheckResult: 门禁检查结果
        """
        current = pipeline.current_stage
        target = target_stage or current.next_stage()

        if target is None:
            return GateCheckResult(
                passed=False,
                stage=current,
                pipeline_id=pipeline.pipeline_id,
                reason=f"已经是最终阶段 '{current.value}'，无法继续推进",
            )

        # 获取目标阶段对应的门禁要求
        gate = pipeline.gate_requirements.get(target)
        if gate is None:
            # 无门禁配置，默认允许
            return GateCheckResult(
                passed=True,
                stage=target,
                pipeline_id=pipeline.pipeline_id,
                reason=f"阶段 '{target.value}' 无门禁配置，默认放行",
                current_reviewers=len(pipeline.reviewers),
                required_reviewers=0,
                current_approvals=0,
                required_approvals=0,
            )

        # 只统计当前阶段的复核记录
        stage_reviewers = [
            r for r in pipeline.reviewers
            # 这里可按需过滤：仅统计在 current stage 阶段提交的复核
            # 当前简化：统计全部 active reviewers
        ]

        # ── 检查项 ──
        issues = []
        details = {}

        # 1. 最少复核人数
        reviewer_count = len(stage_reviewers) if stage_reviewers else len(pipeline.reviewers)
        details["reviewer_count"] = reviewer_count
        if reviewer_count < gate.min_reviewers:
            issues.append(
                f"复核人数不足: 需要至少 {gate.min_reviewers} 人，当前 {reviewer_count} 人"
            )

        # 2. 必填身份检查
        present_identities = {r.identity for r in (stage_reviewers or pipeline.reviewers)}
        required_ids = set(gate.required_identities)
        missing_ids = required_ids - present_identities
        details["present_identities"] = [i.value for i in present_identities]
        details["required_identities"] = [i.value for i in required_ids]
        if missing_ids:
            issues.append(
                f"缺少必要身份: {[i.value for i in missing_ids]}"
            )

        # 3. 最少同意票数
        approvals = sum(
            1 for r in (stage_reviewers or pipeline.reviewers)
            if r.action == "approve"
        )
        details["current_approvals"] = approvals
        if approvals < gate.min_approvals:
            issues.append(
                f"同意票不足: 需要至少 {gate.min_approvals} 票，当前 {approvals} 票"
            )

        # 4. 最大否决票数
        rejections = sum(
            1 for r in (stage_reviewers or pipeline.reviewers)
            if r.action == "reject"
        )
        details["current_rejections"] = rejections
        if rejections > gate.max_rejections:
            issues.append(
                f"否决票过多: 最多允许 {gate.max_rejections} 票，当前 {rejections} 票"
            )

        # 5. 禁止自审检查
        if gate.forbid_self_review:
            author_reviewers = [
                r for r in (stage_reviewers or pipeline.reviewers)
                if r.reviewer_id == pipeline.created_by
            ]
            if author_reviewers:
                issues.append(
                    f"禁止自审: 作者 '{pipeline.created_by}' 不能复核自己的管线"
                )

        # 6. 跨团队检查
        if gate.require_cross_team and pipeline.team_id:
            non_team_reviewers = [
                r for r in (stage_reviewers or pipeline.reviewers)
                if r.team_id and r.team_id != pipeline.team_id
            ]
            if not non_team_reviewers:
                issues.append("需要至少一位跨团队成员参与复核")

        passed = len(issues) == 0
        reason = "所有门禁条件满足 ✓" if passed else "; ".join(issues)

        return GateCheckResult(
            passed=passed,
            stage=target,
            pipeline_id=pipeline.pipeline_id,
            reason=reason,
            details=details,
            missing_identities=[i.value for i in missing_ids] if not passed else [],
            current_reviewers=reviewer_count,
            required_reviewers=gate.min_reviewers,
            current_approvals=approvals,
            required_approvals=gate.min_approvals,
        )

    # ── Stage Transitions ───────────────────────────────

    async def advance(
        self,
        pipeline_id: str,
        triggered_by: str = "system",
        force: bool = False,
    ) -> Tuple[Optional[StageTransition], GateCheckResult]:
        """推进管线到下一阶段。

        Args:
            pipeline_id: 管线ID
            triggered_by: 触发者ID
            force: 是否强制执行（跳过门禁）

        Returns:
            (transition, gate_result) 元组
        """
        pipeline = await self._store.get_pipeline(pipeline_id)
        if pipeline is None:
            raise ValueError(f"Pipeline '{pipeline_id}' not found")

        current = pipeline.current_stage
        target = current.next_stage()
        if target is None:
            return (None, GateCheckResult(
                passed=False,
                stage=current,
                pipeline_id=pipeline_id,
                reason=f"已是最终阶段 '{current.value}'",
            ))

        # 单人 review：触发推进的真人即视为完成复核并同意（降低门槛，单人即可推进）。
        # identity 用 PEER，同时满足历史管线里仍要求 peer 身份的门禁。
        if triggered_by and triggered_by != "system" and not force:
            already_approved = any(
                r.reviewer_id == triggered_by and r.action == "approve"
                for r in pipeline.reviewers
            )
            if not already_approved:
                updated = await self._store.add_reviewer(pipeline_id, ReviewerRecord(
                    reviewer_id=triggered_by,
                    reviewer_name=triggered_by,
                    identity=ReviewerIdentity.PEER,
                    team_id=pipeline.team_id,
                    action="approve",
                    comment="单人推进：触发者自动复核同意",
                    reviewed_at=datetime.now(timezone.utc).isoformat(),
                ))
                if updated:
                    pipeline = updated

        # 门禁检查
        gate_result = self.check_gate(pipeline, target)
        if not gate_result.passed and not force:
            # 生成 Todo 提示缺口
            await self._generate_gate_todos(pipeline, gate_result)
            raise GateValidationError(gate_result)

        # 执行迁移
        transition = await self._store.record_transition(
            pipeline_id=pipeline_id,
            from_stage=current,
            to_stage=target,
            transition_type=TransitionType.ADVANCE,
            triggered_by=triggered_by,
            gate_result=gate_result,
            metadata={"force": force},
        )

        if transition:
            logger.info(f"✅ Pipeline {pipeline_id} advanced to {target.value}")
            # 为新阶段生成 Todo
            await self._generate_stage_todos(pipeline_id, target)

        return (transition, gate_result)

    async def reject(
        self,
        pipeline_id: str,
        triggered_by: str = "system",
        reason: str = "",
    ) -> Optional[StageTransition]:
        """打回管线到上一阶段."""
        pipeline = await self._store.get_pipeline(pipeline_id)
        if pipeline is None:
            raise ValueError(f"Pipeline '{pipeline_id}' not found")

        current = pipeline.current_stage
        target = current.prev_stage()
        if target is None:
            logger.warning(f"Cannot reject from {current.value} (no previous stage)")
            return None

        transition = await self._store.record_transition(
            pipeline_id=pipeline_id,
            from_stage=current,
            to_stage=target,
            transition_type=TransitionType.REJECT,
            triggered_by=triggered_by,
            gate_result=GateCheckResult(
                passed=True,
                stage=target,
                pipeline_id=pipeline_id,
                reason=f"打回: {reason}" if reason else "打回到上一阶段",
            ),
            metadata={"reject_reason": reason},
        )

        if transition:
            logger.info(f"↩️ Pipeline {pipeline_id} rejected to {target.value}")
        return transition

    async def reset(
        self,
        pipeline_id: str,
        triggered_by: str = "system",
    ) -> Optional[StageTransition]:
        """重置管线到草稿阶段."""
        pipeline = await self._store.get_pipeline(pipeline_id)
        if pipeline is None:
            raise ValueError(f"Pipeline '{pipeline_id}' not found")

        current = pipeline.current_stage
        if current == PipelineStage.DRAFT:
            return None

        transition = await self._store.record_transition(
            pipeline_id=pipeline_id,
            from_stage=current,
            to_stage=PipelineStage.DRAFT,
            transition_type=TransitionType.RESET,
            triggered_by=triggered_by,
            gate_result=GateCheckResult(
                passed=True,
                stage=PipelineStage.DRAFT,
                pipeline_id=pipeline_id,
                reason="手动重置到草稿",
            ),
        )

        if transition:
            logger.info(f"🔄 Pipeline {pipeline_id} reset to draft")
        return transition

    # ── Reviewer Actions ────────────────────────────────

    async def submit_review(
        self,
        pipeline_id: str,
        reviewer_id: str,
        action: str,
        identity: str = "peer",
        team_id: str = "",
        comment: str = "",
        reviewer_name: str = "",
    ) -> Optional[ExtractionPipeline]:
        """提交复核记录."""
        pipeline = await self._store.get_pipeline(pipeline_id)
        if pipeline is None:
            raise ValueError(f"Pipeline '{pipeline_id}' not found")

        # 自审检查
        if pipeline.created_by == reviewer_id:
            # 检查门禁是否禁止自审
            current_gate = pipeline.gate_requirements.get(
                pipeline.current_stage.next_stage() or pipeline.current_stage
            )
            if current_gate and current_gate.forbid_self_review:
                raise ValueError("禁止自审：作者不能复核自己的管线")

        reviewer = ReviewerRecord(
            reviewer_id=reviewer_id,
            reviewer_name=reviewer_name,
            identity=ReviewerIdentity(identity) if identity else ReviewerIdentity.PEER,
            team_id=team_id,
            action=action,
            comment=comment,
        )

        updated = await self._store.add_reviewer(pipeline_id, reviewer)

        # 如果配置了 auto_advance，检查是否可以自动推进
        if updated:
            target = updated.current_stage.next_stage()
            if target:
                gate = updated.gate_requirements.get(target)
                if gate and gate.auto_advance:
                    try:
                        await self.advance(pipeline_id, triggered_by=reviewer_id)
                    except GateValidationError:
                        pass  # 条件尚未满足

        return updated

    # ── Todo Management ─────────────────────────────────

    async def _generate_stage_todos(
        self,
        pipeline_id: str,
        stage: PipelineStage,
    ) -> List[TodoItem]:
        """为新阶段生成待办事项."""
        pipeline = await self._store.get_pipeline(pipeline_id)
        if pipeline is None:
            return []

        gate = pipeline.gate_requirements.get(stage)
        if gate is None:
            return []

        todos = []
        now = datetime.now(timezone.utc).isoformat()

        # 为每个必填身份生成复核待办
        for identity in gate.required_identities:
            todo = TodoItem(
                pipeline_id=pipeline_id,
                stage=stage,
                title=f"[{stage.value}] 需要 {identity.value} 复核",
                description=f"管线 '{pipeline.name}' 需要 {identity.value} 身份的人进行复核",
                required_identity=identity,
                created_at=now,
            )
            await self._store.add_todo(pipeline_id, todo)
            todos.append(todo)

        return todos

    async def _generate_gate_todos(
        self,
        pipeline: ExtractionPipeline,
        gate_result: GateCheckResult,
    ) -> List[TodoItem]:
        """根据门禁缺口生成待办."""
        todos = []
        now = datetime.now(timezone.utc).isoformat()

        for missing_id in gate_result.missing_identities:
            todo = TodoItem(
                pipeline_id=pipeline.pipeline_id,
                stage=gate_result.stage,
                title=f"[门禁缺口] 缺少 {missing_id} 身份复核人",
                description=f"需要 {missing_id} 身份的复核才能推进到 {gate_result.stage.value} 阶段",
                created_at=now,
            )
            await self._store.add_todo(pipeline.pipeline_id, todo)
            todos.append(todo)

        if gate_result.current_reviewers < gate_result.required_reviewers:
            todo = TodoItem(
                pipeline_id=pipeline.pipeline_id,
                stage=gate_result.stage,
                title=f"[门禁缺口] 还需要 {gate_result.required_reviewers - gate_result.current_reviewers} 位复核人",
                description=f"当前 {gate_result.current_reviewers}/{gate_result.required_reviewers} 人",
                created_at=now,
            )
            await self._store.add_todo(pipeline.pipeline_id, todo)
            todos.append(todo)

        return todos

    async def resolve_todo(
        self,
        pipeline_id: str,
        todo_id: str,
        resolver_id: str = "",
    ) -> Optional[TodoItem]:
        """解决待办事项并尝试自动推进管线."""
        updated = await self._store.update_todo(
            pipeline_id, todo_id,
            {
                "status": TodoStatus.COMPLETED,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        if updated:
            # 检查是否可以自动推进
            pipeline = await self._store.get_pipeline(pipeline_id)
            if pipeline:
                target = pipeline.current_stage.next_stage()
                if target:
                    gate = pipeline.gate_requirements.get(target)
                    if gate and gate.auto_advance:
                        try:
                            await self.advance(pipeline_id, triggered_by=resolver_id or "todo_resolver")
                        except GateValidationError:
                            pass

        return updated

    async def get_all_todos(
        self,
        assignee_id: Optional[str] = None,
        status: Optional[str] = None,
        pipeline_id: Optional[str] = None,
    ) -> List[TodoItem]:
        """获取所有待办."""
        return await self._store.get_todos(
            assignee_id=assignee_id,
            status=status,
            pipeline_id=pipeline_id,
        )

    # ── Stats ───────────────────────────────────────────

    async def get_stats(self) -> Dict[str, Any]:
        """获取管线统计."""
        return await self._store.get_stats()


# ── Global singleton ────────────────────────────────────

_engine: Optional[ExtractionPipelineEngine] = None


def get_extraction_engine() -> ExtractionPipelineEngine:
    global _engine
    if _engine is None:
        _engine = ExtractionPipelineEngine()
    return _engine


def init_extraction_engine(store: Optional[ExtractionStore] = None) -> ExtractionPipelineEngine:
    global _engine
    _engine = ExtractionPipelineEngine(store=store)
    return _engine
