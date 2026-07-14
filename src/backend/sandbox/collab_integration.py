# -*- coding: utf-8 -*-
"""协作模式集成建议 — 物竞适者反馈台 P1.

从 final_ranking[].collab_genome 生成写回建议（metadata.eco_collab）。
默认不写真身；apply 由 API 层 confirm 后执行。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


_DIMS = ("share_tendency", "signal_tendency", "follow_tendency", "mate_choosiness")


def _clamp01(x: Any) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        v = 0.5
    return max(0.0, min(1.0, v))


def _norm_collab(raw: Optional[Dict[str, Any]]) -> Dict[str, float]:
    raw = raw or {}
    return {d: _clamp01(raw.get(d, 0.5)) for d in _DIMS}


def blend_collab(existing: Dict[str, float], proposed: Dict[str, float], alpha: float = 0.5) -> Dict[str, float]:
    """加权混合：new = (1-α)*existing + α*proposed。"""
    a = _clamp01(alpha)
    out = {}
    for d in _DIMS:
        out[d] = round((1.0 - a) * _clamp01(existing.get(d, 0.5)) + a * _clamp01(proposed.get(d, 0.5)), 4)
    return out


def build_collab_suggestions(
    result: Dict[str, Any],
    *,
    top_k: int = 12,
    default_strategy: str = "blend",
) -> Dict[str, Any]:
    """纯函数：从演练结果生成协作写回建议."""
    ranking = list(result.get("final_ranking") or [])
    ranking = sorted(ranking, key=lambda r: int(r.get("survival_ticks") or 0), reverse=True)
    suggestions: List[Dict[str, Any]] = []
    for r in ranking[: max(1, top_k)]:
        aid = str(r.get("agent_id") or "")
        if not aid:
            continue
        cg = _norm_collab(r.get("collab_genome") if isinstance(r.get("collab_genome"), dict) else {})
        suggestions.append({
            "agent_id": aid,
            "population": r.get("population") or "",
            "survival_ticks": int(r.get("survival_ticks") or 0),
            "collab": cg,
            "strategy": default_strategy if default_strategy in ("overwrite", "blend", "snapshot") else "blend",
            "reason": "eco_drill_final_ranking",
        })
    # 种群均值（参考）
    means = {d: 0.0 for d in _DIMS}
    n = 0
    for s in suggestions:
        n += 1
        for d in _DIMS:
            means[d] += s["collab"][d]
    if n:
        means = {d: round(means[d] / n, 4) for d in _DIMS}
    return {
        "write_policy": "suggest_only",
        "suggestions": suggestions,
        "population_mean": means,
        "count": len(suggestions),
    }


def materialize_collab_payload(
    suggestion: Dict[str, Any],
    *,
    existing_meta: Optional[Dict[str, Any]] = None,
    fingerprint: str = "",
    strategy_override: Optional[str] = None,
) -> Dict[str, Any]:
    """生成将写入 metadata.eco_collab 的对象."""
    strategy = strategy_override or suggestion.get("strategy") or "blend"
    proposed = _norm_collab(suggestion.get("collab"))
    existing_meta = existing_meta or {}
    prev = existing_meta.get("eco_collab") if isinstance(existing_meta.get("eco_collab"), dict) else {}
    prev_vals = _norm_collab(prev)
    if strategy == "overwrite":
        vals = proposed
    elif strategy == "snapshot":
        vals = proposed  # 仍写盘，但标记 snapshot_only 供运行时可选忽略
    else:
        vals = blend_collab(prev_vals, proposed, alpha=0.55)
    return {
        "share_tendency": vals["share_tendency"],
        "signal_tendency": vals["signal_tendency"],
        "follow_tendency": vals["follow_tendency"],
        "mate_choosiness": vals["mate_choosiness"],
        "source": "eco_drill",
        "strategy": strategy,
        "eco_fp": fingerprint or "",
        "survival_ticks": suggestion.get("survival_ticks"),
        "reason": suggestion.get("reason") or "eco_feedback",
    }
