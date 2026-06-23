# -*- coding: utf-8 -*-
"""Phase 11 AWS 降本 Case · 离线单测（不依赖 LLM，可进 CI / pre-commit）.

覆盖：
  - aws_ops_team 模板结构（6 角色 / 工具真实 / team_id 不冲突）
  - _aws_costdown_script_criteria.score_script（满分 / 各缺一 / 空串）
  - _aws_costdown_assertions 的 G1/G2b/G3/G4 纯函数分支
不调 LLM、不发 HTTP。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# scripts/ 在仓库根，加入 path 以 import _aws_costdown_*
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from _aws_costdown_script_criteria import score_script, CRITERIA  # noqa: E402
from _aws_costdown_assertions import (  # noqa: E402
    assert_g1, assert_g2b, assert_g2c, assert_g3, assert_g4,
    G1_TEMPLATE, EXPECTED_AGENT_COUNT, TEAM_ID, EXISTING_CLOUD_TEAM_IDS,
)
from agents.teams.aws_ops_team import (  # noqa: E402
    create_aws_ops_team, AWS_OPS_ROLES,
)


# ── 满分脚本样本（含全部 5 项 criteria）──
FULL_SCRIPT = """
DOMAIN=my-es
aws es describe-elasticsearch-domain --domain-name $DOMAIN
aws es update-elasticsearch-domain-config --domain-name $DOMAIN --instance-type r6g.large.search
while true; do
  STATUS=$(aws es describe-domain --domain-name $DOMAIN --query 'DomainStatus.Processing')
  sleep 30
  if [[ "$STATUS" == "false" ]]; then echo Active; break; fi
done
aws cloudwatch put-metric-alarm --alarm-name es-cpu-high --metric-name CPUUtilization
if [ "$ROLLBACK" = "1" ]; then
  aws pricing get-products --service-code AmazonES
  echo 成本回滚 backup 已就绪
else
  echo 正常变更
