# -*- coding: utf-8 -*-
"""孪生一致性评测 (数字办公室协作演练 M5-2, PICon 式).

孪生副本要能替生产真身做竞标决策，前提是二者在同一情境下的决策足够一致；
否则孪生失真，竞标结论不可迁移到生产。本模块提供纯函数一致率评测：

    输入 = 决策配对列表 [{situation_id, twin:{action,target,skill_used}, real:{...}}]
    输出 = 各维度一致率 + 总体一致率 + 可信度判定（低于阈值告警）。

纯函数、无 LLM / 无 IO，可完全单测；供竞标(M4)前置可信度门与演练页展示使用。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _norm(v: Any) -> str:
    """None/空 归一为 ''，其余转小写字符串，便于稳健比较。"""
    if v is None:
        return ""
    return str(v).strip().lower()


def compare_decision(twin: Dict[str, Any], real: Dict[str, Any]) -> Dict[str, bool]:
    """单情境下孪生 vs 真身的三维一致性。"""
    twin = twin or {}
    real = real or {}
    action_match = _norm(twin.get("action")) == _norm(real.get("action"))
    target_match = _norm(twin.get("target") or twin.get("to")) == _norm(real.get("target") or real.get("to"))
    skill_match = _norm(twin.get("skill_used") or twin.get("skill")) == _norm(real.get("skill_used") or real.get("skill"))
    return {
        "action_match": action_match,
        "target_match": target_match,
        "skill_match": skill_match,
        "full_match": action_match and target_match and skill_match,
    }


def consistency_report(pairs: List[Dict[str, Any]], *, threshold: float = 0.8) -> Dict[str, Any]:
    """一致性评测报告 + 可信度判定。

    Args:
        pairs: [{situation_id, twin:{...}, real:{...}}]
        threshold: 总体一致率可信下限（默认 0.8）。

    Returns:
        {total, action_rate, target_rate, skill_rate, overall_rate,
         trustworthy, verdict, mismatches:[situation_id,...]}
    """
    total = len(pairs or [])
    if total == 0:
        return {
            "total": 0, "action_rate": 0.0, "target_rate": 0.0, "skill_rate": 0.0,
            "overall_rate": 0.0, "trustworthy": False, "verdict": "no_data",
            "reason": "无决策配对，无法评估孪生保真度", "mismatches": [],
        }

    a = t = s = full = 0
    mismatches: List[Optional[str]] = []
    for i, p in enumerate(pairs):
        cmp = compare_decision(p.get("twin", {}), p.get("real", {}))
        a += cmp["action_match"]
        t += cmp["target_match"]
        s += cmp["skill_match"]
        if cmp["full_match"]:
            full += 1
        else:
            mismatches.append(p.get("situation_id", str(i)))

    overall_rate = round(full / total, 4)
    trustworthy = overall_rate >= threshold
    verdict = "trustworthy" if trustworthy else "diverged"
    reason = (
        f"孪生与真身决策一致率 {overall_rate:.2%} ≥ 阈值 {threshold:.0%}，竞标结论可迁移"
        if trustworthy else
        f"孪生与真身决策一致率 {overall_rate:.2%} < 阈值 {threshold:.0%}，孪生失真，竞标结论不可迁移到生产"
    )
    return {
        "total": total,
        "action_rate": round(a / total, 4),
        "target_rate": round(t / total, 4),
        "skill_rate": round(s / total, 4),
        "overall_rate": overall_rate,
        "trustworthy": trustworthy,
        "verdict": verdict,
        "reason": reason,
        "mismatches": mismatches,
    }
