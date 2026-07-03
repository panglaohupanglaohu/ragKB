"""Token 优化目标 — 成本页的「方向盘」。

存储: storage/cost_targets.json（沿用项目 JSON 存储风格）
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_DB_PATH = Path(__file__).resolve().parents[3] / "storage" / "cost_targets.json"


@dataclass
class TokenTarget:
    id: str = ""
    scope: str = "team"           # team | skill
    ref_id: str = ""              # team_id 或 skill_id
    metric: str = "score_per_1k"  # tokens_per_goal | score_per_1k
    baseline: float = 0.0
    target: float = 0.0
    lever: str = "skill_extraction"  # skill_extraction | collaboration_routing
    status: str = "active"        # active | achieved | abandoned
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)


class TargetStore:
    """JSON 文件存储的优化目标管理。"""

    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path or _DB_PATH)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._targets: Dict[str, TokenTarget] = {}
        self._load()
        self._migrate_baselines()

    def _load(self) -> None:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                for item in data.get("targets", []):
                    t = TokenTarget(**item)
                    self._targets[t.id] = t
            except Exception as e:
                logger.warning(f"加载 cost_targets.json 失败: {e}")

    def _migrate_baselines(self) -> None:
        """P10.3: 重算 tokens_per_goal 存量目标的 baseline 为「每调用 token」口径（幂等）。"""
        migrated = False
        for t in self._targets.values():
            if t.metric == "tokens_per_goal" and t.status == "active":
                new_baseline = self._current_value(t)
                if abs(new_baseline - t.baseline) > 1.0:  # 量纲差异 >1 说明需要迁移
                    t.baseline = new_baseline
                    migrated = True
        if migrated:
            self._save()
            logger.info("P10.3: tokens_per_goal baseline 已迁移到「每调用 token」口径")

    def _save(self) -> None:
        data = {"targets": [t.to_dict() for t in self._targets.values()]}
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def create(self, scope: str, ref_id: str, metric: str, target: float,
               lever: str, baseline: Optional[float] = None) -> TokenTarget:
        """创建优化目标。baseline 不提供时自动取 LEDGER 当前值。"""
        tid = f"tgt_{uuid.uuid4().hex[:8]}"
        if baseline is None:
            baseline = self._auto_baseline(scope, ref_id, metric)

        t = TokenTarget(
            id=tid, scope=scope, ref_id=ref_id, metric=metric,
            baseline=baseline, target=target, lever=lever,
        )
        self._targets[tid] = t
        self._save()
        return t

    def _auto_baseline(self, scope: str, ref_id: str, metric: str) -> float:
        """从当前值取 baseline（与 _current_value 同口径，确保量纲一致）。"""
        probe = TokenTarget(scope=scope, ref_id=ref_id, metric=metric)
        try:
            return float(self._current_value(probe))
        except Exception as e:
            logger.debug(f"自动 baseline 失败: {e}")
            return 0.0
            logger.debug(f"自动 baseline 失败: {e}")
        return 0.0

    def list_targets(self, status: str = "") -> List[TokenTarget]:
        if status:
            return [t for t in self._targets.values() if t.status == status]
        return list(self._targets.values())

    def get(self, tid: str) -> Optional[TokenTarget]:
        return self._targets.get(tid)

    def get_progress(self, tid: str) -> Dict:
        """计算目标进度。

        P8.6.2 修复：
        - tokens_per_goal（越低越好）→ current = 总 token，progress = (baseline-current)/(baseline-target)
        - score_per_1k（越高越好）→ current = 实测效率，progress = (current-baseline)/(target-baseline)
        """
        t = self._targets.get(tid)
        if not t:
            return {"error": "not_found"}

        current = self._current_value(t)

        if t.metric == "tokens_per_goal":
            # baseline 高、target 低 → progress = (baseline - current) / (baseline - target)
            if t.baseline != t.target:
                progress = (t.baseline - current) / (t.baseline - t.target)
            else:
                progress = 0.0
        else:
            # score_per_1k: baseline 低、target 高 → progress = (current - baseline) / (target - baseline)
            if t.target != t.baseline:
                progress = (current - t.baseline) / (t.target - t.baseline)
            else:
                progress = 0.0

        progress = max(0.0, min(progress, 1.0))

        # P8.6.4: 达成自动收口
        if progress >= 1.0 and t.status == "active":
            self.update_status(tid, "achieved")
            # P8R.6: 达成自动推进 cost_efficiency 棘轮
            try:
                from .ratchet_ledger import get_ratchet_ledger
                from .sustainability import collect_team_usage, evaluate_team
                if t.scope == "team":
                    eff = float(evaluate_team(collect_team_usage(t.ref_id)).get("token_efficiency", 0) or 0)
                    if eff > 0:
                        get_ratchet_ledger().advance(
                            f"cost_efficiency:{t.ref_id}", eff,
                            evidence={"source": "target_achieved", "target_id": tid},
                            tolerance=0.02,
                        )
            except Exception as e:
                logger.debug(f"达成自动棘轮失败(非致命): {e}")

        return {
            "id": t.id,
            "scope": t.scope,
            "ref_id": t.ref_id,
            "metric": t.metric,
            "baseline": t.baseline,
            "target": t.target,
            "current": round(current, 4),
            "progress": round(progress, 4),
            "lever": t.lever,
            "status": t.status,
        }

    def _current_value(self, t) -> float:
        """根据 metric 取当前值。

        - tokens_per_goal → 平均每次调用 token = total/calls（越低越好）
        - score_per_1k → 当前实测效率 score/1k tokens（越高越好）
        """
        try:
            from .token_ledger import LEDGER
            if t.metric == "tokens_per_goal":
                # 9.2: 用「平均每次调用 token」(total/calls) 而非窗口累计总量。
                # 累计总量只增不减→目标永远 0%；每调用 token 在路由命中/萃取后会下降，可推进。
                if t.scope == "team":
                    items = LEDGER.by_team("7d")
                    item = next((i for i in items if i.get("team_id") == t.ref_id), None)
                    return round(item["total"] / max(item.get("calls", 0), 1), 2) if item else 0.0
                elif t.scope == "skill":
                    items = LEDGER.by_skill("7d")
                    item = next((i for i in items if i.get("skill_id") == t.ref_id), None)
                    return round(item["total"] / max(item.get("calls", 0), 1), 2) if item else 0.0
                return 0.0
            else:  # score_per_1k
                if t.scope == "team":
                    from .sustainability import collect_team_usage, evaluate_team
                    ev = evaluate_team(collect_team_usage(t.ref_id))
                    return float(ev.get("token_efficiency", 0) or 0)
                # skill 维度效率暂无 score 来源 → 显式 0（前端显示「—」，不编造）
                return 0.0
        except Exception as e:
            logger.debug(f"取 current 值失败: {e}")
            return 0.0

    def update_status(self, tid: str, status: str) -> bool:
        t = self._targets.get(tid)
        if not t:
            return False
        t.status = status
        t.updated_at = datetime.now(timezone.utc).isoformat()
        self._save()
        return True

    def delete(self, tid: str) -> bool:
        if tid in self._targets:
            del self._targets[tid]
            self._save()
            return True
        return False


_store: Optional[TargetStore] = None


def get_target_store() -> TargetStore:
    global _store
    if _store is None:
        _store = TargetStore()
    return _store
