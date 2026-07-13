# -*- coding: utf-8 -*-
"""以 T_i = survival_ticks 为根的 skill / 协作 / 残差可解释分解.

原则（用户 2026-07-14）：
- 不引入第二适应度；T_i 仍是唯一原生量。
- 分解是对「每个存活 tick 的主因归因」，使
    skill_ticks + collab_ticks + residual_ticks = T_i  （在可观测帧内对齐）
- 无法从 timeline 观测的 tick（采样丢帧）归入 residual。

归因优先级（每个帧、每个仍在 actions 里的 agent，对应 1 个存活 tick 的主因）：
  1) collab_recv  — 本帧收到他人分享（shared_to == me）
  2) skill_forage — 本帧 can_serve 且 outcome=success（自身 skill 匹配需求）
  3) collab_follow — 本帧 followed 且 outcome=success（信息协作增益）
  4) collab_follow_soft — followed 且 miss（跟随减损但仍是协作通道）
  5) residual     — 其余（静息/避险/求偶/纯代谢/捕食前苟活/采样缺口）

输出 share 之和 = 1（对 T_i>0）；T_i=0 则全 0。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _outcome_success(act: Dict[str, Any]) -> bool:
    o = act.get("outcome")
    return o is True or o == "success"


def _outcome_miss(act: Dict[str, Any]) -> bool:
    o = act.get("outcome")
    return o is False or o == "miss" or o == "miss/idle"


def decompose_survival_from_timeline(
    timeline: Optional[Dict[str, Any]],
    ranking: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """从 timeline.steps[].actions 分解每个 agent 的 T_i.

    Returns:
      { agent_id: {
          T_i, skill_ticks, collab_ticks, residual_ticks,
          skill_share, collab_share, residual_share,
          counts: {skill_forage, collab_recv, collab_follow, ...},
          explain: str
        } }
    """
    timeline = timeline or {}
    steps = list(timeline.get("steps") or [])
    ranking = ranking or []

    # 预建：每帧谁分给了谁
    # 累加器
    skill_ticks: Dict[str, float] = {}
    collab_ticks: Dict[str, float] = {}
    residual_ticks: Dict[str, float] = {}
    observed: Dict[str, int] = {}
    counts: Dict[str, Dict[str, int]] = {}

    def _c(aid: str) -> Dict[str, int]:
        return counts.setdefault(aid, {
            "skill_forage": 0,
            "collab_recv": 0,
            "collab_follow": 0,
            "collab_follow_soft": 0,
            "residual": 0,
            "frames_seen": 0,
        })

    for fr in steps:
        actions = fr.get("actions") or {}
        # 本帧收到分享的人
        receivers = set()
        for aid, act in actions.items():
            st = act.get("shared_to")
            if st:
                receivers.add(st)

        for aid, act in actions.items():
            if not isinstance(act, dict):
                continue
            # 有 action 记录且 survival_ticks 在增长过程中 → 计 1 tick 归因
            # （死亡帧仍可能有 action；以 survival_ticks 字段存在为准）
            observed[aid] = observed.get(aid, 0) + 1
            c = _c(aid)
            c["frames_seen"] += 1

            can_serve = bool(act.get("can_serve"))
            followed = bool(act.get("followed"))
            success = _outcome_success(act)
            miss = _outcome_miss(act)

            if aid in receivers:
                collab_ticks[aid] = collab_ticks.get(aid, 0.0) + 1.0
                c["collab_recv"] += 1
            elif can_serve and success:
                skill_ticks[aid] = skill_ticks.get(aid, 0.0) + 1.0
                c["skill_forage"] += 1
            elif followed and success:
                # 跟随信号成功觅食：协作信息为主
                collab_ticks[aid] = collab_ticks.get(aid, 0.0) + 1.0
                c["collab_follow"] += 1
            elif followed and miss:
                collab_ticks[aid] = collab_ticks.get(aid, 0.0) + 1.0
                c["collab_follow_soft"] += 1
            else:
                residual_ticks[aid] = residual_ticks.get(aid, 0.0) + 1.0
                c["residual"] += 1

    out: Dict[str, Dict[str, Any]] = {}
    for row in ranking:
        aid = row.get("agent_id") or ""
        if not aid:
            continue
        T = int(row.get("survival_ticks") or 0)
        s = float(skill_ticks.get(aid, 0.0))
        c = float(collab_ticks.get(aid, 0.0))
        r = float(residual_ticks.get(aid, 0.0))
        obs = s + c + r

        # 将归因 ticks 缩放到 T_i：timeline 可能采样，obs 可能 ≠ T
        if T <= 0:
            ss = cc = rr = 0.0
        elif obs <= 0:
            # 无观测帧：全部 residual
            ss, cc, rr = 0.0, 0.0, float(T)
        else:
            # 比例缩放使 s'+c'+r' = T
            scale = T / obs
            ss, cc, rr = s * scale, c * scale, r * scale

        def _share(x: float) -> float:
            return round(x / T, 4) if T > 0 else 0.0

        sk_sh, co_sh, re_sh = _share(ss), _share(cc), _share(rr)
        # 浮点修正
        if T > 0:
            drift = 1.0 - (sk_sh + co_sh + re_sh)
            re_sh = round(re_sh + drift, 4)

        cnt = counts.get(aid) or {}
        # 解释句
        if T <= 0:
            explain = "未产生存活时长"
        elif sk_sh >= co_sh and sk_sh >= re_sh:
            explain = f"存活主因偏 skill（匹配需求觅食成功占 {sk_sh:.0%}）"
        elif co_sh >= sk_sh and co_sh >= re_sh:
            explain = f"存活主因偏协作（分享/跟随占 {co_sh:.0%}）"
        else:
            explain = f"存活主因偏基线/残余（静息·避险·采样占 {re_sh:.0%}）"

        out[aid] = {
            "agent_id": aid,
            "population": row.get("population") or "",
            "T_i": T,
            "skill_ticks": round(ss, 2),
            "collab_ticks": round(cc, 2),
            "residual_ticks": round(rr, 2),
            "skill_share": sk_sh,
            "collab_share": co_sh,
            "residual_share": re_sh,
            "counts": cnt,
            "frames_observed": int(observed.get(aid, 0)),
            "explain": explain,
        }
    return out


def attach_attribution_to_ranking(
    ranking: List[Dict[str, Any]],
    attribution: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """把分解字段浅拷贝进 ranking 行，便于前端直接画条。"""
    out = []
    for row in ranking:
        r = dict(row)
        att = attribution.get(r.get("agent_id") or "")
        if att:
            r["attr_skill_share"] = att["skill_share"]
            r["attr_collab_share"] = att["collab_share"]
            r["attr_residual_share"] = att["residual_share"]
            r["attr_explain"] = att["explain"]
        out.append(r)
    return out
