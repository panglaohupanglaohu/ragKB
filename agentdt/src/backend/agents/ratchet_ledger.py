# -*- coding: utf-8 -*-
"""Ratchet Ledger — 全局正向棘轮账本 (全局优化 G-4).

系统级"只进不退": 跨试炼、跨团队的指标推进记录与门禁。
metric_key 约定:
  scenario_best:{scenario_id}:{team_id}   场景最佳分
  skill_effectiveness:{skill_name}:{team_id}  技能有效性
  cost_efficiency:{team_id}               单位 token 产出
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[3]
LEDGER_DIR = _ROOT / "storage" / "ratchet"
LEDGER_FILE = LEDGER_DIR / "ledger.json"


class RatchetLedger:
    """正向棘轮账本 — 指标只进不退，退步拒绝并给出原因."""

    def __init__(self, ledger_file: Optional[Path] = None):
        self._file = ledger_file or LEDGER_FILE
        self._file.parent.mkdir(parents=True, exist_ok=True)
        # metric_key -> {"generation", "value", "updated_at", "history": [...]}
        self._metrics: Dict[str, Dict[str, Any]] = {}
        self._load()

    # ── 持久化（原子写 + .bak 自愈，对齐 trial_store 模式） ──

    def _load(self) -> None:
        for path in (self._file, self._file.with_suffix(".json.bak")):
            if path.exists():
                try:
                    self._metrics = json.loads(path.read_text(encoding="utf-8")).get("metrics", {})
                    return
                except Exception as e:
                    logger.warning(f"棘轮账本读取失败 ({path.name}): {e}")
        self._metrics = {}

    def _save(self) -> None:
        data = {"metrics": self._metrics,
                "updated_at": datetime.now(timezone.utc).isoformat()}
        if self._file.exists():
            try:
                self._file.replace(self._file.with_suffix(".json.bak"))
            except OSError:
                pass
        tmp = self._file.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.rename(self._file)

    # ── 核心: 推进 ────────────────────────────────────────

    def advance(
        self,
        metric_key: str,
        value: float,
        evidence: Optional[Dict[str, Any]] = None,
        min_delta: float = 0.0,
        tolerance: float = 0.0,
    ) -> Dict[str, Any]:
        """尝试推进指标 (G4-1).

        规则:
        - 首次记录: 直接推进 generation=1
        - value >= current + min_delta: 推进 generation+1
        - current - tolerance <= value < current + min_delta: 持平，不推进不拒绝 (held)
        - value < current - tolerance: 退步，拒绝并给出原因
        """
        now = datetime.now(timezone.utc).isoformat()
        entry = self._metrics.get(metric_key)

        if entry is None:
            record = {"generation": 1, "value": float(value), "updated_at": now,
                      "evidence": evidence or {}}
            self._metrics[metric_key] = {**record, "history": [dict(record)]}
            self._save()
            return {"advanced": True, "generation": 1, "current": float(value),
                    "reason": "first_record"}

        current = float(entry["value"])
        if value >= current + min_delta:
            if value < current:  # min_delta 为负时仍不允许低于当前
                return {"advanced": False, "generation": entry["generation"],
                        "current": current,
                        "reason": f"regression: {value:.4f} < current {current:.4f}"}
            gen = entry["generation"] + 1
            record = {"generation": gen, "value": float(value), "updated_at": now,
                      "evidence": evidence or {}}
            entry.update(record)
            entry.setdefault("history", []).append(dict(record))
            entry["history"] = entry["history"][-100:]
            self._save()
            return {"advanced": True, "generation": gen, "current": float(value),
                    "reason": f"improved: {current:.4f} → {value:.4f}"}

        if value >= current - tolerance:
            return {"advanced": False, "generation": entry["generation"],
                    "current": current, "held": True,
                    "reason": f"held: {value:.4f} 在容忍区间内 (current={current:.4f}, "
                              f"min_delta={min_delta}, tolerance={tolerance})"}

        return {"advanced": False, "generation": entry["generation"], "current": current,
                "reason": f"regression_rejected: {value:.4f} < {current:.4f} - tolerance({tolerance})"}

    # ── 查询与维护 ────────────────────────────────────────

    def get(self, metric_key: str) -> Optional[Dict[str, Any]]:
        e = self._metrics.get(metric_key)
        if not e:
            return None
        return {k: v for k, v in e.items() if k != "history"}

    def history(self, metric_key: str) -> List[Dict[str, Any]]:
        return list(self._metrics.get(metric_key, {}).get("history", []))

    def list_metrics(self, prefix: str = "") -> List[Dict[str, Any]]:
        result = []
        for key, e in sorted(self._metrics.items()):
            if prefix and not key.startswith(prefix):
                continue
            result.append({"metric_key": key, "generation": e["generation"],
                           "value": e["value"], "updated_at": e["updated_at"]})
        return result

    def force_reset(self, metric_key: str, reason: str) -> Dict[str, Any]:
        """人工重置（留痕）— 棘轮僵化时的逃生门 (G4-1)."""
        entry = self._metrics.get(metric_key)
        if not entry:
            return {"ok": False, "error": "metric_not_found"}
        now = datetime.now(timezone.utc).isoformat()
        entry.setdefault("history", []).append({
            "generation": entry["generation"], "value": entry["value"],
            "updated_at": now, "evidence": {"force_reset": True, "reason": reason},
        })
        old_value = entry["value"]
        entry["value"] = 0.0
        entry["generation"] = entry["generation"]  # 代数保留，价值清零允许重建
        entry["updated_at"] = now
        self._save()
        logger.warning(f"⚠️ 棘轮人工重置: {metric_key} (was {old_value}) reason={reason}")
        return {"ok": True, "metric_key": metric_key, "previous_value": old_value,
                "reason": reason}


# ── 单例 ──────────────────────────────────────────────────

_ledger: Optional[RatchetLedger] = None


def get_ratchet_ledger() -> RatchetLedger:
    global _ledger
    if _ledger is None:
        _ledger = RatchetLedger()
    return _ledger


def reset_ratchet_ledger(**kwargs) -> RatchetLedger:
    global _ledger
    _ledger = RatchetLedger(**kwargs)
    return _ledger
