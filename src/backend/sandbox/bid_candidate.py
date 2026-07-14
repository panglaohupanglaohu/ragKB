# -*- coding: utf-8 -*-
"""物竞 × 成本 — BidCandidate 候选构型（先适者后省钱）.

存储: storage/eco_bid_candidates/{team_id}/{candidate_id}.json
质量门 Q1–Q5；成本棘轮仅允许 quality_passed。
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[3]
STORE_DIR = _ROOT / "storage" / "eco_bid_candidates"

# 默认阈值（可被 payload 覆盖）
DEFAULT_QUALITY = {
    "require_task": True,          # Q1
    "require_feedback": True,      # Q2
    "min_best_T": 1,               # Q3 soft threshold
    "max_top_residual": 0.85,      # Q4 soft
    "require_demand_overlap": False,  # Q5 soft, default off
    "q3_hard": False,
    "q4_hard": False,
    "q5_hard": False,
}


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe(s: str) -> str:
    return "".join(c for c in (s or "default") if c.isalnum() or c in "-_") or "default"


def store_root(base: Optional[Path] = None) -> Path:
    p = base or STORE_DIR
    p.mkdir(parents=True, exist_ok=True)
    return p


def team_dir(team_id: str, base: Optional[Path] = None) -> Path:
    d = store_root(base) / _safe(team_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def new_candidate_id() -> str:
    return f"bid_{uuid.uuid4().hex[:12]}"


def _ranking_top(result: Dict[str, Any], k: int = 8) -> List[Dict[str, Any]]:
    ranking = list(result.get("final_ranking") or [])
    ranking = sorted(ranking, key=lambda r: int(r.get("survival_ticks") or 0), reverse=True)
    out = []
    for r in ranking[:k]:
        out.append({
            "agent_id": r.get("agent_id"),
            "population": r.get("population"),
            "survival_ticks": int(r.get("survival_ticks") or 0),
            "attr_skill_share": r.get("attr_skill_share"),
            "attr_collab_share": r.get("attr_collab_share"),
            "attr_residual_share": r.get("attr_residual_share"),
        })
    return out


def build_candidate_from_result(
    *,
    team_id: str,
    result: Dict[str, Any],
    feedback: Dict[str, Any],
    task_id: str = "",
    plan_id: str = "",
    race_mode: str = "",
    candidate_id: str = "",
) -> Dict[str, Any]:
    """从物竞 result + 反馈状态构造 BidCandidate 文档."""
    ranking = list(result.get("final_ranking") or [])
    ranking = sorted(ranking, key=lambda r: int(r.get("survival_ticks") or 0), reverse=True)
    best = ranking[0] if ranking else {}
    contract = result.get("contract") or {}
    provenance = contract.get("provenance") or {}
    eco_fp = (
        feedback.get("fingerprint")
        or provenance.get("fingerprint")
        or contract.get("plan_id")
        or plan_id
        or ""
    )
    integration = result.get("integration") or {}
    dominant = integration.get("dominant_skills") or []
    if not dominant and result.get("gene_pool"):
        gp = result["gene_pool"].get("dominant") or []
        dominant = [d if isinstance(d, str) else (d.get("skill") or "") for d in gp]
    dominant = [d for d in dominant if d]

    att = result.get("survival_attribution") or {}
    top_att = {}
    if best.get("agent_id") and isinstance(att, dict):
        top_att = att.get(best["agent_id"]) or {}
    residual = best.get("attr_residual_share")
    if residual is None:
        residual = top_att.get("residual_share")

    fb_status = feedback.get("feedback") or feedback.get("status") or "unknown"
    if feedback.get("skipped") or fb_status == "skipped":
        fb_status = "skipped"
    elif feedback.get("skill_applied") or feedback.get("collab_applied") \
            or feedback.get("channel_applied") or feedback.get("relation_applied") \
            or fb_status == "done":
        fb_status = "done"

    task_id = task_id or feedback.get("task_id") or contract.get("task_id") or ""
    plan_id = plan_id or contract.get("plan_id") or provenance.get("plan_id") or ""

    cid = candidate_id or new_candidate_id()
    doc: Dict[str, Any] = {
        "candidate_id": cid,
        "team_id": team_id,
        "task_id": task_id,
        "plan_id": plan_id,
        "eco_fp": str(eco_fp)[:128],
        "race_mode": race_mode or result.get("race_mode") or "",
        "champion_agent_id": best.get("agent_id") or "",
        "best_T": int(best.get("survival_ticks") or 0),
        "ranking_summary": _ranking_top(result),
        "dominant_skills": dominant[:12],
        "collab_profile": best.get("collab_genome") if isinstance(best.get("collab_genome"), dict) else {},
        "survival_attribution": {
            "top_agent_id": best.get("agent_id"),
            "skill_share": best.get("attr_skill_share", top_att.get("skill_share")),
            "collab_share": best.get("attr_collab_share", top_att.get("collab_share")),
            "residual_share": residual,
        },
        "feedback_status": fb_status,
        "skill_applied": bool(feedback.get("skill_applied")),
        "collab_applied": bool(feedback.get("collab_applied")),
        "channel_applied": bool(feedback.get("channel_applied")),
        "relation_applied": bool(feedback.get("relation_applied")),
        "skip_reason": feedback.get("reason") or feedback.get("skip_reason") or "",
        "habitat_snapshot": result.get("env") or result.get("habitat") or {},
        "contract_topic": contract.get("topic") or "",
        "niches_count": len(contract.get("niches") or []),
        # 成本门 — 后填
        "tokens_baseline": feedback.get("tokens_baseline"),
        "tokens_candidate": feedback.get("tokens_candidate"),
        "token_efficiency": feedback.get("token_efficiency"),
        "cost_gate": "pending",
        "ratchet_state": "none",
        "quality_status": "pending",
        "quality_checks": {},
        "quality_reasons": [],
        "created_at": _utc(),
        "updated_at": _utc(),
        "source": "eco_drill_feedback",
    }
    doc = apply_quality_check(doc)
    return doc


def apply_quality_check(
    candidate: Dict[str, Any],
    *,
    thresholds: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Q1–Q5 质量门. 返回更新后的 candidate（含 quality_status / checks / reasons）."""
    th = dict(DEFAULT_QUALITY)
    if thresholds:
        th.update({k: v for k, v in thresholds.items() if v is not None})

    checks: Dict[str, Any] = {}
    reasons: List[str] = []
    hard_fail = False

    # Q1 task
    has_task = bool(str(candidate.get("task_id") or "").strip())
    checks["Q1_task"] = {"ok": has_task, "detail": candidate.get("task_id") or ""}
    if th.get("require_task") and not has_task:
        hard_fail = True
        reasons.append("Q1: 无 task_id（任务主闭环要求挂接业务场景实例）")

    # Q2 feedback
    fb = candidate.get("feedback_status") or ""
    fb_ok = fb in ("done", "skipped")
    if fb == "skipped" and not (candidate.get("skip_reason") or "").strip():
        fb_ok = False
    checks["Q2_feedback"] = {"ok": fb_ok, "detail": fb}
    if th.get("require_feedback") and not fb_ok:
        hard_fail = True
        reasons.append("Q2: 须反馈 done 或 skipped+原因")

    # Q3 best_T
    best_t = int(candidate.get("best_T") or 0)
    min_t = int(th.get("min_best_T") or 1)
    q3_ok = best_t >= min_t
    checks["Q3_survival"] = {"ok": q3_ok, "detail": f"best_T={best_t} min={min_t}"}
    if not q3_ok:
        msg = f"Q3: 适者存活 T={best_t} < {min_t}"
        if th.get("q3_hard"):
            hard_fail = True
            reasons.append(msg)
        else:
            reasons.append(msg + "（软）")

    # Q4 residual
    att = candidate.get("survival_attribution") or {}
    residual = att.get("residual_share")
    try:
        residual_f = float(residual) if residual is not None else None
    except (TypeError, ValueError):
        residual_f = None
    max_res = float(th.get("max_top_residual") or 0.85)
    q4_ok = residual_f is None or residual_f < max_res
    checks["Q4_residual"] = {
        "ok": q4_ok,
        "detail": f"residual={residual_f} max={max_res}",
    }
    if residual_f is not None and not q4_ok:
        msg = f"Q4: top 适者 residual%={residual_f:.2f} ≥ {max_res}（疑似苟活）"
        if th.get("q4_hard"):
            hard_fail = True
            reasons.append(msg)
        else:
            reasons.append(msg + "（软）")

    # Q5 demand overlap / skill applied
    dom = candidate.get("dominant_skills") or []
    skill_applied = bool(candidate.get("skill_applied"))
    q5_ok = skill_applied or bool(dom) or not th.get("require_demand_overlap")
    if th.get("require_demand_overlap"):
        q5_ok = skill_applied or bool(dom)
    checks["Q5_skill_loop"] = {
        "ok": q5_ok,
        "detail": f"skill_applied={skill_applied} dominant={len(dom)}",
    }
    if th.get("require_demand_overlap") and not q5_ok:
        msg = "Q5: 无 dominant skill 且未写回 Skill"
        if th.get("q5_hard"):
            hard_fail = True
            reasons.append(msg)
        else:
            reasons.append(msg + "（软）")

    # hard 仅 Q1 Q2 默认；软原因不挡 quality_passed
    if hard_fail:
        status = "quality_failed"
    else:
        status = "quality_passed"
        soft = [r for r in reasons if "（软）" in r]
        if soft and not reasons:
            pass

    candidate = dict(candidate)
    candidate["quality_status"] = status
    candidate["quality_checks"] = checks
    candidate["quality_reasons"] = reasons
    candidate["updated_at"] = _utc()
    return candidate


