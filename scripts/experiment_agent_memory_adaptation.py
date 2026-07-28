#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""五组 Agent 记忆行为适应实验（隔离存储，不写生产 storage/agent_memory）。

Groups: cold_start | full_inheritance | selective_inheritance | stale_memory | contaminated_memory
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

from agents.agent_memory_core import AgentMemoryCore, AgentMemoryStore  # noqa: E402
from agents.agent_memory_migration import (  # noqa: E402
    build_export_v2,
    import_transaction,
)

GROUPS = [
    "cold_start",
    "full_inheritance",
    "selective_inheritance",
    "stale_memory",
    "contaminated_memory",
]

SCENARIOS = [
    {
        "id": "es_scale",
        "query": "扩容",
        "success_tags": ["扩容", "es", "IO"],
        "failure_pattern": "盲目缩容",
    },
    {
        "id": "centos_migrate",
        "query": "迁移",
        "success_tags": ["迁移", "Rocky", "兼容"],
        "failure_pattern": "全量一次性切换",
    },
    {
        "id": "cost_ri",
        "query": "RI",
        "success_tags": ["RI", "预留", "覆盖率"],
        "failure_pattern": "忽略闲置实例",
    },
]


@dataclass
class RoundOutcome:
    success: bool
    score: float
    used_inherited: bool = False
    false_positive: bool = False
    detail: str = ""


def _seed_mentor(store: AgentMemoryStore, team: str, agent: str, scenario: Dict[str, Any], *, good: bool = True) -> None:
    core = AgentMemoryCore(team, agent, store=store)
    core.bind(True)
    tags = list(scenario["success_tags"])
    if good:
        core.log.append(
            {
                "action": "关键决策",
                "detail": f"成功处理 {scenario['id']}：采用分批与监控",
                "importance": 9,
                "tags": tags + ["good"],
            }
        )
        core.semantic.add(f"规则：{scenario['id']} 必须分批", strength=0.8, tags=tags)
    else:
        # contaminated: wrong advice that looks relevant
        core.log.append(
            {
                "action": "错误经验",
                "detail": f"{scenario['failure_pattern']} 被误记为最佳实践",
                "importance": 9,
                "tags": tags + ["bad", "contaminated"],
            }
        )
        core.semantic.add(
            f"错误规则：{scenario['failure_pattern']}",
            strength=0.9,
            tags=tags + ["contaminated"],
        )


def _seed_stale(store: AgentMemoryStore, team: str, agent: str, scenario: Dict[str, Any], stale_ms: int) -> None:
    core = AgentMemoryCore(team, agent, store=store)
    core.bind(True)
    old_t = 1_600_000_000_000  # fixed past
    core.log.append(
        {
            "t": old_t,
            "action": "过时手册",
            "detail": f"旧版 {scenario['id']} 流程（版本边界 t<{stale_ms}）",
            "importance": 8,
            "tags": list(scenario["success_tags"]) + ["stale"],
        }
    )
    core.semantic.add(f"过时：{scenario['id']} v1", strength=0.7, tags=["stale"])


def prepare_agent(
    group: str,
    store: AgentMemoryStore,
    scenario: Dict[str, Any],
    seed: int,
) -> AgentMemoryCore:
    team = f"exp_{seed}"
    agent = f"{group}_{scenario['id']}"
    core = AgentMemoryCore(team, agent, store=store)
    core.bind(True)

    if group == "cold_start":
        return core

    # Each group gets an isolated mentor identity. Reusing mentor_<scenario>
    # leaked the good full-inheritance seed into stale/contaminated groups.
    mentor = AgentMemoryCore(team, f"mentor_{group}_{scenario['id']}", store=store)
    if group == "contaminated_memory":
        _seed_mentor(store, team, mentor.agent_id, scenario, good=False)
    elif group == "stale_memory":
        _seed_stale(store, team, mentor.agent_id, scenario, stale_ms=1_700_000_000_000)
    else:
        _seed_mentor(store, team, mentor.agent_id, scenario, good=True)

    bundle = build_export_v2(AgentMemoryCore(team, mentor.agent_id, store=store))
    if group == "selective_inheritance":
        import_transaction(
            core,
            bundle,
            strategy="selective",
            selected_layers=["semantic"],
            transfer_id=f"tx_{group}_{seed}_{scenario['id']}",
        )
    elif group == "full_inheritance":
        import_transaction(
            core,
            bundle,
            strategy="merge",
            transfer_id=f"tx_{group}_{seed}_{scenario['id']}",
        )
    elif group in ("stale_memory", "contaminated_memory"):
        import_transaction(
            core,
            bundle,
            strategy="merge",
            transfer_id=f"tx_{group}_{seed}_{scenario['id']}",
        )
    return core


