# -*- coding: utf-8 -*-
"""AWS 降本 Case · G1~G4 断言（纯函数分支，离线可单测）.

把每个 Gate 的断言逻辑抽成纯函数：接收 dict（来自 HTTP 响应或 fixture），
返回 {"ok": bool, "reason": str}。主脚本 aws_ops_costdown_e2e.py 调 HTTP 拿到
dict 后调这里的函数判定；离线单测用 fixture dict 直接验证断言逻辑本身。
设计依据：docs/superpowers/specs/2026-06-22-phase11-aws-costdown-best-practice-design.md §1。
"""

from __future__ import annotations

from typing import Any, Dict, List

try:
    from ._aws_costdown_script_criteria import score_script  # 包内导入
except ImportError:
    from _aws_costdown_script_criteria import score_script  # 顶层导入（scripts/ 在 sys.path）

# G1 模板（与 aws_ops_team.AWS_OPS_ROLES 同源，供断言比对）
G1_TEMPLATE = {
    "aws_lead":   {"tools": ["run_shell", "delegate_task"],            "skills": ["aws_es_scaling_orchestration"]},
    "aws_arch":   {"tools": ["run_shell", "read_file"],                "skills": ["aws_es_capacity_planning"]},
    "aws_oper":   {"tools": ["run_shell", "run_python"],               "skills": ["aws_cli_script_authoring"]},
    "aws_mon":    {"tools": ["run_shell", "set_alarm", "watch_file"],  "skills": ["monitor_alarms_setup"]},
    "aws_cost":   {"tools": ["run_shell", "run_python"],               "skills": ["cost_ri_advisor"]},
    "aws_region": {"tools": ["run_shell", "search_files"],             "skills": ["compliance_region_guard"]},
}
EXPECTED_AGENT_COUNT = 6
TEAM_ID = "aws-ops"
# 既有云运维团队 id（防冲突）
EXISTING_CLOUD_TEAM_IDS = {"cloud-ops-team", "d083a568"}  # xops=d083a568


def _tool_set(agent: Dict[str, Any]) -> set:
    """从 agent dict 取 tool_id 集合（兼容 tools=[str] 与 tools=[{tool_id}] 两种形态）."""
    out: set = set()
    for t in agent.get("tools") or []:
        if isinstance(t, dict):
            v = t.get("tool_id") or t.get("name")
            if v:
                out.add(str(v))
        elif t:
            out.add(str(t))
    return out


def _skill_set(agent: Dict[str, Any]) -> set:
    out: set = set()
    for s in agent.get("skills") or []:
        if isinstance(s, dict):
            v = s.get("skill_id") or s.get("name")
            if v:
                out.add(str(v))
        elif s:
            out.add(str(s))
    return out


def assert_g1(agents: List[Dict[str, Any]], registered_tools: set,
              team_id: str = TEAM_ID) -> Dict[str, Any]:
    """G1 · 角色能力对齐：6 角色 / 工具真实 / 与模板一致 / team_id 不冲突."""
    if len(agents) != EXPECTED_AGENT_COUNT:
        return {"ok": False, "reason": f"角色数 {len(agents)} ≠ {EXPECTED_AGENT_COUNT}"}
    for a in agents:
        aid = a.get("agent_id") or ""
        tmpl = G1_TEMPLATE.get(aid)
        if not tmpl:
            return {"ok": False, "reason": f"未知角色 {aid}"}
        tools = _tool_set(a)
        if not tools:
            return {"ok": False, "reason": f"{aid} 未绑定工具"}
        if not tools.issubset(registered_tools):
            miss = tools - registered_tools
            return {"ok": False, "reason": f"{aid} 绑定未注册工具: {sorted(miss)}"}
        if tools != set(tmpl["tools"]):
            return {"ok": False, "reason": f"{aid} 工具与模板不一致: {sorted(tools)} ≠ {sorted(tmpl['tools'])}"}
        if _skill_set(a) != set(tmpl["skills"]):
            return {"ok": False, "reason": f"{aid} 技能与模板不一致"}
    if team_id in EXISTING_CLOUD_TEAM_IDS:
        return {"ok": False, "reason": f"team_id {team_id} 与既有云运维团队冲突"}
    return {"ok": True, "reason": f"6 角色对齐，工具均已注册，team_id={team_id}"}


