# -*- coding: utf-8 -*-
"""任务 Token 治理：cache / compress / by_task / token_scope task_id."""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))


@pytest.fixture(autouse=True)
def _isolate_settings_from_repo(tmp_path, monkeypatch):
    """Never write real config/settings.json during unit tests (R10 regression)."""
    sp = tmp_path / "settings.json"
    sp.write_text("{}", encoding="utf-8")
    try:
        from agents.token_governance import settings as tg_settings
        monkeypatch.setattr(tg_settings, "_SETTINGS_PATH", sp)
    except Exception:
        pass
    try:
        from agents.budget import guard as bg
        monkeypatch.setattr(bg, "_SETTINGS_PATH", sp)
    except Exception:
        pass
    yield


def test_compress_dedupe_and_truncate():
    from agents.prompt_cache import compress_messages

    msgs = [
        {"role": "system", "content": "S" * 9000},
        {"role": "user", "content": "same"},
        {"role": "user", "content": "same"},
        {"role": "tool", "content": "T" * 8000},
    ]
    r = compress_messages(msgs, system_max_chars=1000, msg_max_chars=500)
    assert r["after_tokens"] < r["before_tokens"]
    assert r["saved_tokens_est"] > 0
    assert "dedupe_adjacent" in r["actions"]


def test_prompt_cache_hit():
    from agents.prompt_cache import PromptCache

    c = PromptCache(max_size=16)
    msgs = [{"role": "user", "content": "hello world"}]
    k = c.store_messages(msgs, compress=False)
    assert k
    hit = c.lookup_messages(msgs, compress=False)
    assert hit["hit"] is True
    st = c.stats()
    assert st["hits"] >= 1
    assert st["writes"] >= 1


def test_by_task_aggregation():
    from agents.budget.models import UsageRecord
    from agents.budget.store import UsageStore
    from agents.token_ledger import TokenLedger

    with tempfile.TemporaryDirectory() as tmp:
        store = UsageStore(Path(tmp) / "u.db")
        store.record_usage(
            UsageRecord(
                session_id="s1", agent_id="a", team_id="t1",
                input_tokens=100, output_tokens=50, total_tokens=150,
                scenario_id="task_alpha", run_id="r1", phase="task",
            )
        )
        store.record_usage(
            UsageRecord(
                session_id="s2", agent_id="a", team_id="t1",
                input_tokens=10, output_tokens=5, total_tokens=15,
                scenario_id="task_alpha", run_id="r2", phase="task",
            )
        )
        store.record_usage(
            UsageRecord(
                session_id="s3", agent_id="b", team_id="t1",
                input_tokens=20, output_tokens=10, total_tokens=30,
                scenario_id="", run_id="run_only", phase="task",
            )
        )
        L = TokenLedger(store=store)
        items = L.by_task(window="all", team_id="t1")
        by_key = {i["task_key"]: i for i in items}
        assert by_key["task_alpha"]["total"] == 165
        assert by_key["run_only"]["total"] == 30


def test_token_scope_task_id_maps_scenario():
    from agents.token_context import get_token_ctx, token_scope

    with token_scope(task_id="task_xyz", team_id="aws-ops", phase="task"):
        ctx = get_token_ctx()
        assert ctx.get("scenario_id") == "task_xyz"
        assert ctx.get("task_id") == "task_xyz"


def test_fingerprint_stable():
    from agents.prompt_cache import fingerprint_messages

    a = fingerprint_messages([{"role": "user", "content": "x"}])
    b = fingerprint_messages([{"role": "user", "content": "x"}])
    c = fingerprint_messages([{"role": "user", "content": "y"}])
    assert a == b and a != c


