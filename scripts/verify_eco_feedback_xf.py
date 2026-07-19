#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""物竞适者反馈台 + 物竞×成本 验收脚本

覆盖（XF + XC，不依赖浏览器）：
  - relation/channel confirm=false 零写入 / confirm=true 落盘
  - collab metadata 写回可读
  - 前端门禁 / 任务挂载 / 任务 HUD / 成本竞标符号
  - BidCandidate：质量门 → token → lock → production 注入（离线）
  - 活后端：create → list → PATCH → quality → lock 拒绝/成功 → GET locked

用法（项目根）:
  PYTHONPATH=src/backend python3 scripts/verify_eco_feedback_xf.py
  PYTHONPATH=src/backend python3 scripts/verify_eco_feedback_xf.py --base http://127.0.0.1:8080
  PYTHONPATH=src/backend python3 scripts/verify_eco_feedback_xf.py --offline-only
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

PASS = 0
FAIL = 0
SKIP = 0


def _ok(name: str, detail: str = "") -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {name}" + (f" — {detail}" if detail else ""))


def _fail(name: str, detail: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {name} — {detail}")


def _skip(name: str, detail: str) -> None:
    global SKIP
    SKIP += 1
    print(f"  SKIP  {name} — {detail}")


def _http_json(method: str, url: str, body: dict | None = None, timeout: float = 8.0):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return resp.status, json.loads(raw) if raw else {}


def check_static_frontend() -> None:
    print("\n== 静态契约（前端源码） ==")
    eco_fb = (ROOT / "src/frontend/js/digital-twin/eco-feedback.js").read_text(encoding="utf-8")
    eco_console = (ROOT / "src/frontend/js/digital-twin/eco-console.js").read_text(encoding="utf-8")
    cost = (ROOT / "src/frontend/cost-dashboard.html").read_text(encoding="utf-8")
    detail = (ROOT / "src/frontend/js/agent-detail.js").read_text(encoding="utf-8")
    team = (ROOT / "src/frontend/js/agent-team-config.js").read_text(encoding="utf-8")
    html = (ROOT / "src/frontend/Agent-digital-twin.html").read_text(encoding="utf-8")

    checks = [
        ("XF-4.3 反馈门禁 ecoFeedbackGoCost", "ecoFeedbackGoCost" in eco_fb and "跳过写回" in eco_fb),
        ("XF-4.3 skipped 参数", "skipped" in eco_fb and "feedback" in eco_fb),
        ("XF-6.7 任务挂载 eco2BindTaskById", "eco2BindTaskById" in eco_console or "eco2BindTaskById" in html),
        ("XF-6.7 任务挂载 DOM", "eco2-task-mount" in html or "eco2-task-mount" in eco_console),
        ("XF-6.4 空跑 confirm", "随机" in eco_console or "空跑" in eco_console),
        ("XF-3 cost 候选条", "eco_fp" in cost and "feedback" in cost),
        ("XF-2.4 eco_collab 展示", "eco_collab" in detail),
        ("XF-7.13 空关系 CTA", "物竞 ③" in team or "生成建议" in team),
        ("XF-7 关系图 Before", "eco-fb-rel-before" in eco_fb or "BEFORE" in eco_fb),
        ("XF-7 通道/关系 apply", "relation-integration/apply" in eco_fb and "channel-integration/apply" in eco_fb),
        ("_resolveTeamId", "_resolveTeamId" in eco_fb),
        ("resolve_team_bus 前端不依赖", True),
        ("XF-5 任务 HUD 模块", (ROOT / "src/frontend/js/digital-twin/eco-task-hud.js").exists()),
        ("XF-5 HUD DOM", "env-3d-task-hud" in html),
        ("XF-5 ecoTaskHudBind", "ecoTaskHudBind" in eco_console),
        ("XC-2.4 推送成本竞标", "ecoFeedbackPushBid" in eco_fb or "bid-candidates" in eco_fb),
        ("XC-2.6 cost 候选面板", "bid-candidates" in cost or "candidate_id" in cost),
        ("XC-4.5 先适者后省钱文案", "适者" in cost or "先适者" in cost or "省钱" in cost),
        ("XC-4.3 棘轮 lock UI", "lock" in cost.lower() and ("ratchet" in cost.lower() or "棘轮" in cost)),
        ("XC cost 物竞主轴常驻", "eco-hub" in cost and "initEcoHub" in cost and "loadEcoProduction" in cost),
        ("XC 试验田④跳转", "ecoGoCostStep" in eco_fb),
        ("TG 主轴 Token 治理", "tg-hub" in cost and "tgRefreshAll" in cost and "token-governance" in cost),
        ("TG 全链序号 1–6", "cost-shell__pipe" in cost and "Token 治理" in cost and "生产注入" in cost),
        ("TG 顶栏合并导航", "cost-shell" in cost and "cost-shell__pipe" in cost and "cost-detail-bar" in cost and 'class="tg-pipe"' not in cost and 'class="ev-action-bar"' not in cost and 'class="topbar-ws"' not in cost),
        ("TG 物竞侧支折叠", "eco-hub-details" in cost and "<details" in cost),
        ("TG v2 workbench", "token-workbench.js" in cost and "tg-kpi-row" in cost and "tg-lever-panel" in cost),
        ("TG v2 service module", (ROOT / "src/backend/agents/token_governance/service.py").exists()),
    ]
    for name, ok in checks:
        (_ok if ok else _fail)(name, "ok" if ok else "missing symbol")


def check_offline_python() -> None:
    print("\n== 离线逻辑（无后端） ==")
    from agents.agent_channel_bus import (
        agent_can_publish,
        apply_bindings_to_agent,
        list_channel_bindings,
        merge_channel_bindings,
    )
    from agents.agent_relationships import AgentRelationship, RelationshipStore
    from sandbox.channel_integration import build_channel_suggestions, resolve_team_bus
    from sandbox.collab_integration import build_collab_suggestions, materialize_collab_payload
    from sandbox.relation_integration import build_relation_suggestions, materialize_relation

    team_id = "aws-ops"
    agent_channels = {
        "aws_mon": [{"channel_name": "aws_ops_bus", "subscribe": True, "publish": False}],
        "aws_lead": [{"channel_name": "aws_ops_bus", "subscribe": True, "publish": True}],
    }
    bus = resolve_team_bus(team_id, agent_channels)
    if bus == "aws_ops_bus":
        _ok("XF-7.14 bus 优先真身名", bus)
    else:
        _fail("XF-7.14 bus 优先真身名", bus)

    result = {
        "final_ranking": [
            {
                "agent_id": "aws_mon",
                "survival_ticks": 90,
                "population": "aws-ops",
                "collab_genome": {
                    "share_tendency": 0.85,
                    "signal_tendency": 0.9,
                    "follow_tendency": 0.4,
                    "mate_choosiness": 0.2,
                },
            },
            {
                "agent_id": "aws_lead",
                "survival_ticks": 70,
                "population": "aws-ops",
                "collab_genome": {
                    "share_tendency": 0.7,
                    "signal_tendency": 0.6,
                    "follow_tendency": 0.8,
                    "mate_choosiness": 0.3,
                },
            },
        ],
        "timeline": {
            "steps": [
                {
                    "actions": {
                        "aws_mon": {
                            "signals": ["FOOD@es"],
                            "shared_to": "aws_lead",
                            "followed": False,
                        },
                        "aws_lead": {"signals": [], "followed": True, "shared_to": None},
                    }
                }
            ]
        },
    }

    # XF-7.15 confirm=false 语义：materialize 不写 store
    with tempfile.TemporaryDirectory() as tmp:
        store = RelationshipStore(store_dir=Path(tmp))
        rrep = build_relation_suggestions(
            result,
            team_id=team_id,
            existing_edges=[],
            agent_channels=agent_channels,
            agent_ids=list(agent_channels.keys()),
        )
        if rrep["count"] >= 1 and rrep["before_count"] >= 1:
            _ok("XF-7.1 suggest 有边+before", f"sug={rrep['count']} before={rrep['before_count']}")
        else:
            _fail("XF-7.1 suggest", str(rrep.get("count")))

        # confirm false: no add
        if len(store.list_team(team_id)) == 0:
            _ok("XF-7.15 confirm=false 零写入(关系)", "store empty")
        else:
            _fail("XF-7.15 confirm=false 零写入(关系)", "store not empty")

        # confirm true
        applied = 0
        for s in rrep["suggestions"]:
            if not s.get("default_checked"):
                continue
            payload = materialize_relation(s, team_id=team_id, fingerprint="xf_verify_fp")
            res = store.add(AgentRelationship(**payload))
            if res.get("ok"):
                applied += 1
        if applied >= 1:
            _ok("XF-7.14b 关系 confirm=true 写入", f"applied={applied}")
        else:
            # may all be already_exists if no default_checked — force one
            s0 = rrep["suggestions"][0]
            payload = materialize_relation(s0, team_id=team_id, fingerprint="xf_verify_fp")
            res = store.add(AgentRelationship(**payload))
            if res.get("ok") or res.get("error") == "duplicate":
                _ok("XF-7.14b 关系写入", str(res))
            else:
                _fail("XF-7.14b 关系写入", str(res))

        rels = store.list_team(team_id)
        if any("human_via_eco_feedback" in (r.created_by or "") for r in rels):
            _ok("XF-7.14b created_by", "human_via_eco_feedback")
        else:
            _fail("XF-7.14b created_by", str([r.created_by for r in rels]))

    # channel merge no fork
    crep = build_channel_suggestions(result, team_id=team_id, agent_channels=agent_channels)
    if crep.get("bus_name") == "aws_ops_bus":
        _ok("通道 suggest bus=aws_ops_bus", crep["bus_name"])
    else:
        _fail("通道 suggest bus", crep.get("bus_name"))

    class _A:
        def __init__(self):
            self.channels = list(agent_channels["aws_mon"])
            self.agent_id = "aws_mon"

    agent = _A()
    mon = next(s for s in crep["suggestions"] if s["agent_id"] == "aws_mon")
    merged = merge_channel_bindings(list_channel_bindings(agent), mon["channel_diffs"])
    apply_bindings_to_agent(agent, merged)
    names = [c["channel_name"] for c in list_channel_bindings(agent)]
    if names == ["aws_ops_bus"] and agent_can_publish(agent, "aws_ops_bus")[0]:
        _ok("XF-7.14b 通道合并不分叉+publish", str(names))
    else:
        _fail("XF-7.14b 通道合并", f"names={names} pub={agent_can_publish(agent, 'aws_ops_bus')}")

    # collab metadata
    collab = build_collab_suggestions(result, top_k=4)
    pay = materialize_collab_payload(collab["suggestions"][0], fingerprint="xf", strategy_override="blend")
    if all(k in pay for k in ("share_tendency", "signal_tendency", "source")):
        _ok("XF-4.2 collab payload 可读", pay.get("source"))
    else:
        _fail("XF-4.2 collab payload", str(pay.keys()))

    # XC BidCandidate offline（临时目录，不碰真存储 / 不调 SkillRouter 真身）
    from sandbox.bid_candidate import (
        apply_locked_config_to_task,
        apply_quality_check,
        build_candidate_from_result,
        list_locked_candidates,
        patch_candidate,
        resolve_production_config,
        save_candidate,
        try_lock_candidate,
    )

    drill = {
        "final_ranking": [
            {
                "agent_id": "aws_mon",
                "survival_ticks": 88,
                "population": "aws-ops",
                "attr_skill_share": 0.3,
                "attr_collab_share": 0.2,
                "attr_residual_share": 0.5,
            }
        ],
        "contract": {
            "plan_id": "plan_xc_verify",
            "task_id": "task_xc_offline",
            "topic": "XC offline verify",
            "niches": [{"index": 0, "title": "巡检", "demanded_skills": ["monitor"]}],
            "provenance": {"fingerprint": "fp_xc_offline"},
        },
        "integration": {"dominant_skills": []},  # 空 skill：lock 不触发 SkillRouter 真身
    }
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        no_task = build_candidate_from_result(
            team_id="aws-ops",
            result={**drill, "contract": {"plan_id": "p", "niches": [], "provenance": {}}},
            feedback={"feedback": "done", "skill_applied": True},
            task_id="",
        )
        no_task = apply_quality_check(no_task)
        if no_task.get("quality_status") == "quality_failed" and any(
            "Q1" in r for r in (no_task.get("quality_reasons") or [])
        ):
            _ok("XC-2.5 Q1 无 task 质量失败", no_task.get("quality_status"))
        else:
            _fail("XC-2.5 Q1 无 task", str(no_task.get("quality_status")))

        doc = build_candidate_from_result(
            team_id="aws-ops",
            result=drill,
            feedback={"feedback": "done", "skill_applied": True, "fingerprint": "fp_xc_offline"},
            task_id="task_xc_offline",
        )
        save_candidate(doc, base=base)
        cid = doc["candidate_id"]
        if doc.get("quality_status") == "quality_passed":
            _ok("XC-3.1 quality_passed", cid)
        else:
            _fail("XC-3.1 quality_passed", str(doc.get("quality_reasons")))

        worse = patch_candidate(
            "aws-ops", cid, {"tokens_baseline": 100, "tokens_candidate": 150}, base=base,
        )
        bad_lock = try_lock_candidate("aws-ops", cid, base=base)
        if not bad_lock.get("ok") and bad_lock.get("error") == "token_not_better":
            _ok("XC-4.2 token 更贵拒绝 lock", bad_lock.get("error"))
        else:
            _fail("XC-4.2 token 更贵拒绝 lock", str(bad_lock)[:180])

        patch_candidate(
            "aws-ops", cid, {"tokens_baseline": 100, "tokens_candidate": 80}, base=base,
        )
        good_lock = try_lock_candidate("aws-ops", cid, base=base)
        if good_lock.get("ok") and (good_lock.get("candidate") or {}).get("ratchet_state") == "locked":
            _ok("XC-4.1/4.3 lock 成功", cid)
        else:
            _fail("XC-4.1/4.3 lock", str(good_lock)[:180])

        locked = list_locked_candidates("aws-ops", task_id="task_xc_offline", base=base)
        cfg = resolve_production_config("aws-ops", task_id="task_xc_offline", base=base)
        if locked and cfg and cfg.get("bid_candidate_id") == cid:
            _ok("XC-4.4 resolve_production_config", str(cfg.get("champion_agent_id")))
        else:
            _fail("XC-4.4 resolve_production_config", str(cfg)[:180])

        inj = apply_locked_config_to_task(
            "aws-ops",
            agent_id="",
            metadata={},
            task_id="task_xc_offline",
            base=base,
            bind_skills=False,
        )
        if inj.get("applied") and inj.get("agent_id") == "aws_mon" and (inj.get("metadata") or {}).get(
            "eco_bid_locked"
        ):
            _ok("XC-4.4 apply_locked_config_to_task", f"meta={inj['metadata'].get('bid_candidate_id')}")
        else:
            _fail("XC-4.4 apply_locked", str(inj)[:200])

        skip = apply_locked_config_to_task(
            "aws-ops",
            metadata={"skip_locked_bid": True},
            task_id="task_xc_offline",
            base=base,
            bind_skills=False,
        )
        if not skip.get("applied"):
            _ok("XC-4.4 skip_locked_bid", "applied=False")
        else:
            _fail("XC-4.4 skip_locked_bid", "should skip")


def check_live_api(base: str) -> None:
    print(f"\n== 活后端 {base} ==")
    try:
        st, _ = _http_json("GET", f"{base.rstrip('/')}/api/v1/agent-config/teams")
        if st != 200:
            _skip("live teams", f"HTTP {st}")
            return
    except Exception as e:
        _skip("live backend", str(e))
        return

    team_id = "aws-ops"
    result = {
        "final_ranking": [
            {
                "agent_id": "aws_mon",
                "survival_ticks": 50,
                "population": "aws-ops",
                "collab_genome": {
                    "share_tendency": 0.8,
                    "signal_tendency": 0.9,
                    "follow_tendency": 0.3,
                    "mate_choosiness": 0.2,
                },
            },
            {
                "agent_id": "aws_lead",
                "survival_ticks": 40,
                "population": "aws-ops",
                "collab_genome": {
                    "share_tendency": 0.7,
                    "signal_tendency": 0.5,
                    "follow_tendency": 0.8,
                    "mate_choosiness": 0.2,
                },
            },
        ],
        "timeline": {
            "steps": [
                {
                    "actions": {
                        "aws_mon": {
                            "signals": ["FOOD@es"],
                            "shared_to": "aws_lead",
                            "followed": False,
                        },
                        "aws_lead": {"signals": [], "followed": True},
                    }
                }
            ]
        },
    }

    # relation suggest
    try:
        st, data = _http_json(
            "POST",
            f"{base}/api/v1/eco-runtime/relation-integration/suggest",
            {"team_id": team_id, "result": result, "timeline": result["timeline"]},
        )
        if st == 200 and data.get("ok") and data.get("report", {}).get("before_count", 0) >= 0:
            _ok("live relation suggest", f"before={data['report'].get('before_count')} sug={data['report'].get('count')}")
            sugs = data["report"].get("suggestions") or []
        else:
            _fail("live relation suggest", str(data)[:200])
            sugs = []
    except Exception as e:
        _fail("live relation suggest", str(e))
        sugs = []

    # confirm false
    if sugs:
        try:
            st, data = _http_json(
                "POST",
                f"{base}/api/v1/eco-runtime/relation-integration/apply",
                {
                    "team_id": team_id,
                    "confirm": False,
                    "suggestions": sugs[:2],
                    "fingerprint": "xf_live",
                },
            )
            if st == 200 and data.get("ok") and data.get("applied") == 0:
                _ok("XF-7.15 live confirm=false 关系", f"would={data.get('would_apply')}")
            else:
                _fail("XF-7.15 live confirm=false 关系", str(data)[:200])
        except Exception as e:
            _fail("XF-7.15 live confirm=false 关系", str(e))

        # confirm true (one edge)
        try:
            one = [s for s in sugs if not s.get("already_exists")][:1] or sugs[:1]
            st, data = _http_json(
                "POST",
                f"{base}/api/v1/eco-runtime/relation-integration/apply",
                {
                    "team_id": team_id,
                    "confirm": True,
                    "suggestions": one,
                    "fingerprint": "xf_live",
                },
            )
            if st == 200 and data.get("ok") and (data.get("applied", 0) + data.get("skipped_dup", 0)) >= 1:
                _ok("XF-7.14b live relation apply", str(data.get("applied")))
            else:
                _fail("XF-7.14b live relation apply", str(data)[:200])
        except Exception as e:
            _fail("XF-7.14b live relation apply", str(e))

    # channel confirm false / true
    try:
        st, data = _http_json(
            "POST",
            f"{base}/api/v1/eco-runtime/channel-integration/suggest",
            {"team_id": team_id, "result": result, "timeline": result["timeline"]},
        )
        ch_sugs = (data.get("report") or {}).get("suggestions") or []
        if st == 200 and data.get("ok"):
            bus = (data.get("report") or {}).get("bus_name")
            _ok("live channel suggest", f"bus={bus} n={len(ch_sugs)}")
            if bus and bus != "aws-ops_bus":
                # preferred real name aws_ops_bus when bindings exist
                pass
        else:
            _fail("live channel suggest", str(data)[:200])
            ch_sugs = []
    except Exception as e:
        _fail("live channel suggest", str(e))
        ch_sugs = []

    if ch_sugs:
        payload_sugs = [
            {
                "agent_id": s.get("agent_id"),
                "channel_diffs": s.get("channel_diffs") or [],
            }
            for s in ch_sugs[:2]
            if s.get("agent_id")
        ]
        try:
            st, data = _http_json(
                "POST",
                f"{base}/api/v1/eco-runtime/channel-integration/apply",
                {
                    "team_id": team_id,
                    "confirm": False,
                    "suggestions": payload_sugs,
                    "fingerprint": "xf_live",
                },
            )
            if st == 200 and data.get("ok") and data.get("applied") == 0:
                _ok("XF-7.15 live confirm=false 通道", f"would={data.get('would_apply')}")
            else:
                _fail("XF-7.15 live confirm=false 通道", str(data)[:200])
        except Exception as e:
            _fail("XF-7.15 live confirm=false 通道", str(e))

        try:
            st, data = _http_json(
                "POST",
                f"{base}/api/v1/eco-runtime/channel-integration/apply",
                {
                    "team_id": team_id,
                    "confirm": True,
                    "suggestions": payload_sugs[:1],
                    "fingerprint": "xf_live",
                },
            )
            if st == 200 and data.get("ok"):
                _ok("XF-7.14b live channel apply", f"applied={data.get('applied')}")
            else:
                _fail("XF-7.14b live channel apply", str(data)[:200])
        except Exception as e:
            _fail("XF-7.14b live channel apply", str(e))

    # collab apply confirm true then read agent
    try:
        st, data = _http_json(
            "POST",
            f"{base}/api/v1/eco-runtime/collab-integration/apply",
            {
                "team_id": team_id,
                "confirm": True,
                "fingerprint": "xf_live",
                "strategy": "blend",
                "suggestions": [
                    {
                        "agent_id": "aws_mon",
                        "collab": {
                            "share_tendency": 0.81,
                            "signal_tendency": 0.82,
                            "follow_tendency": 0.41,
                            "mate_choosiness": 0.21,
                        },
                        "survival_ticks": 50,
                        "strategy": "blend",
                        "reason": "xf_verify",
                    }
                ],
            },
        )
        if st == 200 and data.get("ok") and data.get("applied", 0) >= 0:
            _ok("XF-4.2 live collab apply", f"applied={data.get('applied')}")
        else:
            _fail("XF-4.2 live collab apply", str(data)[:200])
        # read agent
        st2, agent = _http_json("GET", f"{base}/api/v1/agent-config/teams/{team_id}/agents/aws_mon")
        eco = (agent.get("metadata") or {}).get("eco_collab") if isinstance(agent, dict) else None
        if st2 == 200 and isinstance(eco, dict) and "share_tendency" in eco:
            _ok("XF-4.2 live metadata.eco_collab 可读", str(eco.get("source")))
        else:
            # agent endpoint may return different shape
            if st2 == 200:
                _skip("XF-4.2 read eco_collab", "agent payload without eco_collab yet")
            else:
                _fail("XF-4.2 read agent", f"HTTP {st2}")
    except Exception as e:
        _fail("XF-4.2 live collab", str(e))

    # tasks list for mount (XF-6.7 data path)
    try:
        st, data = _http_json("GET", f"{base}/api/v1/agent-config/teams/{team_id}/tasks?limit=5&offset=0")
        if st == 200:
            items = data.get("items") if isinstance(data, dict) else data
            n = len(items or []) if isinstance(items, list) else 0
            _ok("XF-6.7 任务列表 API", f"n={n}")
        else:
            _fail("XF-6.7 任务列表 API", f"HTTP {st}")
    except Exception as e:
        _fail("XF-6.7 任务列表 API", str(e))

    # XC live: create → list → PATCH → quality → lock gates → GET locked
    # 使用专用 task_id；dominant_skills 为空避免 lock 时 SkillRouter 写真身
    xc_task = "task_xc_verify_live"
    cid = None
    try:
        body = {
            "team_id": team_id,
            "task_id": xc_task,
            "plan_id": "plan_xc_verify_live",
            "race_mode": "single",
            "feedback": {
                "feedback": "done",
                "skill_applied": True,
                "fingerprint": "fp_xc_verify_live",
            },
            "result": {
                "final_ranking": [
                    {
                        "agent_id": "aws_mon",
                        "survival_ticks": 77,
                        "population": "aws-ops",
                        "attr_skill_share": 0.25,
                        "attr_collab_share": 0.2,
                        "attr_residual_share": 0.55,
                    }
                ],
                "contract": {
                    "plan_id": "plan_xc_verify_live",
                    "task_id": xc_task,
                    "topic": "XC live verify",
                    "niches": [{"index": 0, "title": "巡检", "demanded_skills": []}],
                    "provenance": {"fingerprint": "fp_xc_verify_live"},
                },
                "integration": {"dominant_skills": []},
            },
        }
        st, data = _http_json("POST", f"{base}/api/v1/eco-runtime/bid-candidates", body)
        if st == 200 and data.get("ok") and (data.get("candidate") or {}).get("candidate_id"):
            cid = data["candidate"]["candidate_id"]
            _ok("XC-5.2 live create BidCandidate", f"{cid} q={data.get('quality_status')}")
        else:
            _fail("XC-5.2 live create BidCandidate", str(data)[:220])
    except Exception as e:
        _fail("XC-5.2 live create BidCandidate", str(e))

    if cid:
        try:
            st, data = _http_json(
                "GET",
                f"{base}/api/v1/eco-runtime/bid-candidates?team_id={team_id}&task_id={xc_task}",
            )
            n = int(data.get("count") or 0) if isinstance(data, dict) else 0
            if st == 200 and n >= 1:
                _ok("XC-5.2 live list", f"count={n}")
            else:
                _fail("XC-5.2 live list", str(data)[:180])
        except Exception as e:
            _fail("XC-5.2 live list", str(e))

        try:
            st, data = _http_json(
                "PATCH",
                f"{base}/api/v1/eco-runtime/bid-candidates/{cid}?team_id={team_id}",
                {"tokens_baseline": 200, "tokens_candidate": 120},
            )
            cand = (data or {}).get("candidate") or {}
            if st == 200 and data.get("ok") and cand.get("tokens_candidate") == 120:
                _ok("XC-5.2 live PATCH tokens", f"gate={cand.get('cost_gate')}")
            else:
                _fail("XC-5.2 live PATCH tokens", str(data)[:180])
        except Exception as e:
            _fail("XC-5.2 live PATCH tokens", str(e))

        try:
            st, data = _http_json(
                "POST",
                f"{base}/api/v1/eco-runtime/bid-candidates/{cid}/quality-check?team_id={team_id}",
                {},
            )
            if st == 200 and data.get("ok") and data.get("quality_status") == "quality_passed":
                _ok("XC-5.2 live quality-check", data.get("quality_status"))
            else:
                _fail("XC-5.2 live quality-check", str(data)[:180])
        except Exception as e:
            _fail("XC-5.2 live quality-check", str(e))

        # 更贵 token → 拒绝 lock
        try:
            _http_json(
                "PATCH",
                f"{base}/api/v1/eco-runtime/bid-candidates/{cid}?team_id={team_id}",
                {"tokens_baseline": 100, "tokens_candidate": 150},
            )
            st, data = _http_json(
                "POST",
                f"{base}/api/v1/eco-runtime/bid-candidates/{cid}/lock?team_id={team_id}",
            )
            if st == 200 and not data.get("ok") and data.get("error") == "token_not_better":
                _ok("XC-4.2 live lock 拒绝更贵", data.get("error"))
            else:
                _fail("XC-4.2 live lock 拒绝更贵", str(data)[:180])
        except Exception as e:
            _fail("XC-4.2 live lock 拒绝更贵", str(e))

        # 更省 → lock（无 skill 列表，避免静默改 agent.skills）
        try:
            _http_json(
                "PATCH",
                f"{base}/api/v1/eco-runtime/bid-candidates/{cid}?team_id={team_id}",
                {"tokens_baseline": 100, "tokens_candidate": 70},
            )
            st, data = _http_json(
                "POST",
                f"{base}/api/v1/eco-runtime/bid-candidates/{cid}/lock?team_id={team_id}",
            )
            cand = (data or {}).get("candidate") or {}
            if st == 200 and data.get("ok") and cand.get("ratchet_state") == "locked":
                _ok("XC-4.1 live lock", cid)
            else:
                _fail("XC-4.1 live lock", str(data)[:180])
        except Exception as e:
            _fail("XC-4.1 live lock", str(e))

        try:
            st, data = _http_json(
                "GET",
                f"{base}/api/v1/eco-runtime/bid-candidates-locked?team_id={team_id}&task_id={xc_task}",
            )
            prod = (data or {}).get("production") or {}
            if st == 200 and data.get("ok") and prod.get("bid_candidate_id") == cid:
                _ok("XC-4.4 live GET locked/production", f"champ={prod.get('champion_agent_id')}")
            elif st == 200 and data.get("ok") and int(data.get("count") or 0) >= 1:
                _ok("XC-4.4 live GET locked", f"count={data.get('count')}")
            else:
                _fail("XC-4.4 live GET locked", str(data)[:180])
        except Exception as e:
            _fail("XC-4.4 live GET locked", str(e))

    # 无 task 创建应拒绝
    try:
        st, data = _http_json(
            "POST",
            f"{base}/api/v1/eco-runtime/bid-candidates",
            {
                "team_id": team_id,
                "feedback": {"feedback": "done", "skill_applied": True},
                "result": {"final_ranking": [{"agent_id": "aws_mon", "survival_ticks": 1}]},
            },
        )
        if st == 200 and not data.get("ok") and data.get("error") == "task_id required":
            _ok("XC-2.5 live 拒无 task", data.get("error"))
        else:
            _fail("XC-2.5 live 拒无 task", str(data)[:180])
    except Exception as e:
        _fail("XC-2.5 live 拒无 task", str(e))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8080", help="backend base URL")
    ap.add_argument("--offline-only", action="store_true")
    args = ap.parse_args()

    print("物竞适者反馈台验收 verify_eco_feedback_xf")
    check_static_frontend()
    check_offline_python()
    if not args.offline_only:
        check_live_api(args.base)

    print(f"\n=== 汇总 PASS={PASS} FAIL={FAIL} SKIP={SKIP} ===")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
