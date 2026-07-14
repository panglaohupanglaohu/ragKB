# -*- coding: utf-8 -*-
"""Skill 集成报告 — 物竞天择 v4 XG-8.

从演练结果 + TaskHabitatContract 派生 IntegrationReport。
默认 write_policy=suggest_only，不写回生产真身。
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional, Set


def build_integration_report(
    result: Dict[str, Any],
    contract: Optional[Dict[str, Any]] = None,
    *,
    write_policy: str = "suggest_only",
    dominant_threshold: float = 0.5,
    agent_bound_skills: Optional[Dict[str, List[str]]] = None,
    reserve_skill_ids: Optional[List[str]] = None,
    team_skill_ids: Optional[List[str]] = None,
    top_k: int = 12,
) -> Dict[str, Any]:
    """构建 SkillIntegrationReport（纯函数，无副作用）.

    写回建议 **只包含 agent 尚未绑定的 skill**，优先：
    1) 任务契约 demand 中该 agent 没有的
    2) 种群 dominant 中该 agent 没有的
    3) 分类储备池 reserve 中该 agent 没有的
    4) 团队技能库中与 demand/dominant 相关且未绑定的

    绝不把「已在 genome/真身绑定」的 skill 放进 add_skills。
    """
    contract = contract or {}
    agent_bound_skills = agent_bound_skills or {}
    reserve_set: Set[str] = set(reserve_skill_ids or [])
    team_set: Set[str] = set(team_skill_ids or [])

    niches = contract.get("niches") or []
    plan_skills: List[str] = []
    for n in niches:
        for s in n.get("demanded_skills") or []:
            if s not in plan_skills:
                plan_skills.append(s)
    if not plan_skills:
        plan_skills = list(contract.get("skill_universe") or [])

    plan_set: Set[str] = set(plan_skills)
    ranking = list(result.get("final_ranking") or [])
    alive = [r for r in ranking if r.get("alive")]
    dead = [r for r in ranking if not r.get("alive")]
    pool = alive or ranking

    freq: Counter = Counter()
    for r in pool:
        for s in r.get("skill_genome") or []:
            freq[s] += 1
    n_pool = max(len(pool), 1)

    dominant = [
        s for s, c in freq.items()
        if c / n_pool >= dominant_threshold and (not plan_set or s in plan_set)
    ]
    # 若有 plan 约束，也列出计划外 dominant 供参考
    dominant_all = [s for s, c in freq.items() if c / n_pool >= dominant_threshold]

    alive_skills = set(freq.keys())
    dead_only: Set[str] = set()
    for r in dead:
        for s in r.get("skill_genome") or []:
            if s not in alive_skills:
                dead_only.add(s)

    missing = [s for s in plan_skills if freq.get(s, 0) == 0]

    def _bound_for(r: Dict[str, Any]) -> Set[str]:
        aid = str(r.get("agent_id") or "")
        bound: Set[str] = set(r.get("skill_genome") or [])
        # 真身绑定优先并入（写回前已有的不能再推荐）
        for s in agent_bound_skills.get(aid) or []:
            bound.add(s)
        # 模糊 key：短 id / 名字
        for k, skills in agent_bound_skills.items():
            if k == aid or aid.startswith(k) or k.startswith(aid[:8]):
                bound.update(skills)
        return {str(x) for x in bound if x}

    # 候选池排序：plan demand → dominant → reserve → 团队库中与 plan/dominant 相关
    def _candidates_for(bound: Set[str]) -> List[Dict[str, str]]:
        ordered: List[Dict[str, str]] = []
        seen: Set[str] = set()

        def _push(sid: str, source: str) -> None:
            s = str(sid)
            if not s or s in bound or s in seen:
                return
            seen.add(s)
            ordered.append({"skill": s, "source": source})

        for s in plan_skills:
            _push(s, "plan_demand")
        for s in dominant or dominant_all:
            _push(s, "dominant")
        for s in sorted(reserve_set):
            # 储备优先挂与考卷/dominant 相关的；其余储备作次级
            if s in plan_set or s in set(dominant_all):
                _push(s, "reserve")
        for s in sorted(reserve_set):
            _push(s, "reserve")
        for s in sorted(team_set):
            if s in plan_set or s in set(dominant_all):
                _push(s, "team_library")
        return ordered

    recommended: List[Dict[str, Any]] = []
    top = sorted(pool, key=lambda r: int(r.get("survival_ticks") or 0), reverse=True)[: max(3, top_k)]
    for r in top:
        bound = _bound_for(r)
        cands = _candidates_for(bound)
        # 每 agent 最多 6 条未绑定建议
        add = [c["skill"] for c in cands[:6]]
        sources = {c["skill"]: c["source"] for c in cands[:6]}
        if add:
            recommended.append({
                "agent_id": r.get("agent_id"),
                "add_skills": add,
                "skill_sources": sources,
                "already_bound": sorted(bound)[:24],
                "reason": "unbound only: plan_demand / dominant / reserve / team_library",
                "survival_ticks": r.get("survival_ticks"),
            })
        else:
            recommended.append({
                "agent_id": r.get("agent_id"),
                "add_skills": [],
                "skill_sources": {},
                "already_bound": sorted(bound)[:24],
                "reason": "no_unbound_candidates",
                "survival_ticks": r.get("survival_ticks"),
            })

    # 学派：共现对（简化）
    pair_counts: Counter = Counter()
    for r in pool:
        gs = sorted(set(r.get("skill_genome") or []))
        for i in range(len(gs)):
            for j in range(i + 1, len(gs)):
                pair_counts[(gs[i], gs[j])] += 1
    schools = [
        {"skills": [a, b], "count": c}
        for (a, b), c in pair_counts.most_common(8)
        if c >= 2
    ]

    return {
        "plan_id": contract.get("plan_id", ""),
        "fingerprint": (contract.get("provenance") or {}).get("fingerprint", ""),
        "dominant_skills": dominant or [s for s in dominant_all if s in plan_set] or dominant_all[:8],
        "dominant_skills_all": dominant_all[:16],
        "missing_plan_skills": missing,
        "deprecated_skills": sorted(dead_only)[:24],
        "recommended_bindings": recommended,
        "school_clusters": schools,
        "write_policy": write_policy,
        "plan_skills": plan_skills,
        "reserve_pool_size": len(reserve_set),
        "n_alive": len(alive),
        "n_ranked": len(ranking),
        "policy_note": "add_skills 仅含未绑定 skill；优先 plan_demand / dominant / reserve",
    }
