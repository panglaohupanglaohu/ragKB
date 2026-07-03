# -*- coding: utf-8 -*-
"""Nightly 全局循环任务 — 每日技能重分类 + 可持续性报告 (全局优化 GP2-4).

做三件事（全部幂等，可重复运行）:
1. 对所有已知团队执行 skill_classifier.reclassify_team（毕业/降级周期推进）
2. 对所有团队跑 sustainability 评估，尝试推进 cost_efficiency 棘轮
3. 报告落盘 storage/nightly_reports/{date}_global_loops.json

用法:
    python src/backend/scripts/nightly_global_loops.py [--teams t1,t2] [--dry-run]
可挂入既有 launchd 机制（config/launchd/，参照 nightly-4h-optimize.plist）。
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src" / "backend"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("nightly_global_loops")

REPORT_DIR = ROOT / "storage" / "nightly_reports"


def discover_teams() -> list:
    """从熟练度缓存与试炼存储发现团队列表."""
    teams = set()
    prof_dir = ROOT / "storage" / "skill_proficiency"
    if prof_dir.exists():
        for f in prof_dir.glob("*.json"):
            teams.add(f.stem)
    trials_file = ROOT / "storage" / "trials" / "trials.json"
    if trials_file.exists():
        try:
            data = json.loads(trials_file.read_text(encoding="utf-8"))
            for t in data.get("trials", {}).values():
                if t.get("team_id"):
                    teams.add(t["team_id"])
        except Exception as e:
            logger.warning(f"trials.json 读取失败: {e}")
    return sorted(teams)


def run(teams: list, dry_run: bool = False) -> dict:
    from agents.skill_classifier import get_classification_store
    from agents.sustainability import collect_team_usage, evaluate_team
    from agents.ratchet_ledger import get_ratchet_ledger

    report = {
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "teams": teams,
        "dry_run": dry_run,
        "reclassification": {},
        "sustainability": {},
        "ratchet": {},
    }

    cls_store = get_classification_store()
    ledger = get_ratchet_ledger()

    for team_id in teams:
        # 1. 技能重分类（毕业/降级周期推进）
        try:
            skills = []
            try:
                from agents.skill_library import get_skill_library
                skills = [s for s in get_skill_library().browse(team_id=team_id) if s.get("_is_own")]
            except Exception as e:
                logger.info(f"[{team_id}] 技能库不可用，跳过重分类: {e}")
            if skills and not dry_run:
                from agents.skill_classifier_routes import _build_evidence_fn
                result = cls_store.reclassify_team(team_id, skills, evidence_fn=_build_evidence_fn(team_id))
                report["reclassification"][team_id] = {
                    "pools": result["pools"], "changes": result["changes"]}
            else:
                report["reclassification"][team_id] = {"skipped": True, "skill_count": len(skills)}
        except Exception as e:
            report["reclassification"][team_id] = {"error": str(e)}

        # 2. 可持续性评估 + cost 棘轮
        try:
            usage = collect_team_usage(team_id)
            result = evaluate_team(usage)
            report["sustainability"][team_id] = {
                "grade": result["grade"],
                "token_efficiency": result["token_efficiency"],
                "sustainability_score": result["sustainability_score"],
                "data_quality": result["data_quality"],
                "recommendations": result["recommendations"],
            }
            if not dry_run and result["token_efficiency"] > 0:
                current = ledger.get(f"cost_efficiency:{team_id}")
                tol = (current["value"] * 0.02) if current else 0.0
                report["ratchet"][team_id] = ledger.advance(
                    f"cost_efficiency:{team_id}", result["token_efficiency"],
                    evidence={"source": "nightly"}, tolerance=tol)
        except Exception as e:
            report["sustainability"][team_id] = {"error": str(e)}

    # G1-3: C/D 级团队自动生成议事广场整改议题（settings.auto_plaza_sustainability_topics 可关）
    try:
        settings_path = ROOT / "config" / "settings.json"
        settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
        if settings.get("auto_plaza_sustainability_topics", True) and not dry_run:
            from agents.sustainability import build_plaza_topics, collect_team_usage as _ctu, evaluate_group
            group = evaluate_group([_ctu(t) for t in teams])
            topics = build_plaza_topics(group)
            if topics:
                from agents.plaza_engine import get_plaza_engine
                engine = get_plaza_engine()
                plazas = engine.list_plazas()
                if plazas:
                    created = []
                    for t in topics[:3]:  # 每晚最多 3 个议题，防骚扰
                        disc = engine.create_discussion(plazas[0].id, t["topic"], t["description"])
                        if disc:
                            created.append(disc.id)
                    report["plaza_topics"] = created
                    logger.info(f"💬 G1-3: 创建 {len(created)} 个可持续整改议题")
                else:
                    report["plaza_topics"] = {"skipped": "无可用 plaza"}
    except Exception as e:
        report["plaza_topics"] = {"error": str(e)}

    # C-3.7: 自动触发进化运行（settings.auto_evolution_nightly 可关，默认 false）
    try:
        if settings.get("auto_evolution_nightly", False) and not dry_run:
            import asyncio
            from sandbox.evolution_bridge import get_evolution_bridge
            from sandbox.scenario_store import get_scenario_store
            from sandbox.evolution_api import _trial_ids_for
            evo_report = {"triggered": [], "skipped": [], "errors": []}
            bridge = get_evolution_bridge()
            sc_store = get_scenario_store()
            scenarios = sc_store.list()
            for team_id in teams:
                for sc in scenarios:
                    try:
                        trial_ids = _trial_ids_for(team_id, sc.scenario_id)
                        if len(trial_ids) < 2:
                            evo_report["skipped"].append(f"{team_id}/{sc.scenario_id}: trial<2")
                            continue
                        weak = bridge.identify_weak_skills(team_id, sc.scenario_id, trial_ids)
                        if weak:
                            run_result = asyncio.run(bridge.start_run(
                                team_id=team_id,
                                scenario_id=sc.scenario_id,
                                trial_ids=trial_ids,
                                skill_names=[w["skill_name"] for w in weak[:3]],
                                triggered_by="nightly",
                            ))
                            evo_report["triggered"].append({
                                "team_id": team_id, "scenario_id": sc.scenario_id,
                                "run_id": run_result.run_id,
                                "weak_skills": [w["skill_name"] for w in weak[:3]],
                            })
                            logger.info(f"🌙 C-3.7: 自动触发进化 {team_id}/{sc.scenario_id} → {run_result.run_id}")
                    except Exception as e:
                        evo_report["errors"].append(f"{team_id}/{sc.scenario_id}: {e}")
            report["evolution_auto"] = evo_report
    except Exception as e:
        report["evolution_auto"] = {"error": str(e)}

    if not dry_run:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path = REPORT_DIR / f"{date}_global_loops.json"
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        report["report_path"] = str(path)
        logger.info(f"📄 nightly 报告: {path}")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--teams", default="", help="逗号分隔的团队列表，默认自动发现")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    team_list = [t.strip() for t in args.teams.split(",") if t.strip()] or discover_teams()
    if not team_list:
        print(json.dumps({"ok": True, "note": "未发现团队，无事可做"}, ensure_ascii=False))
        sys.exit(0)
    result = run(team_list, dry_run=args.dry_run)
    print(json.dumps({"ok": True, "teams": len(team_list),
                      "report": result.get("report_path", "(dry-run)")}, ensure_ascii=False))
