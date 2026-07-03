# -*- coding: utf-8 -*-
"""Evolution Bridge — 演练数据驱动的技能进化编排器 (v4 C-3).

闭环: identify(弱skill识别) → reflect(失败反思) → mutate(变体生成)
     → ab_test(沙箱对照验证) → promote(门禁晋升写回)

胶水层设计: 连通既有模块 evolution/(mutator,fitness)、skill_evolver、
skill_library、twin_loop，本身不持有 LLM/存储实现。
全部外部依赖可注入，便于测试 mock。
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from .models import EvolutionRun, EvolutionRunStatus
from .proficiency_store import aggregate_usages, get_proficiency_store

logger = logging.getLogger(__name__)

# C-3.3: 每轮最多变体数
MAX_CANDIDATES = 4
# C-3.5: 晋升条件
PROMOTE_MIN_IMPROVEMENT = 0.05   # fitness 提升 >= 5%
PROMOTE_MAX_DIM_DROP = 0.10      # 任何单维不得低于基线 10% 以上
# C-3.1: 弱 skill 默认阈值
DEFAULT_WEAK_THRESHOLD = 0.6
# C-3.6: 默认进化预算 (token)
DEFAULT_BUDGET_TOKENS = 200_000


class EvolutionBridge:
    """进化运行编排器."""

    def __init__(
        self,
        proficiency_store=None,
        chat_harness=None,
        skill_library=None,
        skill_evolver=None,
        reflect_fn: Optional[Callable] = None,
        mutate_fn: Optional[Callable] = None,
        ab_runner: Optional[Callable] = None,
        budget_tokens: int = 0,
        event_callback: Optional[Callable] = None,
        persist_dir=None,
    ):
        self._persist_dir = persist_dir  # None → 默认 storage/evolution_runs
        self._prof_store = proficiency_store or get_proficiency_store()
        self._chat_harness = chat_harness
        self._skill_library = skill_library
        self._skill_evolver = skill_evolver
        self._reflect_fn = reflect_fn       # async (instructions, failures) -> reflection dict
        self._mutate_fn = mutate_fn         # async (instructions, reflection) -> [candidate dict]
        self._ab_runner = ab_runner         # async (run, candidate|None) -> {fitness, dims}
        self._budget_tokens = budget_tokens or self._load_budget()
        self._event_callback = event_callback  # (run, phase) -> None
        self._runs: Dict[str, EvolutionRun] = {}

    @staticmethod
    def _load_budget() -> int:
        """从 config/settings.json 读取 evolution_budget_tokens (C-3.6)."""
        try:
            import json
            from pathlib import Path
            p = Path(__file__).resolve().parents[3] / "config" / "settings.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            return int(data.get("evolution_budget_tokens", DEFAULT_BUDGET_TOKENS))
        except Exception:
            return DEFAULT_BUDGET_TOKENS

    # ── 查询 ──────────────────────────────────────────────

    def get_run(self, run_id: str) -> Optional[EvolutionRun]:
        return self._runs.get(run_id)

    def list_runs(self, team_id: str = "", scenario_id: str = "") -> List[EvolutionRun]:
        result = list(self._runs.values())
        if team_id:
            result = [r for r in result if r.team_id == team_id]
        if scenario_id:
            result = [r for r in result if r.scenario_id == scenario_id]
        return sorted(result, key=lambda r: r.created_at, reverse=True)

    # ── C-3.1: 弱 skill 识别 ──────────────────────────────

    def identify_weak_skills(
        self,
        team_id: str,
        scenario_id: str,
        trial_ids: List[str],
        skill_expectations: Optional[Dict[str, float]] = None,
        window: int = 5,
    ) -> List[Dict[str, Any]]:
        """聚合最近 window 个 trial 的 usage 记录，识别弱 skill.

        规则: 成功率 < 期望 (默认 0.6) 或 趋势连续 3 点下滑.
        输出含证据（失败记录样本）。
        """
        expectations = skill_expectations or {}
        all_usages: List[Dict[str, Any]] = []
        for tid in trial_ids[-window:]:
            all_usages.extend(self._prof_store.load_usages(tid))
        if not all_usages:
            return []

        weak: List[Dict[str, Any]] = []
        for stat in aggregate_usages(all_usages):
            skill = stat["skill_name"]
            threshold = float(expectations.get(skill, DEFAULT_WEAK_THRESHOLD))
            reasons = []
            if stat["success_rate"] < threshold:
                reasons.append(f"成功率 {stat['success_rate']:.0%} < 期望 {threshold:.0%}")
            # 趋势下滑检查（来自熟练度缓存）
            prof_data = self._prof_store.load_proficiency(team_id)
            for key, p in prof_data.items():
                if p.get("skill_name") == skill:
                    trend = p.get("trend", [])
                    if len(trend) >= 3 and trend[-1] < trend[-2] < trend[-3]:
                        reasons.append(f"趋势连续下滑 {trend[-3:]}")
                        break
            if reasons:
                weak.append({
                    "skill_name": skill,
                    "baseline_success_rate": stat["success_rate"],
                    "expected": threshold,
                    "total_uses": stat["total_uses"],
                    "reason": "; ".join(reasons),
                    "failure_samples": stat["failure_samples"],
                    "agents": stat["agents"],
                })
        return weak

    # ── 全流程编排 ────────────────────────────────────────

    async def start_run(
        self,
        team_id: str,
        scenario_id: str,
        trial_ids: List[str],
        skill_names: Optional[List[str]] = None,
        skill_expectations: Optional[Dict[str, float]] = None,
        baseline_trial_id: str = "",
        auto_apply: bool = False,
        triggered_by: str = "manual",
    ) -> EvolutionRun:
        """创建并执行一次进化运行（同步阶段推进，可由 API 包成后台任务）."""
        run = EvolutionRun(
            team_id=team_id, scenario_id=scenario_id,
            baseline_trial_id=baseline_trial_id or (trial_ids[-1] if trial_ids else ""),
            auto_apply=auto_apply, triggered_by=triggered_by,
        )
        self._runs[run.run_id] = run

        try:
            # Phase 1: identify
            self._phase(run, EvolutionRunStatus.IDENTIFYING)
            weak = self.identify_weak_skills(team_id, scenario_id, trial_ids, skill_expectations)
            if skill_names:
                weak = [w for w in weak if w["skill_name"] in skill_names]
                # 用户指定但未在弱名单 → 仍纳入（以当前统计为基线）
                known = {w["skill_name"] for w in weak}
                for name in skill_names:
                    if name not in known:
                        weak.append({"skill_name": name, "baseline_success_rate": 0.5,
                                     "expected": DEFAULT_WEAK_THRESHOLD, "total_uses": 0,
                                     "reason": "manual_selected", "failure_samples": [], "agents": []})
            if not weak:
                run.status = EvolutionRunStatus.REJECTED
                run.error = "no_weak_skills_identified"
                # C-2.1: 返回结构化原因, 区分"无usage数据"vs"有数据但都达标"
                _win = 5  # 默认窗口
                _scanned = trial_ids[-_win:]
                _usages_count = sum(len(self._prof_store.load_usages(t)) for t in _scanned)
                run.error_detail = {
                    "reason": "no_usage" if _usages_count == 0 else "all_meet",
                    "scanned_trials": len(_scanned),
                    "usages": _usages_count,
                }
                run.completed_at = self._now()
                return run
            # 每轮只针对最弱的 1 个 skill（控制成本）
            weak.sort(key=lambda w: w["baseline_success_rate"])
            run.target_skills = weak[:1]
            target = run.target_skills[0]

            # 取 skill 当前 instructions（快照供前端 diff 展示）
            instructions = self._get_skill_instructions(team_id, target["skill_name"])
            target["instructions_snapshot"] = instructions[:4000]

            # Phase 2: reflect
            self._phase(run, EvolutionRunStatus.REFLECTING)
            if not self._check_budget(run):
                return run
            reflection = await self._do_reflect(instructions, target["failure_samples"])
            run.reflection = reflection

            # Phase 3: mutate
            self._phase(run, EvolutionRunStatus.MUTATING)
            if not self._check_budget(run):
                return run
            candidates = await self._do_mutate(instructions, reflection)
            candidates = candidates[:MAX_CANDIDATES]
            if not candidates:
                run.status = EvolutionRunStatus.FAILED
                run.error = "no_candidates_generated"
                run.completed_at = self._now()
                return run
            run.candidates = candidates

            # Phase 4: A/B test
            self._phase(run, EvolutionRunStatus.AB_TESTING)
            if not self._check_budget(run):
                return run
            baseline_result = await self._do_ab(run, None)
            best = None
            best_fitness = -1.0
            for cand in run.candidates:
                result = await self._do_ab(run, cand)
                cand["fitness"] = result.get("fitness", 0.0)
                cand["dims"] = result.get("dims", {})
                cand["ab_trial_id"] = result.get("trial_id", "")
                if result.get("trial_id"):
                    run.ab_trial_ids.append(result["trial_id"])
                if cand["fitness"] > best_fitness:
                    best_fitness = cand["fitness"]
                    best = cand

            baseline_fitness = baseline_result.get("fitness", 0.0)
            baseline_dims = baseline_result.get("dims", {})
            if baseline_result.get("trial_id"):
                run.baseline_trial_id = baseline_result["trial_id"]

            # Phase 5: gate / promote (C-3.5)
            self._phase(run, EvolutionRunStatus.GATING)
            verdict = self._judge(best, best_fitness, baseline_fitness, baseline_dims)
            if not verdict["pass"]:
                run.status = EvolutionRunStatus.REJECTED
                run.error = verdict["reason"]
                run.completed_at = self._now()
                return run

            run.winner = {
                "skill_name": target["skill_name"],
                "strategy": best.get("strategy", ""),
                "instructions": best.get("instructions", ""),
                "fitness": best_fitness,
                "baseline_fitness": baseline_fitness,
                "baseline_dims": baseline_dims,
                "improvement": round(best_fitness - baseline_fitness, 4),
            }

            if auto_apply:
                applied = self.apply_winner(run)
                if not applied.get("ok"):
                    run.status = EvolutionRunStatus.FAILED
                    run.error = applied.get("error", "apply_failed")
                    run.completed_at = self._now()
                    return run
                run.status = EvolutionRunStatus.APPLIED
                run.completed_at = self._now()
            # auto_apply=False 时停在 GATING，等人工 approve (B-3.4)
            return run

        except Exception as e:
            logger.error(f"❌ EvolutionRun {run.run_id} 失败: {e}", exc_info=True)
            run.status = EvolutionRunStatus.FAILED
            run.error = str(e)
            run.completed_at = self._now()
            return run
        finally:
            self._persist_run(run)

    def approve(self, run_id: str) -> Dict[str, Any]:
        """人工批准晋升 (B-3.4)."""
        run = self._runs.get(run_id)
        if not run:
            return {"ok": False, "error": "run_not_found"}
        if run.status != EvolutionRunStatus.GATING or not run.winner:
            return {"ok": False, "error": f"invalid_status: {run.status.value}"}
        result = self.apply_winner(run)
        if result.get("ok"):
            run.status = EvolutionRunStatus.APPLIED
            run.completed_at = self._now()
            self._phase(run, EvolutionRunStatus.APPLIED)
        return result

    def reject(self, run_id: str, reason: str = "manual_reject") -> Dict[str, Any]:
        run = self._runs.get(run_id)
        if not run:
            return {"ok": False, "error": "run_not_found"}
        run.status = EvolutionRunStatus.REJECTED
        run.error = reason
        run.completed_at = self._now()
        self._phase(run, EvolutionRunStatus.REJECTED)
        return {"ok": True, "status": "rejected"}

    def apply_winner(self, run: EvolutionRun) -> Dict[str, Any]:
        """胜者写回: publish_gate → version_snapshot → apply_evolution (C-3.5)."""
        winner = run.winner or {}
        skill_name = winner.get("skill_name", "")
        new_instructions = winner.get("instructions", "")
        if not skill_name or not new_instructions:
            return {"ok": False, "error": "invalid_winner"}

        lib = self._get_skill_library()
        evolver = self._get_skill_evolver()
        if not lib or not evolver:
            return {"ok": False, "error": "skill_library_or_evolver_unavailable"}

        skill = self._find_skill_by_name(run.team_id, skill_name)
        if not skill:
            return {"ok": False, "error": f"skill_not_found: {skill_name}"}

        # 全局 G4-3: 棘轮门禁 — skill_effectiveness 推进失败则阻断写回
        try:
            from agents.ratchet_ledger import get_ratchet_ledger
            ratchet = get_ratchet_ledger().advance(
                f"skill_effectiveness:{skill_name}:{run.team_id}",
                float(winner.get("fitness", 0)),
                evidence={"run_id": run.run_id, "scenario_id": run.scenario_id},
            )
            winner["ratchet"] = ratchet
            if not ratchet.get("advanced") and not ratchet.get("held"):
                run.error = f"ratchet_blocked: {ratchet.get('reason')}"
                return {"ok": False, "error": run.error, "ratchet": ratchet}
        except ImportError:
            pass  # 账本模块不可用时不阻断（向后兼容）
        except Exception as e:
            logger.warning(f"棘轮门禁检查失败 (放行): {e}")

        # 发布门禁（gate 失败不阻断 team_local 写回，但记录在案）
        gate = {}
        try:
            gate = lib.evaluate_publish_gate(run.team_id, skill.skill_id)
        except Exception as e:
            gate = {"ok": False, "reason": f"gate_error: {e}"}

        try:
            lib.create_version_snapshot(
                skill,
                reason=f"evolution_run:{run.run_id}",
                metadata={"scenario_id": run.scenario_id,
                          "fitness": winner.get("fitness"),
                          "baseline_fitness": winner.get("baseline_fitness")},
            )
            result = evolver.apply_evolution(run.team_id, skill.skill_id, new_instructions)
            if result.get("error"):
                return {"ok": False, "error": result["error"]}
            winner["new_version"] = result.get("version")
            winner["gate"] = {"ok": gate.get("ok", False), "reason": gate.get("reason", "")}
            return {"ok": True, "skill_id": skill.skill_id,
                    "new_version": result.get("version"), "gate": winner["gate"]}
        except Exception as e:
            return {"ok": False, "error": f"apply_failed: {e}"}

    # ── 内部: 可注入依赖的默认实现 ─────────────────────────

    async def _do_reflect(self, instructions: str, failure_samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        if self._reflect_fn:
            return await self._reflect_fn(instructions, failure_samples)
        from agents.evolution.mutator import reflect_on_failures
        failures = [
            {"task_input": f.get("task_id", ""), "agent_output": f.get("failure_reason", ""),
             "rubric": "技能在演练中成功执行", "composite": 0.0, "reasoning": f.get("failure_reason", "")}
            for f in failure_samples
        ]
        rr = await reflect_on_failures(instructions, failures, chat_harness=self._chat_harness)
        self._track_cost(2000)
        return rr.to_dict() if hasattr(rr, "to_dict") else dict(rr.__dict__)

    async def _do_mutate(self, instructions: str, reflection: Dict[str, Any]) -> List[Dict[str, Any]]:
        if self._mutate_fn:
            return await self._mutate_fn(instructions, reflection)
        from agents.evolution.mutator import generate_candidates, ReflectionResult
        rr = ReflectionResult()
        rr.root_causes = reflection.get("root_causes", [])
        rr.specific_defects = reflection.get("specific_defects", [])
        rr.improvement_directions = reflection.get("improvement_directions", [])
        cands = await generate_candidates(instructions, rr, chat_harness=self._chat_harness)
        self._track_cost(3000 * max(len(cands), 1))
        return [{"strategy": c.strategy, "instructions": c.instructions} for c in cands]

    async def _do_ab(self, run: EvolutionRun, candidate: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """跑一次对照试炼。candidate=None 表示基线。

        默认实现需要 orchestrator 在运行时注入 (evolution_api 提供)，
        测试时通过 ab_runner 注入 mock。
        """
        if self._ab_runner:
            return await self._ab_runner(run, candidate)
        raise RuntimeError("ab_runner 未注入 — 需在 API 层提供沙箱对照执行器")

    def _judge(self, best: Optional[Dict[str, Any]], best_fitness: float,
               baseline_fitness: float, baseline_dims: Dict[str, float]) -> Dict[str, Any]:
        """晋升判定 (C-3.5): fitness 提升 >= 5% 且单维不低于基线 10% 以上."""
        if not best:
            return {"pass": False, "reason": "no_best_candidate"}
        if baseline_fitness > 0:
            improvement = (best_fitness - baseline_fitness) / baseline_fitness
        else:
            improvement = best_fitness - baseline_fitness
        if improvement < PROMOTE_MIN_IMPROVEMENT:
            return {"pass": False,
                    "reason": f"improvement {improvement:.1%} < {PROMOTE_MIN_IMPROVEMENT:.0%}"}
        best_dims = best.get("dims", {})
        for dim, base_val in (baseline_dims or {}).items():
            cand_val = best_dims.get(dim, 0.0)
            if base_val > 0 and (base_val - cand_val) / base_val > PROMOTE_MAX_DIM_DROP:
                return {"pass": False,
                        "reason": f"dimension {dim} dropped {(base_val-cand_val)/base_val:.1%} > {PROMOTE_MAX_DIM_DROP:.0%}"}
        return {"pass": True, "reason": ""}

    # ── 内部辅助 ──────────────────────────────────────────

    def _phase(self, run: EvolutionRun, status: EvolutionRunStatus) -> None:
        run.status = status
        if self._event_callback:
            try:
                self._event_callback(run, status.value)
            except Exception:
                pass
        self._persist_run(run)
        logger.info(f"🧬 EvolutionRun {run.run_id} → {status.value}")

    def _persist_run(self, run: EvolutionRun) -> None:
        """A-4.3: EvolutionRun 持久化到 storage/evolution_runs/."""
        try:
            import json
            from pathlib import Path
            d = Path(self._persist_dir) if self._persist_dir else (
                Path(__file__).resolve().parents[3] / "storage" / "evolution_runs")
            d.mkdir(parents=True, exist_ok=True)
            path = d / f"{run.run_id}.json"
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(run.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.rename(path)
        except Exception as e:
            logger.warning(f"EvolutionRun 持久化失败 (非致命): {e}")

    def _check_budget(self, run: EvolutionRun) -> bool:
        """成本闸门 (C-3.6)."""
        if run.cost_tokens > self._budget_tokens:
            run.status = EvolutionRunStatus.FAILED
            run.error = f"budget_exceeded: {run.cost_tokens} > {self._budget_tokens}"
            run.completed_at = self._now()
            logger.warning(f"💸 EvolutionRun {run.run_id} 超预算中止")
            return False
        return True

    def _track_cost(self, tokens: int) -> None:
        """LLM 调用计费（估算值，接入 cost_policy 记账）."""
        for run in self._runs.values():
            if run.status in (EvolutionRunStatus.REFLECTING, EvolutionRunStatus.MUTATING,
                              EvolutionRunStatus.AB_TESTING):
                run.cost_tokens += tokens
        try:
            from agents.cost_models import record_usage  # 若存在则真实记账
            record_usage(component="evolution_bridge", tokens=tokens)
        except Exception:
            pass

    def _get_skill_library(self):
        if self._skill_library:
            return self._skill_library
        try:
            from agents.skill_library import get_skill_library
            return get_skill_library()
        except Exception as e:
            logger.warning(f"skill_library 不可用: {e}")
            return None

    def _get_skill_evolver(self):
        if self._skill_evolver:
            return self._skill_evolver
        try:
            from agents.skill_evolver import get_skill_evolver
            return get_skill_evolver()
        except Exception as e:
            logger.warning(f"skill_evolver 不可用: {e}")
            return None

    def _find_skill_by_name(self, team_id: str, name: str):
        """按 skill_id 或 name 查找团队技能."""
        lib = self._get_skill_library()
        if not lib:
            return None
        skill = lib._find_skill(team_id, name)
        if skill:
            return skill
        try:
            for d in lib.browse(team_id=team_id):
                if d.get("name") == name or d.get("skill_id") == name or d.get("slug") == name:
                    return lib._find_skill(team_id, d.get("skill_id", ""))
        except Exception:
            pass
        return None

    def _get_skill_instructions(self, team_id: str, name: str) -> str:
        skill = self._find_skill_by_name(team_id, name)
        if skill and getattr(skill, "instructions", ""):
            return skill.instructions
        return f"技能 {name}: 按照团队规范执行该技能对应的任务。"

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()


# ── 全局单例 ───────────────────────────────────────────────

_bridge: Optional[EvolutionBridge] = None


def get_evolution_bridge() -> EvolutionBridge:
    global _bridge
    if _bridge is None:
        _bridge = EvolutionBridge()
    return _bridge


def reset_evolution_bridge(**kwargs) -> EvolutionBridge:
    global _bridge
    _bridge = EvolutionBridge(**kwargs)
    return _bridge