def run_round(core: AgentMemoryCore, scenario: Dict[str, Any], round_i: int) -> RoundOutcome:
    """Deterministic adaptation: success if good memory available or learned after fails."""
    q = scenario["query"]
    hits = core.log.recall(q, k=5)
    from agents.agent_memory_migration import inherited_hits_for_recall

    inh = inherited_hits_for_recall(core.store, core.team_id, core.agent_id, q, k=5)
    texts = []
    used_inherited = False
    contaminated = False
    stale = False
    good = False
    for h in hits:
        e = h.get("event") or {}
        t = f"{e.get('detail') or ''} {' '.join(e.get('tags') or [])}"
        texts.append(t)
        if "contaminated" in t or "错误" in t or scenario["failure_pattern"] in t:
            contaminated = True
        if "stale" in t or "过时" in t:
            stale = True
        if "good" in t or "分批" in t or "成功" in t:
            good = True
    for h in inh:
        used_inherited = True
        t = h.get("summary") or ""
        tags = " ".join((h.get("item") or {}).get("tags") or [])
        blob = t + " " + tags
        texts.append(blob)
        if "contaminated" in blob or "错误" in blob or scenario["failure_pattern"] in blob:
            contaminated = True
        if "stale" in blob or "过时" in blob:
            stale = True
        if "分批" in blob or "成功" in blob or "good" in blob:
            good = True

    # learning: after failures, agent encodes correct lesson. Wrong inherited
    # memory keeps interfering for one extra round, which makes negative
    # transfer observable against the cold-start baseline.
    if round_i >= 1:
        core.update_from_evidence(
            {
                "source_type": "adaptation_round",
                "source_id": f"{scenario['id']}:r{round_i}",
                "agent_id": core.agent_id,
                "summary": f"学习分批处理 {scenario['id']}",
                "success": True,
                "action": "适应学习",
                "tags": list(scenario["success_tags"]) + ["learned", "good"],
            }
        )
        good = True

    if contaminated and round_i < 2:
        success = False
        fp = True
        score = 0.05
        detail = "负迁移：污染记忆主导"
    elif stale and round_i < 2:
        success = False
        fp = False
        score = 0.1
        detail = "过时记忆未适配"
    elif good or (used_inherited and not contaminated and not stale):
        success = True
        fp = False
        score = 0.9 if used_inherited else 0.75
        detail = "命中有效经验"
    else:
        # cold start first round fails, later learns
        success = round_i >= 1
        fp = False
        score = 0.85 if success else 0.15
        detail = "冷启动探索" if not success else "探索后学会"
        if success:
            core.log.append(
                {
                    "action": "探索成功",
                    "detail": f"分批完成 {scenario['id']}",
                    "importance": 8,
                    "tags": list(scenario["success_tags"]) + ["good", "learned"],
                }
            )

    return RoundOutcome(
        success=success,
        score=score,
        used_inherited=used_inherited,
        false_positive=fp,
        detail=detail,
    )


