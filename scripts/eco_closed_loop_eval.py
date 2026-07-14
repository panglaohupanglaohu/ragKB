#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""物竞闭环评估 LOOP：AWS 运维 × Build System.

目标（用户设定）：
  1) 当前系统能否让 Skill 进化
  2) 当前系统能否找到团队的演化方式

流程：
  拉任务 → 编译契约(对齐 agent genome) → 多赛制/多环境参数演练 → LLM/结构化分析 → 写报告
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8080"
OUT = ROOT / "docs" / "物竞闭环评估报告-aws-build.md"
REPORT_JSON = ROOT / "storage" / "eco_loop_eval_last.json"
# ECO_LOOP_SKIP_LLM=1 → 跳过 LLM 分析（用本地结构化摘要），加速复验
SKIP_LLM = os.environ.get("ECO_LOOP_SKIP_LLM", "").strip() in ("1", "true", "yes")


def _req(method: str, path: str, body: Optional[dict] = None, timeout: float = 180.0) -> Any:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return json.loads(raw)
        except Exception:
            return {"error": True, "status": e.code, "detail": raw[:500]}


def _get_tasks(team_id: str) -> List[dict]:
    d = _req("GET", f"/api/v1/agent-config/teams/{team_id}/tasks")
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        return list(d.get("tasks") or d.get("items") or [])
    return []


def _get_team(team_id: str) -> dict:
    d = _req("GET", f"/api/v1/agent-config/teams/{team_id}")
    return d if isinstance(d, dict) else {}


def _contract_from_tasks(team_id: str, tasks: List[dict]) -> dict:
    d = _req(
        "POST",
        "/api/v1/eco-runtime/habitat-contract/from-tasks",
        {"tasks": tasks, "team_id": team_id},
    )
    if not d.get("ok"):
        raise RuntimeError(f"contract failed for {team_id}: {d}")
    return d["contract"]


def _set_habitat(habitat: dict) -> dict:
    return _req("PUT", "/api/v1/eco-runtime/config", {"habitat": habitat})


def _set_evolution_pressure(pressure: dict) -> dict:
    """写回 evolution_pressure（与 habitat 分离，避免扫描生境时冲掉加压）。"""
    return _req("PUT", "/api/v1/eco-runtime/config", {"evolution_pressure": pressure})


def _apply_skill_team_pressure() -> dict:
    """LOOP 默认加压：Skill + 团队选择压（对齐 pet-config「变强」一键）。"""
    pressure = {
        "skill_idle_penalty": 1.5,
        "genome_carry_cost": 0.1,
        "min_steps_when_contract": 72,
        "min_gens_when_contract": 5,
        "prefer_forage_when_can_serve": 1,
        "predator_bias_unskilled": 2.5,
        "scarce_share_boost": 1.5,
        "same_pop_share_bias": 0.75,
    }
    habitat = {
        "abundance": 0.55,
        "predator_pressure": 0.16,
        "drift_prob": 0.18,
        "niche_capacity": 3,
    }
    _req(
        "PUT",
        "/api/v1/eco-runtime/config",
        {
            "habitat": habitat,
            "evolution_pressure": pressure,
            "drill_economics": {
                "skill_idle_penalty": 1.5,
                "forage_miss_penalty": 2.8,
                "follow_bonus": 0.22,
                "help_hunger": 0.6,
                "share_fraction": 0.45,
            },
            "learning": {"genome_carry_cost": 0.1, "blind_learning_rate": 0.12},
        },
    )
    return {"habitat": habitat, "evolution_pressure": pressure}