def test_tool_loop_record_usage_uses_task_env(monkeypatch):
    import os
    from agents.budget.models import UsageRecord
    from agents.budget.store import UsageStore
    from agents.runtime import tool_loop
    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        store = UsageStore(Path(tmp) / "u.db")
        # patch get_budget_guard to use temp store
        class G:
            def record_usage(self, rec: UsageRecord):
                store.record_usage(rec)
        monkeypatch.setattr(tool_loop, "get_budget_guard", lambda: G())
        monkeypatch.setenv("AG_TASK_ID", "task_attr_demo")
        monkeypatch.setenv("AG_TEAM_ID", "aws-ops")
        tool_loop._record_usage(
            {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            model="m",
            session_id="sess1",
            agent_id="aws_mon",
            team_id="",
        )
        from agents.token_ledger import TokenLedger
        items = TokenLedger(store=store).by_task(window="all")
        assert items and items[0]["task_key"] == "task_attr_demo"
        assert items[0]["total"] == 15


def test_precheck_budget_helpers_exist():
    from agents.api import _estimate_prompt_tokens, _precheck_team_token_budget
    assert _estimate_prompt_tokens("abcd") >= 1
    r = _precheck_team_token_budget("aws-ops", estimated_tokens=1, agent_id="__tg_test__")
    assert "allowed" in r and "budget" in r


def test_prepare_request_pipeline_saves():
    from agents.token_governance import get_token_governance
    from agents.token_governance.service import TokenGovernanceService

    svc = TokenGovernanceService()
    # 关 behavior 注入以免短消息净增；测 compress/simplify 净省
    svc.update_settings({
        "ponytail_level": "off",
        "caveman_level": "off",
        "skill_route_hint": False,
        "codegraph_context": False,
    })
    msgs = [
        {"role": "system", "content": ("你是助手。\n\n" * 15) + "S" * 3000},
        {"role": "user", "content": "hello"},
        {"role": "user", "content": "hello"},
    ]
    out = svc.prepare_request(msgs, task_id="t1", team_id="aws-ops", agent_id="a1")
    assert out["after_tokens"] <= out["before_tokens"]
    assert isinstance(out.get("levers"), list)
    assert "budget" in out
    dash = svc.dashboard(window="24h")
    assert dash.get("ok") is True
    assert "attribution" in dash and "levers" in dash


def test_semantic_lite_fingerprint_strips_uuid():
    from agents.token_governance.service import semantic_lite_fingerprint

    a = semantic_lite_fingerprint([{"role": "user", "content": "task 550e8400-e29b-41d4-a716-446655440000 ok"}])
    b = semantic_lite_fingerprint([{"role": "user", "content": "task 123e4567-e89b-12d3-a456-426614174000 ok"}])
    assert a == b


def test_prepare_skill_and_model_counters():
    from agents.token_governance.service import TokenGovernanceService

    svc = TokenGovernanceService()
    svc.update_settings({
        "skill_route_hint": True,
        "ponytail_level": "off",
        "caveman_level": "off",
        "codegraph_context": False,
    })
    # force skill hint path with empty router by mocking
    def fake_hint(team_id, query):
        return {"skill_ids": ["monitor", "scale"], "top_score": 0.9}

    svc._skill_hint = fake_hint  # type: ignore
    out = svc.prepare_request(
        [{"role": "user", "content": "x" * 100}],
        task_id="t",
        team_id="aws-ops",
        agent_id="a",
        query_for_skill="monitor es",
    )
    kinds = [x.get("kind") for x in (out.get("levers") or [])]
    assert "skill_route" in kinds
    c = svc.counters()["counters"]
    assert c.get("skill_hints", 0) >= 1
    skill_lev = [x for x in out.get("levers") or [] if x.get("kind") == "skill_route"][0]
    assert skill_lev.get("injected") or skill_lev.get("system_truncated") or skill_lev.get("skills")


def test_budget_aware_compact_threshold():
    from agents.chat_harness import ChatSession, ChatMessage, UsageSummary

    s = ChatSession(session_id="c1", compact_after=20)
    s.total_usage = UsageSummary(input_tokens=180000, output_tokens=0, total_tokens=180000)
    for i in range(25):
        s.messages.append(ChatMessage(role="user", content=f"m{i}"))
    s.compact_if_needed()
    # near budget should compact more aggressively than keep half of 20
    assert len(s.messages) < 20


def test_skill_shorten_truncates_long_system():
    from agents.token_governance.service import TokenGovernanceService

    svc = TokenGovernanceService()
    svc.update_settings({
        "skill_route_hint": True,
        "ponytail_level": "off",
        "caveman_level": "off",
        "codegraph_context": False,
        "compress": True,
        "simplify_prompt": False,
    })
    svc._skill_hint = lambda team_id, query: {"skill_ids": ["monitor"], "top_score": 0.9}  # type: ignore
    long_sys = "背景说明。" * 1200  # well beyond 3500 chars
    out = svc.prepare_request(
        [
            {"role": "system", "content": long_sys},
            {"role": "user", "content": "巡检 ES"},
        ],
        task_id="task_shorten",
        team_id="aws-ops",
        agent_id="aws_mon",
        query_for_skill="ES 监控巡检",
    )
    sys_out = (out["messages"][0].get("content") or "")
    assert len(sys_out) < len(long_sys)
    assert "[TG_SKILL_BODY]" in sys_out or "prefer skills" in sys_out.lower() or "skill" in sys_out.lower()
    skill_levers = [x for x in out["levers"] if x.get("kind") == "skill_route"]
    assert skill_levers and (skill_levers[0].get("system_truncated") or skill_levers[0].get("injected"))


def test_savings_store_roundtrip(tmp_path):
    from agents.token_governance import savings_store as ss

    p = tmp_path / "s.jsonl"
    ss.append_event({"task_id": "t1", "team_id": "aws-ops", "saved_tokens_est": 100, "lever_kinds": ["compress"]}, path=p)
    ss.append_event({"task_id": "t1", "team_id": "aws-ops", "saved_tokens_est": 50, "lever_kinds": ["skill_route"]}, path=p)
    ss.append_event({"task_id": "t2", "team_id": "aws-ops", "saved_tokens_est": 10, "lever_kinds": ["cache"]}, path=p)
    agg = ss.aggregate_by_task(path=p, team_id="aws-ops")
    by = {a["task_id"]: a for a in agg}
    assert by["t1"]["saved_tokens_est"] == 150
    assert by["t1"]["events"] == 2
    recent = ss.recent_events(path=p, task_id="t1", limit=5)
    assert len(recent) == 2


def test_skill_hint_accepts_routing_session_object():
    from agents.token_governance.service import TokenGovernanceService

    svc = TokenGovernanceService()

    class RR:
        def __init__(self):
            self.skill_id = "skill_es_mon"
            self.score = 0.91

    class RS:
        results = [RR()]

    class FakeRouter:
        def route(self, **kwargs):
            return RS()

        def _generate_inject_prompt(self, team_id, skill_ids):
            return f"### {skill_ids[0]}\ninstructions"

    import agents.skill_router as sr
    orig = sr.get_skill_router
    sr.get_skill_router = lambda: FakeRouter()  # type: ignore
    try:
        hint = svc._skill_hint("aws-ops", "ES monitor")
        assert "skill_es_mon" in hint.get("skill_ids", [])
        assert hint.get("source") == "skill_router"
    finally:
        sr.get_skill_router = orig


def test_savings_api_shape():
    from agents.token_governance_routes import list_savings
    # call endpoint function directly
    out = list_savings(task_id="", team_id="aws-ops", limit=10)
    assert out.get("ok") is True
    assert "events" in out and "by_task" in out


def test_lever_catalog_has_six_with_industry():
    from agents.token_governance.lever_catalog import get_lever_catalog, catalog_with_runtime

    cat = get_lever_catalog()
    assert len(cat) >= 6
    ids = {c["id"] for c in cat}
    for need in ("simplify_prompt", "compress", "cache", "skill_route", "model_route", "budget"):
        assert need in ids
    for c in cat:
        assert c.get("industry", {}).get("inspired_by"), c["id"]
        assert c.get("ours", {}).get("module"), c["id"]
        assert c.get("ours", {}).get("algorithm"), c["id"]
    runtime = catalog_with_runtime(
        {"simplify_prompt": True, "compress": True, "cache_mode": "observe",
         "model_route": True, "skill_route_hint": True, "budget_enforce_turn": True},
        {"simplify_saves": 1},
        {"hits": 0, "misses": 1, "size": 0, "hit_rate": 0},
        {"current_tier": "standard"},
    )
    assert runtime[0]["enabled"] is True


def test_levers_api_includes_architecture():
    from agents.token_governance_routes import get_levers
    out = get_levers()
    assert out.get("ok")
    assert out.get("architecture", {}).get("entry")
    assert len(out.get("catalog") or []) >= 6
    # 每条 catalog 必须能驱动 UI 完整卡
    for c in out["catalog"]:
        assert c.get("title")
        assert c.get("industry", {}).get("inspired_by")
        assert c.get("ours", {}).get("module")
        assert c.get("ours", {}).get("algorithm")
        assert c.get("exec_path")


def test_disable_compress_no_compress_lever():
    """R7.5：关 compress 后再 prepare，结果中无 compress 节省行。"""
    from agents.token_governance.service import TokenGovernanceService

    svc = TokenGovernanceService()
    msgs = [
        {"role": "system", "content": "S" * 5000},
        {"role": "user", "content": "same"},
        {"role": "user", "content": "same"},
        {"role": "tool", "content": "T" * 6000},
    ]
    svc.update_settings({"compress": True, "simplify_prompt": True})
    on = svc.prepare_request(msgs, task_id="off_cmp_on", team_id="aws-ops")
    kinds_on = [x.get("kind") for x in (on.get("levers") or [])]
    # 关后一定没有 compress；开时若有则关后 saved 应更小或相等
    svc.update_settings({"compress": False})
    off = svc.prepare_request(msgs, task_id="off_cmp_off", team_id="aws-ops")
    kinds_off = [x.get("kind") for x in (off.get("levers") or [])]
    assert "compress" not in kinds_off
    svc.update_settings({"compress": True})
    if "compress" in kinds_on:
        assert (off.get("saved_tokens_est") or 0) <= (on.get("saved_tokens_est") or 0) + 1


def test_prepare_lever_fields_for_ui():
    """试跑表依赖的 before/after/module/catalog_id 字段。"""
    from agents.token_governance.service import TokenGovernanceService

    svc = TokenGovernanceService()
    svc.update_settings({"compress": True, "simplify_prompt": True, "model_route": True})
    msgs = [
        {"role": "system", "content": ("你是运维助手。\n\n" * 20) + "背景。" * 200},
        {"role": "user", "content": "hello"},
        {"role": "user", "content": "hello"},
        {"role": "tool", "content": "x" * 3000},
    ]
    out = svc.prepare_request(msgs, task_id="ui_fields", team_id="aws-ops", agent_id="a1")
    levers = out.get("levers") or []
    assert levers, "expected at least some levers"
    for x in levers:
        assert x.get("kind")
        assert x.get("catalog_id") or x.get("kind")
        assert x.get("module")
        if x["kind"] in ("simplify", "compress"):
            assert "saved" in x
            assert "before" in x and "after" in x


def test_task_messages_snapshot_roundtrip(tmp_path, monkeypatch):
    from agents.token_governance import task_messages as tm

    monkeypatch.setattr(tm, "_PIPELINE", tmp_path / "pipeline")
    monkeypatch.setattr(tm, "_TASKS", tmp_path / "tasks")
    (tmp_path / "tasks").mkdir()
    tid = "task_real_abc"
    path = tm.save_prepare_messages(
        tid,
        [
            {"role": "system", "content": "you are agent"},
            {"role": "user", "content": "do work"},
            {"role": "tool", "content": "tool out " * 100},
        ],
        team_id="aws-ops",
        agent_id="a1",
        source="tool_loop",
    )
    assert path and Path(path).exists()
    loaded = tm.load_task_messages(tid)
    assert loaded["ok"] is True
    assert loaded["source"] == "snapshot"
    assert len(loaded["messages"]) == 3
    assert loaded["messages"][1]["content"] == "do work"


def test_task_messages_reconstruct_from_tool_trace(tmp_path, monkeypatch):
    from agents.token_governance import task_messages as tm

    monkeypatch.setattr(tm, "_PIPELINE", tmp_path / "pipeline")
    monkeypatch.setattr(tm, "_TASKS", tmp_path / "tasks")
    (tmp_path / "tasks").mkdir()
    tid = "task_recon_1"
    (tmp_path / "tasks" / f"{tid}.json").write_text(
        json.dumps({
            "task_id": tid, "team_id": "build_system", "agent_id": "dev",
            "title": "fix task", "description": "desc body",
            "status": "completed", "metadata": {"workflow": []},
        }, ensure_ascii=False),
        encoding="utf-8",
    )
    pdir = tmp_path / "pipeline" / tid
    pdir.mkdir(parents=True)
    (pdir / "04_develop_tool_trace.json").write_text(
        json.dumps({
            "task_id": tid, "step": "develop", "log": [
                {"name": "list_files", "args": "{}", "ok": True, "summary": "a,b,c"},
            ],
            "summary": "done",
        }),
        encoding="utf-8",
    )
    loaded = tm.load_task_messages(tid)
    assert loaded["ok"] is True
    assert loaded["source"] == "reconstructed"
    assert any(m.get("role") == "tool" for m in loaded["messages"])


def test_simulate_prefers_task_source(tmp_path, monkeypatch):
    from agents.token_governance import task_messages as tm
    from agents.token_governance.service import TokenGovernanceService

    monkeypatch.setattr(tm, "_PIPELINE", tmp_path / "pipeline")
    monkeypatch.setattr(tm, "_TASKS", tmp_path / "tasks")
    (tmp_path / "tasks").mkdir()
    tid = "task_sim_src"
    tm.save_prepare_messages(
        tid,
        [
            {"role": "system", "content": ("你是助手。\n\n" * 10) + "S" * 500},
            {"role": "user", "content": "hello"},
            {"role": "user", "content": "hello"},
            {"role": "tool", "content": "Enumerating objects\n" + ("M  a/b.py\n" * 20) + "z" * 3000},
        ],
        team_id="aws-ops",
    )
    loaded = tm.load_task_messages(tid)
    svc = TokenGovernanceService()
    svc.update_settings({
        "ponytail_level": "off", "caveman_level": "off",
        "skill_route_hint": False, "codegraph_context": False,
        "rtk_tool_compress": True, "compress": True,
    })
    out = svc.prepare_request(
        loaded["messages"], task_id=tid, team_id="aws-ops",
    )
    assert out["after_tokens"] <= out["before_tokens"]
    kinds = {x.get("kind") for x in (out.get("levers") or [])}
    assert "rtk_tool" in kinds or "compress" in kinds


def test_rtk_tool_compress_saves_on_noise():
    from agents.token_governance.rtk_tool_compress import rtk_compress_messages

    noise = "Enumerating objects: 5, done.\n" + ("ERROR same\n" * 40)
    for i in range(30):
        noise += f"M  src/mod/file{i}.py\n"
    for i in range(20):
        noise += f"test_foo_{i} ... ok\n"
    noise += "payload " * 2000
    msgs = [
        {"role": "user", "content": "run tests"},
        {"role": "tool", "content": noise},
    ]
    out = rtk_compress_messages(msgs)
    assert out["after_tokens"] < out["before_tokens"]
    assert out["saved_tokens_est"] > 0
    assert out["tool_msgs_touched"] >= 1


def test_progressive_collapse_long_history():
    from agents.token_governance.progressive_history import progressive_collapse

    msgs = [{"role": "system", "content": "sys"}]
    msgs.append({"role": "user", "content": "GOAL: fix billing"})
    for i in range(14):
        msgs.append({"role": "user", "content": f"turn {i} " + ("detail " * 100)})
        msgs.append({"role": "assistant", "content": f"reply {i} " + ("text " * 100)})
    out = progressive_collapse(msgs, keep_recent=4, min_total_for_collapse=8)
    assert out["collapsed"] > 0
    assert out["saved_tokens_est"] > 0
    assert any("[TG_MEM_INDEX]" in str(m.get("content")) for m in out["messages"])


def test_codegraph_local_symbol_slice():
    from agents.token_governance.codegraph_bridge import compress_source_blobs

    src = "#!/usr/bin/env python3\n"
    for i in range(15):
        src += f"def func_{i}(x):\n"
        src += ("    y = x + 1\n" * 50)
        src += "    return y\n\n"
    msgs = [{"role": "tool", "content": src}]
    out = compress_source_blobs(msgs, min_chars=500)
    assert out["replaced"] >= 1
    assert out["saved_tokens_est"] > 0
    assert "TG_CODEGRAPH" in out["messages"][0]["content"]


def test_cost_tier_simple_is_economy():
    from agents.token_governance.cost_tier import classify_complexity

    r = classify_complexity([{"role": "user", "content": "ping ok?"}])
    assert r["tier_hint"] == "economy"


def test_prepare_r9_pipeline_real_savings():
    """R9：rtk + progressive + codegraph + behavior 真进 prepare，净省 > 0。"""
    from agents.token_governance.service import TokenGovernanceService

    svc = TokenGovernanceService()
    svc.update_settings({
        "compress": True,
        "simplify_prompt": True,
        "rtk_tool_compress": True,
        "progressive_memory": True,
        "codegraph_context": True,
        "ponytail_level": "full",
        "caveman_level": "full",
        "cost_tier_route": True,
        "skill_route_hint": False,
        "cache_mode": "observe",
    })
    tool_noise = "Enumerating objects: done.\n" + ("line err\n" * 50)
    for i in range(25):
        tool_noise += f"M  src/a/f{i}.py\n"
    tool_noise += "z" * 4000
    src = "from x import y\n"
    for i in range(12):
        src += f"def big_{i}():\n" + ("    pass  # body\n" * 60)
    msgs = [{"role": "system", "content": ("你是助手。\n\n" * 20) + "S" * 2000}]
    msgs.append({"role": "user", "content": "GOAL fix aws alarm"})
    for i in range(10):
        msgs.append({"role": "user", "content": f"mid {i} " + ("pad " * 60)})
        msgs.append({"role": "assistant", "content": f"ans {i} " + ("pad " * 60)})
    msgs.append({"role": "tool", "content": tool_noise})
    msgs.append({"role": "tool", "content": src})
    msgs.append({"role": "user", "content": "continue"})
    out = svc.prepare_request(msgs, task_id="r9", team_id="aws-ops", agent_id="a1")
    assert out["after_tokens"] < out["before_tokens"]
    assert out["saved_tokens_est"] == max(0, out["before_tokens"] - out["after_tokens"])
    kinds = {x.get("kind") for x in (out.get("levers") or [])}
    # at least some R9 levers should fire
    assert kinds & {"rtk_tool", "progressive_mem", "codegraph", "compress", "simplify", "behavior"}
    c = svc.counters()["counters"]
    assert int(c.get("tokens_saved_est") or 0) >= out["saved_tokens_est"]
    # restore production defaults so other tests / live process stay sane
    svc.update_settings({
        "compress": True,
        "simplify_prompt": True,
        "rtk_tool_compress": True,
        "progressive_memory": True,
        "codegraph_context": True,
        "ponytail_level": "full",
        "caveman_level": "full",
        "cost_tier_route": True,
        "skill_route_hint": True,
        "model_route": True,
        "cache_mode": "observe",
        "budget_enforce_turn": True,
        "budget_enforce_submit": True,
    })


def test_saved_est_matches_measured_before_after():
    """总省量只认 before→after 净减，禁止 step 加总虚增。"""
    from agents.token_governance.service import TokenGovernanceService

    svc = TokenGovernanceService()
    svc.update_settings({"compress": True, "simplify_prompt": True, "cache_mode": "observe"})
    msgs = [
        {"role": "system", "content": ("你是助手。\n\n" * 20) + "S" * 4000},
        {"role": "user", "content": "hello"},
        {"role": "user", "content": "hello"},
        {"role": "tool", "content": "T" * 5000},
    ]
    out = svc.prepare_request(msgs, task_id="meas_save", team_id="aws-ops", agent_id="a1")
    measured = max(0, int(out["before_tokens"]) - int(out["after_tokens"]))
    assert int(out["saved_tokens_est"]) == measured
    # KPI 累计须包含 compress/simplify 净省（旧 bug：只记 cache HIT）
    c = svc.counters()["counters"]
    assert int(c.get("tokens_saved_est") or 0) >= measured
    if measured > 0:
        assert int(c.get("compress_saves") or 0) + int(c.get("simplify_saves") or 0) >= 1


def test_observe_cache_hit_not_counted_as_saved():
    """cache_mode=observe 时 HIT 只计量，不虚增 tokens_saved_est。"""
    from agents.token_governance.service import TokenGovernanceService

    svc = TokenGovernanceService()
    svc.update_settings({
        "compress": False,
        "simplify_prompt": False,
        "skill_route_hint": False,
        "cache_mode": "observe",
    })
    msgs = [{"role": "user", "content": "stable cache probe body for observe mode"}]
    svc.prepare_request(msgs, task_id="obs1", team_id="t")
    before = int(svc.counters()["counters"].get("tokens_saved_est") or 0)
    out2 = svc.prepare_request(msgs, task_id="obs2", team_id="t")
    after = int(svc.counters()["counters"].get("tokens_saved_est") or 0)
    assert out2.get("cache_hit") is True
    kinds = [x.get("kind") for x in (out2.get("levers") or [])]
    assert "cache" in kinds
    # observe HIT 不增加「已省」
    assert after == before


def test_r10_param_clamp_and_defaults():
    from agents.token_governance.lever_params import clamp_param, normalize_params

    assert clamp_param("alert_threshold", 1.5) == 0.99
    assert clamp_param("alert_threshold", 0.1) == 0.5
    assert clamp_param("max_tool_chars", 50) == 500
    assert clamp_param("on_exceed", "nope") == "halt"
    p = normalize_params({"max_tool_chars": 99999, "evil": 1})
    assert p["max_tool_chars"] == 8000
    assert "evil" not in p


def _isolate_tg_settings(tmp_path, monkeypatch):
    """Prevent tests from writing real config/settings.json."""
    from agents.token_governance import settings as tg_settings
    from agents.budget import guard as bg

    sp = tmp_path / "settings.json"
    sp.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(tg_settings, "_SETTINGS_PATH", sp)
    monkeypatch.setattr(bg, "_SETTINGS_PATH", sp)
    return sp


def test_r10_prepare_uses_max_tool_chars(tmp_path, monkeypatch):
    """Tighter max_tool_chars should compress tool blobs more (or equal)."""
    _isolate_tg_settings(tmp_path, monkeypatch)
    from agents.token_governance.service import TokenGovernanceService

    svc = TokenGovernanceService()
    big_tool = "noise line\n" * 200 + ("path/a.py\n" * 80)
    msgs = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "run tools"},
        {"role": "tool", "content": big_tool},
    ]
    svc.update_settings({
        "compress": False,
        "simplify_prompt": False,
        "progressive_memory": False,
        "codegraph_context": False,
        "skill_route_hint": False,
        "rtk_tool_compress": True,
        "cache_mode": "off",
        "params": {"max_tool_chars": 8000},
    })
    loose = svc.prepare_request(msgs, task_id="p_loose", team_id="t")
    svc.update_settings({"params": {"max_tool_chars": 600}})
    tight = svc.prepare_request(msgs, task_id="p_tight", team_id="t")
    assert int(tight["after_tokens"]) <= int(loose["after_tokens"])


