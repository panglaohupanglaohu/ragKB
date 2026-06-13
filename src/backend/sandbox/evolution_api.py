# -*- coding: utf-8 -*-
"""Evolution API — 演练驱动技能进化 REST 接口 (v4 B-3)."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .evolution_bridge import EvolutionBridge, get_evolution_bridge
from .models import EvolutionRunStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/twin-evolution", tags=["twin-evolution"])

# run_id -> [事件 dict]，供 SSE
_run_events: Dict[str, List[Dict[str, Any]]] = {}
# run_id -> asyncio.Task
_run_tasks: Dict[str, asyncio.Task] = {}


class StartEvolutionRequest(BaseModel):
    team_id: str = "default"
    scenario_id: str = ""
    skill_ids: List[str] = Field(default_factory=list)
    baseline_trial_id: str = ""
    auto_apply: bool = False
    ab_max_steps: int = Field(default=60, ge=10, le=200)


def _emit(run, phase: str) -> None:
    _run_events.setdefault(run.run_id, []).append({
        "run_id": run.run_id, "phase": phase, "status": run.status.value,
        "timestamp": time.time(),
    })


async def _default_ab_runner(run, candidate: Optional[Dict[str, Any]], max_steps: int = 60) -> Dict[str, Any]:
    """默认 A/B 执行器: 同场景创建对照 Trial → 跑完 → 评估 (C-3.4).

    candidate=None 为基线分支。候选 instructions 通过 skill_overrides
    注入该 session（LLM 决策模式下生效；规则模式下提升熟练度判定概率）。
    
    同 run 内所有对照使用同一随机种子（run_id 哈希），保证可复现对比。
    """
    import random, hashlib

    # C-3.4: 确定性随机种子 — 同 run 的 baseline + candidates 共用
    seed_base = int(hashlib.md5(run.run_id.encode()).hexdigest()[:8], 16)
    seed = seed_base + (0 if candidate is None else hash(candidate.get("strategy", "")) % 1000)
    random.seed(seed)
    from .trial_api import create_trial, evaluate_trial, CreateTrialRequest
    from .api import get_orchestrator

    label = "baseline" if candidate is None else f"cand-{candidate.get('strategy', '?')}"
    created = await create_trial(CreateTrialRequest(
        team_id=run.team_id,
        scenario_id=run.scenario_id,
        task_goal={"name": f"AB-{run.run_id[:8]}-{label}"},
        mode="what_if",
        max_steps=max_steps,
        acceleration=100,
    ))
    trial_id = created["trial_id"]
    session_id = created.get("session_id")

    orch = get_orchestrator()
    if session_id:
        if candidate is not None and run.target_skills:
            skill_name = run.target_skills[0]["skill_name"]
            orch.twin_loop.set_skill_overrides(session_id, {skill_name: candidate.get("instructions", "")})
        try:
            await orch.run_full_pipeline(session_id)
        except Exception as e:
            logger.warning(f"A/B run_full_pipeline 失败 ({label}): {e}")

    evaluation = await evaluate_trial(trial_id)
    total = float(evaluation.get("total_score", 0))
    dims = {k: float(evaluation.get(k, 0)) for k in
            ("task_completion", "collaboration_efficiency", "resilience",
             "cost_efficiency", "extractability")}

    # 目标 skill 在该 trial 的成功率
    skill_rate = 0.5
    if run.target_skills:
        skill_name = run.target_skills[0]["skill_name"]
        for s in evaluation.get("skill_breakdown", []):
            if s.get("skill_name") == skill_name:
                skill_rate = float(s.get("success_rate", 0.5))
                break

    # 综合 fitness = 0.6*五维总分 + 0.4*skill 成功率
    fitness = round(0.6 * total + 0.4 * skill_rate, 6)
    return {"fitness": fitness, "dims": dims, "trial_id": trial_id,
            "total_score": total, "skill_success_rate": skill_rate}


def _trial_ids_for(team_id: str, scenario_id: str) -> List[str]:
    """按时间序返回该 team+scenario 的 trial id 列表."""
    try:
        from .trial_api import _trials
        trials = [t for t in _trials.values()
                  if t.team_id == team_id and (not scenario_id or getattr(t, "scenario_id", "") == scenario_id)]
        trials.sort(key=lambda t: t.created_at)
        return [t.id for t in trials]
    except Exception:
        return []


@router.post("/runs")
async def start_evolution_run(req: StartEvolutionRequest) -> Dict[str, Any]:
    """B-3.1: 创建进化运行（后台执行）."""
    bridge = get_evolution_bridge()
    bridge._event_callback = _emit  # 接入 SSE 事件

    async def runner(run_holder: Dict[str, Any]):
        ab = lambda run, cand: _default_ab_runner(run, cand, req.ab_max_steps)  # noqa: E731
        bridge._ab_runner = ab
        trial_ids = _trial_ids_for(req.team_id, req.scenario_id)
        expectations = None
        try:
            from .scenario_store import get_scenario_store
            spec = get_scenario_store().get(req.scenario_id) if req.scenario_id else None
            if spec:
                expectations = spec.rubric.skill_expectations
        except Exception:
            pass
        run = await bridge.start_run(
            team_id=req.team_id, scenario_id=req.scenario_id,
            trial_ids=trial_ids, skill_names=req.skill_ids or None,
            skill_expectations=expectations,
            baseline_trial_id=req.baseline_trial_id,
            auto_apply=req.auto_apply,
        )
        run_holder["run"] = run
        _emit(run, "done")

    # 先同步创建 run_id（identify 之前的占位通过 bridge.start_run 内部生成，
    # 这里直接启动后台任务并立即扫描新 run）
    holder: Dict[str, Any] = {}
    before = set(r.run_id for r in bridge.list_runs())
    task = asyncio.create_task(runner(holder))
    # 等待 run 注册（最多 2s）
    run_id = None
    for _ in range(40):
        await asyncio.sleep(0.05)
        new = [r for r in bridge.list_runs() if r.run_id not in before]
        if new:
            run_id = new[0].run_id
            break
        if task.done():
            break
    if run_id is None and holder.get("run"):
        run_id = holder["run"].run_id
    if run_id is None:
        raise HTTPException(status_code=500, detail="EvolutionRun 启动失败")
    _run_tasks[run_id] = task
    return {"run_id": run_id, "status": "started"}


@router.get("/runs")
async def list_evolution_runs(team_id: str = Query(default=""),
                              scenario_id: str = Query(default="")) -> Dict[str, Any]:
    """B-3.3: 历史列表."""
    bridge = get_evolution_bridge()
    return {"runs": [r.to_dict() for r in bridge.list_runs(team_id, scenario_id)]}


@router.get("/runs/{run_id}")
async def get_evolution_run(run_id: str) -> Dict[str, Any]:
    """B-3.2: 运行状态与各阶段产物."""
    run = get_evolution_bridge().get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"EvolutionRun {run_id} not found")
    return run.to_dict()


@router.post("/runs/{run_id}/approve")
async def approve_evolution_run(run_id: str) -> Dict[str, Any]:
    """B-3.4: 人工批准晋升."""
    result = get_evolution_bridge().approve(run_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/runs/{run_id}/reject")
async def reject_evolution_run(run_id: str) -> Dict[str, Any]:
    """B-3.4: 人工拒绝."""
    result = get_evolution_bridge().reject(run_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/runs/{run_id}/events/stream")
async def stream_evolution_events(run_id: str, request: Request) -> StreamingResponse:
    """B-3.5: SSE 进化事件流."""
    run = get_evolution_bridge().get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"EvolutionRun {run_id} not found")

    async def gen():
        sent = 0
        terminal = {EvolutionRunStatus.APPLIED, EvolutionRunStatus.REJECTED, EvolutionRunStatus.FAILED}
        for _ in range(1200):  # 最长 ~10 分钟
            if await request.is_disconnected():
                break
            events = _run_events.get(run_id, [])
            while sent < len(events):
                yield f"data: {json.dumps(events[sent], ensure_ascii=False)}\n\n"
                sent += 1
            current = get_evolution_bridge().get_run(run_id)
            if current and current.status in terminal:
                yield f"data: {json.dumps({'run_id': run_id, 'phase': 'terminal', 'status': current.status.value}, ensure_ascii=False)}\n\n"
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/proficiency")
async def query_proficiency(team_id: str = Query(default="default"),
                            scenario_category: str = Query(default="")) -> Dict[str, Any]:
    """B-3.6: 团队技能熟练度聚合查询（技能进化面板主数据源）."""
    from .proficiency_store import get_proficiency_store
    items = get_proficiency_store().query(team_id, scenario_category)
    return {"team_id": team_id, "proficiency": items, "total": len(items)}
