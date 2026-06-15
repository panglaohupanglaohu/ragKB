#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS ops end-to-end smoke for AgentsGroup2026.

This script intentionally uses the running HTTP service instead of importing
backend internals. The goal is to verify the product path the user described:
team setup -> plaza discussion -> skill extraction/injection -> digital twin
practice -> system evolution -> cost governance.
"""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import random
import sys
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"
WARN = "WARN"
DEFAULT_AWS_TEAM_NAME = "AWS 运维团队"
LEGACY_AWS_TEAM_PREFIX = "AWS 运维团队 aws_ops_e2e_"
PREVIOUS_DEFAULT_AWS_TEAM_NAMES = {"AWS 运维团队 E2E Demo"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def compact(value: Any, limit: int = 1400) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    return text if len(text) <= limit else text[:limit] + "...(truncated)"


def items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return [x for x in payload["items"] if isinstance(x, dict)]
    return []


@dataclass
class StepResult:
    step: str
    status: str
    started_at: str
    ended_at: str
    detail: str = ""
    data: dict[str, Any] = field(default_factory=dict)


class ApiClient:
    def __init__(self, base_url: str, timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.csrf = ""

    def request(
        self,
        method: str,
        path: str,
        data: Any = None,
        *,
        timeout: int | None = None,
        raw_base: bool = False,
    ) -> tuple[Any, int]:
        url = path if path.startswith("http") else self.base_url + path
        body = json.dumps(data, ensure_ascii=False).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body, method=method.upper())
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        if method.upper() in {"POST", "PUT", "PATCH", "DELETE"} and self.csrf:
            req.add_header("X-CSRF-Token", self.csrf)
        try:
            with self.opener.open(req, timeout=timeout or self.timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                if not raw:
                    return {}, resp.status
                try:
                    return json.loads(raw), resp.status
                except json.JSONDecodeError:
                    return {"raw": raw}, resp.status
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            try:
                payload = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                payload = {"raw": raw}
            return payload, exc.code
        except Exception as exc:
            return {"error": str(exc)}, 0

    def get(self, path: str, **kwargs) -> tuple[Any, int]:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, data: Any = None, **kwargs) -> tuple[Any, int]:
        return self.request("POST", path, data, **kwargs)

    def put(self, path: str, data: Any = None, **kwargs) -> tuple[Any, int]:
        return self.request("PUT", path, data, **kwargs)

    def delete(self, path: str, **kwargs) -> tuple[Any, int]:
        return self.request("DELETE", path, **kwargs)


class Runner:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.client = ApiClient(args.base_url, timeout=args.timeout)
        self.run_id = args.run_id or f"aws_ops_e2e_{int(time.time())}_{random.randint(1000,9999)}"
        self.results: list[StepResult] = []
        self.ctx: dict[str, Any] = {
            "run_id": self.run_id,
            "base_url": args.base_url.rstrip("/"),
            "started_at": utc_now(),
            "objects": {},
            "warnings": [],
            "improvement_todos": [],
        }

    def step(self, name: str, fn: Callable[[], dict[str, Any] | None], *, critical: bool = True) -> dict[str, Any]:
        started = utc_now()
        print(f"\n== {name}", flush=True)
        try:
            data = fn() or {}
            status = data.pop("_status", PASS)
            detail = data.pop("_detail", "")
            if status == PASS:
                print(f"  PASS {detail}", flush=True)
            elif status == WARN:
                print(f"  WARN {detail}", flush=True)
            elif status == SKIP:
                print(f"  SKIP {detail}", flush=True)
            else:
                print(f"  FAIL {detail}", flush=True)
            self.results.append(StepResult(name, status, started, utc_now(), detail, data))
            return data
        except Exception as exc:
            detail = f"{exc.__class__.__name__}: {exc}"
            print(f"  FAIL {detail}", flush=True)
            if self.args.verbose:
                traceback.print_exc()
            self.results.append(StepResult(name, FAIL, started, utc_now(), detail, {}))
            if critical and self.args.fail_fast:
                raise
            return {}

    def require_status(self, payload: Any, code: int, expected: set[int], context: str) -> None:
        if code not in expected:
            raise AssertionError(f"{context} HTTP {code}: {compact(payload, 700)}")

    def bootstrap_auth(self) -> dict[str, Any]:
        user = f"{self.run_id}_user"
        password = "TestPass123!"
        payload, code = self.client.post("/api/v1/auth/register", {"username": user, "password": password})
        if code not in {200, 201, 409}:
            payload, code = self.client.post("/api/v1/auth/login", {"username": user, "password": password})
        self.require_status(payload, code, {200, 201, 409}, "auth")
        csrf, csrf_code = self.client.get("/api/v1/auth/csrf-token")
        self.require_status(csrf, csrf_code, {200}, "csrf")
        self.client.csrf = str(csrf.get("csrf_token") or "")
        me, me_code = self.client.get("/api/v1/auth/me")
        self.require_status(me, me_code, {200}, "auth/me")
        if not me.get("authenticated"):
            raise AssertionError(f"auth/me not authenticated: {me}")
        self.ctx["objects"]["user"] = user
        return {"username": user, "csrf": bool(self.client.csrf), "_detail": user}

    def find_codebuddy_model(self) -> dict[str, Any]:
        teams_payload, code = self.client.get("/api/v1/agent-config/teams?limit=200&offset=0")
        self.require_status(teams_payload, code, {200}, "teams")
        candidates: list[dict[str, Any]] = []
        for team in items(teams_payload):
            team_id = team.get("team_id") or ""
            models_payload, m_code = self.client.get(f"/api/v1/agent-config/teams/{team_id}/models?limit=200&offset=0")
            if m_code != 200:
                continue
            for model in items(models_payload):
                name = str(model.get("name") or "")
                provider = str(model.get("provider") or "")
                model_id = str(model.get("model_id") or "")
                is_codebuddy = "codebuddy" in model_id.lower() or "codebuddy" in name.lower()
                matches_screenshot = (
                    name == "deepseek-v4-pro"
                    and provider == "deepseek"
                    and int(model.get("max_tokens") or 0) == 4096
                    and abs(float(model.get("temperature") or 0) - 0.7) < 0.0001
                )
                if is_codebuddy or matches_screenshot:
                    candidates.append({"team_id": team_id, "team_name": team.get("name"), **model})
        if not candidates:
            status, _ = self.client.get("/api/v1/agent-config/llm/status")
            self.ctx["improvement_todos"].append("补齐模型池中的 codebuddy/deepseek-v4-pro 默认配置，并保存 API key。")
            return {"_status": FAIL, "_detail": "未找到截图对应的 CodeBuddy/DeepSeek 模型池配置", "llm_status": status}

        preferred = next((m for m in candidates if m.get("is_default")), candidates[0])
        test_payload = {
            "provider": preferred.get("provider") or "deepseek",
            "name": preferred.get("name") or "deepseek-v4-pro",
            "model_id": preferred.get("model_id") or "",
            "api_key": "",
            "api_base_url": preferred.get("api_base_url") or "",
            "max_tokens": int(preferred.get("max_tokens") or 4096),
            "temperature": float(preferred.get("temperature") or 0.7),
        }
        llm_test, t_code = self.client.post("/api/v1/agent-config/llm/test-model", test_payload, timeout=self.args.llm_timeout)
        preferred["test_result"] = llm_test
        self.ctx["objects"]["codebuddy_model"] = preferred
        if t_code != 200 or not llm_test.get("success"):
            self.ctx["improvement_todos"].append("修复 CodeBuddy/DeepSeek 模型连接：检查 API key、base_url、网络连通性和默认模型同步。")
            return {
                "_status": FAIL,
                "_detail": f"找到模型但 LLM test 失败 HTTP {t_code}: {compact(llm_test, 500)}",
                "model": preferred,
            }
        return {"_detail": f"{preferred.get('team_name')} / {preferred.get('model_id')} / {preferred.get('name')}", "model": preferred}

    def cleanup_legacy_aws_e2e_teams(self) -> dict[str, Any]:
        if self.args.keep_legacy_aws_teams:
            return {"_status": SKIP, "_detail": "kept by --keep-legacy-aws-teams"}
        payload, code = self.client.get("/api/v1/agent-config/teams?limit=200&offset=0")
        self.require_status(payload, code, {200}, "list teams for cleanup")
        deleted: list[dict[str, Any]] = []
        for team in items(payload):
            name = str(team.get("name") or "")
            team_id = str(team.get("team_id") or team.get("id") or "")
            if not team_id or not name.startswith(LEGACY_AWS_TEAM_PREFIX):
                continue
            result, d_code = self.client.delete(f"/api/v1/agent-config/teams/{urllib.parse.quote(team_id, safe='')}")
            deleted.append({"team_id": team_id, "name": name, "code": d_code, "result": result})
        self.ctx["objects"]["deleted_legacy_aws_teams"] = deleted
        status = PASS if all(row["code"] in {200, 404} for row in deleted) else WARN
        return {"_status": status, "_detail": f"deleted={len(deleted)}", "deleted": deleted}

    def create_aws_team(self) -> dict[str, Any]:
        team_name = self.args.aws_team_name.strip() or DEFAULT_AWS_TEAM_NAME
        description = "E2E 演示团队：一个 AWS 运维团队，内部包含 Leader、架构师、操作员、巡检监控、成本优化和北美 AI 项目运维成员。"
        teams_payload, list_code = self.client.get("/api/v1/agent-config/teams?limit=200&offset=0")
        self.require_status(teams_payload, list_code, {200}, "list teams")
        existing = next((team for team in items(teams_payload) if team.get("name") == team_name), None)
        if not existing:
            existing = next((team for team in items(teams_payload) if team.get("name") in PREVIOUS_DEFAULT_AWS_TEAM_NAMES), None)
        if existing:
            team_id = existing.get("team_id") or existing.get("id")
            if not team_id:
                raise AssertionError(f"existing team_id missing: {existing}")
            self.client.put(
                f"/api/v1/agent-config/teams/{urllib.parse.quote(str(team_id), safe='')}",
                {"name": team_name, "description": description},
            )
            self.ctx["objects"]["aws_team_id"] = team_id
            self.ctx["objects"]["aws_team_name"] = team_name
            return {"team_id": team_id, "team": existing, "reused": True, "_detail": f"reused {team_id}"}
        team_payload = {
            "name": team_name,
            "description": description,
        }
        team, code = self.client.post("/api/v1/agent-config/teams", team_payload)
        self.require_status(team, code, {201}, "create team")
        team_id = team.get("team_id")
        if not team_id:
            raise AssertionError(f"team_id missing: {team}")
        self.ctx["objects"]["aws_team_id"] = team_id
        self.ctx["objects"]["aws_team_name"] = team_name
        return {"team_id": team_id, "team": team, "reused": False, "_detail": f"created {team_id}"}

    def list_tools_and_skills(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        tools_payload, t_code = self.client.get("/api/v1/agent-config/tools?limit=200&offset=0")
        self.require_status(tools_payload, t_code, {200}, "tools")
        skills_payload, s_code = self.client.get("/api/v1/agent-config/skills/search?q=&limit=200&offset=0")
        self.require_status(skills_payload, s_code, {200}, "skills")
        return items(tools_payload), items(skills_payload)

    def pick_by_keywords(self, rows: list[dict[str, Any]], keywords: list[str], id_key: str, limit: int = 6) -> list[str]:
        picked: list[str] = []
        for row in rows:
            hay = " ".join(str(row.get(k, "")) for k in ("name", "description", "category", "tool_id", "skill_id", "slug")).lower()
            if any(k.lower() in hay for k in keywords):
                value = row.get(id_key) or row.get("name") or row.get("slug")
                if value and value not in picked:
                    picked.append(str(value))
            if len(picked) >= limit:
                break
        if not picked:
            for row in rows[:limit]:
                value = row.get(id_key) or row.get("name") or row.get("slug")
                if value:
                    picked.append(str(value))
        return picked

    def create_agents_and_bind_capabilities(self) -> dict[str, Any]:
        team_id = self.ctx["objects"]["aws_team_id"]
        all_tools, all_skills = self.list_tools_and_skills()
        tool_ids = self.pick_by_keywords(
            all_tools,
            ["aws", "terraform", "shell", "kubectl", "monitor", "cost", "http", "file", "script"],
            "tool_id",
            limit=8,
        )
        skill_ids = self.pick_by_keywords(
            all_skills,
            ["aws", "ops", "运维", "monitor", "cost", "review", "test", "脚本", "cloud", "compliance"],
            "slug",
            limit=8,
        )
        tool_enable_results: list[dict[str, Any]] = []
        for tool_id in tool_ids:
            result, code = self.client.post(f"/api/v1/agent-config/teams/{team_id}/tools/{urllib.parse.quote(tool_id, safe='')}/enable")
            tool_enable_results.append({"tool_id": tool_id, "code": code, "result": result})
        skill_enable_results: list[dict[str, Any]] = []
        for skill_id in skill_ids:
            result, code = self.client.post(f"/api/v1/agent-config/teams/{team_id}/skills/{urllib.parse.quote(skill_id, safe='')}/enable")
            skill_enable_results.append({"skill_ref": skill_id, "code": code, "result": result})

        role_specs = [
            ("ops_leader", "运维 Leader", "整体协调、任务派发、风险升级、变更窗口把关"),
            ("cloud_architect", "上云架构师", "AWS/ElasticSearch 资源规划、容量建模、可用区和网络设计"),
            ("ops_operator", "运维操作员", "Terraform/脚本执行、资源创建、变更落地"),
            ("monitor_responder", "巡检监控员", "指标巡检、告警监控、故障定位与恢复"),
            ("cost_optimizer", "成本优化成员", "账单分析、RI/Savings Plan、成本治理目标制定"),
            ("na_ai_operator", "北美 AI 项目运维员", "北美区域 AWS AI 项目部署、合规和数据驻留要求"),
        ]
        existing_payload, existing_code = self.client.get(f"/api/v1/agent-config/teams/{team_id}/agents?limit=200&offset=0")
        existing_agents = items(existing_payload) if existing_code == 200 else []
        existing_by_name = {str(agent.get("name") or ""): agent for agent in existing_agents}
        agents: list[dict[str, Any]] = []
        for idx, (key, name, role) in enumerate(role_specs):
            agent_payload = {
                "name": name,
                "role": role,
                "description": f"{name}：{role}",
                "template_type": "custom",
                "system_prompt": f"你是 AWS 运维团队的{name}，负责{role}。回答必须围绕 ElasticSearch 伸缩、稳定性、成本和合规。",
            }
            if name in existing_by_name:
                agent_id = existing_by_name[name].get("agent_id")
                agent, code = self.client.put(
                    f"/api/v1/agent-config/teams/{team_id}/agents/{agent_id}",
                    agent_payload,
                )
                self.require_status(agent, code, {200}, f"update agent {name}")
            else:
                agent, code = self.client.post(
                    f"/api/v1/agent-config/teams/{team_id}/agents",
                    agent_payload,
                )
                self.require_status(agent, code, {201}, f"create agent {name}")
            agent_id = agent.get("agent_id")
            agent_tool_ids = tool_ids[idx % max(len(tool_ids), 1):] + tool_ids[: idx % max(len(tool_ids), 1)]
            agent_skill_ids = skill_ids[idx % max(len(skill_ids), 1):] + skill_ids[: idx % max(len(skill_ids), 1)]
            agent_tool_ids = agent_tool_ids[: min(4, len(agent_tool_ids))]
            agent_skill_ids = agent_skill_ids[: min(4, len(agent_skill_ids))]
            if agent_id:
                tool_bind, tool_bind_code = self.client.put(f"/api/v1/agent-config/teams/{team_id}/agents/{agent_id}/tools", {"tool_ids": agent_tool_ids})
                skill_bind, skill_bind_code = self.client.put(f"/api/v1/agent-config/teams/{team_id}/agents/{agent_id}/skills", {"skill_ids": agent_skill_ids})
                if tool_bind_code == 200:
                    agent["tools"] = tool_bind.get("tools", agent_tool_ids)
                if skill_bind_code == 200:
                    agent["skills"] = skill_bind.get("skills", agent_skill_ids)
                personality = {
                    "tone": "professional",
                    "language": "zh-CN",
                    "expertise_areas": ["AWS", "ElasticSearch", "运维自动化", "成本治理", "合规"],
                    "response_style": "concise",
                    "creativity": 0.35,
                }
                self.client.put(f"/api/v1/agent-config/teams/{team_id}/agents/{agent_id}/personality", personality)
            agent["e2e_key"] = key
            agents.append(agent)
        self.ctx["objects"]["aws_agents"] = agents
        self.ctx["objects"]["initial_tool_ids"] = tool_ids
        self.ctx["objects"]["initial_skill_refs"] = skill_ids
        team_skills_payload, team_skills_code = self.client.get(f"/api/v1/agent-config/teams/{team_id}/skills?limit=200&offset=0")
        actual_team_skills = items(team_skills_payload) if team_skills_code == 200 else []
        bound_skill_count = sum(len(agent.get("skills") or []) for agent in agents)
        tool_enable_ok = all(row["code"] == 200 for row in tool_enable_results)
        skill_enable_ok = all(row["code"] == 200 for row in skill_enable_results)
        status = PASS if tool_ids and tool_enable_ok and skill_ids and skill_enable_ok and actual_team_skills and bound_skill_count > 0 else FAIL
        detail = f"team_agents={len(agents)}, tools={len(tool_ids)}, skill_refs={len(skill_ids)}, actual_team_skills={len(actual_team_skills)}, bound_skills={bound_skill_count}"
        if status == FAIL:
            self.ctx["improvement_todos"].append("补充 AWS/Terraform/监控/成本/合规相关默认工具和技能，避免新团队初始化为空。")
            self.ctx["improvement_todos"].append("团队技能绑定必须校验 enable/bind 返回码，优先使用 slug/name 作为技能引用，避免 search skill_id 与注册表实例不一致。")
        return {
            "_status": status,
            "_detail": detail,
            "agents": agents,
            "tool_ids": tool_ids,
            "skill_refs": skill_ids,
            "tool_enable_results": tool_enable_results,
            "skill_enable_results": skill_enable_results,
            "actual_team_skills": actual_team_skills,
        }

    def plaza_discussion(self) -> dict[str, Any]:
        team_id = self.ctx["objects"]["aws_team_id"]
        agents = self.ctx["objects"]["aws_agents"]
        selected = [
            {
                "agent_id": a.get("agent_id"),
                "agent_name": a.get("name"),
                "role": a.get("role"),
                "team_id": team_id,
            }
            for a in agents
            if a.get("agent_id")
        ]
        plaza, code = self.client.post(
            "/api/v1/agent-config/plaza",
            {
                "name": f"ES 伸缩运维议事厅 {self.run_id}",
                "description": "围绕 ElasticSearch 实例伸缩、自动化脚本、成本与北美合规进行协作决策。",
                "selected_agents": selected,
                "chairperson_agent_id": selected[0]["agent_id"] if selected else "",
            },
        )
        self.require_status(plaza, code, {201}, "create plaza")
        plaza_id = plaza.get("id")
        discussion, d_code = self.client.post(
            f"/api/v1/agent-config/plaza/{plaza_id}/discussions",
            {
                "topic": "ElasticSearch 实例资源缩放",
                "description": "评估生产 ElasticSearch 集群从 r6g.large 扩容到 r6g.xlarge 或增加节点的策略，覆盖脚本、监控、成本和北美 AI 项目合规。",
                "goal": "形成可执行计划：Build System 编写运维脚本；AWS 运维团队负责评审、执行、监控、成本治理与区域合规。",
                "moderator_agent_id": selected[0]["agent_id"] if selected else "",
                "max_rounds": 2,
            },
        )
        self.require_status(discussion, d_code, {201}, "create discussion")
        discussion_id = discussion.get("id")
        self.ctx["objects"]["plaza_id"] = plaza_id
        self.ctx["objects"]["discussion_id"] = discussion_id

        start, s_code = self.client.post(
            f"/api/v1/agent-config/plaza/{plaza_id}/discussions/{discussion_id}/start",
            timeout=self.args.llm_timeout,
        )
        if s_code != 200:
            self.ctx["improvement_todos"].append("Plaza 讨论启动失败时增加计划生成兜底，至少保留结构化空计划和 request_id。")
            return {"_status": FAIL, "_detail": f"discussion start HTTP {s_code}: {compact(start, 500)}", "plaza": plaza, "discussion": discussion}
        detail, g_code = self.client.get(f"/api/v1/agent-config/plaza/{plaza_id}/discussions/{discussion_id}")
        self.require_status(detail, g_code, {200}, "get discussion")
        plan_text = compact(detail.get("plan") or detail.get("summary") or detail.get("key_conclusions") or "", 6000)
        self.ctx["objects"]["discussion_plan_text"] = plan_text
        if len(plan_text.strip()) < 20:
            self.ctx["improvement_todos"].append("Plaza 讨论完成后 plan/summary 为空，需要补强 LLM 输出解析和前端错误提示。")
            return {"_status": FAIL, "_detail": "讨论完成但 plan/summary 为空", "discussion_detail": detail}
        return {"_detail": f"plaza={plaza_id}, discussion={discussion_id}", "discussion_detail": detail, "start": start}

    def dispatch_and_record_outputs(self) -> dict[str, Any]:
        plaza_id = self.ctx["objects"]["plaza_id"]
        discussion_id = self.ctx["objects"]["discussion_id"]
        dispatch, code = self.client.post(
            f"/api/v1/agent-config/plaza/{plaza_id}/discussions/{discussion_id}/dispatch",
            {"team_id": "build_system"},
            timeout=120,
        )
        status = PASS
        if code != 200 or int(dispatch.get("task_count") or 0) < 1:
            status = FAIL
            self.ctx["improvement_todos"].append("讨论计划派发到 Build System 未产生任务，需要检查 plan 表格解析和任务创建错误态。")
        out, out_code = self.client.post(
            f"/api/v1/agent-config/plaza/{plaza_id}/discussions/{discussion_id}/outputs",
            {"output_type": "skill_candidate", "team_id": self.ctx["objects"]["aws_team_id"], "status_value": "created"},
        )
        if out_code != 200:
            status = FAIL
        self.ctx["objects"]["build_tasks"] = dispatch.get("tasks", []) if isinstance(dispatch, dict) else []
        return {"_status": status, "_detail": f"task_count={dispatch.get('task_count') if isinstance(dispatch, dict) else '?'}", "dispatch": dispatch, "skill_output": out}

    def extract_and_approve_skills(self) -> dict[str, Any]:
        team_id = self.ctx["objects"]["aws_team_id"]
        source = self.ctx["objects"].get("discussion_plan_text") or ""
        source += "\n\n补充测试材料：需要将 ElasticSearch 实例伸缩流程抽象成可复用技能，包括容量评估、Terraform 变更、代码 review、监控回滚、成本优化和北美合规。"
        start, code = self.client.post(
            f"/api/v1/agent-config/teams/{team_id}/skill-extract/start",
            {
                "source_text": source,
                "source_title": f"ES 伸缩运维技能萃取 {self.run_id}",
                "source_type": "plaza_discussion",
            },
            timeout=90,
        )
        self.require_status(start, code, {200, 201}, "skill extract start")
        item_id = start.get("item_id")
        ready: list[dict[str, Any]] = []
        for _ in range(max(1, self.args.skill_wait_seconds // 3)):
            queue, q_code = self.client.get(f"/api/v1/agent-config/teams/{team_id}/skill-extract/queue")
            if q_code == 200:
                ready = [x for x in items(queue) if x.get("status") == "ready_for_review" and (x.get("source_title") or "").startswith("ES 伸缩运维技能萃取")]
                if len(ready) >= 3:
                    break
                if item_id:
                    detail, _ = self.client.get(f"/api/v1/agent-config/teams/{team_id}/skill-extract/{item_id}")
                    if detail.get("status") == "error":
                        break
            time.sleep(3)
        if len(ready) < 3:
            self.ctx["improvement_todos"].append("技能萃取未稳定产出 3 个候选，需要优化 prompt、拆分策略或 LLM 超时/错误提示。")
            return {"_status": FAIL, "_detail": f"ready candidates={len(ready)}", "start": start, "ready": ready}

        agents = self.ctx["objects"]["aws_agents"]
        trait_agent = next((a for a in agents if a.get("e2e_key") == "na_ai_operator"), agents[-1])
        approve_specs = [
            ("public", ""),
            ("trait", trait_agent.get("agent_id") or ""),
            ("reserve", ""),
        ]
        approved: list[dict[str, Any]] = []
        for candidate, (skill_type, target_agent_id) in zip(ready[:3], approve_specs):
            payload = {
                "reviewer": "aws_ops_e2e",
                "skill_type": skill_type,
                "target_agent_id": target_agent_id,
                "edited_fields": {
                    "description": (candidate.get("draft_description") or "") + f"\n\nE2E run: {self.run_id}",
                },
            }
            result, a_code = self.client.post(
                f"/api/v1/agent-config/teams/{team_id}/skill-extract/{candidate['item_id']}/approve",
                payload,
            )
            self.require_status(result, a_code, {200}, f"approve {candidate['item_id']}")
            result["e2e_skill_type"] = skill_type
            result["e2e_skill_id"] = result.get("draft_slug") or result.get("skill_id") or candidate.get("draft_slug") or candidate.get("item_id")
            approved.append(result)
        self.ctx["objects"]["approved_skills"] = approved
        return {"_detail": f"approved={len(approved)}", "approved": approved}

    def verify_evolve_publish_skills(self) -> dict[str, Any]:
        team_id = self.ctx["objects"]["aws_team_id"]
        approved = self.ctx["objects"].get("approved_skills") or []
        if not approved:
            return {"_status": SKIP, "_detail": "no approved skills"}
        results: list[dict[str, Any]] = []
        status = PASS
        for skill in approved:
            skill_id = skill.get("e2e_skill_id")
            if not skill_id:
                status = FAIL
                continue
            verify, v_code = self.client.post("/api/v1/agent-config/skill-library/verify", {"team_id": team_id, "skill_id": skill_id}, timeout=120)
            gate, g_code = self.client.post("/api/v1/agent-config/skill-library/publish-gate", {"team_id": team_id, "skill_id": skill_id})
            evolve, e_code = self.client.post("/api/v1/agent-config/skill-library/evolve", {"team_id": team_id, "skill_id": skill_id}, timeout=self.args.llm_timeout)
            publish = {}
            p_code = 0
            if skill.get("e2e_skill_type") == "public":
                publish, p_code = self.client.post("/api/v1/agent-config/skill-library/publish", {"team_id": team_id, "skill_id": skill_id})
            row = {
                "skill_id": skill_id,
                "type": skill.get("e2e_skill_type"),
                "verify_code": v_code,
                "verify": verify,
                "gate_code": g_code,
                "gate": gate,
                "evolve_code": e_code,
                "evolve": evolve,
                "publish_code": p_code,
                "publish": publish,
            }
            if v_code >= 500 or g_code >= 500 or e_code >= 500 or (p_code and p_code >= 500):
                status = FAIL
            results.append(row)
        if status == FAIL:
            self.ctx["improvement_todos"].append("技能验证/演化/发布存在 5xx，需要补 EvidenceRun 错误详情和门禁失败原因。")
        return {"_status": status, "_detail": f"skill_ops={len(results)}", "results": results}

    def sandbox_workshop(self) -> dict[str, Any]:
        approved = self.ctx["objects"].get("approved_skills") or []
        seed_skill = (approved[0].get("e2e_skill_id") if approved else None) or None
        create, code = self.client.post(
            "/api/v1/sandbox/sessions",
            {
                "team_id": "build_system",
                "mode": "what_if",
                "max_steps": 10,
                "speed_factor": 100,
                "parallel_branches": 1,
                "trigger_description": "模拟 Build System 团队编写 ElasticSearch 伸缩运维脚本，并通过代码 review、重构、测试技能提升交付质量。",
                "use_llm": True,
                "sync_dt": True,
                "initial_skill_id": seed_skill,
            },
            timeout=120,
        )
        self.require_status(create, code, {200}, "create sandbox")
        sid = create.get("session_id")
        self.client.post(f"/api/v1/sandbox/sessions/{sid}/pause")
        steps = []
        for _ in range(2):
            step, s_code = self.client.post(f"/api/v1/sandbox/sessions/{sid}/step", timeout=120)
            steps.append({"code": s_code, "step": step})
        inject_skill, _ = self.client.post(f"/api/v1/sandbox/sessions/{sid}/inject", {"confirm": True, "type": "skill_inject", "skill_id": seed_skill})
        inject_task, _ = self.client.post(f"/api/v1/sandbox/sessions/{sid}/inject", {"confirm": True, "type": "task_change"})
        session, g_code = self.client.get(f"/api/v1/sandbox/sessions/{sid}")
        self.require_status(session, g_code, {200}, "get sandbox")
        self.ctx["objects"]["workshop_session_id"] = sid
        ok_steps = sum(1 for s in steps if s["code"] == 200)
        status = PASS if ok_steps >= 1 else FAIL
        if status == FAIL:
            self.ctx["improvement_todos"].append("Build System 工作坊沙箱无法单步执行，需要检查 team sync、LLM 决策和 step 错误态。")
        return {"_status": status, "_detail": f"session={sid}, steps={ok_steps}", "create": create, "steps": steps, "inject_skill": inject_skill, "inject_task": inject_task, "session": session}

    def aws_trial(self) -> dict[str, Any]:
        team_id = self.ctx["objects"]["aws_team_id"]
        create, code = self.client.post(
            "/api/v1/twin-trials",
            {
                "team_id": team_id,
                "task_goal": {"name": "ElasticSearch 实例资源缩放演练", "description": "扩容、监控、回滚、成本治理、北美合规"},
                "mode": "chaos_drill",
                "max_steps": 10,
                "acceleration": 100,
                "parallel_branches": 1,
                "routing_strategy": "proficiency_first",
            },
            timeout=120,
        )
        self.require_status(create, code, {200}, "create trial")
        trial_id = create.get("trial_id")
        branch_id = create.get("branch_id")
        session_id = create.get("session_id")
        self.ctx["objects"]["aws_trial_id"] = trial_id
        self.ctx["objects"]["aws_trial_branch_id"] = branch_id
        self.ctx["objects"]["aws_trial_session_id"] = session_id
        steps = []
        for _ in range(2):
            step, s_code = self.client.post(f"/api/v1/sandbox/sessions/{session_id}/step", timeout=120)
            steps.append({"code": s_code, "step": step})
        chaos_results = []
        for event_type in ["network_delay", "agent_leave", "task_change", "skill_degraded", "model_hallucination", "logic_deadlock"]:
            event, e_code = self.client.post(
                f"/api/v1/twin-trials/{trial_id}/branches/{branch_id}/events",
                {"event_type": event_type, "payload": {"source": "aws_ops_e2e"}, "trigger_at_step": None},
            )
            chaos_results.append({"type": event_type, "code": e_code, "event": event})
        stats, stats_code = self.client.get(f"/api/v1/twin-trials/{trial_id}/skill-stats")
        eval_result, eval_code = self.client.post(f"/api/v1/twin-trials/{trial_id}/evaluate", {"force_refresh": True}, timeout=120)
        sop, sop_code = self.client.post(f"/api/v1/twin-trials/{trial_id}/extract-sop", {}, timeout=120)
        feedback, fb_code = self.client.post(f"/api/v1/twin-trials/{trial_id}/feedback", {}, timeout=120)
        status = PASS
        if not all(x["code"] == 200 and x["event"].get("injected") for x in chaos_results):
            status = FAIL
        if stats_code != 200 or eval_code != 200 or sop_code >= 500 or fb_code >= 500:
            status = FAIL
        if status == FAIL:
            self.ctx["improvement_todos"].append("AWS trial 演练链路存在失败：补齐 session step、6类故障注入、评分/SOP/反哺的统一错误态。")
        return {
            "_status": status,
            "_detail": f"trial={trial_id}, chaos={sum(1 for x in chaos_results if x['code']==200)}",
            "create": create,
            "steps": steps,
            "chaos": chaos_results,
            "skill_stats": stats,
            "evaluate": eval_result,
            "sop": sop,
            "feedback": feedback,
        }

    def evolution_loop(self) -> dict[str, Any]:
        plaza_id = self.ctx["objects"].get("plaza_id")
        discussion_id = self.ctx["objects"].get("discussion_id")
        team_id = self.ctx["objects"].get("aws_team_id")
        evolved = {}
        e_code = 0
        if plaza_id and discussion_id:
            evolved, e_code = self.client.post(
                f"/api/v1/agent-config/plaza/{plaza_id}/discussions/{discussion_id}/evolve",
                {"team_id": team_id},
                timeout=120,
            )
        audit, a_code = self.client.post("/api/v1/agent-teams/evolution/audit", timeout=120)
        cycle, c_code = self.client.post("/api/v1/agent-teams/evolution/cycle", timeout=120)
        verify, v_code = self.client.post("/api/v1/agent-teams/evolution/verify", timeout=120)
        summary, s_code = self.client.get("/api/v1/agent-teams/evolution/summary")
        ev_items, i_code = self.client.get("/api/v1/agent-teams/evolution/items?limit=20&offset=0")
        status = PASS if all(code == 200 for code in [a_code, c_code, v_code, s_code, i_code]) else FAIL
        if e_code not in {0, 200}:
            status = FAIL
        if status == FAIL:
            self.ctx["improvement_todos"].append("系统演进 Loop 未完整跑通：检查 plaza evolve 的 plan_source、演进引擎注册和 verify 证据输出。")
        return {"_status": status, "_detail": f"items={len(items(ev_items))}", "plaza_evolve": evolved, "audit": audit, "cycle": cycle, "verify": verify, "summary": summary, "items": ev_items}

    def cost_governance(self) -> dict[str, Any]:
        summary, s_code = self.client.get("/api/v1/cost/summary?aggregation=team&window=7d")
        by_team, bt_code = self.client.get("/api/v1/cost/by-team?window=7d")
        sustainability, su_code = self.client.get("/api/v1/sustainability/group")
        plan = {
            "resource_changes": [
                {
                    "address": "aws_opensearch_domain.es_scaling",
                    "type": "aws_opensearch_domain",
                    "name": "es_scaling",
                    "provider_name": "aws",
                    "change": {"actions": ["update"]},
                    "values": {
                        "instance_type": "r6g.4xlarge.search",
                        "instance_count": 12,
                        "region": "us-east-1",
                        "tags": {"Environment": "production", "Owner": "aws-ops-e2e"},
                    },
                }
            ]
        }
        gate, g_code = self.client.post(
            "/api/v1/cost-gate/evaluate",
            {
                "plan": plan,
                "project_id": f"es-scaling-{self.run_id}",
                "metadata": {
                    "source": "aws_ops_e2e",
                    "team_id": self.ctx["objects"].get("aws_team_id"),
                    "plaza_topic_id": self.ctx["objects"].get("plaza_id"),
                    "discussion_id": self.ctx["objects"].get("discussion_id"),
                    "trial_id": self.ctx["objects"].get("aws_trial_id"),
                },
            },
        )
        status = PASS if all(code == 200 for code in [s_code, bt_code, su_code, g_code]) else FAIL
        if status == FAIL:
            self.ctx["improvement_todos"].append("成本治理 API 未完整返回：检查 OpenCost 聚合、sustainability 数据源和 Cost Gate 证据写入。")
        heaviest = None
        teams = sustainability.get("teams") if isinstance(sustainability, dict) else []
        if teams:
            heaviest = max(teams, key=lambda x: x.get("tokens_consumed", 0) or 0)
        return {"_status": status, "_detail": f"cost_gate={gate.get('decision') if isinstance(gate, dict) else '?'}", "cost_summary": summary, "by_team": by_team, "sustainability": sustainability, "heaviest_token_team": heaviest, "cost_gate": gate}

    def build_report(self) -> dict[str, Any]:
        self.ctx["ended_at"] = utc_now()
        self.ctx["results"] = [r.__dict__ for r in self.results]
        counts: dict[str, int] = {PASS: 0, FAIL: 0, WARN: 0, SKIP: 0}
        for result in self.results:
            counts[result.status] = counts.get(result.status, 0) + 1
        self.ctx["summary"] = counts
        existing_todos = set(self.ctx["improvement_todos"])

        def add_todo(todo: str) -> None:
            if todo not in existing_todos:
                self.ctx["improvement_todos"].append(todo)
                existing_todos.add(todo)

        for result in self.results:
            if result.status != FAIL:
                continue
            if result.step.startswith("T0-2"):
                add_todo("LLM 前置门禁：在保存模型配置后立即执行 /llm/test-model，失败时禁止标记为默认模型。")
                add_todo("CodeBuddy/DeepSeek 连接修复伪代码：load default model -> call provider healthcheck -> assert success -> write masked latency/error evidence。")
            elif result.step.startswith("T2 plaza discussion"):
                add_todo("Plaza 讨论启动后增加轮询收敛：start_discussion -> poll detail until summary/plan/messages 非空或 timeout。")
                add_todo("Plaza 计划兜底伪代码：if LLM failed or plan empty: build deterministic plan from topic/goal/participants and mark source=fallback。")
            elif result.step.startswith("T2 branch"):
                add_todo("Dispatch 前置校验：if plan empty return actionable error with discussion_id, topic, expected plan schema, and regenerate endpoint。")
                add_todo("Build System 派发伪代码：parse plan.steps -> create task per owner/action/check -> persist plaza/discussion trace。")
            elif result.step.startswith("T3 skill extraction"):
                add_todo("技能萃取候选不足时拆分源文本：capacity / terraform / monitor / cost / compliance 至少生成 3 个 review candidates。")
                add_todo("技能萃取降级伪代码：if LLM unavailable: create deterministic candidates with confidence<=0.3 and status=needs_llm_review, not green ready_for_review。")
            elif result.step.startswith("T4 Build System workshop"):
                add_todo("Sandbox step 500 需要返回结构化错误：session_id、team_id、use_llm、selected_agent、missing_skill_id、backend traceback id。")
                add_todo("Build System 工作坊修复伪代码：sync build_system agents -> ensure twins_count>0 -> pause created session -> step once -> assert total_steps_executed increments。")
        if not self.ctx["improvement_todos"]:
            self.ctx["improvement_todos"].append("本轮未发现阻塞项；建议补真实浏览器 UI 回归，覆盖按钮状态和截图证据。")
        return self.ctx

    def write_reports(self) -> None:
        report = self.build_report()
        json_path = Path(self.args.report_json)
        md_path = Path(self.args.report_md)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

        lines = [
            "# AWS 运维端到端测试报告",
            "",
            f"- run_id: `{self.run_id}`",
            f"- base_url: `{self.args.base_url}`",
            f"- started_at: `{report.get('started_at')}`",
            f"- ended_at: `{report.get('ended_at')}`",
            f"- summary: PASS={report['summary'].get(PASS,0)} / FAIL={report['summary'].get(FAIL,0)} / WARN={report['summary'].get(WARN,0)} / SKIP={report['summary'].get(SKIP,0)}",
            "",
            "## 关键对象",
            "",
        ]
        for key, value in report.get("objects", {}).items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                lines.append(f"- `{key}`: `{value}`")
        lines.extend(["", "## 步骤结果", ""])
        for result in self.results:
            lines.append(f"- [{result.status}] **{result.step}**：{result.detail or '-'}")
        lines.extend(["", "## 失败原因分析", ""])
        failed = [r for r in self.results if r.status == FAIL]
        if failed:
            for result in failed:
                lines.append(f"- `{result.step}`：{result.detail}")
        else:
            lines.append("- 未发现 FAIL；请继续补真实浏览器 UI 回归。")
        lines.extend(["", "## 改进 TODOS", ""])
        for todo in report.get("improvement_todos", []):
            lines.append(f"- [ ] {todo}")
        lines.extend(["", "## 原始 JSON", "", f"- `{json_path}`", ""])
        md_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"\nReports written:\n  {md_path}\n  {json_path}", flush=True)

    def run(self) -> int:
        self.step("T0-1 auth bootstrap", self.bootstrap_auth)
        self.step("T0-1b cleanup legacy duplicate AWS E2E teams", self.cleanup_legacy_aws_e2e_teams, critical=False)
        self.step("T0-2 CodeBuddy DeepSeek LLM config and real call", self.find_codebuddy_model, critical=False)
        self.step("T1-1 create AWS ops team", self.create_aws_team)
        self.step("T1-2/T1-3 create agents and bind initial tools/skills", self.create_agents_and_bind_capabilities, critical=False)
        self.step("T2 plaza discussion for ElasticSearch scaling", self.plaza_discussion, critical=False)
        self.step("T2 branch A/B dispatch tasks and record skill output", self.dispatch_and_record_outputs, critical=False)
        self.step("T3 skill extraction and public/trait/reserve approvals", self.extract_and_approve_skills, critical=False)
        self.step("T3 verify/evolve/publish approved skills", self.verify_evolve_publish_skills, critical=False)
        self.step("T4 Build System workshop sandbox", self.sandbox_workshop, critical=False)
        self.step("T5 AWS ops trial chaos drill", self.aws_trial, critical=False)
        self.step("T6 system evolution loop", self.evolution_loop, critical=False)
        self.step("T7 cost governance and token sustainability", self.cost_governance, critical=False)
        self.write_reports()
        failed = [r for r in self.results if r.status == FAIL]
        return 1 if failed else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AWS ops E2E smoke against AgentsGroup2026.")
    parser.add_argument("--base-url", default=os.environ.get("AGENTS_BASE_URL", "http://127.0.0.1:8080"))
    parser.add_argument("--run-id", default="")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--llm-timeout", type=int, default=240)
    parser.add_argument("--skill-wait-seconds", type=int, default=180)
    parser.add_argument("--aws-team-name", default=DEFAULT_AWS_TEAM_NAME)
    parser.add_argument("--keep-legacy-aws-teams", action="store_true")
    parser.add_argument("--report-md", default="docs/reports/aws-ops-e2e-report.md")
    parser.add_argument("--report-json", default="docs/reports/aws-ops-e2e-report.json")
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runner = Runner(args)
    return runner.run()


if __name__ == "__main__":
    raise SystemExit(main())
