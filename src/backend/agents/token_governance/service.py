# -*- coding: utf-8 -*-
"""TokenGovernanceService — 任务 LLM 请求的统一治理管线.

prepare_request 顺序 (R9):
  simplify → rtk_tool → compress → progressive_mem → codegraph
  → cache → skill → behavior(ponytail/caveman) → cost_tier+model → budget
"""
from __future__ import annotations

import logging
import re
import threading
import time
from collections import deque
from typing import Any, Dict, List, Optional

from ..prompt_cache import (
    compress_messages,
    estimate_messages_tokens,
    fingerprint_messages,
    get_prompt_cache,
)
from .prompt_simplify import simplify_messages
from .settings import load_tg_settings, save_tg_settings

logger = logging.getLogger(__name__)

# 动态片段剥离（semantic-lite exact 指纹）
_UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I,
)
_ISO_TS_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}")
_HEX_ID_RE = re.compile(r"\b[0-9a-f]{12,}\b", re.I)


def _strip_dynamics(text: str) -> str:
    t = _UUID_RE.sub("<UUID>", text or "")
    t = _ISO_TS_RE.sub("<TS>", t)
    t = _HEX_ID_RE.sub("<HEXID>", t)
    return t


def semantic_lite_fingerprint(messages: List[Dict[str, Any]]) -> str:
    stripped = []
    for m in messages or []:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role") or "user")
        content = m.get("content")
        if not isinstance(content, str):
            content = str(content or "")
        stripped.append({"role": role, "content": _strip_dynamics(content)})
    return fingerprint_messages(stripped)