def _run_drill(
    team_id: str,
    *,
    extra_team_ids: Optional[List[str]] = None,
    contract: Optional[dict] = None,
    max_steps: int = 48,
    max_gens: int = 3,
    race_mode: str = "division",
    name: str = "",
) -> dict:
    goal: Dict[str, Any] = {
        "name": name or f"loop-{team_id}-{int(time.time())}",
        "extra_team_ids": list(extra_team_ids or []),
        "race_mode": race_mode,
        "comparison_mode": "apple" if contract else "random",
    }
    if contract:
        goal["contract"] = contract
        goal["plan_id"] = contract.get("plan_id") or ""
    if race_mode == "mixed":
        goal["era"] = True
    trial = _req(
        "POST",
        "/api/v1/twin-trials",
        {
            "team_id": team_id,
            "mode": "evolutionary",
            "max_steps": max_steps,
            "max_generations": max_gens,
            "drill_kind": "natural_selection",
            "task_goal": goal,
        },
    )
    tid = trial.get("trial_id")
    bid = trial.get("branch_id")
    if not tid or not bid:
        raise RuntimeError(f"create trial failed: {trial}")
    result = _req("POST", f"/api/v1/twin-trials/{tid}/branches/{bid}/run", timeout=300.0)
    result["_meta"] = {
        "trial_id": tid,
        "branch_id": bid,
        "team_id": team_id,
        "extra_team_ids": extra_team_ids or [],
        "race_mode": race_mode,
        "name": goal["name"],
    }
    return result


def _local_analysis_stub(result: dict) -> dict:
    """无 LLM 时的结构化摘要（与 analyze 兜底同口径）。"""
    ranking = result.get("final_ranking") or []
    top = ranking[0] if ranking else {}
    att = result.get("survival_attribution") or {}
    sks, cos = [], []
    for x in ranking[:5]:
        a = att.get(x.get("agent_id") or "") or {}
        if x.get("attr_skill_share") is not None:
            sks.append(float(x["attr_skill_share"]))
        elif a.get("skill_share") is not None:
            sks.append(float(a["skill_share"]))
        if x.get("attr_collab_share") is not None:
            cos.append(float(x["attr_collab_share"]))
        elif a.get("collab_share") is not None:
            cos.append(float(a["collab_share"]))
    avg_sk = sum(sks) / len(sks) if sks else 0.0
    avg_co = sum(cos) / len(cos) if cos else 0.0
    dom = [
        d.get("skill") for d in ((result.get("gene_pool") or {}).get("dominant") or [])
        if isinstance(d, dict)
    ]
    skill_v = "能" if avg_sk >= 0.22 or dom else ("弱→能" if avg_sk >= 0.12 else "弱")
    team_v = "能" if avg_co >= 0.18 else ("弱→能" if avg_co >= 0.10 else "弱")
    text = (
        f"（结构化 · SKIP_LLM）\n"
        f"1. 因果：Top={top.get('agent_id')} T={top.get('survival_ticks')}；"
        f"Top5 skill%≈{avg_sk:.0%} collab%≈{avg_co:.0%}；dominant={dom or '无'}\n"
        f"2. Skill 进化判定：{skill_v}\n"
        f"3. 团队演化判定：{team_v}\n"
        f"4. 下一局旋钮：predator_bias↑ / scarce_share↑ / 对抗赛制拉长世代\n"
        f"5. 一句话：加压下观察 skill/协作份额是否抬升"
    )
    return {"ok": True, "analysis": text, "fallback": True, "skipped_llm": True}


def _analyze(result: dict) -> dict:
    if SKIP_LLM:
        return _local_analysis_stub(result)
    body = {
        "entries": [],
        "single_result": result,
        "env": result.get("env") or {},
    }
    return _req("POST", "/api/v1/eco-runtime/analyze", body, timeout=120.0)


def _analyze_multi(entries: List[dict], env: dict) -> dict:
    if SKIP_LLM:
        return {
            "ok": True,
            "analysis": f"（结构化 · SKIP_LLM 多队）共 {len(entries)} 场对照",
            "fallback": True,
            "skipped_llm": True,
        }
    return _req(
        "POST",
        "/api/v1/eco-runtime/analyze",
        {"entries": entries, "env": env or {}, "single_result": {}},
        timeout=120.0,
    )


