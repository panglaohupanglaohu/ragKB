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
) -> Dict[str, Any]:
    """构建 SkillIntegrationReport（纯函数，无副作用）."""
    contract = contract or {}
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

    # 推荐：对 top survivors 补齐 missing plan skills
    recommended: List[Dict[str, Any]] = []
    top = sorted(pool, key=lambda r: int(r.get("survival_ticks") or 0), reverse=True)[:3]
    for r in top:
        genome = set(r.get("skill_genome") or [])
        add = [s for s in missing if s not in genome]
        # 也推荐 dominant plan skills 缺失者
        for s in dominant:
            if s not in genome and s not in add:
                add.append(s)
        if add:
            recommended.append({
                "agent_id": r.get("agent_id"),
                "add_skills": add,
                "reason": "high frequency among top survivors / missing plan skills",
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
        "n_alive": len(alive),
        "n_ranked": len(ranking),
    }