def test_r10_prepare_compress_system_max(tmp_path, monkeypatch):
    _isolate_tg_settings(tmp_path, monkeypatch)
    from agents.token_governance.service import TokenGovernanceService

    svc = TokenGovernanceService()
    msgs = [
        {"role": "system", "content": "S" * 9000},
        {"role": "user", "content": "hi"},
    ]
    svc.update_settings({
        "compress": True,
        "simplify_prompt": False,
        "rtk_tool_compress": False,
        "progressive_memory": False,
        "codegraph_context": False,
        "skill_route_hint": False,
        "cache_mode": "off",
        "params": {"system_max_chars": 1000, "msg_max_chars": 4000},
    })
    out = svc.prepare_request(msgs, task_id="sys_cut", team_id="t")
    sys_c = (out["messages"][0].get("content") or "") if out.get("messages") else ""
    assert len(sys_c) < 2000
    assert int(out["saved_tokens_est"]) > 0


def test_r10_budget_knobs_via_update_settings(tmp_path, monkeypatch):
    from agents.token_governance import settings as tg_settings
    from agents.token_governance.service import TokenGovernanceService

    _isolate_tg_settings(tmp_path, monkeypatch)

    svc = TokenGovernanceService()
    out = svc.update_settings({
        "params": {
            "alert_threshold": 0.9,
            "on_exceed": "warn",
            "per_session_max": 123456,
            "max_tool_chars": 1500,
        }
    })
    assert out["params"]["max_tool_chars"] == 1500
    # budget keys not stored under tg params
    assert "alert_threshold" not in out["params"]
    knobs = tg_settings.load_budget_knobs()
    assert abs(float(knobs["alert_threshold"]) - 0.9) < 1e-6
    assert knobs["on_exceed"] == "warn"
    assert int(knobs["per_session_max"]) == 123456
