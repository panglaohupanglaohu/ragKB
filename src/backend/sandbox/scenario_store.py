# -*- coding: utf-8 -*-
"""Scenario Store — 场景库持久化 (v4 A-4.1).

内置场景: config/scenarios/*.json (只读)
自定义场景: storage/scenarios/{scenario_id}.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .scenario_models import ScenarioSpec, validate_scenario

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[3]
BUILTIN_DIR = _ROOT / "config" / "scenarios"
CUSTOM_DIR = _ROOT / "storage" / "scenarios"


class ScenarioStore:
    """场景库 — 内置(只读) + 自定义(可写)."""

    def __init__(self, builtin_dir: Optional[Path] = None, custom_dir: Optional[Path] = None):
        self._builtin_dir = builtin_dir or BUILTIN_DIR
        self._custom_dir = custom_dir or CUSTOM_DIR
        self._scenarios: Dict[str, ScenarioSpec] = {}
        self._load_errors: List[str] = []
        self.reload()

    def reload(self) -> None:
        """重新加载全部场景，启动时校验 schema."""
        self._scenarios = {}
        self._load_errors = []
        for d, source in ((self._builtin_dir, "builtin"), (self._custom_dir, "custom")):
            if not d.exists():
                continue
            for f in sorted(d.glob("*.json")):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    errors = validate_scenario(data)
                    if errors:
                        self._load_errors.append(f"{f.name}: {'; '.join(errors[:3])}")
                        logger.warning(f"⚠️ 场景 {f.name} schema 校验失败: {errors[:3]}")
                        continue
                    spec = ScenarioSpec.from_dict(data)
                    if data.get("source") in (None, ""):
                        spec.source = source
                    self._scenarios[spec.scenario_id] = spec
                except Exception as e:
                    self._load_errors.append(f"{f.name}: {e}")
                    logger.warning(f"⚠️ 场景文件 {f.name} 加载失败: {e}")
        logger.info(f"📚 ScenarioStore: 加载 {len(self._scenarios)} 个场景"
                    + (f", {len(self._load_errors)} 个失败" if self._load_errors else ""))

    # ── 查询 ──────────────────────────────────────────────

    def list(self, category: str = "", tag: str = "") -> List[ScenarioSpec]:
        result = list(self._scenarios.values())
        if category:
            result = [s for s in result if s.category == category]
        if tag:
            result = [s for s in result if tag in s.tags]
        return sorted(result, key=lambda s: (s.source != "builtin", s.scenario_id))

    def get(self, scenario_id: str) -> Optional[ScenarioSpec]:
        return self._scenarios.get(scenario_id)

    # ── 写入 ──────────────────────────────────────────────

    def save(self, spec: ScenarioSpec) -> Dict[str, Any]:
        """保存自定义场景 (builtin 不可覆盖)."""
        existing = self._scenarios.get(spec.scenario_id)
        if existing and existing.source == "builtin":
            return {"ok": False, "error": "builtin 场景不可覆盖"}
        errors = validate_scenario(spec.to_dict())
        if errors:
            return {"ok": False, "error": "schema 校验失败", "errors": errors}
        if spec.source == "builtin":
            spec.source = "custom"
        self._custom_dir.mkdir(parents=True, exist_ok=True)
        path = self._custom_dir / f"{spec.scenario_id}.json"
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(spec.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
        self._scenarios[spec.scenario_id] = spec
        return {"ok": True, "scenario_id": spec.scenario_id}

    def delete(self, scenario_id: str) -> Dict[str, Any]:
        """删除自定义场景 (builtin 不可删)."""
        spec = self._scenarios.get(scenario_id)
        if not spec:
            return {"ok": False, "error": "not_found"}
        if spec.source == "builtin":
            return {"ok": False, "error": "builtin 场景不可删除"}
        path = self._custom_dir / f"{scenario_id}.json"
        if path.exists():
            path.unlink()
        self._scenarios.pop(scenario_id, None)
        return {"ok": True}

    @property
    def load_errors(self) -> List[str]:
        return list(self._load_errors)


# ── 全局单例 ───────────────────────────────────────────────

_store: Optional[ScenarioStore] = None


def get_scenario_store() -> ScenarioStore:
    global _store
    if _store is None:
        _store = ScenarioStore()
    return _store


def reset_scenario_store(**kwargs) -> ScenarioStore:
    """重置单例 (测试用)."""
    global _store
    _store = ScenarioStore(**kwargs)
    return _store