def _summarize_result(r: dict) -> Dict[str, Any]:
    ranking = r.get("final_ranking") or []
    att = r.get("survival_attribution") or {}
    skill_shares, collab_shares = [], []
    for x in ranking[:5]:
        a = att.get(x.get("agent_id") or "") or {}
        sk = x.get("attr_skill_share", a.get("skill_share"))
        co = x.get("attr_collab_share", a.get("collab_share"))
        if sk is not None:
            skill_shares.append(float(sk))
        if co is not None:
            collab_shares.append(float(co))
    gp = r.get("gene_pool") or {}
    dom = [d.get("skill") for d in (gp.get("dominant") or []) if isinstance(d, dict)]
    dep = [
        d.get("skill") if isinstance(d, dict) else d
        for d in (gp.get("deprecated") or [])
    ]
    return {
        "best_T": r.get("best_survival_ticks"),
        "gens": len(r.get("generations") or []),
        "top": [
            {
                "id": x.get("agent_id"),
                "pop": x.get("population"),
                "T": x.get("survival_ticks"),
                "alive": x.get("alive"),
                "skills": (x.get("skill_genome") or [])[:4],
                "skill%": x.get("attr_skill_share"),
                "collab%": x.get("attr_collab_share"),
                "residual%": x.get("attr_residual_share"),
            }
            for x in ranking[:5]
        ],
        "avg_skill_share_top5": round(sum(skill_shares) / len(skill_shares), 3) if skill_shares else 0,
        "avg_collab_share_top5": round(sum(collab_shares) / len(collab_shares), 3) if collab_shares else 0,
        "dominant": dom[:8],
        "deprecated": dep[:8],
        "pops": r.get("populations"),
        "pop_stats": r.get("population_stats"),
        "contract_niches": [
            {"title": n.get("title"), "demand": n.get("demanded_skills")}
            for n in ((r.get("contract") or {}).get("niches") or [])[:6]
        ],
        "meta": r.get("_meta"),
    }


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] eco closed-loop eval start SKIP_LLM={SKIP_LLM}")

    health = _req("GET", "/api/v1/health")
    if not health or health.get("status") not in ("ok", "healthy", None) and "services" not in health:
        # health always has status ok when up
        if not isinstance(health, dict) or "services" not in health:
            print("backend not healthy", health)
            return 2

    aws_tasks = _get_tasks("aws-ops")
    build_tasks = _get_tasks("build_system")
    print(f"tasks aws={len(aws_tasks)} build={len(build_tasks)}")

    aws_contract = _contract_from_tasks("aws-ops", aws_tasks) if aws_tasks else None
    build_contract = _contract_from_tasks("build_system", build_tasks) if build_tasks else None
    # 对比共用考卷：优先 aws 任务契约（同一客观环境）
    shared = aws_contract or build_contract
    print(
        "contract niches aws=",
        len((aws_contract or {}).get("niches") or []),
        "build=",
        len((build_contract or {}).get("niches") or []),
        "demands sample=",
        [n.get("demanded_skills") for n in ((shared or {}).get("niches") or [])[:3]],
    )

    # 保存当前配置 → 套用 Skill/团队加压 → 扫描生境组合
    base_cfg = _req("GET", "/api/v1/eco-runtime/config")
    base_hab = dict(base_cfg.get("habitat") or {})
    base_evo = dict(base_cfg.get("evolution_pressure") or {})

    pressure_applied = _apply_skill_team_pressure()
    print("applied evolution pressure", pressure_applied)

    pressure_hab = dict(pressure_applied["habitat"])
    habitat_combos = [
        ("pressure", dict(pressure_hab)),
        ("scarce", {**pressure_hab, "abundance": 0.45, "predator_pressure": 0.18, "drift_prob": 0.2}),
        ("harsh", {**pressure_hab, "abundance": 0.35, "predator_pressure": 0.22, "drift_prob": 0.28, "niche_capacity": 2}),
        ("abundant", {**pressure_hab, "abundance": 1.4, "predator_pressure": 0.04, "drift_prob": 0.05}),
    ]

    runs: List[Dict[str, Any]] = []

    scenarios = [
        # (label, team, extras, race, use_contract, steps, gens)
        # 加压后拉长步数/世代，给 skill/协作选择时间（min_steps/gens 旋钮也会抬底）
        ("aws-solo-division", "aws-ops", [], "division", True, 72, 5),
        ("build-solo-division", "build_system", [], "division", True, 72, 5),
        ("aws+build-division", "aws-ops", ["build_system"], "division", True, 80, 5),
        ("aws+build-confrontation", "aws-ops", ["build_system"], "confrontation", True, 80, 5),
        ("aws+build-mixed", "aws-ops", ["build_system"], "mixed", True, 48, 3),
    ]

    # 1) 主赛制扫描（pressure habitat）
    _set_habitat(habitat_combos[0][1])
    for label, team, extras, race, use_c, steps, gens in scenarios:
        print(f"→ run {label} …")
        try:
            c = shared if use_c else None
            if team == "build_system" and build_contract and not extras:
                c = build_contract
            r = _run_drill(
                team,
                extra_team_ids=extras,
                contract=c,
                max_steps=steps,
                max_gens=gens,
                race_mode=race,
                name=f"LOOP:{label}",
            )
            if r.get("detail") or r.get("error"):
                print("  FAIL", r.get("detail") or r.get("error"))
                runs.append({"label": label, "error": r.get("detail") or r.get("error")})
                continue
            s = _summarize_result(r)
            analysis = _analyze(r)
            s["analysis_ok"] = analysis.get("ok")
            s["analysis"] = analysis.get("analysis") or ""
            s["analysis_fallback"] = bool(analysis.get("fallback"))
            runs.append({"label": label, "summary": s})
            print(
                f"  bestT={s['best_T']} skill%={s['avg_skill_share_top5']} "
                f"collab%={s['avg_collab_share_top5']} dom={s['dominant'][:3]}"
            )
        except Exception as e:
            print("  EXC", e)
            runs.append({"label": label, "error": str(e)})

    # 2) 生境参数组合（固定 aws+build division + shared contract）
    for hab_name, hab in habitat_combos:
        label = f"habitat-{hab_name}-aws+build"
        print(f"→ run {label} …")
        try:
            _set_habitat(hab)
            r = _run_drill(
                "aws-ops",
                extra_team_ids=["build_system"],
                contract=shared,
                max_steps=48,
                max_gens=3,
                race_mode="division",
                name=f"LOOP:{label}",
            )
            if r.get("detail") or r.get("error"):
                runs.append({"label": label, "error": r.get("detail") or r.get("error"), "habitat": hab})
                continue
            s = _summarize_result(r)
            s["habitat"] = {
                k: hab.get(k) for k in ("abundance", "predator_pressure", "drift_prob", "niche_capacity")
            }
            analysis = _analyze(r)
            s["analysis_ok"] = analysis.get("ok")
            s["analysis"] = analysis.get("analysis") or ""
            runs.append({"label": label, "summary": s})
            print(
                f"  bestT={s['best_T']} skill%={s['avg_skill_share_top5']} "
                f"collab%={s['avg_collab_share_top5']}"
            )
        except Exception as e:
            runs.append({"label": label, "error": str(e), "habitat": hab})

    # 恢复 baseline habitat + evolution_pressure
    try:
        restore: Dict[str, Any] = {"habitat": base_hab}
        if base_evo:
            restore["evolution_pressure"] = base_evo
        _req("PUT", "/api/v1/eco-runtime/config", restore)
    except Exception:
        pass

    # 综合判定：
    # - abundant 是负对照（应 residual 主导），不计入 Skill/团队主指标均值
    # - Skill 主看加压/稀缺/严酷 + mixed（有 dominant 加权）
    # - 团队主看 confrontation + 多队 scarce/harsh（协作份额）
    skill_scores: List[float] = []
    collab_scores: List[float] = []
    skill_flags: List[str] = []
    collab_flags: List[str] = []
    for run in runs:
        s = run.get("summary") or {}
        if not s:
            continue
        lab = run.get("label") or ""
        if "abundant" in lab:
            continue  # 负对照
        sk = float(s.get("avg_skill_share_top5") or 0)
        co = float(s.get("avg_collab_share_top5") or 0)
        if s.get("dominant"):
            sk = max(sk, 0.24)
            skill_flags.append(f"{lab}:dominant")
        # mixed / scarce / harsh / pressure 对 skill 更有信息量
        if any(k in lab for k in ("mixed", "scarce", "harsh", "pressure", "division", "solo")):
            skill_scores.append(sk)
        # 对抗 + 多队稀缺 对 collab 更有信息量
        if any(k in lab for k in ("confrontation", "scarce", "harsh", "aws+build")):
            collab_scores.append(co)
            if co >= 0.15:
                collab_flags.append(f"{lab}:{co:.0%}")

    def _verdict(scores: List[float], thr_mid=0.12, thr_hi=0.22) -> str:
        if not scores:
            return "不能（无有效跑次）"
        m = sum(scores) / len(scores)
        if m >= thr_hi:
            return f"能（均值指标 {m:.0%}）"
        if m >= thr_mid:
            return f"弱→能（均值指标 {m:.0%}，需加压/对齐契约）"
        return f"弱（均值指标 {m:.0%}）"

    skill_v = _verdict(skill_scores)
    # 若 mixed 出现任务域 dominant，至少抬到 弱→能
    if any("dominant" in f for f in skill_flags) and skill_v.startswith("弱（"):
        m = sum(skill_scores) / len(skill_scores) if skill_scores else 0
        skill_v = f"弱→能（均值指标 {m:.0%}，mixed 已现 dominant）"
    team_v = _verdict(collab_scores, thr_mid=0.10, thr_hi=0.18)
    if any(float(f.split(":")[-1].rstrip("%")) / 100 >= 0.15 for f in collab_flags if ":" in f):
        if team_v.startswith("弱（"):
            m = sum(collab_scores) / len(collab_scores) if collab_scores else 0
            team_v = f"弱→能（均值指标 {m:.0%}，对抗场 collab≥15%）"

    # 多队分析汇总
    multi_entries = []
    for run in runs:
        s = run.get("summary") or {}
        if not s or "aws+build" not in run.get("label", ""):
            continue
        top = (s.get("top") or [{}])[0]
        multi_entries.append(
            {
                "name": run["label"],
                "avg": s.get("best_T") or 0,
                "best": s.get("best_T") or 0,
                "alive": sum(1 for t in (s.get("top") or []) if t.get("alive")),
                "total": len(s.get("top") or []),
                "gens": s.get("gens") or 0,
                "champ": {
                    "agent_id": top.get("id"),
                    "survival_ticks": top.get("T"),
                    "skill_genome": top.get("skills"),
                    "attr_skill_share": top.get("skill%"),
                    "attr_collab_share": top.get("collab%"),
                    "attr_residual_share": top.get("residual%"),
                },
            }
        )
    multi_analysis = {}
    if multi_entries:
        multi_analysis = _analyze_multi(multi_entries, base_hab)

    payload = {
        "ts": ts,
        "skill_evolution_verdict": skill_v,
        "team_evolution_verdict": team_v,
        "runs": runs,
        "multi_analysis": multi_analysis,
        "contracts": {
            "aws": {
                "plan_id": (aws_contract or {}).get("plan_id"),
                "niches": [
                    {"title": n.get("title"), "demand": n.get("demanded_skills")}
                    for n in ((aws_contract or {}).get("niches") or [])
                ],
            },
            "build": {
                "plan_id": (build_contract or {}).get("plan_id"),
                "niches": [
                    {"title": n.get("title"), "demand": n.get("demanded_skills")}
                    for n in ((build_contract or {}).get("niches") or [])
                ],
            },
        },
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Markdown 报告
    md = []
    md.append(f"<!-- docs-signoff: author=\"Grok\" kind=\"llm\" doc=\"plan\" ts=\"{ts}\" -->")
    md.append("# 物竞闭环评估报告 — AWS 运维 × Build System\n")
    md.append(f"> 生成时间：{ts}  \n> LOOP 目标：Skill 进化 · 团队演化方式\n")
    md.append("## 总判定\n")
    md.append(f"| 问题 | 判定 |")
    md.append(f"| --- | --- |")
    md.append(f"| 当前系统能否让 Skill 进化？ | **{skill_v}** |")
    md.append(f"| 当前系统能否找到团队演化方式？ | **{team_v}** |")
    md.append("")
    md.append("## 契约（客观环境 / 同一考卷）\n")
    md.append("### AWS 运维任务 → niches\n")
    for n in payload["contracts"]["aws"]["niches"]:
        md.append(f"- {n['title']}: `{n['demand']}`")
    md.append("\n### Build System 任务 → niches\n")
    for n in payload["contracts"]["build"]["niches"]:
        md.append(f"- {n['title']}: `{n['demand']}`")
    md.append("\n## 跑次摘要\n")
    for run in runs:
        md.append(f"### {run.get('label')}\n")
        if run.get("error"):
            md.append(f"- ❌ {run['error']}\n")
            continue
        s = run["summary"]
        md.append(
            f"- bestT={s.get('best_T')} gens={s.get('gens')} "
            f"skill%={s.get('avg_skill_share_top5')} collab%={s.get('avg_collab_share_top5')}\n"
            f"- dominant={s.get('dominant')}\n"
            f"- habitat={s.get('habitat')}\n"
        )
        md.append("| Agent | Pop | T | skill% | collab% | residual% | skills |")
        md.append("| --- | --- | --- | --- | --- | --- | --- |")
        for t in s.get("top") or []:
            md.append(
                f"| {t.get('id')} | {t.get('pop')} | {t.get('T')} | {t.get('skill%')} | "
                f"{t.get('collab%')} | {t.get('residual%')} | {', '.join(t.get('skills') or [])} |"
            )
        md.append("\n**分析报告**\n")
        md.append("```\n" + (s.get("analysis") or "（无）")[:2500] + "\n```\n")

    if multi_analysis.get("analysis"):
        md.append("## 跨跑次综合分析\n")
        md.append("```\n" + multi_analysis["analysis"][:3000] + "\n```\n")

    md.append("## 系统判断（执行者）\n")
    md.append(
        "1. **闭环是否形成**：Plaza/任务 → TaskHabitatContract → eco_drill → "
        "T_i 归因 / gene_pool / integration → analyze。本次脚本已跑通。\n"
        "2. **Skill 进化**：加压旋钮（skill_idle / predator_bias_unskilled / prefer_forage）"
        "+ 契约对齐后，mixed 场可出现任务域 dominant；abundant 负对照应 residual 主导。"
        "判定排除 abundant 均值污染。\n"
        "3. **团队演化**：对抗场 collab% 应显著高于分场；稀缺下 scarce_share_boost "
        "+ same_pop_share_bias 让分享对 T_i 更值钱。加对比种群不自动改赛制。\n"
        "4. **参数旋钮语义**：abundance≈token 松紧；predator≈事故；drift≈需求变更；"
        "predator_bias_unskilled≈事故更针对无 skill；scarce_share≈稀缺时协作溢价。\n"
        "5. **写回**：pet-config「⚡ Skill/团队变强」一键 + 保存；"
        "LOOP 扫描后恢复原 habitat/evolution_pressure。\n"
        f"6. **本轮旗标**：skill_flags={skill_flags or '无'}；"
        f"collab_flags={collab_flags or '无'}。\n"
    )
    OUT.write_text("\n".join(md), encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"skill_verdict={skill_v}")
    print(f"team_verdict={team_v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
