# -*- coding: utf-8 -*-
"""Proficiency Store — 技能使用记录 + 熟练度持久化 (v4 A-4.3/A-4.4).

- SkillUsageRecord: 按 trial 追加写 storage/twin_trials/{trial_id}_skill_usage.jsonl
- SkillProficiency: 缓存写 storage/skill_proficiency/{team_id}.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import SkillProficiency, SkillUsageRecord

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[3]
USAGE_DIR = _ROOT / "storage" / "twin_trials"
PROF_DIR = _ROOT / "storage" / "skill_proficiency"


class ProficiencyStore:
    """技能使用记录（jsonl 追加）与熟练度聚合缓存（json）."""

    def __init__(self, usage_dir: Optional[Path] = None, prof_dir: Optional[Path] = None):
        self._usage_dir = usage_dir or USAGE_DIR
        self._prof_dir = prof_dir or PROF_DIR
        self._usage_dir.mkdir(parents=True, exist_ok=True)
        self._prof_dir.mkdir(parents=True, exist_ok=True)

    # ── 使用记录 ──────────────────────────────────────────

    def append_usages(self, trial_id: str, records: List[SkillUsageRecord]) -> int:
        """批量追加 usage 记录到 trial 对应的 jsonl."""
        if not trial_id or not records:
            return 0
        path = self._usage_dir / f"{trial_id}_skill_usage.jsonl"
        with path.open("a", encoding="utf-8") as f:
            for r in records:
                d = r.to_dict() if hasattr(r, "to_dict") else dict(r)
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
        return len(records)

    def load_usages(self, trial_id: str) -> List[Dict[str, Any]]:
        """读取某 trial 全部 usage 记录."""
        path = self._usage_dir / f"{trial_id}_skill_usage.jsonl"
        if not path.exists():
            return []
        records = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records

    def aggregate_trial(self, trial_id: str) -> List[Dict[str, Any]]:
        """聚合某 trial 的 per-skill 统计 (B-2.2 数据源)."""
        usages = self.load_usages(trial_id)
        return aggregate_usages(usages)

    # ── 熟练度缓存 ────────────────────────────────────────

    def _prof_path(self, team_id: str) -> Path:
        safe = "".join(c for c in (team_id or "default") if c.isalnum() or c in "-_") or "default"
        return self._prof_dir / f"{safe}.json"

    def load_proficiency(self, team_id: str) -> Dict[str, Dict[str, Any]]:
        """读取团队熟练度缓存. key = f"{agent_id}::{skill_name}" """
        path = self._prof_path(team_id)
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"熟练度缓存读取失败 ({team_id}): {e}")
            return {}

    def save_proficiency(self, team_id: str, data: Dict[str, Dict[str, Any]]) -> None:
        path = self._prof_path(team_id)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)

    def get_agent_proficiency(self, team_id: str, agent_id: str) -> Dict[str, float]:
        """获取某 agent 的 skill -> success_rate 映射 (twin spawn 用)."""
        data = self.load_proficiency(team_id)
        result: Dict[str, float] = {}
        prefix = f"{agent_id}::"
        for key, prof in data.items():
            if key.startswith(prefix):
                result[prof.get("skill_name", key[len(prefix):])] = float(prof.get("success_rate", 0.5))
        return result

    def update_from_trial(self, team_id: str, trial_id: str,
                          scenario_category: str = "general") -> Dict[str, Any]:
        """trial 完成后增量更新熟练度缓存 (A-4.4)."""
        usages = self.load_usages(trial_id)
        if not usages:
            return {"updated": 0}
        data = self.load_proficiency(team_id)
        # 按 agent x skill 分组
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for u in usages:
            key = f"{u.get('agent_id','')}::{u.get('skill_name','')}"
            grouped.setdefault(key, []).append(u)

        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        for key, items in grouped.items():
            agent_id, skill_name = key.split("::", 1)
            prev = data.get(key, {
                "skill_name": skill_name, "agent_id": agent_id,
                "scenario_category": scenario_category,
                "total_uses": 0, "success_count": 0,
                "success_rate": 0.5, "avg_reward_delta": 0.0, "trend": [],
            })
            uses = len(items)
            succ = sum(1 for i in items if i.get("outcome") == "success")
            trial_rate = succ / uses if uses else 0.0
            total = prev["total_uses"] + uses
            success_total = prev["success_count"] + succ
            reward_sum = prev.get("avg_reward_delta", 0.0) * prev["total_uses"] + sum(
                float(i.get("reward_delta", 0)) for i in items)
            prev.update({
                "total_uses": total,
                "success_count": success_total,
                "success_rate": round(success_total / total, 4) if total else 0.5,
                "avg_reward_delta": round(reward_sum / total, 4) if total else 0.0,
                "scenario_category": scenario_category,
                "last_updated": now,
            })
            trend = prev.get("trend", [])
            trend.append(round(trial_rate, 4))
            prev["trend"] = trend[-10:]
            data[key] = prev

        self.save_proficiency(team_id, data)
        return {"updated": len(grouped), "team_id": team_id, "trial_id": trial_id}

    def rebuild(self, team_id: str, trial_ids: List[str],
                scenario_category: str = "general") -> Dict[str, Any]:
        """全量重建熟练度缓存（数据修复用）."""
        self.save_proficiency(team_id, {})
        for tid in trial_ids:
            self.update_from_trial(team_id, tid, scenario_category)
        return {"rebuilt": True, "trials": len(trial_ids)}

    def query(self, team_id: str, scenario_category: str = "") -> List[Dict[str, Any]]:
        """查询团队熟练度列表 (B-3.6 数据源)."""
        data = self.load_proficiency(team_id)
        result = list(data.values())
        if scenario_category:
            result = [r for r in result if r.get("scenario_category") == scenario_category]
        return sorted(result, key=lambda r: r.get("success_rate", 0))


def aggregate_usages(usages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """按 skill_name 聚合 usage 记录."""
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for u in usages:
        grouped.setdefault(u.get("skill_name", "?"), []).append(u)
    result = []
    for skill, items in grouped.items():
        uses = len(items)
        succ = sum(1 for i in items if i.get("outcome") == "success")
        failures = [i for i in items if i.get("outcome") == "failure"]
        result.append({
            "skill_name": skill,
            "total_uses": uses,
            "success_count": succ,
            "success_rate": round(succ / uses, 4) if uses else 0.0,
            "avg_reward_delta": round(sum(float(i.get("reward_delta", 0)) for i in items) / uses, 4) if uses else 0.0,
            "agents": sorted({i.get("agent_id", "") for i in items}),
            "failure_samples": [
                {"step_index": f.get("step_index"), "agent_id": f.get("agent_id"),
                 "failure_reason": f.get("failure_reason", ""), "task_id": f.get("task_id", "")}
                for f in failures[:5]
            ],
        })
    return sorted(result, key=lambda r: r["success_rate"])


# ── 全局单例 ───────────────────────────────────────────────

_store: Optional[ProficiencyStore] = None


def get_proficiency_store() -> ProficiencyStore:
    global _store
    if _store is None:
        _store = ProficiencyStore()
    return _store


def reset_proficiency_store(**kwargs) -> ProficiencyStore:
    global _store
    _store = ProficiencyStore(**kwargs)
    return _store
