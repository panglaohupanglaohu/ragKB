# -*- coding: utf-8 -*-
"""主优化循环 — 照搬 Hermes Optimization Loop.

SELECT TARGET → BUILD EVAL DATASET → WRAP MODULE →
RUN OPTIMIZER (反思式) → EVALUATE & COMPARE → DEPLOY (ratchet)
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from .constraints import validate_all
from .dataset_builder import EvalDataset, build_full_dataset
from .fitness import SkillFitnessReport, apply_length_penalty, evaluate_skill
from .mutator import (
    MutationCandidate,
    ReflectionResult,
    generate_candidates,
    reflect_on_failures,
)

logger = logging.getLogger("evolution.optimizer")

RUNS_DIR = Path(__file__).resolve().parents[3] / "storage" / "evolution_runs"


class OptimizationRun:
    """一次完整的优化运行记录."""

    def __init__(self, target_type: str, target_id: str, team_id: str = ""):
        self.run_id = str(uuid4())[:12]
        self.target_type = target_type  # skill, rule, prompt
        self.target_id = target_id
        self.team_id = team_id
        self.status = "running"  # running, completed, failed
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.completed_at: Optional[str] = None

        # Config
        self.iterations: int = 5
        self.strategies: List[str] = []

        # Results
        self.baseline_score: float = 0.0
        self.best_score: float = 0.0
        self.score_delta: float = 0.0
        self.original_instructions: str = ""
        self.best_instructions: str = ""
        self.iteration_log: List[Dict[str, Any]] = []
        self.reflection_log: List[Dict[str, Any]] = []
        self.dataset_id: str = ""
        self.dataset_size: int = 0

    @property
    def improved(self) -> bool:
        return self.score_delta > 0.05  # At least 5% improvement

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "team_id": self.team_id,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "iterations_planned": self.iterations,
            "iterations_completed": len(self.iteration_log),
            "baseline_score": round(self.baseline_score, 3),
            "best_score": round(self.best_score, 3),
            "score_delta": round(self.score_delta, 3),
            "improved": self.improved,
            "original_instructions": self.original_instructions,
            "best_instructions": self.best_instructions,
            "iteration_log": self.iteration_log,
            "reflection_log": self.reflection_log,
            "dataset_id": self.dataset_id,
            "dataset_size": self.dataset_size,
        }

    def save(self):
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        fp = RUNS_DIR / f"{self.run_id}.json"
        fp.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2))

    @classmethod
    def load(cls, run_id: str) -> Optional["OptimizationRun"]:
        fp = RUNS_DIR / f"{run_id}.json"
        if not fp.exists():
            return None
        data = json.loads(fp.read_text())
        run = cls(data["target_type"], data["target_id"], data.get("team_id", ""))
        run.run_id = data["run_id"]
        run.status = data["status"]
        run.started_at = data["started_at"]
        run.completed_at = data.get("completed_at")
        run.iterations = data.get("iterations_planned", 5)
        run.baseline_score = data.get("baseline_score", 0)
        run.best_score = data.get("best_score", 0)
        run.score_delta = data.get("score_delta", 0)
        run.original_instructions = data.get("original_instructions", "")
        run.best_instructions = data.get("best_instructions", "")
        run.iteration_log = data.get("iteration_log", [])
        run.reflection_log = data.get("reflection_log", [])
        run.dataset_id = data.get("dataset_id", "")
        run.dataset_size = data.get("dataset_size", 0)
        return run


async def optimize_skill(
    team_id: str,
    skill_id: str,
    skill_name: str,
    instructions: str,
    tags: List[str],
    iterations: int = 5,
    on_progress: Optional[Callable] = None,
    chat_harness=None,
) -> OptimizationRun:
    """主优化循环 — 照搬 Hermes Optimization Loop.

    1. Build eval dataset
    2. Evaluate baseline
    3. For each iteration:
       a. Find failures
       b. Reflect on failures (GEPA-style)
       c. Generate mutation candidates
       d. Evaluate candidates
       e. Keep best if passes constraints
    4. Return result
    """
    run = OptimizationRun(target_type="skill", target_id=skill_id, team_id=team_id)
    run.iterations = iterations
    run.original_instructions = instructions

    def _emit(event: str, data: Dict = None):
        if on_progress:
            on_progress({"event": event, "run_id": run.run_id, **(data or {})})

    try:
        # ── Step 1: Build evaluation dataset ──
        _emit("building_dataset")
        dataset = await build_full_dataset(
            skill_name=skill_name,
            skill_id=skill_id,
            instructions=instructions,
            tags=tags,
            synthetic_count=12,
            chat_harness=chat_harness,
        )
        run.dataset_id = dataset.id
        run.dataset_size = len(dataset.examples)

        if len(dataset.train) < 3:
            run.status = "failed"
            run.iteration_log.append({"error": "评估数据集过小 (< 3 examples)"})
            run.save()
            return run

        # Save dataset
        dataset.save("skills")
        _emit("dataset_ready", {"size": len(dataset.examples)})

        # ── Step 2: Evaluate baseline ──
        _emit("evaluating_baseline")
        baseline_report = await evaluate_skill(
            skill_id=skill_id,
            skill_name=skill_name,
            instructions=instructions,
            eval_examples=dataset.val,  # Evaluate on validation set
            chat_harness=chat_harness,
        )
        run.baseline_score = baseline_report.mean_composite
        run.best_score = run.baseline_score
        run.best_instructions = instructions
        _emit("baseline_evaluated", {"score": run.baseline_score})

        # ── Step 3: Iterative optimization ──
        current_best = instructions
        current_score = run.baseline_score
        current_failures = baseline_report.failures

        for iteration in range(iterations):
            _emit("iteration_start", {"iteration": iteration + 1, "current_score": current_score})

            # 3a. Reflect on failures
            if not current_failures:
                # If no failures on val, try on train for more signal
                train_report = await evaluate_skill(
                    skill_id, skill_name, current_best, dataset.train, chat_harness
                )
                current_failures = train_report.failures

            if not current_failures:
                # Perfect score — no room for improvement
                run.iteration_log.append({
                    "iteration": iteration + 1,
                    "action": "stopped",
                    "reason": "no_failures_to_fix",
                    "score": current_score,
                })
                break

            # 3b. Reflect (GEPA-style reflective analysis)
            reflection = await reflect_on_failures(current_best, current_failures, chat_harness)
            run.reflection_log.append({
                "iteration": iteration + 1,
                "root_causes": reflection.root_causes,
                "defects": reflection.specific_defects,
                "directions": reflection.improvement_directions,
            })
            _emit("reflected", {
                "iteration": iteration + 1,
                "root_causes": reflection.root_causes,
            })

            # 3c. Generate mutation candidates
            candidates = await generate_candidates(current_best, reflection, chat_harness=chat_harness)

            if not candidates:
                run.iteration_log.append({
                    "iteration": iteration + 1,
                    "action": "no_candidates",
                    "score": current_score,
                })
                continue

            # 3d. Evaluate candidates
            iter_result = {
                "iteration": iteration + 1,
                "candidates_generated": len(candidates),
                "candidates_evaluated": [],
                "best_candidate": None,
                "score_before": current_score,
                "score_after": current_score,
            }

            for candidate in candidates:
                # Constraint check
                cv = validate_all(instructions, candidate.instructions, "skill")
                if not cv["passed"]:
                    candidate.constraint_passed = False
                    candidate.constraint_violations = cv["violations"]
                    iter_result["candidates_evaluated"].append({
                        "strategy": candidate.strategy,
                        "passed_constraints": False,
                        "violations": cv["violations"],
                    })
                    continue

                # Evaluate on validation set
                cand_report = await evaluate_skill(
                    skill_id, skill_name, candidate.instructions,
                    dataset.val, chat_harness
                )
                # Apply length penalty
                cand_score = apply_length_penalty(
                    cand_report.mean_composite,
                    len(instructions),
                    len(candidate.instructions),
                )
                candidate.score = cand_score

                iter_result["candidates_evaluated"].append({
                    "strategy": candidate.strategy,
                    "passed_constraints": True,
                    "score": round(cand_score, 3),
                    "improvement": round(cand_score - current_score, 3),
                })

                # 3e. Keep best
                if cand_score > current_score:
                    current_best = candidate.instructions
                    current_score = cand_score
                    iter_result["best_candidate"] = candidate.strategy
                    iter_result["score_after"] = round(cand_score, 3)

                    # Re-evaluate failures for next iteration
                    current_failures = cand_report.failures

            run.iteration_log.append(iter_result)
            _emit("iteration_done", {
                "iteration": iteration + 1,
                "score": current_score,
                "improved": current_score > run.best_score,
            })

            # Update best
            if current_score > run.best_score:
                run.best_score = current_score
                run.best_instructions = current_best

        # ── Step 4: Final evaluation on holdout ──
        if run.best_instructions != instructions and dataset.holdout:
            _emit("holdout_evaluation")
            holdout_report = await evaluate_skill(
                skill_id, skill_name, run.best_instructions,
                dataset.holdout, chat_harness
            )
            # Update best_score to holdout score (more reliable)
            run.best_score = holdout_report.mean_composite

        run.score_delta = run.best_score - run.baseline_score
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc).isoformat()
        _emit("completed", {
            "baseline": run.baseline_score,
            "best": run.best_score,
            "delta": run.score_delta,
            "improved": run.improved,
        })

    except Exception as e:
        logger.exception("Optimization run failed: %s", e)
        run.status = "failed"
        run.iteration_log.append({"error": str(e)})
        _emit("error", {"message": str(e)})

    run.save()
    return run


# ── Convenience: optimize rule descriptions (Phase 2) ────────────

async def optimize_rule_description(
    rule_id: str,
    current_title: str,
    current_description: str,
    iterations: int = 3,
    on_progress: Optional[Callable] = None,
    chat_harness=None,
) -> OptimizationRun:
    """Phase 2: 优化审查规则描述."""
    # Treat title + description as "instructions" for the optimization loop
    combined = f"标题: {current_title}\n描述: {current_description}"
    run = await optimize_skill(
        team_id="__rules__",
        skill_id=rule_id,
        skill_name=f"Rule: {rule_id}",
        instructions=combined,
        tags=["audit_rule", rule_id],
        iterations=iterations,
        on_progress=on_progress,
        chat_harness=chat_harness,
    )
    run.target_type = "rule"
    run.save()
    return run


# ── Convenience: optimize prompt section (Phase 3) ───────────────

async def optimize_prompt_section(
    section_name: str,
    current_content: str,
    team_id: str = "",
    iterations: int = 3,
    on_progress: Optional[Callable] = None,
    chat_harness=None,
) -> OptimizationRun:
    """Phase 3: 优化系统提示词段落."""
    run = await optimize_skill(
        team_id=team_id or "__prompts__",
        skill_id=section_name,
        skill_name=f"Prompt: {section_name}",
        instructions=current_content,
        tags=["system_prompt", section_name],
        iterations=iterations,
        on_progress=on_progress,
        chat_harness=chat_harness,
    )
    run.target_type = "prompt"
    run.save()
    return run


# ── List runs ────────────────────────────────────────────────────

def list_runs(target_type: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """列出优化运行记录."""
    if not RUNS_DIR.exists():
        return []
    runs = []
    for fp in sorted(RUNS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(fp.read_text())
            if target_type and data.get("target_type") != target_type:
                continue
            # Return summary only
            runs.append({
                "run_id": data["run_id"],
                "target_type": data["target_type"],
                "target_id": data["target_id"],
                "team_id": data.get("team_id", ""),
                "status": data["status"],
                "started_at": data["started_at"],
                "baseline_score": data.get("baseline_score", 0),
                "best_score": data.get("best_score", 0),
                "score_delta": data.get("score_delta", 0),
                "improved": data.get("improved", False),
            })
        except (json.JSONDecodeError, OSError):
            continue
        if len(runs) >= limit:
            break
    return runs
