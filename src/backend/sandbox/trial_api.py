# -*- coding: utf-8 -*-
"""Trial API — 数字孪生试炼三层模型 REST 接口.

阶段二核心: 实现 Trial/Branch/Session 三层模型的完整 CRUD,
包含分支分裂、步进控制、混沌注入、五维评分、SOP 萃取、反哺闭环.
(A-01 ~ A-12 全部接口)
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .models import (
    Branch, BranchStatus, SOPCandidate, Trial, TrialEvent,
    TrialEvaluation, TrialEventType, TrialMode, TrialStatus,
)
from .api import get_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/twin-trials", tags=["twin-trials"])

# ── 内存存储 (生产环境可替换为 Redis/DB) ──

_trials: Dict[str, Trial] = {}
_branches: Dict[str, Branch] = {}
_trial_events: Dict[str, List[TrialEvent]] = {}  # trial_id -> events


# ── Pydantic Request Models ──


class CreateTrialRequest(BaseModel):
    team_id: str = "default"
    task_goal: Dict[str, Any] = Field(default_factory=dict)
    scenario: str = ""
    mode: str = Field(default="what_if", description="what_if | multi_branch | chaos_drill | evolutionary | replay")
    max_steps: int = Field(default=150, ge=10, le=500)
    acceleration: int = Field(default=1, ge=1, le=100)
    parallel_branches: int = Field(default=1, ge=1, le=8)


class ForkBranchRequest(BaseModel):
    fork_from_branch_id: str
    fork_at_step: Optional[int] = None
    name: str = ""
    initial_conditions: Dict[str, Any] = Field(default_factory=dict)


class InjectEventRequest(BaseModel):
    event_type: str  # network_delay | agent_leave | task_change | skill_degraded | model_hallucination | logic_deadlock
    payload: Dict[str, Any] = Field(default_factory=dict)
    trigger_at_step: Optional[int] = None


class EvaluateRequest(BaseModel):
    force_refresh: bool = False


class ExtractSopRequest(BaseModel):
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source_branch_id: Optional[str] = None


class FeedbackRequest(BaseModel):
    sop_ids: List[str] = Field(default_factory=list)  # 空列表表示全部 approved SOPs
    target_agent_ids: Optional[List[str]] = None      # 空则自动推断


# ── Helper Functions ──


def _get_trial(trial_id: str) -> Trial:
    t = _trials.get(trial_id)
    if not t:
        raise HTTPException(status_code=404, detail=f"Trial {trial_id} not found")
    return t


def _get_branch(branch_id: str) -> Branch:
    b = _branches.get(branch_id)
    if not b:
        raise HTTPException(status_code=404, detail=f"Branch {branch_id} not found")
    return b


def _generate_color(index: int) -> str:
    """为分支生成唯一颜色."""
    colors = ["#4A90E2", "#F5A623", "#7ED321", "#BD10E0", "#D0021B", "#50E3C2", "#F8E71C"]
    return colors[index % len(colors)]


def _compute_evaluation(trial: Trial) -> TrialEvaluation:
    """计算五维评分 (E-01~E-06)."""
    eval_obj = TrialEvaluation(trial_id=trial.id)

    # 收集所有分支数据
    branch_ids = trial.branches or []
    all_steps_total = 0
    all_rewards = []
    branch_max_scores: Dict[str, float] = {}

    for bid in branch_ids:
        b = _branches.get(bid)
        if not b:
            continue
        branch_steps = b.current_step or 0
        all_steps_total += branch_steps
        if b.reward_curve:
            max_r = max((p.get("reward", 0) for p in b.reward_curve), default=0)
            branch_max_scores[bid] = max_r
            all_rewards.append(max_r)

    total_possible_steps = max(trial.max_steps * max(len(branch_ids), 1), 1)

    # E-01: 目标完成度 = 最高 reward / 理论最大值(假设为1.0)
    best_reward = max(all_rewards) if all_rewards else 0.0
    eval_obj.task_completion = min(best_reward / 1.0, 1.0)

    # E-02: 协作效率 = 平均并行度 * (1 - 交接惩罚系数)
    avg_parallelism = min(all_steps_total / total_possible_steps, 1.0) if total_possible_steps > 0 else 0
    transfer_penalty = min(len(branch_ids) * 0.02, 0.15)  # 分支越多交接越多
    eval_obj.collaboration_efficiency = max(avg_parallelism - transfer_penalty, 0.0)

    # E-03: 韧性评分 = 1 - (恢复步数 / 最大步数)，无故障默认满分
    fault_count = sum(
        len(b.injected_events) for bid in branch_ids if (b := _branches.get(bid))
    )
    if fault_count > 0 and all_steps_total > 0:
        recovery_ratio = min(fault_count / all_steps_total, 1.0)
        eval_obj.resilience = 1.0 - recovery_ratio * 0.5  # 有故障但最多扣一半分
    else:
        eval_obj.resilience = 1.0

    # E-04: 成本控制 = 1 - (实际步数 / 最大步数)
    actual_ratio = all_steps_total / total_possible_steps if total_possible_steps > 0 else 1.0
    eval_obj.cost_efficiency = max(1.0 - actual_ratio * 0.3, 0.0)  # 步数越多成本越低

    # E-05: 可萃取性 = reward 曲线稳定性（简化：有 reward 数据即给基础分）
    if len(all_rewards) >= 2:
        variance = (max(all_rewards) - min(all_rewards)) / (max(max(all_rewards), 0.001))
        eval_obj.extractability = max(0.5 - variance * 0.3, 0.1) + 0.3 * (len(all_rewards) / max(len(branch_ids), 1))
    elif len(all_rewards) == 1:
        eval_obj.extractability = 0.4
    else:
        eval_obj.extractability = 0.1

    # E-06: 加权总分
    eval_obj.total_score = round(
        eval_obj.task_completion * 0.30
        + eval_obj.collaboration_efficiency * 0.25
        + eval_obj.resilience * 0.20
        + eval_obj.cost_efficiency * 0.15
        + eval_obj.extractability * 0.10,
        6,
    )

    eval_obj.branch_scores = branch_max_scores
    if branch_max_scores:
        eval_obj.best_branch_id = max(branch_max_scores, key=branch_max_scores.get)
        eval_obj.worst_branch_id = min(branch_max_scores, key=branch_max_scores.get)
    else:
        eval_obj.best_branch_id = branch_ids[0] if branch_ids else None

    # 关键洞察和转折点
    if eval_obj.task_completion > 0.7:
        eval_obj.key_insights.append(f"目标完成度高 ({eval_obj.task_completion:.1%})，策略路径稳定")
    if eval_obj.resilience < 0.8 and fault_count > 0:
        eval_obj.key_insights.append(f"经受 {fault_count} 次故障注入，韧性 {eval_obj.resilience:.1%}")
    if eval_obj.total_score > 0.65:
        eval_obj.key_insights.append(f"综合评分 {eval_obj.total_score:.3f} 达标，建议萃取SOP")

    # 转折点：从 reward_curve 中找突变点
    for bid in branch_ids[:3]:  # 只分析前3个分支
        b = _branches.get(bid)
        if not b or not b.reward_curve or len(b.reward_curve) < 3:
            continue
        curve = b.reward_curve
        for i in range(1, len(curve)):
            delta = abs(curve[i].get("reward", 0) - curve[i - 1].get("reward", 0))
            if delta > 0.08:  # 阈值
                eval_obj.turning_points.append({
                    "branch_id": bid,
                    "step": curve[i].get("step", i),
                    "type": "reward_spike" if delta > 0 else "reward_drop",
                    "delta": round(delta, 4),
                })

    return eval_obj


# ════════════════════════════════════════════════════════════
# A-01: POST /api/v1/twin-trials — 创建试炼
# ════════════════════════════════════════════════════════════


@router.post("")
async def create_trial(req: CreateTrialRequest) -> Dict[str, Any]:
    """创建新试炼，自动创建 baseline Branch 和关联 Session."""
    try:
        mode = TrialMode(req.mode)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {req.mode}")

    import datetime as _dt

    trial = Trial(
        name=req.task_goal.get("name", f"Trial-{_dt.datetime.now().strftime('%H%M%S')}"),
        team_id=req.team_id,
        task_goal=req.task_goal,
        scenario=req.scenario,
        mode=mode,
        max_steps=req.max_steps,
        acceleration=req.acceleration,
        parallel_branches=req.parallel_branches,
        status=TrialStatus.CREATING,
    )

    # 创建 baseline Branch
    baseline = Branch(
        trial_id=trial.id,
        name="baseline",
        label="baseline",
        color="#4A90E2",
        status=BranchStatus.PENDING,
    )
    _branches[baseline.id] = baseline
    trial.branches = [baseline.id]

    # 通过现有 SECS 创建 Session 并关联到 baseline Branch
    session_id = None
    try:
        from .api import CreateSessionRequest
        orch = get_orchestrator()

        # 转换模式映射
        mode_map = {
            TrialMode.WHAT_IF: "what_if",
            TrialMode.MULTI_BRANCH: "parallel",
            TrialMode.CHAOS_DRILL: "evolutionary",
            TrialMode.EVOLUTIONARY: "evolutionary",
            TrialMode.REPLAY: "what_if",
        }
        from .models import SimulationMode
        secs_mode = SimulationMode.WHAT_IF  # 默认 what_if

        sec_session = orch.create_session(
            team_id=req.team_id,
            mode=secs_mode,
            max_steps=req.max_steps,
            speed_factor=float(req.acceleration),
            parallel_branches=req.parallel_branches,
            trigger_description=req.scenario or req.task_goal.get("description", ""),
        )
        session_id = sec_session.session_id

        # 关联 session 到 branch
        baseline.sessions = [session_id]
        baseline.current_session_id = session_id
        sec_session.branch_id = baseline.id
        sec_session.trial_id = trial.id
        trial.total_sessions = 1

    except Exception as e:
        logger.warning(f"Trial 创建 SECS session 失败（继续创建 Trial）: {e}")
        # 即使 SECS 创建失败也保留 Trial 结构

    trial.status = TrialStatus.READY
    trial.updated_at = _dt.datetime.now(_dt.timezone.utc).isoformat()
    _trials[trial.id] = trial

    # 记录事件
    evt = TrialEvent(event_type=TrialEventType.BRANCH_CREATED, trial_id=trial.id, branch_id=baseline.id,
                     data={"label": "baseline", "session_id": session_id})
    _trial_events.setdefault(trial.id, []).append(evt)

    logger.info(f"Trial created: {trial.id}, baseline={baseline.id}, session={session_id}")

    return {
        "trial_id": trial.id,
        "branch_id": baseline.id,
        "session_id": session_id,
        "status": trial.status.value,
        "mode": trial.mode.value,
        "name": trial.name,
    }


# ════════════════════════════════════════════════════════════
# A-02: GET /api/v1/twin-trials — 列表
# ════════════════════════════════════════════════════════════


@router.get("")
async def list_trials(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Dict[str, Any]:
    """返回历史 Trial 列表，按创建时间倒序."""
    all_trials = sorted(_trials.values(), key=lambda t: t.created_at, reverse=True)
    start = (page - 1) * page_size
    paged = all_trials[start:start + page_size]

    items = []
    for t in paged:
        items.append({
            "id": t.id,
            "name": t.name,
            "status": t.status.value,
            "mode": t.mode.value,
            "team_name": t.team_id,
            "max_reward": t.best_score,
            "total_steps": t.total_steps,
            "sop_count": len(t.extracted_sops),
            "branch_count": len(t.branches),
            "created_at": t.created_at,
        })

    return {"trials": items, "total": len(all_trials), "page": page, "page_size": page_size}


# ════════════════════════════════════════════════════════════
# A-03: GET /api/v1/twin-trials/{trial_id} — 详情
# ════════════════════════════════════════════════════════════


@router.get("/{trial_id}")
async def get_trial(trial_id: str) -> Dict[str, Any]:
    """返回完整 Trial 详情."""
    trial = _get_trial(trial_id)

    branches_data = []
    for bid in (trial.branches or []):
        b = _branches.get(bid)
        if b:
            branches_data.append({
                "id": b.id,
                "name": b.name,
                "label": b.label,
                "color": b.color,
                "status": b.status.value,
                "current_step": b.current_step,
                "final_score": b.final_score,
                "session_count": len(b.sessions or []),
                "reward_curve_len": len(b.reward_curve or []),
            })

    result = {
        "id": trial.id,
        "name": trial.name,
        "status": trial.status.value,
        "mode": trial.mode.value,
        "team_id": trial.team_id,
        "task_goal": trial.task_goal,
        "scenario": trial.scenario,
        "max_steps": trial.max_steps,
        "acceleration": trial.acceleration,
        "parallel_branches": trial.parallel_branches,
        "total_sessions": trial.total_sessions,
        "total_steps": trial.total_steps,
        "best_score": trial.best_score,
        "sop_count": len(trial.extracted_sops),
        "created_at": trial.created_at,
        "updated_at": trial.updated_at,
        "branches": branches_data,
        "evaluation": trial.evaluation,
        "incomplete": trial.evaluation is None,
    }
    return result


# ════════════════════════════════════════════════════════════
# A-04: POST /{trial_id}/branches — 分裂分支
# ════════════════════════════════════════════════════════════


@router.post("/{trial_id}/branches")
async def fork_branch(trial_id: str, req: ForkBranchRequest) -> Dict[str, Any]:
    """从指定 step 的状态快照创建新 Branch."""
    trial = _get_trial(trial_id)
    parent = _get_branch(req.fork_from_branch_id)

    color_idx = len(trial.branches)
    new_branch = Branch(
        trial_id=trial_id,
        name=req.name or f"branch-{color_idx}",
        label=req.name or f"v{color_idx}",
        color=_generate_color(color_idx),
        parent_branch_id=parent.id,
        fork_at_step=req.fork_at_step or parent.current_step,
        initial_conditions=req.initial_conditions or dict(parent.initial_conditions),
        status=BranchStatus.PENDING,
    )
    _branches[new_branch.id] = new_branch
    trial.branches.append(new_branch.id)
    trial.updated_at = Trial.__dataclass_fields__["updated_at"].default_factory()  # type: ignore

    # 继承父分支的初始条件
    if parent.sessions:
        try:
            orch = get_orchestrator()
            from .models import SimulationMode
            sec_session = orch.create_session(
                team_id=trial.team_id,
                mode=SimulationMode.WHAT_IF,
                max_steps=trial.max_steps - (new_branch.fork_at_step or 0),
                speed_factor=float(trial.acceleration),
                trigger_description=f"Forked from {parent.label}@step{new_branch.fork_at_step}",
            )
            new_branch.sessions = [sec_session.session_id]
            new_branch.current_session_id = sec_session.session_id
            sec_session.branch_id = new_branch.id
            sec_session.trial_id = trial.id
            trial.total_sessions += 1
        except Exception as e:
            logger.warning(f"Fork branch session creation failed: {e}")

    # 记录事件
    evt = TrialEvent(event_type=TrialEventType.BRANCH_FORKED, trial_id=trial_id,
                     branch_id=new_branch.id, data={"parent": parent.id, "fork_at": new_branch.fork_at_step})
    _trial_events.setdefault(trial_id, []).append(evt)

    return {"branch_id": new_branch.id, "session_id": new_branch.current_session_id, "label": new_branch.label}


# ════════════════════════════════════════════════════════════
# A-05~A-07: Step / Run / Pause — 委托给 SECS session
# ════════════════════════════════════════════════════════════


@router.post("/{trial_id}/branches/{branch_id}/step")
async def branch_step(trial_id: str, branch_id: str) -> Dict[str, Any]:
    """单步推演."""
    _get_trial(trial_id)
    branch = _get_branch(branch_id)

    if not branch.current_session_id:
        raise HTTPException(status_code=400, detail="Branch has no active session")

    try:
        orch = get_orchestrator()
        result = await orch.step_once(branch.current_session_id)

        # 更新分支状态
        step_index = result.get("step_index", result.get("step_id", 0))
        if isinstance(step_index, int):
            branch.current_step = step_index
        reward = result.get("global_reward", result.get("reward"))
        if isinstance(reward, (int, float)):
            branch.reward_curve.append({"step": branch.current_step, "reward": round(float(reward), 6)})
        branch.status = BranchStatus.RUNNING

        # 更新 Trial 统计
        trial = _trials.get(trial_id)
        if trial:
            trial.total_steps = max(trial.total_steps, branch.current_step)
            if reward is not None:
                trial.best_score = max(trial.best_score or 0, float(reward))

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{trial_id}/branches/{branch_id}/run")
async def branch_run(trial_id: str, branch_id: str) -> Dict[str, Any]:
    """启动自动推演."""
    _get_trial(trial_id)
    branch = _get_branch(branch_id)

    if not branch.current_session_id:
        raise HTTPException(status_code=400, detail="Branch has no active session")

    try:
        orch = get_orchestrator()
        result = await orch.run_full_pipeline(branch.current_session_id)
        branch.status = BranchStatus.RUNNING
        _get_trial(trial_id).status = TrialStatus.RUNNING  # type: ignore
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{trial_id}/branches/{branch_id}/pause")
async def branch_pause(trial_id: str, branch_id: str) -> Dict[str, Any]:
    """暂停当前 Branch."""
    _get_trial(trial_id)
    branch = _get_branch(branch_id)

    if branch.current_session_id:
        try:
            orch = get_orchestrator()
            session = orch.get_session(branch.current_session_id)
            if session:
                from .models import SandboxStatus
                session.status = SandboxStatus.PAUSED
        except Exception as e:
            logger.warning(f"Pause session failed: {e}")

    branch.status = BranchStatus.PAUSED
    return {"status": "paused", "current_step": branch.current_step}


# ════════════════════════════════════════════════════════════
# A-08: 注入演练事件
# ════════════════════════════════════════════════════════════


@router.post("/{trial_id}/branches/{branch_id}/events")
async def inject_trial_event(trial_id: str, branch_id: str, req: InjectEventRequest) -> Dict[str, Any]:
    """向指定 Branch 注入演练事件（网络延迟/Agent离队/任务变更/技能退化等）."""
    _get_trial(trial_id)
    branch = _get_branch(branch_id)

    valid_types = {"network_delay", "agent_leave", "task_change", "skill_degraded",
                   "model_hallucination", "logic_deadlock", "agent_failure", "task_mutation"}
    if req.event_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid event_type: {req.event_type}")

    event_record = {
        "event_type": req.event_type,
        "payload": req.payload,
        "trigger_at_step": req.trigger_at_step,
        "injected_at": time.time(),
    }
    branch.injected_events.append(event_record)

    # 如果有活跃 session，同时注入 SECS 混沌事件
    if branch.current_session_id:
        try:
            orch = get_orchestrator()
            chaos_result = await orch.inject_chaos_event(
                session_id=branch.current_session_id,
                event_type=req.event_type,
                target_agent=req.payload.get("target_agent"),
            )
            event_record["secs_result"] = chaos_result
        except Exception as e:
            logger.warning(f"SECS chaos inject failed: {e}")
            event_record["secs_error"] = str(e)

    # 记录事件
    evt = TrialEvent(event_type=TrialEventType.CHAOS_INJECTED, trial_id=trial_id,
                     branch_id=branch_id, data=event_record)
    _trial_events.setdefault(trial_id, []).append(evt)

    return {"injected": True, "event": event_record}


# ════════════════════════════════════════════════════════════
# A-09: 五维评估
# ════════════════════════════════════════════════════════════


@router.post("/{trial_id}/evaluate")
async def evaluate_trial(trial_id: str, req: EvaluateRequest = EvaluateRequest()) -> Dict[str, Any]:
    """计算所有 Branch 的五维评分."""
    trial = _get_trial(trial_id)

    if trial.evaluation and not req.force_refresh:
        return trial.evaluation

    trial.status = TrialStatus.EVALUATING
    eval_result = _compute_evaluation(trial)
    trial.evaluation = {
        "eval_id": eval_result.eval_id,
        "trial_id": eval_result.trial_id,
        "evaluated_at": eval_result.evaluated_at,
        "task_completion": round(eval_result.task_completion, 6),
        "collaboration_efficiency": round(eval_result.collaboration_efficiency, 6),
        "resilience": round(eval_result.resilience, 6),
        "cost_efficiency": round(eval_result.cost_efficiency, 6),
        "extractability": round(eval_result.extractability, 6),
        "total_score": round(eval_result.total_score, 6),
        "branch_scores": eval_result.branch_scores,
        "best_branch_id": eval_result.best_branch_id,
        "worst_branch_id": eval_result.worst_branch_id,
        "key_insights": eval_result.key_insights,
        "turning_points": eval_result.turning_points,
    }
    trial.best_score = eval_result.total_score
    trial.status = TrialStatus.COMPLETED

    evt = TrialEvent(event_type=TrialEventType.EVALUATION_DONE, trial_id=trial_id,
                     data={"total_score": eval_result.total_score})
    _trial_events.setdefault(trial_id, []).append(evt)

    return trial.evaluation


# ════════════════════════════════════════════════════════════
# A-10: SOP 萃取
# ════════════════════════════════════════════════════════════


@router.post("/{trial_id}/extract-sop")
async def extract_sop(trial_id: str, req: ExtractSopRequest = ExtractSopRequest()) -> Dict[str, Any]:
    """从最佳 Branch 提取关键路径作为 SOP 候选."""
    trial = _get_trial(trial_id)

    source_bid = req.source_branch_id
    if not source_bid and trial.evaluation:
        source_bid = trial.evaluation.get("best_branch_id") or (trial.branches[0] if trial.branches else None)

    if not source_bid:
        raise HTTPException(status_code=400, detail="No branch available for extraction")

    branch = _get_branch(source_bid)

    # S-01: 萃取条件检查
    best_reward = 0.0
    if branch.reward_curve:
        best_reward = max((p.get("reward", 0) for p in branch.reward_curve), default=0)

    baseline_reward = trial.best_score or 0.5  # 假设基线
    meets_threshold = best_reward > baseline_reward * 1.05 or best_reward > 0.4

    # S-02: 从最佳 Branch 提取动作序列
    steps_sequence = []
    try:
        orch = get_orchestrator()
        if branch.current_session_id:
            session = orch.get_session(branch.current_session_id)
            if session and session.steps:
                order = 0
                for step in session.steps:
                    for agent_id, action in step.agent_actions.items():
                        if not isinstance(action, dict):
                            continue
                        act_name = action.get("action", "idle")
                        if act_name in ("idle", "waiting"):
                            continue
                        skill = action.get("skill_used", "")
                        steps_sequence.append({
                            "order": order,
                            "agent_role": action.get("role", agent_id),
                            "action": act_name,
                            "precondition": f"Step {step.step_id} completed",
                            "expected_output": f"Reward contribution: {action.get('reward', 0)}",
                            "fallback": "Retry or delegate",
                            "skill_used": skill,
                        })
                        order += 1
    except Exception as e:
        logger.warning(f"SOP extract from session failed: {e}")

    # S-03: 生成结构化 SOP
    confidence = min(best_reward + 0.1, 1.0) if meets_threshold else max(best_reward, 0.1)
    sop = SOPCandidate(
        name=f"SOP-{branch.label}-{len(trial.extracted_sops)+1}" if meets_threshold else f"Draft-SOP-{branch.label}",
        confidence=round(confidence, 3),
        source_branch_id=source_bid,
        applicable_scenarios=[trial.scenario or trial.mode.value],
        steps_count=len(steps_sequence),
        steps=steps_sequence,
        status="validated" if meets_threshold else "candidate",
    )
    sop_dict = {
        "sop_id": sop.sop_id, "name": sop.name, "confidence": sop.confidence,
        "source_branch_id": sop.source_branch_id, "applicable_scenarios": sop.applicable_scenarios,
        "steps_count": sop.steps_count, "steps": sop.steps, "status": sop.status,
    }
    trial.extracted_sops.append(sop_dict)

    evt = TrialEvent(event_type=TrialEventType.SOP_EXTRACTED, trial_id=trial_id,
                     data=sop_dict)
    _trial_events.setdefault(trial_id, []).append(evt)

    return {"sops": [sop_dict], "meets_threshold": meets_threshold, "best_reward": round(best_reward, 4)}


# ════════════════════════════════════════════════════════════
# A-11: 反馈反哺
# ════════════════════════════════════════════════════════════


@router.post("/{trial_id}/feedback")
async def feedback_to_agents(trial_id: str, req: FeedbackRequest = FeedbackRequest()) -> Dict[str, Any]:
    """将 SOP/策略写回到 Agent 技能库或协作图."""
    trial = _get_trial(trial_id)

    sops_to_apply = req.sop_ids if req.sop_ids else [
        s["sop_id"] for s in trial.extracted_sops if s.get("status") == "validated"
    ]

    applied_sops = 0
    updated_agents: set = set()
    updated_skills: set = set()
    collaboration_edges_added: List[Dict[str, Any]] = []

    for sop_data in trial.extracted_sops:
        if sop_data.get("sop_id") not in sops_to_apply:
            continue
        sop_data["status"] = "applied"
        applied_sops += 1

        # R-02: 技能分数提升（模拟）
        for step in sop_data.get("steps", []):
            skill = step.get("skill_used", "")
            if skill:
                updated_skills.add(skill)
            agent_role = step.get("agent_role", "")
            if agent_role:
                updated_agents.add(agent_role)

        # R-03: 协作图边权重增加（模拟）
        agent_roles = list(set(s.get("agent_role", "") for s in sop_data.get("steps", []) if s.get("agent_role")))
        for i, r1 in enumerate(agent_roles):
            for r2 in agent_roles[i+1:]:
                collaboration_edges_added.append({"source": r1, "target": r2, "weight_boost": 0.1})

    trial.feedback_actions.append({
        "applied_sops": applied_sops,
        "updated_agents": list(updated_agents),
        "updated_skills": list(updated_skills),
        "edges_added": len(collaboration_edges_added),
        "timestamp": TrialEvent.__dataclass_fields__["timestamp"].default_factory(),  # type: ignore
    })

    evt = TrialEvent(event_type=TrialEventType.FEEDBACK_APPLIED, trial_id=trial_id,
                     data={"applied_sops": applied_sops, "agents": len(updated_agents)})
    _trial_events.setdefault(trial_id, []).append(evt)

    return {
        "applied_sops": applied_sops,
        "updated_agents": list(updated_agents),
        "updated_skills": list(updated_skills),
        "collaboration_edges_added": collaboration_edges_added,
    }


# ════════════════════════════════════════════════════════════
# A-12: SSE 事件流
# ════════════════════════════════════════════════════════════


@router.get("/{trial_id}/events/stream")
async def stream_trial_events(
    trial_id: str,
    request: Request,
    branch_id: Optional[str] = None,
    since_step: Optional[int] = None,
) -> StreamingResponse:
    """SSE 事件流 — 支持过滤和断线重连续传."""
    _get_trial(trial_id)

    async def event_generator():
        # 发送已有事件
        events = _trial_events.get(trial_id, [])
        for evt in events:
            if branch_id and evt.branch_id != branch_id:
                continue
            yield f"data: {json.dumps({'event_id': evt.event_id, 'type': evt.event_type.value,
                                           'branch_id': evt.branch_id, 'session_id': evt.session_id,
                                           'data': evt.data, 'timestamp': evt.timestamp})}\n\n"

        # 保持连接，等待新事件
        last_count = len(events)
        while True:
            if await request.is_disconnected():
                break
            current = _trial_events.get(trial_id, [])
            if len(current) > last_count:
                for evt in current[last_count:]:
                    if branch_id and evt.branch_id != branch_id:
                        continue
                    yield f"data: {json.dumps({'event_id': evt.event_id, 'type': evt.event_type.value,
                                               'branch_id': evt.branch_id, 'session_id': evt.session_id,
                                               'data': evt.data, 'timestamp': evt.timestamp})}\n\n"
                last_count = len(current)
            await asyncio.sleep(0.3)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


# ── 辅助接口：获取所有分支详情 ──


@router.get("/{trial_id}/branches")
async def list_trial_branches(trial_id: str) -> Dict[str, Any]:
    """列出 Trial 下所有 Branch 详情."""
    _get_trial(trial_id)
    result = []
    for bid in (_trials.get(trial_id, Trial()).branches or []):
        b = _branches.get(bid)
        if b:
            result.append({
                "id": b.id, "name": b.name, "label": b.label, "color": b.color,
                "status": b.status.value, "current_step": b.current_step,
                "final_score": b.final_score, "reward_curve": b.reward_curve,
                "session_count": len(b.sessions or []), "injected_events_count": len(b.injected_events),
                "parent_branch_id": b.parent_branch_id, "fork_at_step": b.fork_at_step,
            })
    return {"branches": result}