fi
"""


# ── 1. 团队模板结构 ──────────────────────────────────────────

class TestAwsOpsTeamTemplate:
    def test_six_roles(self):
        team = create_aws_ops_team()
        assert len(team.agents) == EXPECTED_AGENT_COUNT

    def test_team_id_no_conflict(self):
        assert TEAM_ID == "aws-ops"
        assert TEAM_ID not in EXISTING_CLOUD_TEAM_IDS

    def test_every_agent_has_tools_and_skills(self):
        team = create_aws_ops_team()
        for aid, agent in team.agents.items():
            assert agent.tools, f"{aid} 无工具"
            assert agent.skills, f"{aid} 无技能"

    def test_template_consistent_with_factory(self):
        """工厂产出的角色工具/技能与 G1_TEMPLATE 断言表一致."""
        team = create_aws_ops_team()
        for role, aid, tools, skills in AWS_OPS_ROLES:
            assert aid in team.agents
            tmpl = G1_TEMPLATE[aid]
            assert set(team.agents[aid].tools) == set(tmpl["tools"]), aid
            assert set(team.agents[aid].skills) == set(tmpl["skills"]), aid

    def test_all_tools_are_registered_names(self):
        """模板里每个工具都应能在 tool_registry 找到（杜绝绑不存在的工具）."""
        try:
            from agents.tool_registry import get_tool_registry
        except Exception:
            pytest.skip("tool_registry 不可导入（环境问题），跳过")
        reg = get_tool_registry()
        registered = {t.name for t in reg.list_all()}
        for _, _, tools, _ in AWS_OPS_ROLES:
            for t in tools:
                # get_by_name 是主路径；部分工具可能按 tool_id 注册，双查
                assert (reg.get_by_name(t) is not None) or (t in registered), f"未注册工具 {t}"


# ── 2. score_script 纯函数 ───────────────────────────────────

class TestScoreScript:
    def test_full_score_is_5(self):
        sc = score_script(FULL_SCRIPT)
        assert sc["score"] == 5
        assert sc["missing"] == []
        assert set(sc["hit"]) == {k for k, _ in CRITERIA}

    @pytest.mark.parametrize("remove_substring,criterion", [
        ("describe-elasticsearch-domain", "instance_spec"),
        ("update-elasticsearch-domain-config", "apply_change"),
        ("put-metric-alarm", "monitor_alarm"),
    ])
    def test_missing_one_criteria(self, remove_substring, criterion):
        broken = FULL_SCRIPT.replace(remove_substring, "REMOVED")
        sc = score_script(broken)
        assert sc["score"] == 4
        assert criterion in sc["missing"]

    def test_empty_string_is_zero(self):
        sc = score_script("")
        assert sc["score"] == 0
        assert len(sc["missing"]) == 5

    def test_none_is_zero(self):
        sc = score_script(None)
        assert sc["score"] == 0


# ── 3. assert_g1 纯函数分支 ──────────────────────────────────

REGISTERED = {"run_shell", "run_python", "read_file", "search_files",
              "delegate_task", "send_message", "broadcast",
              "set_alarm", "watch_file", "schedule_task"}


def _agent_dict(aid, tools, skills):
    return {"agent_id": aid, "tools": list(tools), "skills": list(skills)}


def _g1_agents_ok():
    return [_agent_dict(aid, t["tools"], t["skills"]) for aid, t in G1_TEMPLATE.items()]


class TestAssertG1:
    def test_ok(self):
        r = assert_g1(_g1_agents_ok(), REGISTERED)
        assert r["ok"]

    def test_wrong_count(self):
        r = assert_g1(_g1_agents_ok()[:5], REGISTERED)
        assert not r["ok"] and "角色数" in r["reason"]

    def test_unregistered_tool(self):
        agents = _g1_agents_ok()
        agents[0] = _agent_dict("aws_lead", ["run_shell", "ghost_tool"], ["aws_es_scaling_orchestration"])
        r = assert_g1(agents, REGISTERED)
        assert not r["ok"] and "未注册工具" in r["reason"]

    def test_team_conflict(self):
        r = assert_g1(_g1_agents_ok(), REGISTERED, team_id="d083a568")
        assert not r["ok"] and "冲突" in r["reason"]

    def test_tool_mismatch_with_template(self):
        agents = _g1_agents_ok()
        agents[1] = _agent_dict("aws_arch", ["run_shell", "search_files"], ["aws_es_capacity_planning"])
        r = assert_g1(agents, REGISTERED)
        assert not r["ok"] and "不一致" in r["reason"]


# ── 4. assert_g2b 迭代轨迹 ───────────────────────────────────

class TestAssertG2b:
    def test_converges(self):
        r = assert_g2b([3, 4, 5], 5)
        assert r["ok"]

    def test_too_many_rounds(self):
        r = assert_g2b([2, 3, 4, 5], 5)
        assert not r["ok"] and "轮数" in r["reason"]

    def test_regression(self):
        r = assert_g2b([4, 3, 5], 5)
        assert not r["ok"] and "退步" in r["reason"]

    def test_not_full_score(self):
        r = assert_g2b([3, 4], 4)
        assert not r["ok"] and "< 5" in r["reason"]


# ── 5. assert_g3 孪生协作 ────────────────────────────────────

class TestAssertG3:
    def _steps(self, n=6, actors=3, reward=1.0):
        aids = [f"a{i}" for i in range(actors)]
        return [{"agent_actions": [{"agent_id": aids[i % actors]}], "reward": reward} for i in range(n)]

    def test_ok(self):
        assert assert_g3(self._steps())["ok"]

    def test_too_few_steps(self):
        r = assert_g3(self._steps(n=4))
        assert not r["ok"] and "步数" in r["reason"]

    def test_zero_reward(self):
        r = assert_g3(self._steps(reward=0))
        assert not r["ok"] and "reward" in r["reason"]

    def test_few_agents(self):
        r = assert_g3(self._steps(actors=2))
        assert not r["ok"] and "agent" in r["reason"]


# ── 6. assert_g4 真实降本 ────────────────────────────────────

class TestAssertG4:
    def test_ok(self):
        r = assert_g4(baseline_per_call=5000, current_per_call=3500, target=4000,
                      progress={"status": "achieved"},
                      ratchet_metrics=[{"metric_key": "cost_efficiency:aws-ops"}])
        assert r["ok"]

    def test_not_enough_reduction(self):
        r = assert_g4(5000, 4500, 4000, {"status": "achieved"}, [{"metric_key": "cost_efficiency:aws-ops"}])
        assert not r["ok"] and "降幅" in r["reason"]

    def test_target_not_achieved(self):
        r = assert_g4(5000, 3500, 4000, {"status": "active"}, [{"metric_key": "cost_efficiency:aws-ops"}])
        assert not r["ok"] and "achieved" in r["reason"]

    def test_ratchet_missing(self):
        r = assert_g4(5000, 3500, 4000, {"status": "achieved"}, [])
        assert not r["ok"] and "棘轮" in r["reason"]