def assert_g2b(round_scores: List[int], final_score: int) -> Dict[str, Any]:
    """G2-b · 迭代修订：最终轮满分 / 轮数≤3 / 轨迹不退（允许提前达标）."""
    if not round_scores:
        return {"ok": False, "reason": "无迭代轨迹"}
    if len(round_scores) > 3:
        return {"ok": False, "reason": f"轮数 {len(round_scores)} > 3"}
    if final_score != 5:
        return {"ok": False, "reason": f"最终分 {final_score} < 5（未收敛满分）"}
    for i in range(len(round_scores) - 1):
        if round_scores[i] > round_scores[i + 1]:
            return {"ok": False, "reason": f"轨迹退步: 第{i+1}轮 {round_scores[i]} > 第{i+2}轮 {round_scores[i+1]}"}
    return {"ok": True, "reason": f"{len(round_scores)} 轮收敛至满分 5"}


def assert_g2c(verify: Dict[str, Any], evolve: Dict[str, Any],
               publish: Dict[str, Any], plan_content: str = "") -> Dict[str, Any]:
    """G2-c · 三道门禁 + 脚本 fragments 覆盖 5 项 criteria."""
    pass_rate = float(verify.get("pass_rate") or verify.get("passRate") or 0)
    if pass_rate < 0.7:
        return {"ok": False, "reason": f"verify pass_rate {pass_rate} < 0.7"}
    if not evolve.get("version"):
        return {"ok": False, "reason": "evolve 未返回新 version"}
    if publish.get("published") is False:
        return {"ok": False, "reason": "publish 未成功"}
    # 验证产出脚本覆盖 criteria
    sc = score_script(plan_content)
    if sc["score"] < 5:
        return {"ok": False, "reason": f"脚本缺 criteria {sc['missing']}"}
    return {"ok": True, "reason": f"三道门禁通过，脚本满分 5"}


def assert_g3(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """G3 · 孪生协作数据：≥5 步 / 每步有 action / 覆盖≥3 不同 agent / reward 非全 0."""
    if len(steps) < 5:
        return {"ok": False, "reason": f"步数 {len(steps)} < 5"}
    actors: set = set()
    rewards = []
    for st in steps:
        actions = st.get("agent_actions") or []
        if not actions:
            return {"ok": False, "reason": "存在无 action 的步"}
        for act in actions:
            aid = act.get("agent_id") if isinstance(act, dict) else act
            if aid:
                actors.add(str(aid))
        rewards.append(float(st.get("reward") or st.get("global_reward") or 0))
    if len(actors) < 3:
        return {"ok": False, "reason": f"参与 agent {len(actors)} < 3"}
    if not any(r > 0 for r in rewards):
        return {"ok": False, "reason": "reward 全 0（drill 无真实 reward）"}
    return {"ok": True, "reason": f"{len(steps)} 步 / {len(actors)} agent / reward 非零"}


def assert_g4(baseline_per_call: float, current_per_call: float, target: float,
              progress: Dict[str, Any], ratchet_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """G4 · 真实降本：current < target(降≥20%) / 目标 achieved / 棘轮出现 cost_efficiency:aws-ops."""
    if current_per_call >= target:
        return {"ok": False,
                "reason": f"每调用 token {current_per_call} 未降到目标 {target}（降幅不足 20%）"}
    if progress.get("status") != "achieved":
        return {"ok": False, "reason": f"目标状态 {progress.get('status')} ≠ achieved"}
    keys = {m.get("metric_key") for m in (ratchet_metrics or [])}
    if "cost_efficiency:aws-ops" not in keys:
        return {"ok": False, "reason": "棘轮未出现 cost_efficiency:aws-ops"}
    pct = round((baseline_per_call - current_per_call) / baseline_per_call, 4) if baseline_per_call else 0
    return {"ok": True, "reason": f"降幅 {pct*100:.0f}%（{baseline_per_call}→{current_per_call}），棘轮已锁定"}
