# -*- coding: utf-8 -*-
"""Skill × Twin A/B 全量对照评估.

把「赋予 skill / 抬熟练度 / 注入 instructions」在数字孪生场景中跑
baseline vs treatment，量化目标技能成功率增益。

设计参考 scripts/skill_closed_loop_demo.py（code_review_delivery 闭环），
对任意技能：解析 metadata.scenario + target_skill，或按 category 回退映射。
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_REPO = Path(__file__).resolve().parents[3]
_SCENARIO_DIR = _REPO / "config" / "scenarios"

# category / keyword → (scenario_id, target_skill, agents_map)
# agents_map: agent_id → skill list；target skill 必须挂在至少一个 agent 上
_CATEGORY_TWIN: Dict[str, Tuple[str, str, Dict[str, List[str]]]] = {
    "code_delivery": (
        "code_review_delivery",
        "code_review",
        {
            "dev1": ["coding", "testing"],
            "dev2": ["coding"],
            "rev1": ["code_review", "task_breakdown"],
            "tst1": ["testing"],
            "rel1": ["release_ops", "report_writing"],
        },
    ),
    "development": (
        "code_review_delivery",
        "code_review",
        {
            "dev1": ["coding", "testing"],
            "dev2": ["coding"],
            "rev1": ["code_review", "task_breakdown"],
            "tst1": ["testing"],
            "rel1": ["release_ops", "report_writing"],
        },
    ),
    "incident": (
        "capacity_incident",
        "capacity_planning",
        {
            "cmd1": ["incident_command", "communication"],
            "sre1": ["capacity_planning", "scaling"],
            "sre2": ["monitoring", "root_cause"],
            "dev1": ["coding", "rollback"],
        },
    ),
    "automation": (
        "capacity_incident",
        "scaling",
        {
            "cmd1": ["incident_command", "communication"],
            "sre1": ["capacity_planning", "scaling"],
            "sre2": ["monitoring", "root_cause"],
            "dev1": ["coding", "rollback"],
        },
    ),
    "testing": (
        "code_review_delivery",
        "testing",
        {
            "dev1": ["coding", "testing"],
            "dev2": ["coding"],
            "rev1": ["code_review", "task_breakdown"],
            "tst1": ["testing"],
            "rel1": ["release_ops", "report_writing"],
        },
    ),
}

_BASE_PROF = 0.6
_DEFAULT_BASELINE = 0.45
_DEFAULT_TREATMENT = 0.85
_DEFAULT_SEEDS = int(os.environ.get("AG_SKILL_TWIN_AB_SEEDS", "5") or "5")
_GAIN_THRESHOLD = float(os.environ.get("AG_SKILL_TWIN_AB_GAIN", "0.05") or "0.05")
_MAX_STEPS_CAP = int(os.environ.get("AG_SKILL_TWIN_AB_MAX_STEPS", "100") or "100")


def _default_n_seeds() -> int:
    n = _DEFAULT_SEEDS
    return max(1, min(30, n))


def resolve_twin_binding(
    skill: Any,
    *,
    skill_library=None,
    team_id: str = "",
) -> Dict[str, Any]:
    """Resolve scenario_id + target_skill + agents from skill metadata / category."""
    meta: Dict[str, Any] = {}
    # SkillDefinition.config may hold metadata
    cfg = getattr(skill, "config", None) or {}
    if isinstance(cfg, dict):
        meta.update(cfg.get("metadata") or {})
        for k in ("target_skill", "scenario", "closed_loop_demo"):
            if cfg.get(k) and k not in meta:
                meta[k] = cfg[k]
    # SkillStore snapshot.metadata
    if skill_library is not None:
        store = getattr(skill_library, "_skill_store", None)
        sid = getattr(skill, "skill_id", "") or ""
        if store and sid:
            try:
                rec = store.get(sid)
                snap = getattr(rec, "snapshot", None) if rec else None
                sm = getattr(snap, "metadata", None) if snap else None
                if isinstance(sm, dict):
                    for k, v in sm.items():
                        meta.setdefault(k, v)
            except Exception:
                pass

    cat = getattr(skill, "category", None)
    cat_s = (cat.value if hasattr(cat, "value") else str(cat or "general")).lower()

    scenario_id = str(meta.get("scenario") or "").strip()
    target = str(meta.get("target_skill") or "").strip()
    agents: Optional[Dict[str, List[str]]] = None

    if cat_s in _CATEGORY_TWIN:
        sc, tg, ag = _CATEGORY_TWIN[cat_s]
        scenario_id = scenario_id or sc
        target = target or tg
        agents = ag
    elif not scenario_id:
        # keyword fallback from name/slug
        text = f"{getattr(skill, 'name', '')} {getattr(skill, 'slug', '')} {getattr(skill, 'description', '')}".lower()
        if any(k in text for k in ("review", "评审", "code")):
            scenario_id, target, agents = _CATEGORY_TWIN["code_delivery"]
            target = target or "code_review"
        elif any(k in text for k in ("incident", "容量", "扩容", "sre")):
            scenario_id, target, agents = _CATEGORY_TWIN["incident"]

    # metadata-only scenario: pick agents from known map by scenario_id
    if agents is None and scenario_id:
        for sc, tg, ag in _CATEGORY_TWIN.values():
            if sc == scenario_id:
                agents = ag
                target = target or tg
                break

    if not scenario_id or not target:
        return {
            "ok": False,
            "reason": "no_scenario_binding",
            "detail": f"无法为 category={cat_s} 解析孪生场景/target_skill；可在 skill metadata 写 scenario+target_skill",
            "metadata": meta,
            "category": cat_s,
        }

    if agents is None:
        # generic single-focus team: one specialist holds target skill
        agents = {
            "a1": [target, "communication"],
            "a2": ["coding", "testing"],
            "a3": ["monitoring"],
        }

    path = _SCENARIO_DIR / f"{scenario_id}.json"
    if not path.is_file():
        return {
            "ok": False,
            "reason": "scenario_file_missing",
            "detail": f"场景文件不存在: {path}",
            "scenario_id": scenario_id,
            "target_skill": target,
        }

    return {
        "ok": True,
        "scenario_id": scenario_id,
        "target_skill": target,
        "agents": agents,
        "metadata": meta,
        "category": cat_s,
        "scenario_path": str(path),
    }


def _run_once(
    *,
    compiled: Dict[str, Any],
    spec: Any,
    agents: Dict[str, List[str]],
    target_skill: str,
    target_prof: float,
    seed: int,
    instructions_override: str = "",
    max_steps: int = 100,
) -> Dict[str, Any]:
    from sandbox.scenario_compiler import build_chaos_timeline
    from sandbox.twin_loop import TwinLoopEngine
    from sandbox.memory_system import MemoryPool
    from sandbox.world_state import WorldStateManager
    from sandbox.models import SimulationMode

    random.seed(seed)
    ws = WorldStateManager()
    for aid, skills in agents.items():
        ws.sync_agent_state(
            aid,
            {"role": "dev", "state": "idle", "skills": list(skills), "tools": []},
        )
    ws.sync_tasks(compiled.get("pending_tasks") or [])
    if compiled.get("room_stages"):
        ws.set_room_stages(compiled["room_stages"])
    if compiled.get("resources"):
        ws.sync_resources(compiled["resources"])
    if compiled.get("constraints"):
        ws.sync_constraints(compiled["constraints"])

    eng = TwinLoopEngine(ws, MemoryPool())
    steps = min(int(getattr(spec, "recommended_max_steps", None) or max_steps), max_steps)
    sess = eng.create_session(
        team_id="skill_verify_ab",
        mode=SimulationMode.WHAT_IF,
        max_steps=steps,
        speed_factor=1e4,
    )
    eng.set_chaos_timeline(sess.session_id, build_chaos_timeline(spec))

    priors: Dict[str, Dict[str, float]] = {}
    for aid, skills in agents.items():
        priors[aid] = {s: _BASE_PROF for s in skills}
        if target_skill in skills:
            priors[aid][target_skill] = float(target_prof)
    eng.set_proficiency_priors(sess.session_id, priors)

    if instructions_override and target_prof >= 0.7:
        eng.set_skill_overrides(sess.session_id, {target_skill: instructions_override})

    asyncio.get_event_loop() if False else None  # quiet linters
    # run_simulation is async
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # nested: use new loop in thread-less path — create task via asyncio.run not available
            # Caller's verify is async so we use a helper
            raise RuntimeError("use_async_runner")
    except RuntimeError:
        pass

    # sync entry via asyncio.run when no running loop
    async def _go():
        await eng.run_simulation(sess.session_id)
        return eng.drain_usage_records(sess.session_id)

    try:
        recs = asyncio.run(_go())
    except RuntimeError:
        # already in event loop — schedule on a fresh loop via nest workaround
        new_loop = asyncio.new_event_loop()
        try:
            recs = new_loop.run_until_complete(_go())
        finally:
            new_loop.close()

    target_recs = [r for r in recs if getattr(r, "skill_name", "") == target_skill]
    t_ok = sum(1 for r in target_recs if getattr(r, "outcome", "") == "success")
    all_ok = sum(1 for r in recs if getattr(r, "outcome", "") == "success")
    total_reward = sum(getattr(st, "global_reward", 0) or 0 for st in (sess.steps or []))
    return {
        "target_uses": len(target_recs),
        "target_ok": t_ok,
        "all_uses": len(recs),
        "all_ok": all_ok,
        "total_reward": float(total_reward),
    }


async def _run_once_async(
    *,
    compiled: Dict[str, Any],
    spec: Any,
    agents: Dict[str, List[str]],
    target_skill: str,
    target_prof: float,
    seed: int,
    instructions_override: str = "",
    max_steps: int = 100,
) -> Dict[str, Any]:
    from sandbox.scenario_compiler import build_chaos_timeline
    from sandbox.twin_loop import TwinLoopEngine
    from sandbox.memory_system import MemoryPool
    from sandbox.world_state import WorldStateManager
    from sandbox.models import SimulationMode

    random.seed(seed)
    ws = WorldStateManager()
    for aid, skills in agents.items():
        ws.sync_agent_state(
            aid,
            {"role": "dev", "state": "idle", "skills": list(skills), "tools": []},
        )
    ws.sync_tasks(compiled.get("pending_tasks") or [])
    if compiled.get("room_stages"):
        ws.set_room_stages(compiled["room_stages"])
    if compiled.get("resources"):
        ws.sync_resources(compiled["resources"])
    if compiled.get("constraints"):
        ws.sync_constraints(compiled["constraints"])

    eng = TwinLoopEngine(ws, MemoryPool())
    steps = min(int(getattr(spec, "recommended_max_steps", None) or max_steps), max_steps)
    sess = eng.create_session(
        team_id="skill_verify_ab",
        mode=SimulationMode.WHAT_IF,
        max_steps=steps,
        speed_factor=1e4,
    )
    eng.set_chaos_timeline(sess.session_id, build_chaos_timeline(spec))

    priors: Dict[str, Dict[str, float]] = {}
    for aid, skills in agents.items():
        priors[aid] = {s: _BASE_PROF for s in skills}
        if target_skill in skills:
            priors[aid][target_skill] = float(target_prof)
    eng.set_proficiency_priors(sess.session_id, priors)

    if instructions_override and target_prof >= 0.7:
        eng.set_skill_overrides(sess.session_id, {target_skill: instructions_override})

    await eng.run_simulation(sess.session_id)
    recs = eng.drain_usage_records(sess.session_id)

    target_recs = [r for r in recs if getattr(r, "skill_name", "") == target_skill]
    t_ok = sum(1 for r in target_recs if getattr(r, "outcome", "") == "success")
    all_ok = sum(1 for r in recs if getattr(r, "outcome", "") == "success")
    total_reward = sum(getattr(st, "global_reward", 0) or 0 for st in (sess.steps or []))
    return {
        "target_uses": len(target_recs),
        "target_ok": t_ok,
        "all_uses": len(recs),
        "all_ok": all_ok,
        "total_reward": float(total_reward),
    }


def _agg(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    tu = sum(r["target_uses"] for r in runs)
    to = sum(r["target_ok"] for r in runs)
    au = sum(r["all_uses"] for r in runs)
    ao = sum(r["all_ok"] for r in runs)
    return {
        "target_rate": (to / tu) if tu else 0.0,
        "all_rate": (ao / au) if au else 0.0,
        "mean_reward": statistics.mean(r["total_reward"] for r in runs) if runs else 0.0,
        "target_uses": tu,
        "target_ok": to,
        "all_uses": au,
        "all_ok": ao,
        "n_runs": len(runs),
    }


async def run_skill_twin_ab(
    skill: Any,
    *,
    skill_library=None,
    team_id: str = "",
    n_seeds: Optional[int] = None,
    baseline_prof: float = _DEFAULT_BASELINE,
    treatment_prof: float = _DEFAULT_TREATMENT,
    max_steps: Optional[int] = None,
) -> Dict[str, Any]:
    """Full twin A/B for a skill. Returns report dict (never raises for soft skip)."""
    binding = resolve_twin_binding(skill, skill_library=skill_library, team_id=team_id)
    if not binding.get("ok"):
        return {
            "status": "skipped",
            "skipped": True,
            "reason": binding.get("reason"),
            "detail": binding.get("detail"),
            "passed": None,
        }

    scenario_id = binding["scenario_id"]
    target = binding["target_skill"]
    agents = binding["agents"]
    path = Path(binding["scenario_path"])
    seeds_n = max(1, min(30, int(n_seeds if n_seeds is not None else _default_n_seeds())))
    steps_cap = max(20, min(200, int(max_steps if max_steps is not None else _MAX_STEPS_CAP)))

    try:
        from sandbox.scenario_compiler import compile_scenario
        from sandbox.scenario_models import ScenarioSpec

        spec = ScenarioSpec.from_dict(json.loads(path.read_text(encoding="utf-8")))
        compiled = compile_scenario(spec, {})
    except Exception as e:
        logger.warning("twin ab load scenario failed: %s", e)
        return {
            "status": "error",
            "skipped": False,
            "passed": False,
            "error": f"scenario_load_failed: {e}",
            "scenario_id": scenario_id,
            "target_skill": target,
        }

    instructions = (getattr(skill, "instructions", None) or "").strip()
    seeds = list(range(1, seeds_n + 1))

    try:
        base_runs = []
        treat_runs = []
        for s in seeds:
            base_runs.append(await _run_once_async(
                compiled=compiled,
                spec=spec,
                agents=agents,
                target_skill=target,
                target_prof=baseline_prof,
                seed=s,
                instructions_override="",
                max_steps=steps_cap,
            ))
            treat_runs.append(await _run_once_async(
                compiled=compiled,
                spec=spec,
                agents=agents,
                target_skill=target,
                target_prof=treatment_prof,
                seed=s + 1000,  # independent stream
                instructions_override=instructions,
                max_steps=steps_cap,
            ))
        baseline = _agg(base_runs)
        treatment = _agg(treat_runs)
    except Exception as e:
        logger.exception("twin ab run failed")
        return {
            "status": "error",
            "skipped": False,
            "passed": False,
            "error": f"twin_run_failed: {type(e).__name__}: {e}",
            "scenario_id": scenario_id,
            "target_skill": target,
        }

    gain = treatment["target_rate"] - baseline["target_rate"]
    all_gain = treatment["all_rate"] - baseline["all_rate"]
    exercised = int(treatment["target_uses"] or 0) > 0
    if not exercised:
        return {
            "status": "skipped",
            "skipped": True,
            "reason": "target_skill_not_exercised",
            "detail": (
                f"场景 {scenario_id} 未产生 target_skill={target} 的 usage 记录；"
                "请在 skill metadata 指定匹配场景，或换 code_delivery 类技能验证闭环"
            ),
            "passed": None,
            "scenario_id": scenario_id,
            "target_skill": target,
            "baseline": baseline,
            "treatment": treatment,
            "n_seeds": seeds_n,
        }

    passed = gain >= _GAIN_THRESHOLD and exercised

    return {
        "status": "ok",
        "skipped": False,
        "passed": passed,
        "scenario_id": scenario_id,
        "target_skill": target,
        "n_seeds": seeds_n,
        "max_steps": steps_cap,
        "baseline_prof": baseline_prof,
        "treatment_prof": treatment_prof,
        "gain_threshold": _GAIN_THRESHOLD,
        "target_gain": round(gain, 4),
        "target_gain_pp": round(gain * 100, 2),
        "all_gain": round(all_gain, 4),
        "all_gain_pp": round(all_gain * 100, 2),
        "baseline": baseline,
        "treatment": treatment,
        "criteria": (
            f"treatment.{target}_rate - baseline >= {_GAIN_THRESHOLD} "
            f"(got {gain:.3f}, uses={treatment['target_uses']})"
        ),
        "instructions_injected": bool(instructions),
    }


def twin_ab_to_checks(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert twin A/B report into verifier check rows."""
    checks: List[Dict[str, Any]] = []
    if report.get("skipped"):
        checks.append({
            "name": "twin_ab_binding",
            "passed": True,
            "message": f"skipped: {report.get('reason')} — {report.get('detail', '')}",
            "source": "twin_ab",
            "layer": "twin-ab",
            "required": False,
            "hard_fail": False,
        })
        return checks

    if report.get("status") == "error":
        checks.append({
            "name": "twin_ab_run",
            "passed": False,
            "message": report.get("error") or "twin ab error",
            "source": "twin_ab",
            "layer": "twin-ab",
            "required": True,
            "hard_fail": False,
        })
        return checks

    b = report.get("baseline") or {}
    t = report.get("treatment") or {}
    checks.append({
        "name": "twin_ab_ran",
        "passed": True,
        "message": (
            f"scenario={report.get('scenario_id')} target={report.get('target_skill')} "
            f"seeds={report.get('n_seeds')}"
        ),
        "source": "twin_ab",
        "layer": "twin-ab",
        "required": True,
        "hard_fail": False,
    })
    checks.append({
        "name": "twin_ab_target_uses",
        "passed": int(t.get("target_uses") or 0) > 0,
        "message": f"treatment target uses={t.get('target_uses')} baseline uses={b.get('target_uses')}",
        "source": "twin_ab",
        "layer": "twin-ab",
        "required": True,
        "hard_fail": False,
    })
    checks.append({
        "name": "twin_ab_target_gain",
        "passed": bool(report.get("passed")),
        "message": (
            f"baseline={b.get('target_rate', 0):.1%} → treatment={t.get('target_rate', 0):.1%} "
            f"(+{report.get('target_gain_pp', 0)}pp, need ≥{float(report.get('gain_threshold', 0.05))*100:.0f}pp)"
        ),
        "source": "twin_ab",
        "layer": "twin-ab",
        "required": True,
        "hard_fail": False,
    })
    checks.append({
        "name": "twin_ab_team_all_rate",
        "passed": float(t.get("all_rate") or 0) >= float(b.get("all_rate") or 0) - 0.02,
        "message": (
            f"team success baseline={b.get('all_rate', 0):.1%} "
            f"treatment={t.get('all_rate', 0):.1%} ({report.get('all_gain_pp', 0):+.1f}pp)"
        ),
        "source": "twin_ab",
        "layer": "twin-ab",
        "required": False,
        "hard_fail": False,
    })
    return checks