class TokenGovernanceService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._savings: deque = deque(maxlen=500)
        self._counters = {
            "prepare_calls": 0,
            "simplify_saves": 0,
            "compress_saves": 0,
            "rtk_saves": 0,
            "progressive_saves": 0,
            "codegraph_saves": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "skill_hints": 0,
            "skill_tokens_saved_est": 0,
            "model_routes": 0,
            "model_economy_routes": 0,
            "budget_blocks": 0,
            "behavior_injects": 0,
            "tokens_saved_est": 0,
            "output_save_est": 0,
        }

    def settings(self) -> Dict[str, Any]:
        return load_tg_settings()

    def update_settings(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        from .settings import apply_budget_knobs_from_params

        # budget knobs may ride inside params
        params = (updates or {}).get("params")
        if isinstance(params, dict):
            apply_budget_knobs_from_params(params)
            # strip budget keys from tg params before save
            budget_keys = {
                "alert_threshold", "on_exceed",
                "per_session_max", "per_agent_daily_max", "per_team_daily_max",
            }
            clean = {k: v for k, v in params.items() if k not in budget_keys}
            updates = dict(updates or {})
            updates["params"] = clean
            # resize cache if needed
            if "cache_max_size" in clean:
                try:
                    from ..prompt_cache import resize_prompt_cache
                    resize_prompt_cache(int(clean["cache_max_size"]))
                except Exception:
                    pass
        return save_tg_settings(updates)

    def prepare_request(
        self,
        messages: List[Dict[str, Any]],
        *,
        task_id: str = "",
        team_id: str = "",
        agent_id: str = "",
        session_id: str = "",
        phase: str = "task",
        query_for_skill: str = "",
        estimated_extra_tokens: int = 0,
    ) -> Dict[str, Any]:
        """返回治理后的 messages 与路由/预算决策."""
        cfg = load_tg_settings()
        p = cfg.get("params") or {}
        levers: List[Dict[str, Any]] = []
        work = list(messages or [])
        before_all = estimate_messages_tokens(work)
        saved_total = 0

        # 1) simplify
        if cfg.get("simplify_prompt", True):
            step_before = estimate_messages_tokens(work)
            simp = simplify_messages(work)
            if simp.get("saved_tokens_est", 0) > 0:
                work = simp["messages"]
                step_after = estimate_messages_tokens(work)
                saved_total += int(simp["saved_tokens_est"])
                levers.append({
                    "kind": "simplify",
                    "catalog_id": "simplify_prompt",
                    "saved": simp["saved_tokens_est"],
                    "before": step_before,
                    "after": step_after,
                    "module": "prompt_simplify.simplify_messages",
                })
                with self._lock:
                    self._counters["simplify_saves"] += 1

        # 1a) ponytail + caveman early (so skill shorten / compress see full system)
        behavior_meta: Dict[str, Any] = {}
        if (cfg.get("ponytail_level") or "off") != "off" or (cfg.get("caveman_level") or "off") != "off":
            try:
                from .behavior_inject import inject_behavior
                beh = inject_behavior(
                    work,
                    ponytail=str(cfg.get("ponytail_level") or "full"),
                    caveman=str(cfg.get("caveman_level") or "full"),
                )
                work = beh["messages"]
                behavior_meta = {
                    "injected": beh.get("injected") or [],
                    "input_delta": beh.get("input_delta") or 0,
                    "output_save_est": beh.get("output_save_est") or 0,
                }
                if behavior_meta["injected"]:
                    with self._lock:
                        self._counters["behavior_injects"] += 1
                        self._counters["output_save_est"] = (
                            int(self._counters.get("output_save_est") or 0)
                            + int(behavior_meta["output_save_est"] or 0)
                        )
                    levers.append({
                        "kind": "behavior",
                        "catalog_id": "ponytail_caveman",
                        "saved": 0,
                        "input_delta": behavior_meta["input_delta"],
                        "output_save_est": behavior_meta["output_save_est"],
                        "injected": behavior_meta["injected"],
                        "module": "behavior_inject.inject_behavior",
                    })
            except Exception as e:
                logger.debug("behavior_inject skip: %s", e)

        # 1b) RTK tool-output compress (before generic compress)
        if cfg.get("rtk_tool_compress", True):
            try:
                from .rtk_tool_compress import rtk_compress_messages
                step_before = estimate_messages_tokens(work)
                rtk = rtk_compress_messages(
                    work, max_tool_chars=int(p.get("max_tool_chars") or 2200),
                )
                if rtk.get("saved_tokens_est", 0) > 0:
                    work = rtk["messages"]
                    step_after = estimate_messages_tokens(work)
                    saved_total += int(rtk["saved_tokens_est"])
                    levers.append({
                        "kind": "rtk_tool",
                        "catalog_id": "rtk_tool_compress",
                        "saved": rtk["saved_tokens_est"],
                        "before": step_before,
                        "after": step_after,
                        "actions": rtk.get("actions"),
                        "tool_msgs_touched": rtk.get("tool_msgs_touched"),
                        "module": "rtk_tool_compress.rtk_compress_messages",
                    })
                    with self._lock:
                        self._counters["rtk_saves"] += 1
            except Exception as e:
                logger.debug("rtk_tool_compress skip: %s", e)

        # 2) compress (generic)
        if cfg.get("compress", True):
            step_before = estimate_messages_tokens(work)
            cmp_ = compress_messages(
                work,
                system_max_chars=int(p.get("system_max_chars") or 6000),
                msg_max_chars=int(p.get("msg_max_chars") or 4000),
            )
            if cmp_.get("saved_tokens_est", 0) > 0:
                work = cmp_["messages"]
                step_after = estimate_messages_tokens(work)
                saved_total += int(cmp_["saved_tokens_est"])
                levers.append({
                    "kind": "compress",
                    "catalog_id": "compress",
                    "saved": cmp_["saved_tokens_est"],
                    "before": step_before,
                    "after": step_after,
                    "actions": cmp_.get("action_counts"),
                    "module": "prompt_cache.compress_messages",
                })
                with self._lock:
                    self._counters["compress_saves"] += 1

        # 2b) progressive memory (claude-mem style index collapse)
        if cfg.get("progressive_memory", True):
            try:
                from .progressive_history import progressive_collapse
                step_before = estimate_messages_tokens(work)
                prog = progressive_collapse(
                    work,
                    keep_recent=int(p.get("keep_recent") or 6),
                    min_total_for_collapse=int(p.get("min_total_for_collapse") or 10),
                    index_max_chars=int(p.get("index_max_chars") or 140),
                )
                if prog.get("saved_tokens_est", 0) > 0:
                    work = prog["messages"]
                    step_after = estimate_messages_tokens(work)
                    saved_total += int(prog["saved_tokens_est"])
                    levers.append({
                        "kind": "progressive_mem",
                        "catalog_id": "progressive_memory",
                        "saved": prog["saved_tokens_est"],
                        "before": step_before,
                        "after": step_after,
                        "collapsed": prog.get("collapsed"),
                        "module": "progressive_history.progressive_collapse",
                    })
                    with self._lock:
                        self._counters["progressive_saves"] += 1
            except Exception as e:
                logger.debug("progressive_memory skip: %s", e)

        # 2c) codegraph surgical context (MIT package / local symbols)
        if cfg.get("codegraph_context", True):
            try:
                from .codegraph_bridge import apply_codegraph
                step_before = estimate_messages_tokens(work)
                q = query_for_skill or self._last_user_text(work)
                cg = apply_codegraph(
                    work,
                    query=q,
                    use_cli=True,
                    min_blob_chars=int(p.get("min_blob_chars") or 2500),
                )
                # only keep if net save OR we only did local replace with save
                if cg.get("saved_tokens_est", 0) > 0 or cg.get("replaced", 0) > 0:
                    work = cg["messages"]
                    step_after = estimate_messages_tokens(work)
                    save = max(0, step_before - step_after)
                    if save > 0:
                        saved_total += save
                        with self._lock:
                            self._counters["codegraph_saves"] += 1
                    levers.append({
                        "kind": "codegraph",
                        "catalog_id": "codegraph_context",
                        "saved": save,
                        "before": step_before,
                        "after": step_after,
                        "replaced": cg.get("replaced"),
                        "cli_injected": cg.get("cli_injected"),
                        "indexed": cg.get("indexed"),
                        "bin": bool(cg.get("bin")),
                        "module": "codegraph_bridge.apply_codegraph",
                    })
            except Exception as e:
                logger.debug("codegraph_context skip: %s", e)

        # 3) cache
        cache_mode = cfg.get("cache_mode") or "observe"
        cache_hit = False
        cache_key = ""
        cache_entry = None
        if cache_mode != "off":
            # honor cache_max_size from params
            try:
                from ..prompt_cache import resize_prompt_cache
                resize_prompt_cache(int(p.get("cache_max_size") or 256))
            except Exception:
                pass
            cache = get_prompt_cache()
            key_exact = fingerprint_messages(work)
            key_lite = semantic_lite_fingerprint(work)
            cache_key = key_lite
            entry = cache.get(key_lite) or cache.get(key_exact)
            if entry:
                cache_hit = True
                cache_entry = entry
                with self._lock:
                    self._counters["cache_hits"] += 1
                    # observe 只计量不短路：不把 HIT 虚计入「已省」；serve 短路才算真省
                levers.append({
                    "kind": "cache",
                    "catalog_id": "cache",
                    "hit": True,
                    "mode": cache_mode,
                    "key": cache_key[:16],
                    "module": "prompt_cache.PromptCache + semantic_lite_fingerprint",
                })
            else:
                with self._lock:
                    self._counters["cache_misses"] += 1
                # warm exact+lite keys for future
                cache.put(key_lite, value="seen", tokens_est=estimate_messages_tokens(work))
                levers.append({
                    "kind": "cache",
                    "catalog_id": "cache",
                    "hit": False,
                    "mode": cache_mode,
                    "module": "prompt_cache.PromptCache + semantic_lite_fingerprint",
                })

        serve_from_cache = bool(cache_hit and cache_mode == "serve" and cache_entry)
        if serve_from_cache and cache_entry:
            # 真短路：本轮可省下发往 LLM 的上下文量
            hit_tokens = int(cache_entry.get("tokens_est") or estimate_messages_tokens(work) or 0)
            with self._lock:
                self._counters["tokens_saved_est"] += hit_tokens
            for lv in levers:
                if lv.get("kind") == "cache":
                    lv["saved_est"] = hit_tokens
                    lv["serve"] = True
                    break

        # 4) skill route：hint + 真缩短 system（注入精简 skill 指令，裁掉冗长 system 尾）
        skill_hint: Dict[str, Any] = {}
        if cfg.get("skill_route_hint", True) and team_id and (query_for_skill or work):
            skill_hint = self._skill_hint(team_id, query_for_skill or self._last_user_text(work))
            if skill_hint.get("skill_ids"):
                short = self._apply_skill_shorten(
                    work,
                    team_id=team_id,
                    skill_ids=skill_hint["skill_ids"][:5],
                    system_max_chars=int(p.get("skill_system_max_chars") or 3500),
                )
                # 只记真实 before→after；注入指令可能变长则 saved=0（仍标 injected）
                skill_save = max(0, int(short.get("saved_tokens_est") or 0))
                if short.get("messages"):
                    work = short["messages"]
                if skill_save > 0:
                    saved_total += skill_save
                with self._lock:
                    self._counters["skill_hints"] += 1
                    if skill_save > 0:
                        self._counters["skill_tokens_saved_est"] = (
                            int(self._counters.get("skill_tokens_saved_est") or 0) + skill_save
                        )
                        # tokens_saved_est 在末尾按 measured before/after 统一入账，避免与 skill 双计
                levers.append({
                    "kind": "skill_route",
                    "catalog_id": "skill_route",
                    "skills": skill_hint["skill_ids"][:5],
                    "top_score": skill_hint.get("top_score"),
                    "saved_est": skill_save,
                    "system_truncated": bool(short.get("truncated")),
                    "injected": bool(short.get("injected")),
                    "source": skill_hint.get("source"),
                    "module": "skill_router.route + _apply_skill_shorten",
                })
                skill_hint["shorten"] = {
                    "truncated": short.get("truncated"),
                    "injected": short.get("injected"),
                    "saved_tokens_est": skill_save,
                }

        # 5) model route (+ flowork cost-tier hint)
        model_decision: Dict[str, Any] = {}
        cost_tier_meta: Dict[str, Any] = {}
        if cfg.get("model_route", True):
            try:
                from ..runtime.model_router import (
                    ModelTier,
                    clamp_model_to_global,
                    get_model_router,
                    resolve_live_primary_model,
                )
                router = get_model_router()
                est = estimate_messages_tokens(work) + int(estimated_extra_tokens or 0)
                tier_hint = None
                if cfg.get("cost_tier_route", True):
                    from .cost_tier import classify_complexity
                    cost_tier_meta = classify_complexity(work)
                    tier_hint = cost_tier_meta.get("tier_hint")
                    if tier_hint == "economy":
                        router.prefer_tier(ModelTier.ECONOMY, "cost_tier_economy")
                    elif tier_hint == "frontier":
                        router.prefer_tier(ModelTier.FRONTIER, "cost_tier_frontier")
                dec = router.route(tokens_estimated=0)
                # 全局配置为主：prepare 出口的 model 名一律钳制到全局连接模型
                # （档位 tier 仍可记，但不得把 deepseek-v4-pro 等写进上游请求）
                primary, _prov = resolve_live_primary_model()
                safe_model = clamp_model_to_global(dec.model) or primary or dec.model
                reason = dec.reason or ""
                if safe_model and safe_model != (dec.model or ""):
                    reason = f"{reason}+global_primary".strip("+")
                model_decision = {
                    "tier": dec.tier.value,
                    "model": safe_model,
                    "reason": reason or "global_primary",
                    "tokens_est": est,
                    "cost_tier": cost_tier_meta or None,
                    "routed_model": dec.model,
                    "global_primary": primary or None,
                }
                with self._lock:
                    self._counters["model_routes"] += 1
                    if model_decision.get("tier") == "economy":
                        self._counters["model_economy_routes"] = (
                            int(self._counters.get("model_economy_routes") or 0) + 1
                        )
                levers.append({
                    "kind": "model_route",
                    "catalog_id": "model_route",
                    "module": "runtime.model_router.ModelRouter + cost_tier.classify_complexity",
                    **{k: v for k, v in model_decision.items() if k != "cost_tier"},
                    "cost_tier_hint": (cost_tier_meta or {}).get("tier_hint"),
                    "cost_tier_score": (cost_tier_meta or {}).get("score"),
                })
            except Exception as e:
                logger.debug("model_route skip: %s", e)

        # 6) budget
        budget: Dict[str, Any] = {"allowed": True, "events": []}
        if cfg.get("budget_enforce_turn", True):
            try:
                from ..budget import get_budget_guard
                guard = get_budget_guard()
                est = estimate_messages_tokens(work) + int(estimated_extra_tokens or 0)
                check = guard.check(
                    session_id=session_id or f"tg:{task_id or 'na'}",
                    agent_id=agent_id or "unknown",
                    team_id=team_id or "unknown",
                    estimated_tokens=est,
                )
                budget = {
                    "allowed": bool(check.allowed),
                    "events": [
                        {
                            "scope": ev.scope,
                            "level": ev.level,
                            "message": ev.message,
                            "value": ev.value,
                            "limit": ev.limit,
                        }
                        for ev in (check.events or [])
                    ],
                }
                if not check.allowed:
                    with self._lock:
                        self._counters["budget_blocks"] += 1
                    levers.append({
                        "kind": "budget",
                        "catalog_id": "budget",
                        "blocked": True,
                        "module": "budget.guard.BudgetGuard",
                    })
                else:
                    levers.append({
                        "kind": "budget",
                        "catalog_id": "budget",
                        "blocked": False,
                        "allowed": True,
                        "events": len(budget.get("events") or []),
                        "module": "budget.guard.BudgetGuard",
                    })
            except Exception as e:
                logger.debug("budget check skip: %s", e)

        after_all = estimate_messages_tokens(work)
        # 总节省只认真实 before→after（禁止 skill 注入变长时虚增；禁止 step 加总 > 净减）
        measured_save = max(0, before_all - after_all)
        saved_total = measured_save

        event = {
            "at": time.time(),
            "task_id": task_id,
            "team_id": team_id,
            "agent_id": agent_id,
            "session_id": session_id,
            "phase": phase,
            "saved_tokens_est": saved_total,
            "before": before_all,
            "after": after_all,
            "cache_hit": cache_hit,
            "lever_kinds": [x.get("kind") for x in levers],
            "model_tier": (model_decision or {}).get("tier"),
        }
        with self._lock:
            self._counters["prepare_calls"] += 1
            # KPI「治理已省」= 净减少上下文 token（不含 observe 假省）
            if measured_save > 0:
                self._counters["tokens_saved_est"] += measured_save
            self._savings.appendleft(event)
        try:
            from .savings_store import append_event
            append_event(event)
        except Exception as e:
            logger.debug("savings_store append: %s", e)

        # R6.3：可观测行（total_tokens=0，不污染账单总和；model 编码节省量）
        if saved_total > 0 and (task_id or team_id):
            try:
                from ..budget import UsageRecord, get_budget_guard
                get_budget_guard().record_usage(UsageRecord(
                    session_id=session_id or f"tg:{task_id or 'na'}",
                    agent_id=agent_id or "tg",
                    team_id=team_id or "",
                    model=f"tg_prepare_save:{saved_total}",
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    phase="tg_prepare",
                    skill_id=",".join(
                        (skill_hint or {}).get("skill_ids") or []
                    )[:120],
                    scenario_id=task_id or "",
                    run_id=session_id or "",
                ))
            except Exception as e:
                logger.debug("tg_prepare usage row: %s", e)

        return {
            "messages": work,
            "before_tokens": before_all,
            "after_tokens": after_all,
            "saved_tokens_est": saved_total,
            "levers": levers,
            "cache_hit": cache_hit,
            "cache_key": cache_key,
            "serve_from_cache": serve_from_cache,
            "cache_entry": cache_entry if serve_from_cache else None,
            "skill_hint": skill_hint,
            "model": model_decision,
            "budget": budget,
            "settings": {k: cfg[k] for k in (
                "compress", "simplify_prompt", "cache_mode", "model_route", "skill_route_hint",
            )},
            "task_id": task_id,
            "team_id": team_id,
            "agent_id": agent_id,
            "phase": phase,
        }

    def _last_user_text(self, messages: List[Dict[str, Any]]) -> str:
        for m in reversed(messages or []):
            if isinstance(m, dict) and m.get("role") == "user":
                return str(m.get("content") or "")[:2000]
        return ""

    def _apply_skill_shorten(
        self,
        messages: List[Dict[str, Any]],
        *,
        team_id: str,
        skill_ids: List[str],
        system_max_chars: int = 3500,
    ) -> Dict[str, Any]:
        """R5.1：有 skill 时裁 system 长尾 + 注入精简 skill 指令（确定性，不调 LLM）."""
        from ..prompt_cache import estimate_messages_tokens

        work = [dict(m) for m in (messages or [])]
        before = estimate_messages_tokens(work)
        truncated = False
        injected = False
        inject_text = ""
        try:
            from ..skill_router import get_skill_router
            router = get_skill_router()
            if router is not None and hasattr(router, "_generate_inject_prompt"):
                inject_text = router._generate_inject_prompt(team_id, skill_ids) or ""
        except Exception:
            inject_text = ""
        if not inject_text and skill_ids:
            inject_text = (
                "## Prefer bound skills (compact)\n"
                + "\n".join(f"- use skill `{s}` when relevant; do not restate full playbooks." for s in skill_ids)
            )

        if work and work[0].get("role") == "system":
            sys_c = str(work[0].get("content") or "")
            # 已有 skill 可复用 → system 正文硬上限（可调）
            max_sys = max(500, int(system_max_chars or 3500))
            tag = "[TG_SKILL_BODY]"
            if len(sys_c) > max_sys:
                sys_c = sys_c[:max_sys] + f"\n…[tg skill-shorten truncated {len(sys_c) - max_sys} chars]"
                truncated = True
            if tag not in sys_c and inject_text:
                sys_c = sys_c.rstrip() + f"\n\n{tag}\n{inject_text[:1800]}"
                injected = True
            work[0] = {**work[0], "content": sys_c}

        after = estimate_messages_tokens(work)
        return {
            "messages": work,
            "before_tokens": before,
            "after_tokens": after,
            "saved_tokens_est": max(0, before - after),
            "truncated": truncated,
            "injected": injected,
        }

    def _skill_hint(self, team_id: str, query: str) -> Dict[str, Any]:
        if not query or not team_id:
            return {}
        ids: List[str] = []
        top_score = None
        source = ""
        try:
            from ..skill_router import get_skill_router
            router = get_skill_router()
            if router is not None:
                # SkillRouter.route 返回 RoutingSession（非 dict）
                result = router.route(query=query, team_id=team_id, top_k=5, mode="suggest")
                ranked = []
                if hasattr(result, "results"):
                    ranked = list(result.results or [])
                    source = "skill_router"
                elif isinstance(result, dict):
                    ranked = (
                        result.get("ranked")
                        or result.get("results")
                        or result.get("skills")
                        or []
                    )
                    source = "skill_router_dict"
                for item in ranked[:5]:
                    if hasattr(item, "skill_id"):
                        sid = getattr(item, "skill_id", "") or ""
                        sc = getattr(item, "score", None)
                    elif isinstance(item, dict):
                        sid = item.get("skill_id") or item.get("id") or item.get("slug") or ""
                        sc = item.get("score") or item.get("relevance")
                    elif isinstance(item, str):
                        sid, sc = item, None
                    else:
                        continue
                    if sid:
                        ids.append(str(sid))
                    if top_score is None and sc is not None:
                        try:
                            top_score = float(sc)
                        except (TypeError, ValueError):
                            top_score = sc
        except Exception as e:
            logger.debug("skill_hint router: %s", e)
            source = f"error:{e}"

        # pool 为空或未命中 → 团队技能库关键词回退
        if not ids:
            fb = self._skill_keyword_fallback(team_id, query)
            if fb.get("skill_ids"):
                ids = fb["skill_ids"]
                top_score = fb.get("top_score")
                source = "keyword_fallback"

        return {
            "skill_ids": ids[:5],
            "top_score": top_score,
            "source": source,
        }

    def _skill_keyword_fallback(self, team_id: str, query: str) -> Dict[str, Any]:
        """当 SkillRouter pool 为空时，从团队 skills 做轻量关键词匹配."""
        import re
        q = (query or "").lower()
        tokens = set(re.findall(r"[\u4e00-\u9fff]{2,}|[a-z0-9_]{3,}", q))
        if not tokens:
            return {}
        pool: List[Dict[str, Any]] = []
        try:
            from ..team_store import TeamStore
            # team_manager 单例
            try:
                from .. import api as agent_api
                tm = agent_api._tm()
                team = tm.get_team(team_id) if tm else None
                if team and getattr(team, "skills", None):
                    for sid, sk in (team.skills or {}).items():
                        pool.append({
                            "skill_id": getattr(sk, "skill_id", None) or sid,
                            "name": getattr(sk, "name", "") or "",
                            "description": getattr(sk, "description", "") or "",
                            "instructions": (getattr(sk, "instructions", "") or "")[:400],
                        })
            except Exception:
                pass
        except Exception:
            pass
        if not pool:
            try:
                from ..skill_router import get_skill_router
                r = get_skill_router()
                if r:
                    pool = r._get_skill_pool(team_id) or []
            except Exception:
                pass
        scored = []
        for s in pool:
            text = f"{s.get('name','')} {s.get('description','')} {s.get('skill_id','')}".lower()
            words = set(re.findall(r"[\u4e00-\u9fff]{2,}|[a-z0-9_]{3,}", text))
            hit = tokens & words
            if hit:
                scored.append((len(hit), str(s.get("skill_id") or ""), hit))
        scored.sort(reverse=True)
        ids = [sid for n, sid, _ in scored if sid][:5]
        return {
            "skill_ids": ids,
            "top_score": float(scored[0][0]) if scored else None,
        }

    def counters(self) -> Dict[str, Any]:
        with self._lock:
            c = dict(self._counters)
            recent = list(self._savings)[:20]
        cache = get_prompt_cache().stats()
        return {"counters": c, "recent_savings": recent, "cache": cache}

    def dashboard(self, *, window: str = "24h", team_id: str = "") -> Dict[str, Any]:
        from ..token_ledger import LEDGER
        from ..budget import get_budget_guard

        summary = LEDGER.summary(window)
        by_task = LEDGER.by_task(window=window, team_id=team_id or "", limit=40)
        unscoped = next((x for x in by_task if x.get("task_key") == "(unscoped)"), None)
        attributed = [x for x in by_task if x.get("task_key") != "(unscoped)"]
        attr_total = sum(int(x.get("total") or 0) for x in attributed)
        uns_total = int((unscoped or {}).get("total") or 0)
        grand = attr_total + uns_total
        cfg = load_tg_settings()
        stats = self.counters()
        guard = get_budget_guard()
        model_state = {}
        try:
            from ..runtime.model_router import get_model_router
            model_state = get_model_router().get_state_dict()
        except Exception:
            pass
        savings_by_task = []
        recent_savings = []
        try:
            from .savings_store import aggregate_by_task, recent_events
            savings_by_task = aggregate_by_task(limit_tasks=15, team_id=team_id or "")
            recent_savings = recent_events(limit=12, team_id=team_id or "")
        except Exception:
            pass
        return {
            "ok": True,
            "window": window,
            "team_id": team_id,
            "summary": summary,
            "by_task": attributed[:25],
            "unscoped": unscoped,
            "attribution": {
                "attributed_total": attr_total,
                "unscoped_total": uns_total,
                "attributed_share": round(attr_total / grand, 4) if grand else 0.0,
                "task_count": len(attributed),
            },
            "levers": cfg,
            "stats": stats,
            "savings_by_task": savings_by_task,
            "recent_savings": recent_savings,
            "budget": guard.budget.to_dict(),
            "budget_events": (guard.alerts().get("events") or [])[:15],
            "model_router": model_state,
            "policy": {
                "plaza_no_optimize": True,
                "unit": "task_tokens",
                "note": "讨论阶段不优化；执行任务走 prepare_request",
            },
        }


_svc: Optional[TokenGovernanceService] = None
_svc_lock = threading.Lock()


def get_token_governance() -> TokenGovernanceService:
    global _svc
    with _svc_lock:
        if _svc is None:
            _svc = TokenGovernanceService()
        return _svc