def save_candidate(doc: Dict[str, Any], base: Optional[Path] = None) -> Dict[str, Any]:
    team_id = doc.get("team_id") or "default"
    cid = doc.get("candidate_id") or new_candidate_id()
    doc = dict(doc)
    doc["candidate_id"] = cid
    doc["updated_at"] = _utc()
    path = team_dir(team_id, base) / f"{_safe(cid)}.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    return doc


def load_candidate(team_id: str, candidate_id: str, base: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    path = team_dir(team_id, base) / f"{_safe(candidate_id)}.json"
    if not path.exists():
        # 全局扫描
        root = store_root(base)
        for p in root.glob(f"*/*{_safe(candidate_id)}*.json"):
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("load bid candidate: %s", e)
        return None


def list_candidates(
    team_id: str = "",
    task_id: str = "",
    base: Optional[Path] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    root = store_root(base)
    files: List[Path] = []
    if team_id:
        d = team_dir(team_id, base)
        files = sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    else:
        files = sorted(root.glob("*/*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    out: List[Dict[str, Any]] = []
    for p in files:
        if len(out) >= max(1, limit):
            break
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if task_id and str(doc.get("task_id") or "") != str(task_id):
            continue
        out.append(doc)
    return out


def patch_candidate(
    team_id: str,
    candidate_id: str,
    updates: Dict[str, Any],
    base: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    doc = load_candidate(team_id, candidate_id, base=base)
    if not doc:
        return None
    allowed = {
        "tokens_baseline", "tokens_candidate", "token_efficiency",
        "cost_gate", "ratchet_state", "feedback_status", "skip_reason",
        "skill_applied", "collab_applied", "channel_applied", "relation_applied",
        "task_id", "plan_id", "note",
    }
    for k, v in (updates or {}).items():
        if k in allowed:
            doc[k] = v
    # 改反馈/任务后重算质量
    if any(k in (updates or {}) for k in (
        "feedback_status", "skip_reason", "task_id",
        "skill_applied", "tokens_candidate", "tokens_baseline",
    )):
        doc = apply_quality_check(doc)
    # 成本门自动
    tb = doc.get("tokens_baseline")
    tc = doc.get("tokens_candidate")
    try:
        if tb is not None and tc is not None:
            doc["cost_gate"] = "pass" if float(tc) <= float(tb) else "fail"
    except (TypeError, ValueError):
        pass
    return save_candidate(doc, base=base)


def try_lock_candidate(
    team_id: str,
    candidate_id: str,
    base: Optional[Path] = None,
) -> Dict[str, Any]:
    """仅 quality_passed 且 cost_gate!=fail 可锁定."""
    doc = load_candidate(team_id, candidate_id, base=base)
    if not doc:
        return {"ok": False, "error": "not_found"}
    doc = apply_quality_check(doc)
    if doc.get("quality_status") != "quality_passed":
        return {
            "ok": False,
            "error": "quality_not_passed",
            "quality_status": doc.get("quality_status"),
            "reasons": doc.get("quality_reasons") or [],
            "candidate": doc,
        }
    tb, tc = doc.get("tokens_baseline"), doc.get("tokens_candidate")
    if tb is not None and tc is not None:
        try:
            if float(tc) > float(tb):
                return {
                    "ok": False,
                    "error": "token_not_better",
                    "detail": f"tokens_candidate={tc} > baseline={tb}",
                    "candidate": doc,
                }
        except (TypeError, ValueError):
            pass
    doc["ratchet_state"] = "locked"
    doc["cost_gate"] = doc.get("cost_gate") if doc.get("cost_gate") != "fail" else "pass"
    doc["locked_at"] = _utc()
    # 锁定时即静默绑定 skill 到适者（幂等；失败不回滚锁定）
    bind_info = None
    champ = str(doc.get("champion_agent_id") or "")
    skills = list(doc.get("dominant_skills") or [])
    if champ and skills and team_id:
        bind_info = bind_locked_skills_via_router(
            team_id, champ, skills, bid_candidate_id=str(doc.get("candidate_id") or ""),
        )
        doc["skill_bind_on_lock"] = {
            "ok": bind_info.get("ok"),
            "agent_id": champ,
            "assigned": bind_info.get("assigned") or [],
            "already_has": bind_info.get("already_has") or [],
            "error": bind_info.get("error"),
            "at": _utc(),
        }
    save_candidate(doc, base=base)
    return {"ok": True, "candidate": doc, "skill_bind": bind_info}


def list_locked_candidates(
    team_id: str,
    task_id: str = "",
    base: Optional[Path] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """列出 locked 候选；task_id 优先精确匹配，否则返回该队全部 locked."""
    items = list_candidates(team_id=team_id, task_id="", base=base, limit=max(50, limit * 3))
    locked = [c for c in items if (c.get("ratchet_state") or "") == "locked"]
    if task_id:
        exact = [c for c in locked if str(c.get("task_id") or "") == str(task_id)]
        if exact:
            locked = exact
    locked.sort(
        key=lambda c: str(c.get("locked_at") or c.get("updated_at") or ""),
        reverse=True,
    )
    return locked[: max(1, limit)]


def resolve_production_config(
    team_id: str,
    task_id: str = "",
    base: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """生产默认构型：取最新 locked 候选（同 task 优先）."""
    locked = list_locked_candidates(team_id, task_id=task_id, base=base, limit=5)
    if not locked and task_id:
        locked = list_locked_candidates(team_id, task_id="", base=base, limit=5)
    if not locked:
        return None
    c = locked[0]
    skills = list(c.get("dominant_skills") or [])
    return {
        "bid_candidate_id": c.get("candidate_id"),
        "team_id": c.get("team_id") or team_id,
        "task_id": c.get("task_id") or task_id,
        "champion_agent_id": c.get("champion_agent_id") or "",
        "required_skills": skills,
        "best_T": c.get("best_T"),
        "eco_fp": c.get("eco_fp") or "",
        "plan_id": c.get("plan_id") or "",
        "locked_at": c.get("locked_at") or c.get("updated_at"),
        "source": "eco_bid_locked",
        "candidate": c,
    }


def bind_locked_skills_via_router(
    team_id: str,
    agent_id: str,
    skill_ids: List[str],
    *,
    bid_candidate_id: str = "",
) -> Dict[str, Any]:
    """XC-4.4b：经 SkillRouter.assign 静默写入 agent.skills（幂等）.

    - 真身落盘 + 可选熟练度抬升（assign 内建）
    - 失败不抛到调用方硬失败；返回 ok=False + error
    - metadata.skip_locked_skill_bind / skip_locked_bid 由调用方拦截
    """
    skills = [str(s) for s in (skill_ids or []) if s]
    if not team_id or not agent_id or not skills:
        return {
            "ok": False,
            "error": "missing_team_agent_or_skills",
            "assigned": [],
            "already_has": [],
        }
    try:
        from agents.skill_router import get_skill_router
        router = get_skill_router()
        if router is None:
            return {"ok": False, "error": "router_unavailable", "assigned": [], "already_has": []}
        session_id = f"eco_bid_lock:{bid_candidate_id or 'na'}:{agent_id}"
        result = router.assign(
            team_id=team_id,
            agent_id=agent_id,
            skill_ids=skills,
            session_id=session_id,
        )
        if result.get("error"):
            return {
                "ok": False,
                "error": result.get("error"),
                "assigned": result.get("assigned") or [],
                "already_has": result.get("already_has") or [],
            }
        logger.info(
            "eco_bid SkillRouter.bind team=%s agent=%s bid=%s assigned=%s already=%s",
            team_id, agent_id, bid_candidate_id,
            result.get("assigned"), result.get("already_has"),
        )
        return {
            "ok": True,
            "assigned": result.get("assigned") or [],
            "already_has": result.get("already_has") or [],
            "assigned_count": result.get("assigned_count") or 0,
            "proficiency_boosted": result.get("proficiency_boosted") or {},
            "agent_skills_count": result.get("agent_skills_count"),
            "session_id": session_id,
        }
    except Exception as e:
        logger.warning("eco_bid SkillRouter.bind failed: %s", e)
        return {
            "ok": False,
            "error": str(e),
            "assigned": [],
            "already_has": [],
        }


def apply_locked_config_to_task(
    team_id: str,
    *,
    agent_id: str = "",
    metadata: Optional[Dict[str, Any]] = None,
    task_id: str = "",
    base: Optional[Path] = None,
    bind_skills: bool = True,
) -> Dict[str, Any]:
    """把 locked 候选注入任务 metadata；可选补全 agent_id 为适者.

    返回 {metadata, agent_id, applied: bool, config: dict|None, skill_bind: dict|None}
    默认经 SkillRouter 静默绑定 dominant skills 到执行 agent 真身（幂等）。
    """
    meta = dict(metadata or {})
    if meta.get("skip_locked_bid") or meta.get("skip_eco_bid"):
        return {
            "metadata": meta, "agent_id": agent_id, "applied": False,
            "config": None, "skill_bind": None,
        }

    tid = task_id or str(meta.get("task_id") or meta.get("source_task_id") or "")
    cfg = resolve_production_config(team_id, task_id=tid, base=base)
    if not cfg:
        return {
            "metadata": meta, "agent_id": agent_id, "applied": False,
            "config": None, "skill_bind": None,
        }

    meta["bid_candidate_id"] = cfg["bid_candidate_id"]
    meta["eco_bid_locked"] = True
    meta["eco_bid_source"] = "eco_bid_locked"
    if cfg.get("eco_fp"):
        meta.setdefault("eco_fp", cfg["eco_fp"])
    if cfg.get("plan_id"):
        meta.setdefault("plan_id", cfg["plan_id"])
    if cfg.get("best_T") is not None:
        meta["eco_best_T"] = cfg["best_T"]

    skills = list(meta.get("required_skills") or meta.get("skill_genome") or [])
    for s in cfg.get("required_skills") or []:
        if s and s not in skills:
            skills.append(s)
    if skills:
        meta["required_skills"] = skills
        meta.setdefault("skill_genome", list(skills))

    champ = str(cfg.get("champion_agent_id") or "")
    if champ:
        meta.setdefault("champion_agent_id", champ)
    out_agent = agent_id or champ

    skill_bind = None
    do_bind = bool(bind_skills) and not meta.get("skip_locked_skill_bind")
    if do_bind and out_agent and skills:
        skill_bind = bind_locked_skills_via_router(
            team_id,
            out_agent,
            skills,
            bid_candidate_id=str(cfg.get("bid_candidate_id") or ""),
        )
        meta["eco_bid_skill_bind"] = {
            "ok": skill_bind.get("ok"),
            "assigned": skill_bind.get("assigned") or [],
            "already_has": skill_bind.get("already_has") or [],
            "error": skill_bind.get("error"),
        }

    return {
        "metadata": meta,
        "agent_id": out_agent,
        "applied": True,
        "config": {k: v for k, v in cfg.items() if k != "candidate"},
        "skill_bind": skill_bind,
    }