def aggregate(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_group: Dict[str, List[Dict[str, Any]]] = {g: [] for g in GROUPS}
    for r in rows:
        by_group.setdefault(r["group"], []).append(r)

    cold_rows = by_group.get("cold_start", [])
    cold_first = [r["first_task_success"] for r in cold_rows]
    cold_rate = statistics.mean(cold_first) if cold_first else 0.0
    cold_by_case = {(r["seed"], r["scenario"]): r for r in cold_rows}

    for group, items in by_group.items():
        if group == "cold_start":
            continue
        for row in items:
            baseline = cold_by_case.get((row["seed"], row["scenario"]))
            if not baseline:
                row["negative_transfer"] = False
                continue
            row["negative_transfer"] = bool(
                row["first_task_score"] < baseline["first_task_score"]
                or row["adaptation_rounds"] > baseline["adaptation_rounds"]
                or row["repeated_historic_failure_rate"]
                > baseline["repeated_historic_failure_rate"]
            )

    summary = {}
    for g, items in by_group.items():
        if not items:
            continue
        first = [1.0 if x["first_task_success"] else 0.0 for x in items]
        rounds = [x["adaptation_rounds"] for x in items]
        rep = [x["repeated_historic_failure_rate"] for x in items]
        neg = [1.0 if x["negative_transfer"] else 0.0 for x in items]
        summary[g] = {
            "n": len(items),
            "first_task_success_mean": statistics.mean(first),
            "first_task_success_std": statistics.pstdev(first) if len(first) > 1 else 0.0,
            "adaptation_rounds_mean": statistics.mean(rounds),
            "adaptation_rounds_std": statistics.pstdev(rounds) if len(rounds) > 1 else 0.0,
            "repeated_historic_failure_rate_mean": statistics.mean(rep),
            "negative_transfer_rate": statistics.mean(neg),
        }
        if g == "contaminated_memory":
            precs = [x.get("precision") for x in items if x.get("precision") is not None]
            recs = [x.get("recall") for x in items if x.get("recall") is not None]
            fps = [x.get("false_positive_rate") for x in items if x.get("false_positive_rate") is not None]
            summary[g]["precision_mean"] = statistics.mean(precs) if precs else None
            summary[g]["recall_mean"] = statistics.mean(recs) if recs else None
            summary[g]["false_positive_rate_mean"] = statistics.mean(fps) if fps else None

    return {"by_group": summary, "cold_start_first_success_mean": cold_rate}


def run_experiment(
    seeds: List[int],
    max_rounds: int = 3,
    out_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    out_dir = out_dir or (ROOT / "docs" / "reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="ag_mem_exp_") as tmp:
        store = AgentMemoryStore(Path(tmp))
        for seed in seeds:
            for scenario in SCENARIOS:
                for group in GROUPS:
                    core = prepare_agent(group, store, scenario, seed)
                    outcomes: List[RoundOutcome] = []
                    for r in range(max_rounds):
                        outcomes.append(run_round(core, scenario, r))
                    first_ok = outcomes[0].success if outcomes else False
                    adapt = next((i for i, o in enumerate(outcomes) if o.success), max_rounds)
                    # historic failure repeat: if early fail pattern reappears after learn
                    rep_fail = 0.0
                    if len(outcomes) >= 2 and outcomes[0].success is False:
                        rep_fail = 1.0 if (not outcomes[1].success) else 0.0

                    precision = recall = fpr = None
                    if group == "contaminated_memory":
                        # treat contaminated hit as FP when first fails
                        tp = 1 if first_ok else 0
                        fp = 1 if outcomes[0].false_positive else 0
                        fn = 0 if first_ok else 1
                        precision = tp / (tp + fp) if (tp + fp) else 0.0
                        recall = tp / (tp + fn) if (tp + fn) else 0.0
                        fpr = fp / max(1, tp + fp)

                    row = {
                        "seed": seed,
                        "scenario": scenario["id"],
                        "group": group,
                        "first_task_success": first_ok,
                        "first_task_score": outcomes[0].score if outcomes else 0.0,
                        "adaptation_rounds": adapt,
                        "repeated_historic_failure_rate": rep_fail,
                        "negative_transfer": False,
                        "precision": precision,
                        "recall": recall,
                        "false_positive_rate": fpr,
                        "rounds": [
                            {
                                "success": o.success,
                                "score": o.score,
                                "used_inherited": o.used_inherited,
                                "detail": o.detail,
                            }
                            for o in outcomes
                        ],
                    }
                    rows.append(row)
                    if not first_ok and group in ("full_inheritance", "stale_memory", "contaminated_memory"):
                        failures.append(
                            {
                                "seed": seed,
                                "scenario": scenario["id"],
                                "group": group,
                                "detail": outcomes[0].detail if outcomes else "",
                            }
                        )

        summary = aggregate(rows)

    report = {
        "schema": "ag.memory.adaptation_experiment/v1",
        "experiment_type": "deterministic_memory_mechanism",
        "claim_boundary": (
            "验证迁移、检索、过时/污染干扰与再学习机制；不调用真实 LLM，"
            "不能替代线上 Agent 行为效果或统计显著性实验。"
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seeds": seeds,
        "max_rounds": max_rounds,
        "groups": GROUPS,
        "scenarios": [s["id"] for s in SCENARIOS],
        "stale_definition": {
            "boundary": "event.t < 1700000000000 或 tags 含 stale/过时",
            "note": "过时组继承旧版流程记忆，需在后续轮次重学",
        },
        "n_runs": len(rows),
        "summary": summary,
        "rows": rows,
        "failure_cases": failures[:50],
        "storage": "isolated tempfile (not production storage/agent_memory)",
    }

    json_path = out_dir / "agent-memory-adaptation-report.json"
    md_path = out_dir / "agent-memory-adaptation-report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Agent 记忆行为适应实验报告",
        "",
        f"- 生成时间: {report['generated_at']}",
        f"- 种子: {seeds}",
        f"- 场景: {report['scenarios']}",
        f"- 轮次上限: {max_rounds}",
        f"- 样本量: {report['n_runs']}",
        f"- 存储: {report['storage']}",
        f"- 实验类型: {report['experiment_type']}",
        f"- 结论边界: {report['claim_boundary']}",
        "",
        "## 分组摘要",
        "",
    ]
    for g, s in (summary.get("by_group") or {}).items():
        lines.append(f"### {g}")
        lines.append(f"- n={s['n']}")
        lines.append(
            f"- first_task_success={s['first_task_success_mean']:.3f} ± {s['first_task_success_std']:.3f}"
        )
        lines.append(
            f"- adaptation_rounds={s['adaptation_rounds_mean']:.3f} ± {s['adaptation_rounds_std']:.3f}"
        )
        lines.append(f"- repeated_historic_failure_rate={s['repeated_historic_failure_rate_mean']:.3f}")
        lines.append(f"- negative_transfer_rate={s['negative_transfer_rate']:.3f}")
        if g == "contaminated_memory":
            lines.append(
                f"- precision={s.get('precision_mean')} recall={s.get('recall_mean')} "
                f"fp_rate={s.get('false_positive_rate_mean')}"
            )
        lines.append("")
    lines.append("## 过时定义")
    lines.append(json.dumps(report["stale_definition"], ensure_ascii=False))
    lines.append("")
    lines.append("## 失败案例（截断）")
    for f in report["failure_cases"][:20]:
        lines.append(f"- {f}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    report["artifacts"] = {"json": str(json_path), "md": str(md_path)}
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="7,42,2026")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--output-dir", default=str(ROOT / "docs" / "reports"))
    args = ap.parse_args()
    seeds = [int(x.strip()) for x in args.seeds.split(",") if x.strip()]
    report = run_experiment(seeds, max_rounds=args.rounds, out_dir=Path(args.output_dir))
    print(json.dumps({"ok": True, "artifacts": report["artifacts"], "n": report["n_runs"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
