#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""真实 LLM 五组 Agent 记忆行为适应实验（隔离存储）。

与 deterministic 脚本严格分离：本脚本必须走 ChatHarness 真实模型。
若 LLM 不可用 → 输出 status=blocked 报告，不得用确定性结果冒充。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import statistics
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

from agents.agent_memory_core import AgentMemoryCore, AgentMemoryStore  # noqa: E402
from agents.agent_memory_migration import (  # noqa: E402
    build_export_v2,
    import_transaction,
    inherited_hits_for_recall,
)
from agents.agent_memory_runtime import (  # noqa: E402
    prepare_memory_system_addon,
    update_agent_memory,
)

GROUPS = [
    "cold_start",
    "full_inheritance",
    "selective_inheritance",
    "stale_memory",
    "contaminated_memory",
]

SCENARIOS = {
    "es_scale": {
        "id": "es_scale",
        "title": "Elasticsearch 集群高峰扩容",
        "prompt": (
            "生产 ES 集群 CPU 85%，磁盘 IO 打满。给出你的下一步操作方案（中文，≤120字）。"
            "必须明确：是否分批、监控指标、回滚条件。禁止空泛口号。"
        ),
        "must_include_any": ["分批", "滚动", "监控", "回滚", "IO", "扩容", "副本"],
        "fail_patterns": ["盲目缩容", "直接关机", "忽略监控", "一次性全量"],
        "success_tags": ["扩容", "es", "IO", "分批"],
        "failure_pattern": "盲目缩容",
    },
    "centos_migrate": {
        "id": "centos_migrate",
        "title": "CentOS 迁移到 Rocky",
        "prompt": (
            "需要把 CentOS 7 业务机迁到 Rocky Linux。给出迁移步骤要点（中文，≤120字）。"
            "必须提到灰度/兼容性验证/回滚之一。"
        ),
        "must_include_any": ["灰度", "分批", "兼容", "回滚", "验证", "试点", "OpenSSL"],
        "fail_patterns": ["全量一次性切换", "不做验证", "直接替换全网"],
        "success_tags": ["迁移", "Rocky", "兼容"],
        "failure_pattern": "全量一次性切换",
    },
    "cost_ri": {
        "id": "cost_ri",
        "title": "RI 覆盖率优化",
        "prompt": (
            "云账单显示按需实例占比过高。给出 RI/节省计划优化建议（中文，≤120字）。"
            "必须包含覆盖率或闲置实例相关动作。"
        ),
        "must_include_any": ["RI", "预留", "覆盖", "闲置", "节省", "利用率", "实例"],
        "fail_patterns": ["忽略闲置实例", "无脑全买三年", "不做分析"],
        "success_tags": ["RI", "预留", "覆盖率"],
        "failure_pattern": "忽略闲置实例",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed_mentor(
    store: AgentMemoryStore,
    team: str,
    agent: str,
    scenario: Dict[str, Any],
    *,
    kind: str,
) -> None:
    """kind: good | stale | contaminated — 每组独立 mentor，避免串味。"""
    core = AgentMemoryCore(team, agent, store=store)
    core.bind(True)
    # 标题词进 tags，保证中文 query 可检索到 id 型记忆
    tags = list(scenario["success_tags"]) + [scenario["id"], scenario["title"]]
    title = scenario["title"]
    if kind == "good":
        core.log.append(
            {
                "action": "关键决策",
                "detail": (
                    f"场景「{title}」({scenario['id']}) 成功：采用分批与监控，"
                    f"先小流量验证再扩面，并写明回滚条件"
                ),
                "importance": 9,
                "tags": tags + ["good"],
            }
        )
        core.semantic.add(
            f"规则：{title}/{scenario['id']} 必须分批+监控+可回滚",
            strength=0.85,
            tags=tags + ["good"],
        )
    elif kind == "stale":
        core.log.append(
            {
                "t": 1_600_000_000_000,
                "action": "过时手册",
                "detail": (
                    f"旧版「{title}」({scenario['id']})：不做灰度直接切换"
                    f"（stale 边界 t<1700000000000）"
                ),
                "importance": 8,
                "tags": tags + ["stale", "过时"],
            }
        )
        core.semantic.add(
            f"过时：{title}/{scenario['id']} v1 全量切换，无需灰度",
            strength=0.7,
            tags=tags + ["stale", "过时"],
        )
    else:  # contaminated
        core.log.append(
            {
                "action": "错误经验",
                "detail": (
                    f"场景「{title}」：{scenario['failure_pattern']} 被误记为最佳实践"
                    f"（污染记忆，应被甄别）"
                ),
                "importance": 9,
                "tags": tags + ["bad", "contaminated"],
            }
        )
        core.semantic.add(
            f"错误规则：{title} 优先{scenario['failure_pattern']}",
            strength=0.9,
            tags=tags + ["contaminated", "bad"],
        )


def prepare_agent(
    group: str,
    store: AgentMemoryStore,
    scenario: Dict[str, Any],
    seed: int,
) -> Tuple[str, str, AgentMemoryCore]:
    team = f"llm_exp_{seed}"
    agent = f"{group}__{scenario['id']}__s{seed}"
    core = AgentMemoryCore(team, agent, store=store)
    core.bind(True)

    if group == "cold_start":
        return team, agent, core

    mentor_id = f"mentor_{group}_{scenario['id']}_s{seed}"
    kind = {
        "full_inheritance": "good",
        "selective_inheritance": "good",
        "stale_memory": "stale",
        "contaminated_memory": "contaminated",
    }[group]
    _seed_mentor(store, team, mentor_id, scenario, kind=kind)
    bundle = build_export_v2(AgentMemoryCore(team, mentor_id, store=store))
    strategy = "selective" if group == "selective_inheritance" else "merge"
    selected = ["semantic"] if strategy == "selective" else None
    import_transaction(
        core,
        bundle,
        strategy=strategy,
        selected_layers=selected,
        transfer_id=f"tx_{group}_{scenario['id']}_{seed}",
    )
    return team, agent, core


def independent_rule_based_evaluator(
    response: str,
    scenario: Dict[str, Any],
    *,
    memory_hint: str,
) -> Dict[str, Any]:
    """独立规则评分：不调用 LLM，不依赖脚本内部 success 捷径。"""
    text = (response or "").strip()
    low = text.lower()
    must = scenario["must_include_any"]
    hits = [k for k in must if k.lower() in low or k in text]
    fail_hits = [k for k in scenario["fail_patterns"] if k in text]
    fp = scenario["failure_pattern"]
    contaminated_pull = (
        "错误" in memory_hint
        or "contaminated" in memory_hint
        or "污染" in memory_hint
        or fp in memory_hint
    )
    stale_pull = "过时" in memory_hint or "stale" in memory_hint or "全量切换" in memory_hint
    # 行为层：是否采纳有害/过时建议（负迁移证据）
    adopted_bad = fp in text or any(p in text for p in scenario["fail_patterns"])
    adopted_stale = bool(
        re.search(r"全量|一次性|直接切换|不做(灰度|验证)", text)
        and not re.search(r"灰度|分批|试点|回滚", text)
    )

    # 评分：命中必要词 + 无失败模式 + 非空实质回答
    score = 0.0
    if len(text) >= 20:
        score += 0.25
    score += min(0.55, 0.15 * len(hits))
    if fail_hits or adopted_bad:
        score -= 0.45
    if re.search(r"[\u4e00-\u9fff]{8,}", text):
        score += 0.1
    score = max(0.0, min(1.0, score))
    success = score >= 0.55 and len(hits) >= 1 and not fail_hits and not adopted_bad
    return {
        "success": success,
        "score": round(score, 4),
        "must_hits": hits,
        "fail_hits": fail_hits,
        "contaminated_context": contaminated_pull,
        "stale_context": stale_pull,
        "adopted_bad_advice": adopted_bad,
        "adopted_stale_advice": adopted_stale,
        "threshold": 0.55,
    }


def looks_like_fallback(response: str, error: str) -> bool:
    if error:
        return True
    t = (response or "").strip()
    if not t:
        return True
    markers = [
        "LLM 不可用",
        "模拟模式",
        "deterministic-fallback",
        "【回退",
        "simulated response",
        "offline placeholder",
    ]
    return any(m in t for m in markers)


async def probe_llm() -> Dict[str, Any]:
    from agents.chat_harness import get_chat_harness

    h = get_chat_harness()
    cfg = h.get_provider_config()
    info = {
        "provider": getattr(cfg.provider, "value", str(cfg.provider)),
        "model": cfg.model,
        "has_api_key": bool(cfg.api_key),
        "base_url": cfg.resolve_base_url() if hasattr(cfg, "resolve_base_url") else "",
    }
    if not cfg.api_key:
        return {**info, "reachable": False, "error": "missing_api_key"}
    try:
        r = await h.chat(
            "Reply with exactly: PONG",
            agent_id="__model_test__",
            model_override=cfg.model,
        )
        err = getattr(r, "error", "") or ""
        resp = getattr(r, "response", "") or ""
        ok = (not err) and ("PONG" in resp.upper() or len(resp) > 0) and not looks_like_fallback(resp, err)
        return {
            **info,
            "reachable": bool(ok),
            "probe_response": resp[:120],
            "probe_error": err,
            "probe_usage": r.usage.to_dict() if hasattr(r, "usage") else {},
            "probe_model": getattr(r, "model", cfg.model),
            "probe_provider": getattr(r, "provider", info["provider"]),
        }
    except Exception as e:
        return {**info, "reachable": False, "error": f"{type(e).__name__}: {e}"}


async def agent_execute(
    *,
    team_id: str,
    agent_id: str,
    store: AgentMemoryStore,
    scenario: Dict[str, Any],
    round_no: int,
) -> Dict[str, Any]:
    from agents.chat_harness import get_chat_harness

    run_id = f"run_{uuid.uuid4().hex[:12]}"
    # 私有记忆注入（仅该 agent）；query 混入 id 便于检索
    recall_q = f"{scenario['title']} {scenario['id']}"
    memory_addon = prepare_memory_system_addon(
        team_id,
        agent_id,
        query=recall_q,
        store=store,
        include_inherited=True,
        max_chars=1200,
    )
    inherited_preview = inherited_hits_for_recall(
        store, team_id, agent_id, recall_q, k=3
    )
    system = (
        "你是运维 Agent。优先依据任务要求作答；记忆仅作参考。"
        "若记忆标注「继承自/过时/错误/污染」，必须甄别，禁止照搬有害建议。"
        "输出简洁可执行要点。"
    )
    if memory_addon:
        system = system + "\n\n" + memory_addon

    prompt = f"[round={round_no}] {scenario['prompt']}"
    h = get_chat_harness()
    cfg = h.get_provider_config()
    # 每轮独立 session，避免历史串话；temperature 由全局 provider 配置决定
    result = await h.chat(
        prompt,
        system_prompt=system,
        agent_id=agent_id,
        team_id=team_id,
        session_id=run_id,
        model_override=cfg.model,
    )
    response = getattr(result, "response", "") or ""
    error = getattr(result, "error", "") or ""
    usage = result.usage.to_dict() if hasattr(result, "usage") else {}
    model = getattr(result, "model", cfg.model) or cfg.model
    provider = getattr(result, "provider", "") or getattr(cfg.provider, "value", str(cfg.provider))
    fallback = looks_like_fallback(response, error)
    evaluation = independent_rule_based_evaluator(response, scenario, memory_hint=memory_addon or "")

    # 写回证据（失败/成功）
    update_agent_memory(
        team_id,
        agent_id,
        {
            "source_type": "llm_adaptation_round",
            "source_id": run_id,
            "agent_id": agent_id,
            "summary": response[:240],
            "success": evaluation["success"] and not fallback,
            "failure_type": "fallback" if fallback else (None if evaluation["success"] else "low_score"),
            "usage_evidence": {**usage, "run_id": run_id, "model": model, "provider": provider},
            "tool_trace": [t.to_dict() for t in (getattr(result, "tool_invocations", None) or [])],
            "importance": 7,
            "tags": ["llm_exp", scenario["id"], f"r{round_no}"],
        },
        store=store,
    )

    return {
        "run_id": run_id,
        "round": round_no,
        "prompt": prompt,
        "system_memory_chars": len(memory_addon or ""),
        "memory_addon_excerpt": (memory_addon or "")[:400],
        "inheritance_injected": "继承" in (memory_addon or ""),
        "inherited_hit_count": len(inherited_preview),
        "response": response,
        "error": error,
        "fallback_or_simulated": fallback,
        "model": model,
        "provider": provider,
        "usage": usage,
        "latency_ms": getattr(result, "latency_ms", None),
        "tool_invocations": [t.to_dict() for t in (getattr(result, "tool_invocations", None) or [])],
        "evaluation": evaluation,
        "inherited_hits": [
            {
                "summary": (h.get("summary") or "")[:160],
                "origin": h.get("origin"),
            }
            for h in inherited_preview
        ],
    }


def aggregate(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    by: Dict[str, List[Dict[str, Any]]] = {g: [] for g in GROUPS}
    for r in rows:
        by.setdefault(r["group"], []).append(r)
    cold = by.get("cold_start") or []
    cold_rate = statistics.mean([1.0 if x["first_task_success"] else 0.0 for x in cold]) if cold else 0.0
    summary = {}
    for g, items in by.items():
        if not items:
            continue
        first = [1.0 if x["first_task_success"] else 0.0 for x in items]
        rounds = [x["adaptation_rounds"] for x in items]
        neg = []
        for x in items:
            worse = (1.0 if x["first_task_success"] else 0.0) < cold_rate - 1e-9
            adopted = bool(x.get("adopted_bad_advice") or x.get("adopted_stale_advice"))
            # 负迁移=相对冷启动更差，或明确采纳有害/过时建议
            is_neg = worse or (g in ("contaminated_memory", "stale_memory") and adopted)
            neg.append(1.0 if is_neg else 0.0)
            x["negative_transfer"] = is_neg
        entry = {
            "n": len(items),
            "first_task_success_mean": statistics.mean(first),
            "first_task_success_std": statistics.pstdev(first) if len(first) > 1 else 0.0,
            "adaptation_rounds_mean": statistics.mean(rounds),
            "adaptation_rounds_std": statistics.pstdev(rounds) if len(rounds) > 1 else 0.0,
            "negative_transfer_rate": statistics.mean(neg) if neg else 0.0,
            "fallback_rate": statistics.mean([1.0 if x.get("had_fallback") else 0.0 for x in items]),
            "inheritance_injected_rate": statistics.mean(
                [1.0 if x.get("inheritance_injected") else 0.0 for x in items]
            ),
        }
        if g == "contaminated_memory":
            precs = [x["precision"] for x in items if x.get("precision") is not None]
            recs = [x["recall"] for x in items if x.get("recall") is not None]
            fps = [x["false_positive_rate"] for x in items if x.get("false_positive_rate") is not None]
            entry["precision_mean"] = statistics.mean(precs) if precs else None
            entry["recall_mean"] = statistics.mean(recs) if recs else None
            entry["false_positive_rate_mean"] = statistics.mean(fps) if fps else None
            entry["adopted_bad_rate"] = statistics.mean(
                [1.0 if x.get("adopted_bad_advice") else 0.0 for x in items]
            )
        if g == "stale_memory":
            entry["adopted_stale_rate"] = statistics.mean(
                [1.0 if x.get("adopted_stale_advice") else 0.0 for x in items]
            )
        summary[g] = entry
    return {"by_group": summary, "cold_start_first_success_mean": cold_rate}


async def run_experiment(
    *,
    seeds: List[int],
    scenario_ids: List[str],
    max_rounds: int,
    out_dir: Path,
) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    probe = await probe_llm()
    report_base = {
        "schema": "ag.memory.adaptation_experiment_llm/v1",
        "kind": "real_llm_agent_behavior",
        "generated_at": _now(),
        "seeds": seeds,
        "scenarios": scenario_ids,
        "groups": GROUPS,
        "max_rounds": max_rounds,
        "temperature_note": "uses global provider defaults (ChatHarness.chat has no temperature kwarg)",
        "probe": probe,
        "storage": "isolated tempfile (not production storage/agent_memory)",
        "stale_definition": {
            "boundary": "event.t < 1700000000000 或 tags 含 stale/过时",
        },
    }

    if not probe.get("reachable"):
        report = {
            **report_base,
            "status": "blocked",
            "blocked_reason": probe.get("error") or probe.get("probe_error") or "llm_unreachable",
            "n_runs": 0,
            "rows": [],
            "summary": {},
            "failure_cases": [],
            "note": "LLM 不可用；本报告不得被确定性脚本结果替代。",
        }
        jp = out_dir / "agent-memory-adaptation-llm-report.json"
        mp = out_dir / "agent-memory-adaptation-llm-report.md"
        jp.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        mp.write_text(
            "# Agent 记忆真实 LLM 适应实验（BLOCKED）\n\n"
            f"- status: blocked\n- reason: {report['blocked_reason']}\n"
            f"- probe: `{json.dumps(probe, ensure_ascii=False)}`\n",
            encoding="utf-8",
        )
        report["artifacts"] = {"json": str(jp), "md": str(mp)}
        return report

    rows: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []
    raw_runs: List[Dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="ag_mem_llm_exp_") as tmp:
        store = AgentMemoryStore(Path(tmp))
        for seed in seeds:
            for sid in scenario_ids:
                scenario = SCENARIOS[sid]
                for group in GROUPS:
                    team_id, agent_id, _core = prepare_agent(group, store, scenario, seed)
                    round_results = []
                    had_fallback = False
                    for rno in range(max_rounds):
                        rr = await agent_execute(
                            team_id=team_id,
                            agent_id=agent_id,
                            store=store,
                            scenario=scenario,
                            round_no=rno,
                        )
                        if rr["fallback_or_simulated"]:
                            had_fallback = True
                        round_results.append(rr)
                        raw_runs.append(
                            {
                                "seed": seed,
                                "scenario": sid,
                                "group": group,
                                **rr,
                            }
                        )
                        if rr["evaluation"]["success"] and not rr["fallback_or_simulated"]:
                            break

                    # 若任何 round 是 fallback，整行作废为失败（不得记成功）
                    valid_rounds = [x for x in round_results if not x["fallback_or_simulated"]]
                    first_ok = bool(valid_rounds and valid_rounds[0]["evaluation"]["success"])
                    if had_fallback and not valid_rounds:
                        first_ok = False
                    adapt = next(
                        (
                            i
                            for i, x in enumerate(round_results)
                            if x["evaluation"]["success"] and not x["fallback_or_simulated"]
                        ),
                        max_rounds,
                    )

                    precision = recall = fpr = None
                    adopted_bad = False
                    adopted_stale = False
                    inheritance_injected = False
                    if valid_rounds:
                        ev0 = valid_rounds[0]["evaluation"]
                        adopted_bad = bool(ev0.get("adopted_bad_advice"))
                        adopted_stale = bool(ev0.get("adopted_stale_advice"))
                        inheritance_injected = any(
                            r.get("inheritance_injected") for r in valid_rounds
                        )
                    if group == "contaminated_memory" and valid_rounds:
                        ev0 = valid_rounds[0]["evaluation"]
                        # precision: 成功且未采纳坏建议 / 见到污染上下文时的正确甄别
                        saw_contam = bool(ev0.get("contaminated_context"))
                        rejected = first_ok and not adopted_bad
                        tp = 1 if (saw_contam and rejected) else 0
                        fp = 1 if (saw_contam and adopted_bad) else 0
                        fn = 1 if (saw_contam and not rejected) else 0
                        if not saw_contam:
                            # 污染未注入 → 机制失败，记 precision=0
                            precision = recall = fpr = 0.0
                        else:
                            precision = tp / (tp + fp) if (tp + fp) else 0.0
                            recall = tp / (tp + fn) if (tp + fn) else 0.0
                            fpr = fp / max(1, tp + fp)

                    # 非 cold_start 必须有继承注入，否则记机制失败（不算行为成功）
                    mechanism_ok = True
                    if group != "cold_start" and not inheritance_injected:
                        mechanism_ok = False
                        first_ok = False

                    row = {
                        "seed": seed,
                        "scenario": sid,
                        "group": group,
                        "team_id": team_id,
                        "agent_id": agent_id,
                        "first_task_success": first_ok,
                        "adaptation_rounds": adapt,
                        "had_fallback": had_fallback,
                        "negative_transfer": False,
                        "inheritance_injected": inheritance_injected,
                        "mechanism_ok": mechanism_ok,
                        "adopted_bad_advice": adopted_bad,
                        "adopted_stale_advice": adopted_stale,
                        "precision": precision,
                        "recall": recall,
                        "false_positive_rate": fpr,
                        "run_ids": [x["run_id"] for x in round_results],
                        "models": sorted({x["model"] for x in round_results if x.get("model")}),
                        "total_tokens": sum(int((x.get("usage") or {}).get("total_tokens") or 0) for x in round_results),
                        "rounds": [
                            {
                                "run_id": x["run_id"],
                                "success": x["evaluation"]["success"] and not x["fallback_or_simulated"],
                                "score": x["evaluation"]["score"],
                                "fallback": x["fallback_or_simulated"],
                                "usage": x["usage"],
                                "response_excerpt": (x["response"] or "")[:240],
                            }
                            for x in round_results
                        ],
                    }
                    rows.append(row)
                    if not first_ok:
                        failures.append(
                            {
                                "seed": seed,
                                "scenario": sid,
                                "group": group,
                                "run_ids": row["run_ids"],
                                "detail": (round_results[0]["response"] if round_results else "")[:200],
                                "fallback": had_fallback,
                            }
                        )

    # 硬断言：不得含 fallback 却标记成功
    for r in rows:
        for rd in r["rounds"]:
            if rd["fallback"] and rd["success"]:
                raise RuntimeError("invariant violated: fallback marked success")

    summary = aggregate(rows)
    report = {
        **report_base,
        "status": "completed",
        "n_runs": len(rows),
        "n_llm_calls": len(raw_runs),
        "summary": summary,
        "rows": rows,
        "raw_runs": raw_runs,
        "failure_cases": failures[:80],
        "model": probe.get("probe_model") or probe.get("model"),
        "provider": probe.get("probe_provider") or probe.get("provider"),
    }

    jp = out_dir / "agent-memory-adaptation-llm-report.json"
    mp = out_dir / "agent-memory-adaptation-llm-report.md"
    # 原始 run 明细单独存，避免主报告过大时丢失
    raw_path = out_dir / "agent-memory-adaptation-llm-raw-runs.json"
    raw_path.write_text(json.dumps(raw_runs, ensure_ascii=False, indent=2), encoding="utf-8")
    report_for_disk = dict(report)
    # keep raw_runs in main report too for auditability (may be large but required by todos)
    jp.write_text(json.dumps(report_for_disk, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Agent 记忆真实 LLM 行为适应实验报告",
        "",
        f"- status: **{report['status']}**",
        f"- generated_at: {report['generated_at']}",
        f"- model/provider: `{report.get('model')}` / `{report.get('provider')}`",
        f"- seeds: {seeds}",
        f"- scenarios: {scenario_ids}",
        f"- max_rounds: {max_rounds}",
        f"- n_cells: {report['n_runs']} · n_llm_calls: {report['n_llm_calls']}",
        f"- storage: {report['storage']}",
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
        lines.append(f"- negative_transfer_rate={s['negative_transfer_rate']:.3f}")
        lines.append(f"- fallback_rate={s['fallback_rate']:.3f}")
        if "inheritance_injected_rate" in s:
            lines.append(f"- inheritance_injected_rate={s['inheritance_injected_rate']:.3f}")
        if g == "contaminated_memory":
            lines.append(
                f"- precision={s.get('precision_mean')} recall={s.get('recall_mean')} "
                f"fp={s.get('false_positive_rate_mean')} adopted_bad={s.get('adopted_bad_rate')}"
            )
        if g == "stale_memory":
            lines.append(f"- adopted_stale_rate={s.get('adopted_stale_rate')}")
        lines.append("")
    lines.append("## 失败样本（截断）")
    for f in failures[:25]:
        lines.append(
            f"- seed={f['seed']} {f['group']}/{f['scenario']} fallback={f['fallback']} "
            f"runs={f['run_ids']} :: {(f.get('detail') or '')[:120]}"
        )
    lines.append("")
    lines.append("## 产物")
    lines.append(f"- JSON: `{jp}`")
    lines.append(f"- raw runs: `{raw_path}`")
    mp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report["artifacts"] = {"json": str(jp), "md": str(mp), "raw_runs": str(raw_path)}
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="7")
    ap.add_argument("--scenarios", default="es_scale,centos_migrate,cost_ri")
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--output-dir", default=str(ROOT / "docs" / "reports"))
    args = ap.parse_args()
    seeds = [int(x.strip()) for x in args.seeds.split(",") if x.strip()]
    scenarios = [x.strip() for x in args.scenarios.split(",") if x.strip()]
    for s in scenarios:
        if s not in SCENARIOS:
            print(json.dumps({"ok": False, "error": f"unknown scenario {s}"}))
            return 2
    report = asyncio.run(
        run_experiment(
            seeds=seeds,
            scenario_ids=scenarios,
            max_rounds=args.rounds,
            out_dir=Path(args.output_dir),
        )
    )
    print(
        json.dumps(
            {
                "ok": True,
                "status": report.get("status"),
                "n_runs": report.get("n_runs"),
                "n_llm_calls": report.get("n_llm_calls"),
                "artifacts": report.get("artifacts"),
                "blocked_reason": report.get("blocked_reason"),
            },
            ensure_ascii=False,
        )
    )
    return 0 if report.get("status") in ("completed", "blocked") else 1


if __name__ == "__main__":
    raise SystemExit(main())
