# -*- coding: utf-8 -*-
"""M4 竞标编排器 — 同一计划多候选组合竞标演练 (G4).

按 plan.md §4.5 规格:
  - C0 基线 + 单算子变异 R1~R5
  - 每候选跑试炼 → (成功率, 质量, token)
  - 评分: 质量达标(≥90%) ∧ token 最省者居首
  - ratchet: 胜者写 scenario_best:<task_type>:<candidate_hash>

无跨层耦合: 只依赖 scenario_models / ratchet_ledger / token_ledger.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from agents.ratchet_ledger import get_ratchet_ledger

logger = logging.getLogger("bidding_orchestrator")


# ── 数据结构 ──────────────────────────────────────────────


@dataclass
class CandidateCombo:
    """一个候选组合 = 基线 + 一个变异算子."""

    candidate_id: str = ""
    operator: str = ""           # C0 | R1 | R2 | R3 | R4 | R5
    operator_desc: str = ""      # 变异描述
    team_config: Dict[str, Any] = field(default_factory=dict)  # 团队构型
    skill_bindings: Dict[str, List[str]] = field(default_factory=dict)  # agent_id → skills
    execution_order: List[str] = field(default_factory=list)  # 任务执行顺序
    model_tiers: Dict[str, str] = field(default_factory=dict)  # agent_id → economy|standard|frontier
    review_edges: List[Tuple[str, str]] = field(default_factory=list)  # 额外评审回边


@dataclass
class TrialResult:
    """一个候选的试炼结果."""

    candidate_id: str = ""
    success_rate: float = 0.0    # 0.0 ~ 1.0
    quality_score: float = 0.0   # 0.0 ~ 1.0 (rubric 验收)
    token_consumed: int = 0
    collab_heat: float = 0.0     # 协作热度（边数×权重）
    error: str = ""


@dataclass
class BiddingRank:
    """竞标排名条目."""

    rank: int
    candidate_id: str
    operator: str
    success_rate: float
    quality_score: float
    token_consumed: int
    delta_token: int             # 相对 C0 的 token 差
    delta_quality: float         # 相对 C0 的质量差
    is_winner: bool = False


QUALITY_THRESHOLD = 0.9         # 质量达标线
SUCCESS_RATE_THRESHOLD = 0.9    # 成功率达标线


# ── 候选生成 (§4.5 规格) ──────────────────────────────────


def _candidate_hash(c: CandidateCombo) -> str:
    """稳定哈希用于 ratchet key."""
    raw = f"{c.operator}|{sorted(c.team_config.items())}|{sorted(c.skill_bindings.items())}|{c.execution_order}|{sorted(c.model_tiers.items())}|{c.review_edges}"
    return hashlib.md5(raw.encode()).hexdigest()[:10]


def generate_candidates(
    baseline: CandidateCombo,
    available_agents: Optional[List[str]] = None,
    available_skills: Optional[Dict[str, List[str]]] = None,
    max_candidates: int = 4,
) -> List[CandidateCombo]:
    """从基线 C0 生成候选列表: C0 + 单算子变异.

    优先级: R5降档 > R3并行化 > R4加Review > R1换角色 > R2换技能
    非法候选（依赖成环、技能不覆盖）在生成期过滤.
    """
    candidates = [baseline]
    _id = 1

    def _next_id():
        nonlocal _id
        v = f"c{_id}"
        _id += 1
        return v

    # R5: 模型档降级（economy）
    if baseline.model_tiers:
        for aid, tier in baseline.model_tiers.items():
            tier_order = {"frontier": 0, "standard": 1, "economy": 2}
            cur_idx = tier_order.get(tier, 1)
            if cur_idx < 2:
                new_tier = list(tier_order.keys())[cur_idx + 1]
                new_tiers = {**baseline.model_tiers, aid: new_tier}
                c = CandidateCombo(
                    candidate_id=_next_id(), operator="R5",
                    operator_desc=f"{aid} 模型档 {tier}→{new_tier}",
                    team_config=dict(baseline.team_config),
                    skill_bindings=dict(baseline.skill_bindings),
                    execution_order=list(baseline.execution_order),
                    model_tiers=new_tiers,
                    review_edges=list(baseline.review_edges),
                )
                candidates.append(c)
                if len(candidates) >= max_candidates:
                    return candidates
                break

    # R3: 并行化（无依赖兄弟步骤改并行）
    if len(baseline.execution_order) > 1:
        c = CandidateCombo(
            candidate_id=_next_id(), operator="R3",
            operator_desc="无依赖步骤并行化",
            team_config=dict(baseline.team_config),
            skill_bindings=dict(baseline.skill_bindings),
            execution_order=list(baseline.execution_order),  # 顺序不变但标记并行
            model_tiers=dict(baseline.model_tiers),
            review_edges=list(baseline.review_edges),
        )
        c.team_config["parallel"] = True
        candidates.append(c)
        if len(candidates) >= max_candidates:
            return candidates

    # R4: 加 Review（关键步骤后增评审回边）
    if baseline.execution_order:
        last_agent = baseline.execution_order[-1] if baseline.execution_order else ""
        reviewer = available_agents[0] if available_agents else "reviewer"
        c = CandidateCombo(
            candidate_id=_next_id(), operator="R4",
            operator_desc=f"在 {last_agent} 后增加 {reviewer} 评审",
            team_config=dict(baseline.team_config),
            skill_bindings=dict(baseline.skill_bindings),
            execution_order=list(baseline.execution_order),
            model_tiers=dict(baseline.model_tiers),
            review_edges=list(baseline.review_edges) + [(last_agent, reviewer)],
        )
        candidates.append(c)
        if len(candidates) >= max_candidates:
            return candidates

    # R1: 换角色
    if available_agents and len(available_agents) > 1 and baseline.execution_order:
        target_agent = baseline.execution_order[0]
        replacement = next((a for a in available_agents if a != target_agent), None)
        if replacement:
            new_order = list(baseline.execution_order)
            new_order[0] = replacement
            c = CandidateCombo(
                candidate_id=_next_id(), operator="R1",
                operator_desc=f"步骤1 负责人 {target_agent}→{replacement}",
                team_config=dict(baseline.team_config),
                skill_bindings=dict(baseline.skill_bindings),
                execution_order=new_order,
                model_tiers=dict(baseline.model_tiers),
                review_edges=list(baseline.review_edges),
            )
            candidates.append(c)
            if len(candidates) >= max_candidates:
                return candidates

    # R2: 换技能绑定
    if available_skills and baseline.skill_bindings:
        for aid, skills in baseline.skill_bindings.items():
            if skills and aid in available_skills:
                alt_skills = [s for s in available_skills[aid] if s not in skills]
                if alt_skills:
                    new_bindings = dict(baseline.skill_bindings)
                    new_bindings[aid] = skills[:1] + alt_skills[:1]
                    c = CandidateCombo(
                        candidate_id=_next_id(), operator="R2",
                        operator_desc=f"{aid} 技能 {skills[0]}→{alt_skills[0]}",
                        team_config=dict(baseline.team_config),
                        skill_bindings=new_bindings,
                        execution_order=list(baseline.execution_order),
                        model_tiers=dict(baseline.model_tiers),
                        review_edges=list(baseline.review_edges),
                    )
                    candidates.append(c)
                    break

    return candidates[:max_candidates]


# ── 评分与排名 ────────────────────────────────────────────


def _quality_qualified(r: TrialResult) -> bool:
    return r.success_rate >= SUCCESS_RATE_THRESHOLD and r.quality_score >= QUALITY_THRESHOLD


def rank_candidates(
    baseline: CandidateCombo,
    results: List[Tuple[CandidateCombo, TrialResult]],
) -> List[BiddingRank]:
    """评分与排名: 质量达标者中选 token 最省；平票取质量高者."""
    if not results:
        return []

    c0_result = next((r for c, r in results if c.operator == "C0"), None)
    c0_token = c0_result.token_consumed if c0_result else 0
    c0_quality = c0_result.quality_score if c0_result else 0

    # 过滤: 质量达标者优先，不达标者排后
    qualified = [(c, r) for c, r in results if _quality_qualified(r)]
    unqualified = [(c, r) for c, r in results if not _quality_qualified(r)]

    # 达标组: token 升序，平票取质量高
    qualified.sort(key=lambda x: (x[1].token_consumed, -x[1].quality_score))
    # 不达标组: 质量降序
    unqualified.sort(key=lambda x: -x[1].quality_score)

    ranked = qualified + unqualified
    ranks = []
    for i, (c, r) in enumerate(ranked):
        ranks.append(BiddingRank(
            rank=i + 1,
            candidate_id=c.candidate_id,
            operator=c.operator,
            success_rate=r.success_rate,
            quality_score=r.quality_score,
            token_consumed=r.token_consumed,
            delta_token=r.token_consumed - c0_token,
            delta_quality=r.quality_score - c0_quality,
            is_winner=(i == 0 and _quality_qualified(r)),
        ))
    return ranks


# ── Ratchet 锁定 (M4-2) ───────────────────────────────────


def ratchet_lock_winner(
    task_type: str,
    winner: CandidateCombo,
    result: TrialResult,
    ledger: Any = None,
) -> Dict[str, Any]:
    """M4-2: 胜者写 scenario_best:<task_type>:<candidate_hash>。

    后来者须同时满足 质量不降 ∧ token 更省 才能取代。
    """
    if ledger is None:
        ledger = get_ratchet_ledger()

    chash = _candidate_hash(winner)
    metric_key = f"scenario_best:{task_type}:{chash}"
    efficiency = result.quality_score / max(result.token_consumed, 1)

    # 候选级 key（每次新候选 = 新 key，总是 advance）
    ledger.advance(metric_key, efficiency, evidence={
        "candidate_id": winner.candidate_id,
        "operator": winner.operator,
        "success_rate": result.success_rate,
        "quality_score": result.quality_score,
        "token_consumed": result.token_consumed,
    })

    # task_type 级别 key（共享，后来者须更优才能取代 — 棘轮单调）
    best_key = f"scenario_best:{task_type}"
    res = ledger.advance(best_key, efficiency, evidence={
        "candidate_hash": chash,
        "operator": winner.operator,
        "success_rate": result.success_rate,
        "quality_score": result.quality_score,
        "token_consumed": result.token_consumed,
    })
    return res


# ── 竞标 token 入账 (M4-3) ────────────────────────────────


def record_bidding_cost(
    results: List[Tuple[CandidateCombo, TrialResult]],
    team_id: str = "",
) -> Dict[str, Any]:
    """M4-3: 竞标消耗写 token_ledger，标 simulation，不计入生产效能."""
    total_tokens = sum(r.token_consumed for _, r in results)
    if total_tokens <= 0:
        return {"recorded": False, "reason": "no_tokens"}

    try:
        from agents.token_ledger import get_token_ledger
        ledger = get_token_ledger()
        ledger.record(
            phase="simulation",
            team_id=team_id,
            tokens=total_tokens,
            run_id=f"bidding_{results[0][0].candidate_id if results else 'unknown'}",
            detail={"tag": "simulation", "candidates": len(results)},
        )
        return {"recorded": True, "total_tokens": total_tokens, "tag": "simulation"}
    except Exception as e:
        logger.warning("竞标 token 入账失败: %s", e)
        return {"recorded": False, "error": str(e)}


# ── 编排入口 ─────────────────────────────────────────────


TrialRunner = Callable[[CandidateCombo], TrialResult]


def bidding_orchestrator(
    task_type: str,
    baseline: CandidateCombo,
    trial_runner: TrialRunner,
    available_agents: Optional[List[str]] = None,
    available_skills: Optional[Dict[str, List[str]]] = None,
    team_id: str = "",
    max_candidates: int = 4,
    do_ratchet: bool = True,
    do_cost: bool = True,
) -> Dict[str, Any]:
    """M4-1 竞标编排器入口.

    1. 生成候选 (C0 + 单算子变异)
    2. 每候选跑试炼
    3. 排名
    4. ratchet 锁定胜者 (M4-2)
    5. token 入账 (M4-3)

    Returns:
        {ranking, winner, ratchet_result, cost_result, candidates}
    """
    # 1. 生成候选
    candidates = generate_candidates(
        baseline, available_agents, available_skills, max_candidates,
    )

    # 2. 跑试炼
    results: List[Tuple[CandidateCombo, TrialResult]] = []
    for c in candidates:
        try:
            r = trial_runner(c)
            if not r.error:
                results.append((c, r))
            else:
                logger.warning("候选 %s 试炼失败: %s", c.candidate_id, r.error)
        except Exception as e:
            logger.warning("候选 %s 试炼异常: %s", c.candidate_id, e)

    # 3. 排名
    ranking = rank_candidates(baseline, results)

    # 4. ratchet 锁定
    ratchet_result = {"skipped": True}
    if do_ratchet and ranking and ranking[0].is_winner:
        winner_combo = next(c for c, r in results if c.candidate_id == ranking[0].candidate_id)
        winner_result = next(r for c, r in results if c.candidate_id == ranking[0].candidate_id)
        ratchet_result = ratchet_lock_winner(task_type, winner_combo, winner_result)

    # 5. token 入账
    cost_result = {"skipped": True}
    if do_cost:
        cost_result = record_bidding_cost(results, team_id)

    winner = None
    if ranking and ranking[0].is_winner:
        winner = {
            "candidate_id": ranking[0].candidate_id,
            "operator": ranking[0].operator,
            "success_rate": ranking[0].success_rate,
            "quality_score": ranking[0].quality_score,
            "token_consumed": ranking[0].token_consumed,
        }

    return {
        "ranking": [r.__dict__ for r in ranking],
        "winner": winner,
        "ratchet_result": ratchet_result,
        "cost_result": cost_result,
        "candidates": [{"candidate_id": c.candidate_id, "operator": c.operator,
                         "operator_desc": c.operator_desc} for c in candidates],
    }


# ── M5-1: 竞标结论回流讨论 ───────────────────────────────


def reflow_bidding_to_discussion(
    plaza_engine: Any,
    plaza_id: str,
    discussion_id: str,
    bidding_result: Dict[str, Any],
) -> Dict[str, Any]:
    """M5-1: 竞标排名/胜者/协作热度回写讨论时间线与计划面板。

    在讨论时间线中插入一条系统消息，包含竞标结论。
    """
    if not plaza_engine or not plaza_id or not discussion_id:
        return {"ok": False, "error": "missing_plaza_or_discussion"}

    disc = plaza_engine.get_discussion(plaza_id, discussion_id)
    if not disc:
        return {"ok": False, "error": "discussion_not_found"}

    winner = bidding_result.get("winner")
    ranking = bidding_result.get("ranking", [])

    if not winner:
        content = "⚠️ 竞标完成但无候选达标，所有组合质量未通过阈值。"
    else:
        # 构建竞标结论摘要
        lines = [
            f"🏁 竞标演练完成 · 任务类型: {bidding_result.get('task_type', 'unknown')}",
            f"胜者: {winner['operator']} (候选 {winner['candidate_id']})",
            f"  成功率: {winner['success_rate']:.1%} · 质量: {winner['quality_score']:.1%} · Token: {winner['token_consumed']}",
            "",
            "排名:",
        ]
        for r in ranking[:5]:
            marker = "🏆 " if r.get("is_winner") else f"{r['rank']}. "
            lines.append(
                f"{marker}{r['operator']} | 质量 {r['quality_score']:.1%} | "
                f"Token {r['token_consumed']} (Δ{r['delta_token']:+d})"
            )
        content = "\n".join(lines)

    # 插入系统消息到讨论
    try:
        import asyncio
        from agents.plaza import PlazaMessage

        msg = PlazaMessage(
            discussion_id=discussion_id,
            agent_id="bidding_orchestrator",
            agent_name="竞标编排器",
            role="system",
            niche_role="moderator",
            content=content,
            round_number=(disc.current_round or 0) + 1,
        )
        msg.seq = len(disc.messages)
        disc.messages.append(msg)

        # 广播给前端 SSE（无事件循环时跳过，消息已写入讨论记录）
        try:
            asyncio.ensure_future(plaza_engine._broadcast(discussion_id, {
                "type": "message", "message": msg.to_dict(),
            }))
        except RuntimeError:
            pass  # No event loop — 消息已写入，广播在下次 SSE 推送时补

        # 同时在 plan 里记录竞标结论
        if disc.plan and isinstance(disc.plan, dict):
            disc.plan["bidding_result"] = {
                "winner": winner,
                "ranking": ranking[:5],
                "task_type": bidding_result.get("task_type", ""),
            }

        return {"ok": True, "message_id": msg.id, "content_preview": content[:100]}
    except Exception as e:
        logger.warning("竞标回流失败: %s", e)
        return {"ok": False, "error": str(e)}
