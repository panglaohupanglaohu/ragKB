# -*- coding: utf-8 -*-
"""Health Ledger — 代谢账本（物竞天择的唯一选择压力来源）.

对应 docs/Agent仿生生态运行时plan.md §3, §8。

核心立场：不给 Skill/Agent 打分，只记录一件事——它是否活得下去。
每个 tick 按代谢速率扣 Health，行为消耗更多，任务完成能回血；
Health 归零即进入 dormant（映射到已有 AgentState.STOPPED，不删除、可复活）。
`survival_ticks` 本身就是隐式适应度，不需要额外的复合评分公式。

持久化写法对齐 `agents/ratchet_ledger.py` 的原子写 + .bak 自愈模式。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[4]
HEALTH_DIR = _ROOT / "storage" / "health_ledger"


@dataclass
class HealthState:
    """单个 Agent 的健康状态（生理账本条目）."""

    agent_id: str = ""
    health: float = 100.0
    health_max: float = 100.0
    metabolic_rate: float = 1.0
    survival_ticks: int = 0
    generation: int = 0
    parent_agent_id: str = ""
    status: str = "active"    # active | dormant

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "health": self.health,
            "health_max": self.health_max,
            "metabolic_rate": self.metabolic_rate,
            "survival_ticks": self.survival_ticks,
            "generation": self.generation,
            "parent_agent_id": self.parent_agent_id,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "HealthState":
        return cls(
            agent_id=d.get("agent_id", ""),
            health=float(d.get("health", 100.0)),
            health_max=float(d.get("health_max", 100.0)),
            metabolic_rate=float(d.get("metabolic_rate", 1.0)),
            survival_ticks=int(d.get("survival_ticks", 0)),
            generation=int(d.get("generation", 0)),
            parent_agent_id=d.get("parent_agent_id", ""),
            status=d.get("status", "active"),
        )


@dataclass
class TickResult:
    """一次 tick 的代谢结算结果."""

    agent_id: str
    health_before: float
    health_after: float
    consumed: float
    replenished: float
    survival_ticks: int
    became_dormant: bool = False   # 本次 tick 是否刚好从 active 转为 dormant

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "health_before": self.health_before,
            "health_after": self.health_after,
            "consumed": self.consumed,
            "replenished": self.replenished,
            "survival_ticks": self.survival_ticks,
            "became_dormant": self.became_dormant,
        }


class HealthLedger:
    """代谢账本 — 每个 team 一个持久化文件，管理其下全部 Agent 的 Health 状态."""

    def __init__(self, team_id: str, ledger_dir: Optional[Path] = None):
        self.team_id = team_id
        self._dir = ledger_dir or HEALTH_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._file = self._dir / f"{self._safe_name(team_id)}.json"
        self._states: Dict[str, HealthState] = {}
        self._load()

    @staticmethod
    def _safe_name(team_id: str) -> str:
        return "".join(c for c in (team_id or "default") if c.isalnum() or c in "-_") or "default"

    # ── 持久化（原子写 + .bak 自愈，对齐 ratchet_ledger 模式） ──

    def _load(self) -> None:
        for path in (self._file, self._file.with_suffix(".json.bak")):
            if path.exists():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    self._states = {
                        aid: HealthState.from_dict(sd)
                        for aid, sd in data.get("agents", {}).items()
                    }
                    return
                except Exception as e:
                    logger.warning(f"HealthLedger 读取失败 ({path.name}): {e}")
        self._states = {}

    def _save(self) -> None:
        data = {
            "team_id": self.team_id,
            "agents": {aid: s.to_dict() for aid, s in self._states.items()},
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if self._file.exists():
            try:
                self._file.replace(self._file.with_suffix(".json.bak"))
            except OSError:
                pass
        tmp = self._file.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self._file)

    # ── 核心 API ────────────────────────────────────────────

    def get_or_create(
        self,
        agent_id: str,
        health_max: float = 100.0,
        metabolic_rate: float = 1.0,
    ) -> HealthState:
        """获取或初始化一个 Agent 的健康状态（初始 Health = health_max，满血起步）."""
        state = self._states.get(agent_id)
        if state is None:
            state = HealthState(
                agent_id=agent_id,
                health=health_max,
                health_max=health_max,
                metabolic_rate=metabolic_rate,
            )
            self._states[agent_id] = state
        return state

    def get(self, agent_id: str) -> Optional[HealthState]:
        return self._states.get(agent_id)

    def tick(
        self,
        agent_id: str,
        action_cost: float = 0.0,
        reward: float = 0.0,
    ) -> TickResult:
        """代谢结算：扣基础代谢 + 行为消耗，加任务回血.

        dormant 状态的 Agent 不再消耗/不再计入 survival_ticks（定格，plan §3）。
        """
        state = self.get_or_create(agent_id)
        health_before = state.health

        if state.status == "dormant":
            return TickResult(
                agent_id=agent_id,
                health_before=health_before,
                health_after=health_before,
                consumed=0.0,
                replenished=0.0,
                survival_ticks=state.survival_ticks,
                became_dormant=False,
            )

        consumed = max(0.0, state.metabolic_rate + action_cost)
        replenished = max(0.0, reward)
        new_health = state.health - consumed + replenished
        new_health = max(0.0, min(state.health_max, new_health))

        state.health = new_health
        state.survival_ticks += 1

        became_dormant = False
        if state.health <= 0.0:
            state.status = "dormant"
            became_dormant = True

        return TickResult(
            agent_id=agent_id,
            health_before=health_before,
            health_after=state.health,
            consumed=consumed,
            replenished=replenished,
            survival_ticks=state.survival_ticks,
            became_dormant=became_dormant,
        )

    def revive(self, agent_id: str, revive_ratio: float = 0.5) -> Optional[HealthState]:
        """复活：dormant → active，恢复到 health_max * revive_ratio（不满血，避免复活即死抖动）."""
        state = self._states.get(agent_id)
        if state is None:
            return None
        state.status = "active"
        state.health = state.health_max * max(0.0, min(1.0, revive_ratio))
        return state

    def sustained_ratio(self, agent_id: str, saturation_threshold: float = 0.7) -> float:
        """当前是否处于"饱暖"状态的简化度量（Health 占比是否达标），供 libido 计算使用.

        简化版：不做滑动窗口统计，直接用当前 health/health_max 是否 ≥ 阈值判断，
        达标返回 1.0，否则返回 0.0——这是 plan §2 `health_sustained_ratio` 的最小实现，
        避免过度设计滑动窗口（可在后续需要更精细行为时再扩展为真实窗口统计）。
        """
        state = self._states.get(agent_id)
        if state is None or state.health_max <= 0:
            return 0.0
        ratio = state.health / state.health_max
        return 1.0 if ratio >= saturation_threshold else 0.0

    def list_states(self) -> List[HealthState]:
        return list(self._states.values())

    def save(self) -> None:
        self._save()

    # ── P3-2: 特征抽象触发（Health 净收益驱动 skill 提炼） ──────────

    def net_gain_by_skill(
        self,
        agent_id: str,
        skill_id: str,
        usage_records: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """基于已落盘的 SkillUsageRecord，聚合"该 skill 参与的 tick 的净 Health 变化".

        usage_records 由调用方传入（复用 `proficiency_store.load_usages` 的返回结构，
        每条记录含 `agent_id`/`skill_name`/`reward_delta`），本方法只做聚合，不做 I/O，
        便于测试 mock，也不与 proficiency_store 产生硬依赖。

        `reward_delta` 直接作为该次使用的净收益代理（复用现有字段语义，不新增字段）。
        """
        matched = [
            r for r in usage_records
            if r.get("agent_id") == agent_id and r.get("skill_name") == skill_id
        ]
        usage_count = len(matched)
        net_gain = sum(float(r.get("reward_delta", 0.0)) for r in matched)
        return {
            "agent_id": agent_id,
            "skill_id": skill_id,
            "usage_count": usage_count,
            "net_gain": round(net_gain, 6),
            "avg_gain": round(net_gain / usage_count, 6) if usage_count else 0.0,
        }


def should_solidify(
    net_gain: float,
    usage_count: int,
    min_uses: int = 5,
    min_gain: float = 0.0,
) -> bool:
    """判定是否建议触发"特征抽象"（提炼 skill instructions）.

    只返回布尔建议，不在本函数内调用任何 LLM/skill_evolver——是否真正触发改写
    由上层决定（plan §4：避免意外烧 token）。
    """
    if usage_count < min_uses:
        return False
    return net_gain > min_gain


def should_solidify_from_config(net_gain: float, usage_count: int) -> bool:
    """用 EcoRuntimeConfig 的 learning 段阈值判定，配置不可用时回退内置默认。"""
    try:
        from .eco_runtime_config import get_eco_runtime_config
        s = get_eco_runtime_config().get_section("learning")
        return should_solidify(
            net_gain, usage_count,
            min_uses=int(s.get("solidify_min_uses", 5)),
            min_gain=float(s.get("solidify_min_gain", 0.0)),
        )
    except Exception:
        return should_solidify(net_gain, usage_count)


def config_health_defaults() -> Dict[str, float]:
    """返回当前生效的 (health_max, metabolic_rate, revive_ratio, saturation_threshold)."""
    try:
        from .eco_runtime_config import get_eco_runtime_config
        s = get_eco_runtime_config().get_section("metabolism")
        return {
            "health_max": float(s.get("health_max", 100.0)),
            "metabolic_rate": float(s.get("metabolic_rate", 1.0)),
            "revive_ratio": float(s.get("revive_ratio", 0.5)),
            "saturation_threshold": float(s.get("saturation_threshold", 0.7)),
        }
    except Exception:
        return {"health_max": 100.0, "metabolic_rate": 1.0, "revive_ratio": 0.5, "saturation_threshold": 0.7}


# ── 单例（按 team_id 缓存，避免重复加载同一文件） ──

_ledgers: Dict[str, HealthLedger] = {}


def get_health_ledger(team_id: str) -> HealthLedger:
    if team_id not in _ledgers:
        _ledgers[team_id] = HealthLedger(team_id)
    return _ledgers[team_id]


def reset_health_ledgers() -> None:
    """测试专用：清空单例缓存."""
    _ledgers.clear()
