# PM分解 — project_manager

任务: 实现指纹计算模块：模板提取、动态变量剔除、精确哈希、自检与稳定性监控埋点
步骤: pm_decompose
Agent: build_pm

---

📋 任务: 3f9494e1-96d
🤖 Agent: PM (project_manager)
📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
🔧 执行方式: DeepSeek API (直连)
⏱️ 超时: 1200s
────────────────────────────────────────────────────────────
📝 提示词:
  你是 AgentsGroup2026 系统的 PM (project_manager)。
  请执行以下开发任务:
  
  你是项目经理 (PM)。请对以下任务进行分解和规划:
  
  ## 任务
  实现指纹计算模块：模板提取、动态变量剔除、精确哈希、自检与稳定性监控埋点
  Developer, 全栈开发
  
  ## 📂 项目上下文 (系统自动预加载)
  
  ### 项目文件结构 (src/ 目录)
  ```
  src/frontend/agent-team-config.html
  src/frontend/index.html
  src/frontend/login.html
  src/frontend/plaza-dark.html
  src/frontend/plaza-old.html
  src/frontend/plaza-wabisabi-v2.html
  src/frontend/plaza-wabisabi.html
  src/frontend/plaza.html
  src/frontend/system-evolution.html
  src/frontend/tasks.html
  src/frontend/css/agent-team-config.css
  src/frontend/css/openbridge-theme.css
  src/frontend/css/ws-theme-bridge.css
  src/frontend/js/agent-team-config.js
  src/frontend/js/i18n.js
  src/frontend/js/nav-sidebar.js
  src/backend/__init__.py
  src/backend/agent_team_api.py
  src/backend/main.py
  src/backend/main.py.bak
  src/backend/startup_check.py
  src/backend/startup_validator.py
  src/backend/tests/__init__.py
  src/backend/tests/conftest.py
  src/backend/tests/conftest.py.bak
  src/backend/tests/test_ab_testing.py
  src/backend/tests/test_agent_toolbox.py
  src/backend/tests/test_models.py
  src/backend/tests/test_models.py.bak
  src/backend/tests/test_task_engine.py
  src/backend/tests/test_task_engine.py.bak
  src/backend/tests/test_team_manager.py
  src/backend/tests/test_team_manager.py.bak
  src/backend/agents/__init__.py
  src/backend/agents/ab_testing.py
  src/backend/agents/agent_loop.py
  src/backend/agents/agent_toolbox.py
  src/backend/agents/api.py
  src/backend/agents/chat_harness.py
  src/backend/agents/execution_registry.py
  src/backend/agents/hermes_research.py
  src/backend/agents/knowledge_base.py
  src/backend/agents/models.py
  src/backend/agents/plaza.py
  src/backend/agents/plaza_engine.py
  src/backend/agents/plaza_routes.py
  src/backend/agents/plaza_routes.py.bak
  src/backend/agents/plaza_store.py
  src/backend/agents/session_store.py
  src/backend/agents/skill_registry.py
  src/backend/agents/task_engine.py
  src/backend/agents/task_store.py
  src/backend/agents/team_manager.py
  src/backend/agents/team_store.py
  src/backend/agents/tool_executor.py
  src/backend/agents/tool_registry.py
  src/backend/agents/tts_routes.py
  src/backend/agents/teams/__init__.py
  src/backend/agents/teams/ai_coding_team.py
  src/backend/agents/teams/build_team.py
  src/backend/agents/teams/energy_team.py
  src/backend/agents/skills/__init__.py
  src/backend/agents/skills/greeting.py
  src/backend/agents/skills/hello.py
  src/backend/scripts/__init__.py
  src/backend/scripts/validate_startup.py
  src/backend/scripts/validate_telemetry.py
  src/backend/monitoring/__init__.py
  src/backend/monitoring/collector.py
  src/backend/monitoring/models.py
  src/backend/monitoring/plaza_monitor.py
  src/backend/monitoring/plaza_monitor.py.bak
  src/backend/monitoring/sampler.py
  src/backend/channels/__init__.py
  src/backend/channels/bridge_chat.py
  src/backend/channels/evolution_executor.py
  src/backend/channels/marine_base.py
  src/backend/channels/openclaw_sync.py
  src/backend/channels/openclaw_sync.py.bak
  src/backend/channels/system_evolution.py
  src/docs/agent_handoffs/01d37305-090_executor_started_20260509T073232.md
  src/docs/agent_handoffs/0261754d-288_executor_started_20260509T073231.md
  src/docs/agent_handoffs/05014547-ce8_executor_started_20260509T073232.md
  src/docs/agent_handoffs/0597d622-ad4_executor_started_20260509T073232.md
  src/docs/agent_handoffs/06d3f2a5-82c_executor_started_20260509T073231.md
  src/docs/agent_handoffs/073864e5-58b_executor_started_20260509T073231.md
  src/docs/agent_handoffs/073a3fe7-4d5_executor_started_20260509T073232.md
  src/docs/agent_handoffs/09ff3a16-710_executor_started_20260509T073231.md
  src/docs/agent_handoffs/0a242acf-f52_executor_started_20260509T073232.md
  src/docs/agent_handoffs/0af6e1cb-61c_executor_started_20260509T073231.md
  src/docs/agent_handoffs/0c263083-1c8_executor_started_20260509T073231.md
  src/docs/agent_handoffs/0f6d4e48-ea3_executor_started_20260509T073232.md
  src/docs/agent_handoffs/10857dbb-a51_executor_started_20260509T073231.md
  src/docs/agent_handoffs/1356f045-d02_executor_started_20260509T073232.md
  src/docs/agent_handoffs/15554439-6aa_executor_started_20260509T073231.md
  src/docs/agent_handoffs/15a7e2eb-cd1_executor_started_20260509T073232.md
  src/docs/agent_handoffs/18d4b20f-c33_executor_started_20260509T073231.md
  src/docs/agent_handoffs/1aed56ed-eda_executor_started_20260509T073232.md
  src/docs/agent_handoffs/1cc2c0fb-90b_executor_started_20260509T073232.md
  src/docs/agent_handoffs/1ce78c0e-062_architecture_20260503T045804.md
  src/docs/agent_handoffs/1ce78c0e-062_deploy_FAILED_20260503T050220.md
  src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T045845.md
  src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T050025.md
  src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T050150.md
  src/docs/agent_handoffs/1ce78c0e-062_pm_decompose_20260503T045724.md
  src/docs/agent_handoffs/1ce78c0e-062_research_20260503T045739.md
  src/docs/agent_handoffs/1ce78c0e-062_task_init_20260503T045659.md
  src/docs/agent_handoffs/1ce78c0e-062_test_20260503T045905.md
  src/docs/agent_handoffs/1ce78c0e-062_test_20260503T050050.md
  src/docs/agent_handoffs/1ce78c0e-062_test_20260503T050210.md
  src/docs/agent_handoffs/1d2d7607-8a3_executor_started_20260509T073231.md
  src/docs/agent_handoffs/1e04fc38-6e9_executor_started_20260509T073231.md
  src/docs/agent_handoffs/1f835c25-c0f_executor_started_20260509T073232.md
  src/docs/agent_handoffs/1fd87e2e-962_executor_started_20260509T073232.md
  src/docs/agent_handoffs/21750a9a-2ff_executor_started_20260509T073231.md
  src/docs/agent_handoffs/232eac0a-e93_executor_started_20260509T073231.md
  src/docs/agent_handoffs/23cb267e-4e0_executor_started_20260503T114540.md
  src/docs/agent_handoffs/32a3b057-166_executor_started_20260509T073232.md
  src/docs/agent_handoffs/34efc37e-3a1_executor_started_20260509T073231.md
  src/docs/agent_handoffs/35b91517-bfb_executor_started_20260509T073231.md
  src/docs/agent_handoffs/35f5eb68-2b7_executor_started_20260509T073232.md
  src/docs/agent_handoffs/38c98cf4-15b_executor_started_20260509T073231.md
  src/docs/agent_handoffs/38e22004-b64_architecture_20260503T045011.md
  src/docs/agent_handoffs/38e22004-b64_pm_decompose_20260503T044921.md
  src/docs/agent_handoffs/38e22004-b64_research_20260503T044941.md
  src/docs/agent_handoffs/38e22004-b64_task_init_20260503T044856.md
  src/docs/agent_handoffs/39c0911d-173_executor_started_20260509T073232.md
  src/docs/agent_handoffs/3bde709e-2fe_architecture_20260507T031839.md
  src/docs/agent_handoffs/3bde709e-2fe_deploy_FAILED_20260507T033021.md
  src/docs/agent_handoffs/3bde709e-2fe_develop_FAILED_20260507T031910.md
  src/docs/agent_handoffs/3bde709e-2fe_develop_FAILED_20260507T032452.md
  src/docs/agent_handoffs/3bde709e-2fe_develop_FAILED_20260507T032630.md
  src/docs/agent_handoffs/3bde709e-2fe_executor_started_20260507T031444.md
  src/docs/agent_handoffs/3bde709e-2fe_pm_decompose_20260507T031529.md
  src/docs/agent_handoffs/3bde709e-2fe_research_20260507T031614.md
  src/docs/agent_handoffs/3bde709e-2fe_test_FAILED_20260507T031936.md
  src/docs/agent_handoffs/3bde709e-2fe_test_FAILED_20260507T032523.md
  src/docs/agent_handoffs/3bde709e-2fe_test_FAILED_20260507T032706.md
  src/docs/agent_handoffs/415e549a-116_executor_started_20260509T073231.md
  src/docs/agent_handoffs/4b17f83b-805_architecture_20260507T003640.md
  src/docs/agent_handoffs/4b17f83b-805_deploy_FAILED_20260507T004132.md
  src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T003706.md
  src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T003913.md
  src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T004040.md
  src/docs/agent_handoffs/4b17f83b-805_executor_started_20260507T003435.md
  src/docs/agent_handoffs/4b17f83b-805_pm_decompose_20260507T003510.md
  src/docs/agent_handoffs/4b17f83b-805_research_20260507T003555.md
  src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T003732.md
  src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T003939.md
  src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T004102.md
  ... (共 504 个 src/ 文件)
  
  ```
  
  ### 文件: `src/backend/startup_validator.py`
  ```py
  # -*- coding: utf-8 -*-
  """
  Startup Validator - 系统启动完整性验证器
  
  提供:
  1. 后端服务启动检查
  2. API 端点可用性验证
  3. 核心模块初始化状态确认
  4. 结构化验证报告生成
  """
  
  from __future__ import annotations
  
  import asyncio
  import logging
  import time
  from dataclasses import dataclass, field
  from enum import Enum
  from typing import Any, Callable, Dict, List, Optional, Tuple
  
  import httpx
  
  logger = logging.getLogger("startup_validator")
  
  
  class CheckStatus(Enum):
      PASS = "pass"
      FAIL = "fail"
      WARN = "warn"
      SKIP = "skip"
  
  
  @dataclass
  class CheckResult:
      """单个检查项结果"""
      name: str
      status: CheckStatus
      detail: str = ""
      duration_ms: float = 0.0
      error: Optional[str] = None
      metadata: Dict[str, Any] = field(default_factory=dict)
  
  
  @dataclass
  class ValidationReport:
      """完整验证报告"""
      timestamp: float = field(default_factory=time.time)
      total_checks: int = 0
      passed: int = 0
      failed: int = 0
      warnings: int = 0
      skipped: int = 0
      checks: List[CheckResult] = field(default_factory=list)
      summary: str = ""
  
      def add(self, result: CheckResult):
          self.checks.append(result)
          self.total_checks += 1
          if result.status == CheckStatus.PASS:
              self.passed += 1
          elif result.status == CheckStatus.FAIL:
              self.failed += 1
          elif result.status == CheckStatus.WARN:
              self.warnings += 1
          elif result.status == CheckStatus.SKIP:
              self.skipped += 1
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "timestamp": self.timestamp,
              "total_checks": self.total_checks,
              "passed": self.passed,
              "failed": self.failed,
              "warnings": self.warnings,
              "skipped": self.skipped,
              "checks": [
                  {
                      "name": c.name,
                      "status": c.status.value,
                      "detail": c.detail,
                      "duration_ms": round(c.duration_ms, 1),
                      "error": c.error,
                      "metadata": c.metadata,
                  }
                  for c in self.checks
              ],
              "summary": self.summary or self._generate_summary(),
          }
  
      def _generate_summary(self) -> str:
          if self.failed > 0:
              return f"❌ {self.failed}/{self.total_checks} checks FAILED"
          if self.warnings > 0:
              return f"⚠️ {self.warnings}/{self.total_checks} checks have warnings"
          return f"✅ All {self.total_checks} checks passed"
  
  
  class StartupValidator:
      """系统启动验证器"""
  
      def __init__(self, base_url: str = "http://localhost:8080"):
          self.base_url = base_url.rstrip("/")
          self.client = httpx.AsyncClient(timeout=10.0)
          self._results: List[CheckResult] = []
  
      async def close(self):
          await self.client.aclose()
  
      async def _check(
          self,
          name: str,
          check_fn: Callable,
          timeout: float = 10.0,
      ) -> CheckResult:
          """执行单个检查项"""
          start = time.time()
          try:
              result = await asyncio.wait_for(check_fn(), timeout=timeout)
              if isinstance(result, CheckResult):
                  result.duration_ms = (time.time() - start) * 1000
                  return result
              return CheckResult(
                  name=name,
                  status=CheckStatus.PASS if result else CheckStatus.FAIL,
                  detail=str(result) if isinstance(result, str) else "",
                  duration_ms=(time.time() - start) * 1000,
              )
          except asyncio.TimeoutError:
              return CheckResult(
                  name=name,
                  status=CheckStatus.FAIL,
                  error=f"Timeout after {timeout}s",
                  duration_ms=(time.time() - start) * 1000,
              )
          except Exception as e:
              return CheckResult(
                  name=name,
                  status=CheckStatus.FAIL,
                  error=str(e),
                  duration_ms=(time.time() - start) * 1000,
              )
  
      async def run_all(self) -> ValidationReport:
          """运行所有验证检查"""
          report = ValidationReport()
  
          # 1. 基础服务检查
          report.add(await self._check_health())
          report.add(await self._check_info())
  
          # 2. API 端点可用性
          report.add(await self._check_api_endpoints())
  
          # 3. 核心模块状态
          report.add(await self._check_evolution_engine())
          report.add(await self._check_agent_config())
          report.add(await self._check_bridge_chat())
  
          # 4. 认证系统
          report.add(await self._check_auth())
  
          # 5. 前端页面
          report.add(await self._check_frontend_pages())
  
          return report
  
      async def _check_health(self) -> CheckResult:
          """检查健康端点"""
          async def check():
              resp = await self.client.get(f"{self.base_url}/api/v1/health")
              data = resp.json()
              if resp.status_code != 200:
                  return CheckResult(
                      name="health_endpoint",
                      status=CheckStatus.FAIL,
                      error=f"HTTP {resp.status_code}",
                  )
              services = data.get("services", {})
              offline = [k for k, v in services.items() if not v]
              if offline:
                  return CheckResult(
                      name="health_endpoint",
                      status=CheckStatus.WARN,
                      detail=f"Services offline: {', '.join(offline)}",
                      metadata={"services": services},
                  )
              return CheckResult(
                  name="health_endpoint",
                  status=CheckStatus.PASS,
                  detail=f"All services online: {list(services.keys())}",
                  metadata={"services": services},
              )
          return await self._check("health_endpoint", check)
  
      async def _check_info(self) -> CheckResult:
          """检查系统信息端点"""
          async def check():
              resp = await self.client.get(f"{self.base_url}/api/v1/info")
              data = resp.json()
              required_keys = ["name", "version", "capabilities", "endpoints"]
              missing = [k for k in required_keys if k not in data]
              if missing:
                  return CheckResult(
                      name="info_endpoint",
                      status=CheckStatus.FAIL,
                      error=f"Missing keys: {missing}",
                  )
              return CheckResult(
                  name="info_endpoint",
                  status=CheckStatus.PASS,
                  detail=f"System: {data.get('name')} v{data.get('version')}",
                  metadata=data,
              )
          return await self._check("info_endpoint", check)
  
      async def _check_api_endpoints(self) -> CheckResult:
          """检查关键 API 端点"""
          endpoints = [
              ("agent_teams_overview", "/api/v1/agent-teams/overview"),
              ("evolution_status", "/api/v1/agent-teams/evolution/status"),
              ("evolution_summary", "/api/v1/agent-teams/evolution/summary"),
              ("agent_config_teams", "/api/v1/agent-config/teams"),
              ("agent_config_agents", "/api/v1/agent-config/agents"),
          ]
  
          async def check():
              results = []
              for name, path in endpoints:
                  try:
                      resp = await self.client.get(f"{self.base_url}{path}")
                      if resp.status_code in (200, 404):
                          results.append(f"{name}: HTTP {resp.status_code}")
                      else:
                          results.append(f"{name}: HTTP {resp.status_code} (unexpected)")
                  except Exception as e:
                      results.append(f"{name}: ERROR - {str(e)[:50]}")
  
              failed = [r for r in results if "ERROR" in r or "unexpected" in r]
              if failed:
                  return CheckResult(
                      name="api_endpoints",
                      status=CheckStatus.WARN if len(failed) < len(endpoints) else CheckStatus.FAIL,
                      detail="; ".join(results),
                      metadata={"endpoints_checked": len(endpoints), "failed": len(failed)},
                  )
              return CheckResult(
                  name="api_endpoints",
                  status=CheckStatus.PASS,
                  detail=f"All {len(endpoints)} endpoints reachable",
                  metadata={"endpoints": [e[0] for e in endpoints]},
              )
          return await self._check("api_endpoints", check)
  
      async def _check_evolution_engine(self) -> CheckResult:
          """检查演进引擎状态"""
          async def check():
              resp = await self.client.get(
                  f"{self.base_url}/api/v1/agent-teams/evolution/status"
              )
              if resp.status_code == 404:
                  return CheckResult(
                      name="evolution_engine",
                      status=CheckStatus.FAIL,
                      error="Evolution engine not registered (HTTP 404)",
                  )
              data = resp.json()
              if data.get("status") == "initialized":
                  return CheckResult(
                      name="evolution_engine",
                      status=CheckStatus.PASS,
                      detail=f"Engine initialized with {data.get('audit_rules_count', 0)} rules",
                      metadata=data,
                  )
              return CheckResult(
                  name="evolution_engine",
                  status=CheckStatus.WARN,
                  detail=f"Engine status: {data.get('status', 'unknown')}",
                  metadata=data,
              )
          return await self._check("evolution_engine", check)
  
      async def _check_agent_config(self) -> CheckResult:
          """检查 Agent 配置 API"""
          async def check():
              resp = await self.client.get(f"{self.base_url}/api/v1/agent-config/teams")
              if resp.status_code != 200:
                  return CheckResult(
                      name="agent_config",
                      status=CheckStatus.FAIL,
                      error=f"HTTP {resp.status_code}",
                  )
              data = resp.json()
              teams = data if isinstance(data, list) else data.get("teams", [])
              return CheckResult(
                  name="agent_config",
                  status=CheckStatus.PASS,
                  detail=f"{len(teams)} teams configured",
                  metadata={"teams_count": len(teams)},
              )
          return await self._check("agent_config", check)
  
      async def _check_bridge_chat(self) -> CheckResult:
          """检查聊天通道"""
          async def check():
              resp = await self.client.post(
                  f"{self.base_url}/api/v1/bridge-chat/send",
                  json={
                      "message": "ping",
                      "session_id": "startup_validation",
                      "agent_id": "default_agent",
                  },
              )
              if resp.status_code != 200:
                  return CheckResult(
                      name="bridge_chat",
                      status=CheckStatus.FAIL,
                      error=f"HTTP {resp.status_code}",
                  )
              data = resp.json()
              if "reply" in data:
                  return CheckResult(
                      name="bridge_chat",
                      status=CheckStatus.PASS,
                      detail=f"Chat channel responsive (source: {data.get('source', 'unknown')})",
                      metadata={"source": data.get("source")},
                  )
              return CheckResult(
                  name="bridge_chat",
                  status=CheckStatus.WARN,
                  detail="Chat channel responded but no reply content",
                  metadata=data,
              )
          return await self._check("bridge_chat", check)
  
      async def _check_auth(self) -> CheckResult:
          """检查认证系统"""
          async def check():
              # 检查未认证状态
              resp = await self.client.get(
                  f"{self.base_url}/api/v1/auth/me",
                  headers={"Authorization": ""},
              )
              if resp.status_code != 200:
                  return CheckResult(
                      name="auth_system",
                      status=CheckStatus.FAIL,
                      error=f"Auth me endpoint: HTTP {resp.status_code}",
                  )
              data = resp.json()
              if data.get("authenticated") is False:
                  return CheckResult(
                      name="auth_system",
                      status=CheckStatus.PASS,
                      detail="Auth system working (guest mode)",
                      metadata=data,
                  )
              return CheckResult(
                  name="auth_system",
                  status=CheckStatus.WARN,
                  detail=f"Unexpected auth state: {data}",
                  metadata=data,
              )
          return await self._check("auth_system", check)
  
      async def _check_frontend_pages(self) -> CheckResult:
          """检查前端页面可访问性"""
          pages = [
              ("index", "/"),
              ("login", "/login.html"),
              ("plaza", "/plaza.html"),
              ("system_evolution", "/system-evolution.html"),
              ("agent_team_config", "/agent-team-config.html"),
          ]
  
          async def check():
              results = []
              for name, path in pages:
                  try:
                      resp = await self.client.get(f"{self.base_url}{path}")
                      if resp.status_code == 200:
                          content_type = resp.headers.get("content-type", "")
                          if "text/html" in content_type or "text/plain" in content_type:
                              results.append(f"{name}: OK")
                          else:
                              results.append(f"{name}: HTTP 200 but content-type={content_type}")
                      else:
                          results.append(f"{name}: HTTP {resp.status_code}")
                  except Exception as e:
                      results.append(f"{name}: ERROR - {str(e)[:50]}")
  
              failed = [r for r in results if "ERROR" in r or "HTTP 4" in r or "HTTP 5" in r]
              if failed:
                  return CheckResult(
                      name="frontend_pages",
                      status=CheckStatus.WARN if len(failed) < len(pages) else CheckStatus.FAIL,
                      detail="; ".join(results),
                      metadata={"pages_checked": len(pages), "failed": len(failed)},
                  )
              return CheckResult(
                  name="frontend_pages",
                  status=CheckStatus.PASS,
                  detail=f"All {len(pages)} frontend pages accessible",
                  metadata={"pages": [p[0] for p in pages]},
              )
          return await self._check("frontend_pages", check)
  
  
  # ── 便捷函数 ──
  
  async def validate_startup(
      base_url: str = "http://localhost:8080",
      verbose: bool = True,
  ) -> ValidationReport:
      """执行完整的启动验证"""
      validator = StartupValidator(base_url)
      try:
          report = await validator.run_all()
          if verbose:
              _print_report(report)
          return report
      finally:
    
  ```
  
  ### 文件: `src/backend/tests/conftest.py`
  ```py
  # -*- coding: utf-8 -*-
  """pytest 共享 Fixtures — 测试流水线基础设施."""
  
  from __future__ import annotations
  
  import json
  import os
  import sys
  import tempfile
  from pathlib import Path
  from typing import Any, Dict
  from unittest.mock import AsyncMock, MagicMock, patch
  
  import pytest
  from fastapi.testclient import TestClient
  
  # Ensure src/backend is in path
  _backend_root = Path(__file__).resolve().parent.parent
  if str(_backend_root) not in sys.path:
      sys.path.insert(0, str(_backend_root))
  
  
  @pytest.fixture
  def sample_lamport_clock():
      """提供一个标准的 Lamport 时钟实例."""
      from agents.ab_testing import LamportClock
      return LamportClock(node_id="test-node-1")
  
  
  @pytest.fixture
  def default_ewma_config():
      """提供默认 EWMA 配置."""
      from agents.ab_testing import EWMAConfig
      return EWMAConfig()
  
  
  @pytest.fixture
  def default_ewma_engine(default_ewma_config):
      """提供默认 EWMA 阈值引擎."""
      from agents.ab_testing import EWMAThresholdEngine
      return EWMAThresholdEngine(config=default_ewma_config)
  
  
  @pytest.fixture
  def sample_ab_metrics():
      """提供示例 A/B 测试指标."""
      from agents.ab_testing import ABTestMetrics
      return ABTestMetrics(
          false_upgrade_rate=0.05,
          resource_increase_pct=12.0,
          behavior_fingerprint_mutation_rate=0.02,
          anomaly_propagation_depth=1.5,
          prediction_error_rate=0.08,
          energy_increase_pct=3.0,
          temperature_slope=0.01,
          policy_evaluation_latency_ms=45.0,
          evolution_stagnation_rate=0.03,
      )
  
  
  @pytest.fixture
  def temp_team_store():
      """使用临时文件的 TeamStore (测试后自动清理)."""
      from agents.team_store import TeamStore
  
      with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
          f.write("{}")
          tmp_path = Path(f.name)
  
      store = TeamStore(path=tmp_path)
      yield store
  
      # 清理
      if tmp_path.exists():
          tmp_path.unlink(missing_ok=True)
  
  
  @pytest.fixture
  def temp_task_store():
      """使用临时目录的 TaskStore."""
      from agents.task_store import TaskStore
  
      with tempfile.TemporaryDirectory() as tmpdir:
          store = TaskStore(base_dir=Path(tmpdir))
          yield store
  
  
  @pytest.fixture
  def team_manager(temp_team_store):
      """提供 TeamManager 实例 (使用临时存储)."""
      from agents.team_manager import TeamManager
      # TeamManager() 不接受 store 参数，内部自行创建 TeamStore
      return TeamManager()
  
  
  @pytest.fixture
  def sample_team_dict():
      """示例团队字典."""
      return {
          "team_id": "test-team-001",
          "name": "测试团队",
          "description": "自动化测试团队",
      }
  
  
  @pytest.fixture
  def sample_agent_dict():
      """示例 AgentProfile 字典."""
      return {
          "agent_id": "agent-001",
          "name": "TestAgent",
          "role": "developer",
          "state": "idle",
      }
  
  
  @pytest.fixture
  def sample_model_dict():
      """示例 ModelConfig 字典."""
      return {
          "model_id": "model-001",
          "name": "deepseek-v4-test",
          "provider": "deepseek",
          "max_tokens": 65536,
          "temperature": 0.7,
          "is_default": True,
      }
  
  
  @pytest.fixture
  def task_engine():
      """提供 TaskEngine 实例."""
      from agents.task_engine import TaskEngine
      return TaskEngine(max_concurrency=4)
  
  
  @pytest.fixture
  def fastapi_client() -> TestClient:
      """提供 FastAPI TestClient (自动设置环境变量)."""
      # 确保测试时不连真实 LLM
      os.environ.setdefault("DEEPSEEK_API_KEY", "test-key-not-real")
      os.environ.setdefault("OPENAI_API_KEY", "test-key-not-real")
  
      # Mock 掉 LLM 相关依赖，避免真实请求
      from main import app
      return TestClient(app)
  
  
  @pytest.fixture
  def mock_llm_call():
      """Mock LLM 调用，返回固定响应."""
      with patch("agents.chat_harness.call_llm", new_callable=AsyncMock) as mock:
          mock.return_value = "这是模拟的 LLM 回复"
          yield mock
  
  
  @pytest.fixture
  def sample_task_dict():
      """示例任务字典."""
      return {
          "task_id": "task-001",
          "title": "测试任务",
          "description": "一个用于测试的任务",
          "agent_id": "agent-001",
          "priority": 2,
          "dependencies": [],
      }
  
  
  # ── pytest 配置 ─────────────────────────────────────────────
  
  pytest_plugins = []  # 可在此添加 pytest 插件
  
  ```
  
  ### 文件: `src/backend/agents/skill_registry.py`
  ```py
  # -*- coding: utf-8 -*-
  """AgentsGroup2026 Agent Team Framework — Skill Registry.
  
  Provides default skill definitions across general, digital-twin, and automation
  categories, plus a registry class for runtime skill management.
  """
  
  from __future__ import annotations
  
  from typing import Any, Dict, List, Optional
  
  from .models import SkillCategory, SkillDefinition
  
  
  def get_default_skills() -> List[SkillDefinition]:
      """Return the default catalog of skill definitions."""
  
      SC = SkillCategory
      SD = SkillDefinition
      return [
          # ── General skills ─────────────────────────────────────────────
          SD(
              name="competitive_analysis",
              description="Analyze competitors and market positioning",
              category=SC.GENERAL,
              required_tools=['web_search', 'extract_content'],
              instructions="## 竞品分析\n\n1. 使用 web_search 搜索竞品信息\n2. 提取关键数据：市场份额、产品特性、定价策略\n3. 生成 SWOT 对比矩阵\n4. 输出结构化分析报告"),
          SD(
              name="complex_task_executor",
              description="Break down and execute complex multi-step tasks",
              category=SC.GENERAL,
              required=True,
              required_tools=['run_python', 'run_shell', 'send_message'],
              instructions="## 复杂任务执行\n\n1. 将任务分解为可执行子步骤\n2. 评估每步所需工具和依赖\n3. 按序执行，遇错时回退重试\n4. 汇总结果并报告进度"),
          SD(
              name="content_research_writer",
              description="Research topics and produce written content",
              category=SC.GENERAL,
              required_tools=['web_search', 'extract_content', 'write_file'],
              instructions="## 内容研究与写作\n\n1. 确认主题和目标受众\n2. 使用 web_search 收集资料\n3. 提取关键信息并整理大纲\n4. 撰写结构化内容\n5. 保存到工作区文件"),
          SD(
              name="content_writing",
              description="Write and edit documentation and reports",
              category=SC.GENERAL,
              required_tools=['write_file', 'read_file'],
              instructions="## 文档写作\n\n1. 读取现有文档了解上下文\n2. 根据需求撰写/修改内容\n3. 确保格式规范、语言专业\n4. 保存并通知相关人员"),
          SD(
              name="data_analysis",
              description="Analyze datasets and produce insights",
              category=SC.GENERAL,
              required_tools=['run_python', 'read_file'],
              instructions="## 数据分析\n\n1. 读取数据文件\n2. 使用 Python 进行统计分析\n3. 生成可视化图表\n4. 总结关键发现和趋势\n5. 给出数据驱动的建议"),
          SD(
              name="mcp_installer",
              description="Install and configure MCP server integrations",
              category=SC.GENERAL,
              required=True,
              required_tools=['run_shell', 'write_file', 'read_file'],
              instructions="## MCP 服务器安装\n\n1. 检查目标 MCP 服务器兼容性\n2. 执行安装命令\n3. 配置连接参数\n4. 验证连接状态\n5. 注册到工具目录"),
          SD(
              name="meeting_notes",
              description="Capture and summarize meeting notes",
              category=SC.GENERAL,
              required_tools=['write_file'],
              instructions="## 会议记录\n\n1. 记录参会人员和议题\n2. 按时间线记录讨论要点\n3. 标记决策事项和待办\n4. 生成结构化会议纪要\n5. 分发给相关人员"),
          SD(
              name="skill_creator",
              description="Create new custom skills from descriptions",
              category=SC.GENERAL,
              required=True,
              required_tools=['write_file', 'read_file'],
              instructions="## 技能创建\n\n1. 分析技能需求描述\n2. 确定所需工具和流程\n3. 编写技能指令模板\n4. 创建技能定义文件\n5. 注册到技能目录"),
          SD(
              name="web_research",
              description="Conduct web research and summarize findings",
              category=SC.GENERAL,
              required_tools=['web_search', 'navigate_url', 'extract_content'],
              instructions="## 网络研究\n\n1. 制定搜索策略和关键词\n2. 多轮搜索收集信息\n3. 访问并提取相关页面内容\n4. 交叉验证信息准确性\n5. 生成研究报告"),
          # ── Digital Twin skills ────────────────────────────────────────
          SD(name="dt_camera_control", description="Control digital twin camera views and animations",
              category=SC.DIGITAL_TWIN, required_tools=['dt_camera_move'],
              instructions="## 数字孪生相机控制\n\n使用 dt_camera_move 控制相机位置、目标点和过渡动画。支持预设视角（top/front/side/iso）和自定义坐标。"),
          SD(name="dt_coordinate_system", description="Manage coordinate system transformations",
              category=SC.DIGITAL_TWIN, required_tools=['dt_model_transform'],
              instructions="## 坐标系管理\n\n1. 理解场景坐标系（Y-up，单位:米）\n2. 使用 dt_model_transform 进行平移/旋转/缩放\n3. 处理世界坐标与局部坐标转换"),
          SD(name="dt_model_layout", description="Arrange and layout 3D models in the scene",
              category=SC.DIGITAL_TWIN, required_tools=['dt_model_load', 'dt_model_transform'],
              instructions="## 3D模型布局\n\n1. 加载模型到场景\n2. 调整位置/旋转/缩放\n3. 确保各模型间距和对齐\n4. 设置碰撞体积"),
          SD(name="dt_model_import", description="Import 3D models from various formats",
              category=SC.DIGITAL_TWIN, required_tools=['dt_model_load'],
              instructions="## 模型导入\n\n支持格式: GLB/GLTF/OBJ/FBX。加载模型并设置初始变换。"),
          SD(name="dt_interaction_actions", description="Define interactive inspection paths and actions",
              category=SC.DIGITAL_TWIN, required_tools=['dt_inspection_path', 'dt_camera_move'],
              instructions="## 交互巡检\n\n1. 定义巡检路径航路点\n2. 设置相机飞行速度和模式\n3. 在关键点添加标注和检查项"),
          SD(name="dt_material_change", description="Change materials and textures on models",
              category=SC.DIGITAL_TWIN, required_tools=['dt_material_set'],
              instructions="## 材质修改\n\n使用 dt_material_set 修改颜色/金属度/粗糙度。支持PBR材质参数。"),
          SD(name="dt_physics_simulation", description="Configure and run physics simulations",
              category=SC.DIGITAL_TWIN, required_tools=['dt_physics_toggle'],
              instructions="## 物理模拟\n\n控制重力、碰撞检测和刚体动力学。用于物理模拟和系统分析。"),
          SD(name="dt_lighting_control", description="Control scene lighting and shadows",
              category=SC.DIGITAL_TWIN, required_tools=['dt_light_adjust'],
              instructions="## 灯光控制\n\n调整环境光/方向光/点光源的强度、颜色和位置。支持昼夜模拟。"),
          SD(name="dt_rendering_control", description="Control rendering pipeline and effects",
              category=SC.DIGITAL_TWIN, required_tools=['dt_render_mode'],
              instructions="## 渲染控制\n\n切换实体/线框/X光/热力图模式。用于不同分析场景。"),
  
          # ── Automation skills ──────────────────────────────────────────
          SD(name="auto_report", description="定时生成工作报告",
              category=SC.AUTOMATION, icon="📊", required_tools=['write_file'],
              instructions="## 自动报告\n\n1. 收集系统运行数据\n2. 统计关键指标\n3. 生成结构化报告\n4. 按时发送给相关人员"),
          SD(name="auto_monitor", description="监控系统状态并报警",
              category=SC.AUTOMATION, icon="🔔", required_tools=['schedule_task', 'send_message'],
              instructions="## 自动监控\n\n1. 定期检查系统健康状态\n2. 对比阈值判断异常\n3. 触发告警通知\n4. 记录监控日志"),
          SD(name="workflow_runner", description="运行预定义工作流",
              category=SC.AUTOMATION, icon="▶️", required_tools=['run_python', 'run_shell'],
              instructions="## 工作流执行\n\n1. 解析工作流定义\n2. 按步骤执行任务\n3. 处理条件分支\n4. 汇报执行结果"),
          # ── Research skills ─────────────────────────────
          SD(name="cross_session_recall", description="跨会话研究回溯",
              category=SC.RESEARCH, icon="🔍", required_tools=['session_search', 'memory_read'],
              instructions="## 跨会话回溯\n\n1. 搜索历史会话\n2. 提取相关研究发现\n3. 整理知识脉络\n4. 避免重复研究"),
  
          # ── Build Team / PM skills ─────────────────────────────────────
          SD(name="task_decomposition", description="将复杂任务分解为可执行子任务并分配给团队成员",
              category=SC.GENERAL, icon="📋",
              required_tools=['send_message'],
              config_schema={
                  "max_subtasks": {"type": "integer", "default": 10, "description": "最大子任务数"},
                  "auto_assign": {"type": "boolean", "default": True, "description": "自动分配给最佳Agent"},
              },
              instructions="## 任务分解\n\n1. 分析任务目标和范围\n2. 识别关键交付物和里程碑\n3. 将任务分解为 3-10 个可执行子任务\n4. 为每个子任务指定负责Agent和优先级\n5. 设置依赖关系和完成标准\n6. 通过 TaskEngine 提交子任务"),
          SD(name="progress_tracking", description="跟踪项目进度、识别风险和阻塞点",
              category=SC.GENERAL, icon="📊",
              required_tools=['read_file', 'send_message'],
              instructions="## 进度跟踪\n\n1. 查询 TaskEngine 获取任务状态\n2. 计算完成率和延迟风险\n3. 识别阻塞任务和依赖链\n4. 生成进度报告\n5. 向相关Agent发送更新"),
          SD(name="blocker_resolution", description="识别和解决项目阻塞问题",
              category=SC.GENERAL, icon="🔓",
              required_tools=['send_message'],
              instructions="## 阻塞解决\n\n1. 分析阻塞原因\n2. 确定解决方案\n3. 协调相关Agent\n4. 重新分配资源\n5. 更新任务状态"),
          # ── Build Team / Researcher skills ─────────────────────────────
          SD(name="requirements_analysis", description="分析需求文档，提取功能和非功能需求",
              category=SC.GENERAL, icon="📝",
              required_tools=['read_file', 'web_search'],
              instructions="## 需求分析\n\n1. 阅读需求文档\n2. 提取功能需求清单\n3. 识别非功能需求\n4. 标记歧义和缺失项\n5. 生成需求矩阵"),
          # ── Build Team / Architect skills ──────────────────────────────
          SD(name="architecture_design", description="设计系统架构，定义分层和模块边界",
              category=SC.GENERAL, icon="🏗",
              required_tools=['read_file', 'write_file'],
              instructions="## 架构设计\n\n1. 分析需求和约束\n2. 选择架构风格\n3. 定义模块边界和接口\n4. 绘制架构图\n5. 编写 ADR 文档"),
          SD(name="interface_definition", description="定义模块间API接口和数据契约",
              category=SC.GENERAL, icon="🔌",
              required_tools=['write_file', 'read_file'],
              instructions="## 接口定义\n\n1. 确定通信协议\n2. 定义请求/响应模型\n3. 编写 OpenAPI/JSON Schema\n4. 生成接口文档"),
          SD(name="pattern_selection", description="选择适合的设计模式和技术方案",
              category=SC.GENERAL, icon="🧩",
              required_tools=['web_search', 'read_file'],
              instructions="## 模式选择\n\n1. 分析问题场景\n2. 匹配候选设计模式\n3. 评估优劣权衡\n4. 记录选型理由"),
          # ── Build Team / Developer skills ──────────────────────────────
          SD(name="code_implementation", description="编写功能代码，实现需求规格",
              category=SC.GENERAL, icon="💻",
              required_tools=['run_shell', 'write_file', 'read_file'],
              config_schema={
                  "executor": {"type": "string", "default": "claude_code",
                      "enum": ["claude_code", "llm_chat", "manual"],
                      "description": "执行器: claude_code=本地Claude Code, llm_chat=LLM生成, manual=手动编码"},
                  "claude_code_path": {"type": "string", "default": "claude",
                      "description": "Claude Code CLI 路径"},
                  "working_directory": {"type": "string", "default": "",
                      "description": "工作目录 (空=项目根)"},
                  "auto_test": {"type": "boolean", "default": True,
                      "description": "实现后自动运行测试"},
                  "language": {"type": "string", "default": "python",
                      "enum": ["python", "javascript", "typescript"],
                      "description": "主要编程语言"},
              },
              config={
                  "executor": "claude_code",
                  "claude_code_path": "claude",
                  "working_directory": "",
                  "auto_test": True,
                  "language": "python",
              },
              instructions="## 代码实现\n\n1. 阅读任务描述和架构设计\n2. 确定要修改的文件和模块\n3. 编写实现代码\n4. 运行相关测试确保无回归\n5. 提交代码变更\n\n### 执行器模式\n- **claude_code**: 调用本地 Claude Code CLI 执行编码任务\n- **llm_chat**: 通过 LLM API 生成代码\n- **manual**: 生成任务描述供人工编码"),
          SD(name="debugging", description="诊断和修复代码缺陷",
              category=SC.GENERAL, icon="🐛",
              required_tools=['run_shell', 'read_file', 'write_file'],
              instructions="## 调试\n\n1. 复现问题\n2. 分析日志和堆栈\n3. 定位 root cause\n4. 编写修复代码\n5. 验证修复并添加回归测试"),
          SD(name="refactoring", description="重构代码提升可维护性和性能",
              category=SC.GENERAL, icon="♻️",
              required_tools=['read_file', 'write_file', 'run_shell'],
              instructions="## 代码重构\n\n1. 识别代码坏味道\n2. 选择重构策略\n3. 小步修改，保持测试绿色\n4. 验证功能无变化"),
          SD(name="testing", description="编写和执行单元测试",
              category=SC.GENERAL, icon="✅",
              required_tools=['run_shell', 'write_file', 'read_file'],
              instructions="## 测试编写\n\n1. 分析待测代码\n2. 设计测试用例\n3. 编写 pytest 测试\n4. 运行并确认通过"),
          # ── Build Team / Tester skills ─────────────────────────────────
          SD(name="test_design", description="设计测试策略和测试用例",
              category=SC.GENERAL, icon="📐",
              required_tools=['read_file', 'write_file'],
              instructions="## 测试设计\n\n1. 分析功能规格\n2. 设计边界值和等价类\n3. 编写测试矩阵\n4. 确定自动化优先级"),
          SD(name="test_execution", description="执行测试套件并分析结果",
              category=SC.GENERAL, icon="▶️",
              required_tools=['run_shell', 'read_file'],
              instructions="## 测试执行\n\n1. 运行 pytest 测试套件\n2. 收集测试结果\n3. 分析失败用例\n4. 生成测试报告"),
          SD(name="coverage_analysis", description="分析代码覆盖率并识别盲区",
              category=SC.GENERAL, icon="📈",
              required_tools=['run_shell', 'read_file'],
              instructions="## 覆盖率分析\n\n1. 运行 pytest --cov\n2. 分析行覆盖和分支覆盖\n3. 识别未覆盖代码\n4. 建议补充测试"),
          SD(name="regression_testing", description="回归测试确保修改未引入新缺陷",
              category=SC.GENERAL, icon="🔄",
              required_tools=['run_shell'],
              instructions="## 回归测试\n\n1. 确定修改影响范围\n2. 运行相关测试子集\n3. 全量测试验证\n4. 对比前后结果"),
          # ── Build Team / Deployer skills ───────────────────────────────
          SD(name="build_automation", description="自动化构建和打包流程",
              category=SC.GENERAL, icon="🔨",
              required_tools=['run_shell', 'write_file'],
              instructions="## 构建自动化\n\n1. 配置构建脚本\n2. 执行构建命令\n3. 验证产物完整性\n4. 生成构建报告"),
          SD(name="container_management", description="Docker容器构建和管理",
              category=SC.GENERAL, icon="🐳",
              required_tools=['run_shell', 'write_file'],
              instructions="## 容器管理\n\n1. 编写 Dockerfile\n2. 构建镜像\n3. 管理容器生命周期\n4. 配置网络和卷"),
          SD(name="deployment_orchestration", description="编排部署流程和环境管理",
              category=SC.GENERAL, icon="🚀",
              required_tools=['run_shell', 'write_file', 'read_file'],
              instructions="## 部署编排\n\n1. 选择部署策略\n2. 配置环境变量\n3. 执行部署脚本\n4. 验证服务状态"),
          # ── Build Team / Doc Writer skills ─────────────────────────────
          SD(name="technical_writing", description="编写技术文档和开发指南",
              category=SC.GENERAL, icon="📖",
              required_tools=['read_file', 'write_file'],
              instructions="## 技术写作\n\n1. 阅读源代码和注释\n2. 整理技术要点\n3. 编写开发者文档\n4. 添加示例代码"),
          SD(name="api_documentation", description="生成和维护 API 文档",
              category=SC.GENERAL, icon="📄",
              required_tools=['read_file', 'write_file'],
              instructions="## API 文档\n\n1. 扫描 API 端点\n2. 提取参数和返回值\n3. 编写使用示例\n4. 生成 OpenAPI 规格"),
          SD(name="changelog_management", description="维护变更日志和版本记录",
              category=SC.GENERAL, icon="📝",
              required_tools=['read_file', 'write_file'],
              instructions="## 变更日志\n\n1. 收集代码变更\n2. 按类别分组\n3. 编写变更描述\n4. 更新版本号"),
      ]
  
  
  class SkillRegistry:
      """Runtime registry for managing skills."""
  
      def __init__(self) -> None:
          self._skills: Dict[str, SkillDefinition] = {}
  
      def load_defaults(self) -> None:
          """Load all default skills into the registry."""
          for skill in get_default_skills():
              self._skills[skill.skill_id] = skill
  
      def register(self, skill: SkillDefinition) -> None:
          """Regist
  ```
  
  ### 文件: `src/backend/agents/teams/ai_coding_team.py`
  ```py
  # -*- coding: utf-8 -*-
  """AI 编程团队 — 专注软件开发的智能体团队."""
  
  from ..models import (
      AccessLevel, AgentChannelConfig, AgentPermission, AgentPersonality,
      AgentProfile, AgentTeam, ModelConfig, AgentTemplateType, Visibility,
  )
  
  
  def _model_deepseek() -> ModelConfig:
      return ModelConfig(
          model_id="deepseek", provider="deepseek", name="deepseek-v4-flash",
          max_tokens=8192, temperature=0.2, is_default=True,
          api_base_url="https://api.deepseek.com",
      )
  
  
  def _agent_pm() -> AgentProfile:
      return AgentProfile(
          agent_id="coding_pm", name="项目经理", role="project_manager",
          description="负责需求分析、任务拆解、进度跟踪和团队协调",
          template_type=AgentTemplateType.COORDINATOR,
          model_id="deepseek",
          system_prompt=(
              "你是 AI 编程团队的项目经理。你的职责是：\n"
              "1. 分析用户需求，将其拆解为可执行的开发任务\n"
              "2. 协调团队成员的工作，合理分配任务\n"
              "3. 跟踪项目进度，识别和解决阻塞问题\n"
              "4. 组织代码评审和技术讨论\n"
              "5. 确保交付质量符合预期\n"
              "请用中文回答，保持专业、简洁、有条理。"
          ),
          personality=AgentPersonality(
              tone="directive", language="zh-CN",
              expertise_areas=["project_management", "requirements_analysis", "agile", "task_decomposition"],
              response_style="structured", creativity=0.3,
          ),
          permissions=[
              AgentPermission(resource="tasks", access_level=AccessLevel.ADMIN, channels=["coding_bus"]),
              AgentPermission(resource="agents", access_level=AccessLevel.WRITE, channels=["coding_bus"]),
          ],
          channels=[
              AgentChannelConfig(channel_name="coding_bus", subscribe=True, publish=True, priority=10),
              AgentChannelConfig(channel_name="status_reports", subscribe=True, publish=True),
          ],
          skills=["task_decomposition", "progress_tracking", "blocker_resolution", "requirements_analysis"],
          metadata={
              "traits": ["organized", "decisive", "communicative"],
              "behavior_boundaries": ["no_code_changes", "delegate_only"],
          },
      )
  
  
  def _agent_researcher() -> AgentProfile:
      return AgentProfile(
          agent_id="coding_researcher", name="技术研究员", role="researcher",
          description="负责技术选型、方案调研、最佳实践研究和可行性分析",
          template_type=AgentTemplateType.RESEARCHER,
          model_id="deepseek",
          system_prompt=(
              "你是 AI 编程团队的技术研究员。你的职责是：\n"
              "1. 调研技术方案，对比不同框架和工具的优劣\n"
              "2. 研究行业最佳实践和设计模式\n"
              "3. 分析技术可行性，评估实现风险\n"
              "4. 提供详细的技术报告和建议\n"
              "5. 跟踪最新技术动态，推荐合适的技术栈\n"
              "请用中文回答，注重数据和事实，分析要深入全面。"
          ),
          personality=AgentPersonality(
              tone="analytical", language="zh-CN",
              expertise_areas=["technology_research", "architecture_analysis", "best_practices", "feasibility_study"],
              response_style="detailed", creativity=0.6,
          ),
          permissions=[
              AgentPermission(resource="docs", access_level=AccessLevel.WRITE, channels=["coding_bus"]),
              AgentPermission(resource="web", access_level=AccessLevel.READ),
          ],
          channels=[
              AgentChannelConfig(channel_name="coding_bus", subscribe=True, publish=True, priority=5),
              AgentChannelConfig(channel_name="research_findings", subscribe=False, publish=True),
          ],
          skills=["web_research", "competitive_analysis", "requirements_analysis", "architecture_design"],
          metadata={
              "traits": ["curious", "thorough", "analytical"],
              "behavior_boundaries": ["read_only_code", "report_findings"],
          },
      )
  
  
  def _agent_developer() -> AgentProfile:
      return AgentProfile(
          agent_id="coding_developer", name="全栈开发", role="developer",
          description="负责编写代码、实现功能、修复 Bug 和代码优化",
          template_type=AgentTemplateType.DEVELOPER,
          model_id="deepseek",
          system_prompt=(
              "你是 AI 编程团队的全栈开发工程师。你的职责是：\n"
              "1. 根据需求和架构设计编写高质量代码\n"
              "2. 实现前后端功能，确保代码可维护、可测试\n"
              "3. 修复 Bug，优化性能\n"
              "4. 编写清晰的代码注释和技术文档\n"
              "5. 参与代码评审，持续改进代码质量\n"
              "技术栈：Python, FastAPI, JavaScript, HTML/CSS, SQL\n"
              "请用中文回答，代码要规范、高效、安全。"
          ),
          personality=AgentPersonality(
              tone="pragmatic", language="zh-CN",
              expertise_areas=["python", "javascript", "fastapi", "fullstack", "database"],
              response_style="concise", creativity=0.4,
          ),
          permissions=[
              AgentPermission(resource="code", access_level=AccessLevel.WRITE, channels=["coding_bus"]),
              AgentPermission(resource="tests", access_level=AccessLevel.WRITE),
          ],
          channels=[
              AgentChannelConfig(channel_name="coding_bus", subscribe=True, publish=True, priority=7),
              AgentChannelConfig(channel_name="code_reviews", subscribe=True, publish=True),
          ],
          skills=["code_generation", "debugging", "refactoring", "code_review", "api_development"],
          metadata={
              "traits": ["detail_oriented", "efficient", "reliable"],
              "behavior_boundaries": ["follow_architecture", "write_tests"],
          },
      )
  
  
  def _agent_tester() -> AgentProfile:
      return AgentProfile(
          agent_id="coding_tester", name="测试工程师", role="qa_engineer",
          description="负责测试用例设计、自动化测试、质量保障和缺陷跟踪",
          template_type=AgentTemplateType.ANALYST,
          model_id="deepseek",
          system_prompt=(
              "你是 AI 编程团队的测试工程师。你的职责是：\n"
              "1. 设计全面的测试用例，覆盖功能、边界和异常场景\n"
              "2. 编写自动化测试脚本（单元测试、集成测试）\n"
              "3. 执行测试并生成详细的测试报告\n"
              "4. 跟踪和管理缺陷，确保问题被修复\n"
              "5. 评估测试覆盖率，持续提升质量标准\n"
              "请用中文回答，测试要严谨全面，报告要清晰明确。"
          ),
          personality=AgentPersonality(
              tone="meticulous", language="zh-CN",
              expertise_areas=["testing", "pytest", "automation", "quality_assurance"],
              response_style="detailed", creativity=0.3,
          ),
          permissions=[
              AgentPermission(resource="tests", access_level=AccessLevel.WRITE, channels=["coding_bus"]),
              AgentPermission(resource="code", access_level=AccessLevel.READ),
          ],
          channels=[
              AgentChannelConfig(channel_name="coding_bus", subscribe=True, publish=True, priority=6),
              AgentChannelConfig(channel_name="test_results", subscribe=False, publish=True),
          ],
          skills=["test_design", "test_execution", "coverage_analysis", "regression_testing", "debugging"],
          metadata={
              "traits": ["skeptical", "thorough", "patient"],
              "behavior_boundaries": ["no_prod_changes", "report_all_failures"],
          },
      )
  
  
  def create_ai_coding_team() -> AgentTeam:
      """创建 AI 编程团队."""
      team = AgentTeam(
          team_id="ai_coding",
          name="AI 编程团队",
          description="专注软件开发的智能体团队，包含项目经理、技术研究员、全栈开发和测试工程师",
          visibility=Visibility.INTERNAL,
          metadata={"team_type": "coding"},
      )
      team.add_model(_model_deepseek())
      for a in [_agent_pm(), _agent_researcher(), _agent_developer(), _agent_tester()]:
          team.add_agent(a)
      return team
  
  ```
  
  ### 文件: `src/backend/channels/bridge_chat.py`
  ```py
  # -*- coding: utf-8 -*-
  """
  Bridge Chat Channel - 驾驶台智能对话模块
  
  实现驾驶台自然语言交互接口:
  - 中英文双语意图识别
  - 多 Channel 数据路由与整合
  - 模板化智能回复生成
  - 会话上下文管理
  """
  
  from __future__ import annotations
  
  import logging
  import time
  from collections import deque
  from dataclasses import dataclass, field
  from datetime import datetime
  from typing import Any, Dict, List, Optional, Tuple
  
  from .marine_base import MarineChannel, ChannelStatus, ChannelPriority
  
  logger = logging.getLogger(__name__)
  
  
  # ==================== 意图定义 ====================
  
  _INTENT_RULES: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
      ("navigation", (
          "航向", "航速", "位置", "经纬度", "导航",
          "heading", "course", "speed", "sog", "cog", "position", "navigate", "gps",
      )),
      ("colregs", (
          "避碰", "碰撞", "会遇", "让路",
          "colregs", "collision", "cpa", "tcpa", "encounter",
      )),
      ("route", (
          "航线", "路线", "航程", "计划",
          "route", "voyage", "waypoint", "eta",
      )),
      ("engine", (
          "主机", "引擎", "机舱", "转速", "燃油",
          "engine", "rpm", "fuel",
      )),
      ("weather", (
          "天气", "风速", "风向", "浪高", "气压", "台风", "气象", "能见度",
          "weather", "wind", "wave", "sea state",
      )),
      ("ais", (
          "目标船", "周围船舶", "船舶识别", "附近",
          "ais", "target", "vessel", "mmsi",
      )),
      ("alarm", (
          "报警", "告警", "警报", "消音", "确认报警",
          "alarm", "alert", "acknowledge",
      )),
      ("autopilot", (
          "自动舵", "舵角", "转向", "航向保持", "偏航",
          "autopilot", "rudder", "heading hold",
      )),
      ("attitude", (
          "姿态", "横摇", "纵摇", "升沉", "减摇", "稳定",
          "roll", "pitch", "heave", "rcs", "foil", "trim tab",
      )),
      ("safety", (
          "安全", "消防", "水密", "进水", "灭火", "烟雾",
          "safety", "fire", "watertight", "temperature",
      )),
      ("energy", (
          "能效", "排放", "碳排放", "油耗优化",
          "energy", "eexi", "cii", "eedi", "emission", "co2",
      )),
      ("mob", (
          "落水", "人员落水", "搜救", "救援",
          "mob", "man overboard", "overboard",
      )),
  )
  
  
  # ==================== 回复模板 ====================
  
  _REPLY_TEMPLATES: Dict[str, str] = {
      "navigation": "当前航向 {course}°T, 航速 {speed} kn, 位置 {lat}°N / {lon}°E。",
      "colregs": "碰撞风险评估: {risk_count} 个目标在监控中, 最高风险等别: {max_risk}。{detail}",
      "route": "当前航线: {route_name}, 距下一航路点 {dist_wp} nm, ETA {eta}。",
      "engine": "主机状态: {engine_status}, 转速 {rpm} RPM, 功率 {power} kW, 油耗 {fuel_rate} L/h。",
      "weather": "天气概况: 风 {wind_dir}° / {wind_speed} kn, 浪高 {wave_height} m, 气压 {pressure} hPa。",
      "ais": "AIS 监控范围内共 {target_count} 个目标, 最近目标 MMSI {nearest_mmsi}, 距离 {nearest_range} nm。",
      "alarm": "当前活跃报警 {active_count} 条。 {alarm_summary}",
      "autopilot": "自动舵状态: {ap_mode}, 设定航向 {set_heading}°, 偏差 {deviation}°, 舵角 {rudder}°。",
      "attitude": "姿态数据: 横摇 {roll}°, 纵摇 {pitch}°, 升沉 {heave} m。减摇系统: {rcs_status}。",
      "safety": "安全系统状态: {safety_status}。消防分区 {fire_zones} 正常, {safety_detail}",
      "energy": "能效评级: EEXI {eexi}, CII {cii}。当前碳排放强度 {co2_intensity} gCO₂/t·nm。",
      "mob": "MOB 状态: {mob_status}。{mob_detail}",
      "general": "系统综合状态: {channel_ok}/{channel_total} 模块正常运行。{summary}",
  }
  
  _SUGGESTIONS: Dict[str, List[str]] = {
      "navigation": ['查看周围AIS目标', '显示当前航线', '检查避碰态势'],
      "colregs": ['显示CPA/TCPA详情', '查看目标船信息', '检查航向建议'],
      "route": ['查看天气预报', '优化航线能效', '显示航路点列表'],
      "engine": ['检查机舱报警', '查看油耗趋势', '维护计划'],
      "weather": ['查看航线天气', '检查台风路径', '更新气象信息'],
      "ais": ['查看碰撞风险', '显示目标详情', '导航态势概览'],
      "alarm": ['确认/消音报警', '查看报警历史', '安全系统状态'],
      "autopilot": ['切换手动/自动', '调整航向', '检查舵机状态'],
      "attitude": ['减摇系统详情', '调整舒适模式', '查看运动统计'],
      "safety": ['消防分区详情', '水密舱状态', '应急预案'],
      "energy": ['CII改善方案', '燃油消耗统计', '排放合规文档'],
      "mob": ['搜救圈范围', '漂流估算', '通知岸基'],
      "general": ['导航状态', '机舱概览', '安全报警汇总'],
  }
  
  _INTENT_CHANNEL_MAP: Dict[str, str] = {
      "navigation": "intelligent_navigation",
      "colregs": "colregs_brain",
      "route": "route_optimizer",
      "engine": "intelligent_engine",
      "weather": "weather_routing",
      "ais": "ais_processor",
      "alarm": "alarm_management",
      "autopilot": "autopilot_monitor",
      "attitude": "wpc_attitude_control",
      "safety": "safety_system_monitor",
      "energy": "energy_efficiency_channel",
      "mob": "man_overboard",
  }
  
  
  # ==================== 单条对话消息 ====================
  
  @dataclass
  class ChatMessage:
      """单条对话消息."""
      role: str              # "user" | "assistant"
      content: str
      intent: str = ""
      timestamp: datetime = field(default_factory=datetime.now)
  
  
  # ==================== Channel ====================
  
  class BridgeChatChannel(MarineChannel):
      """驾驶台智能对话 Channel.
  
      实现驾驶台自然语言交互接口,
      模板化智能回复生成.
      """
  
      name = "bridge_chat"
      description = "驾驶台智能对话 (Bridge Chat)"
      version = "1.0.0"
      priority = ChannelPriority.P1
      dependencies: List[str] = []
  
      MAX_HISTORY = 100
  
      def __init__(self, channel_registry: Optional[Dict[str, Any]] = None, **kwargs):
          super().__init__(**kwargs)
          self._channel_registry: Dict[str, Any] = channel_registry or {}
          self._sessions: Dict[str, deque] = {}
          self._total_messages: int = 0
          self._intent_stats: Dict[str, int] = {}
  
      # -- MarineChannel interface --
  
      def initialize(self) -> bool:
          self._set_health(ChannelStatus.OK, "Bridge Chat ready")
          self._initialized = True
          return True
  
      def get_status(self) -> Dict[str, Any]:
          return {
              "name": self.name,
              "status": self._health.status.value,
              "sessions": len(self._sessions),
              "total_messages": self._total_messages,
              "intent_stats": dict(self._intent_stats),
              "registry_channels": list(self._channel_registry.keys()),
          }
  
      def shutdown(self) -> bool:
          self._sessions.clear()
          self._set_health(ChannelStatus.OFF, "Shutdown")
          return True
  
      # -- process_event --
  
      async def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
          t0 = time.monotonic()
          msg = (event.get("message") or "").strip()
          session_id = event.get("session_id") or "default"
          lang = event.get("lang") or self._detect_lang(msg)
  
          if not msg:
              return self._empty_reply(lang)
  
          intent = self._classify_intent(msg, session_id)
          self._intent_stats[intent] = self._intent_stats.get(intent, 0) + 1
  
          self._append_history(session_id, ChatMessage(role="user", content=msg, intent=intent))
  
          channel_data, sources = self._fetch_channel_data(intent)
          reply_text = self._build_reply(intent, channel_data, lang)
          urgency = self._assess_urgency(intent, channel_data)
          suggestions = self._get_suggestions(intent, lang)
  
          self._append_history(session_id, ChatMessage(role="assistant", content=reply_text, intent=intent))
          self._total_messages += 1
  
          elapsed_ms = (time.monotonic() - t0) * 1000
          self._record_call(True, elapsed_ms)
  
          return {
              "reply": reply_text,
              "intent": intent,
              "sources": sources,
              "suggestions": suggestions,
              "urgency": urgency,
              "session_id": session_id,
              "elapsed_ms": round(elapsed_ms, 1),
          }
  
      # -- Intent classification --
  
      def _classify_intent(self, message: str, session_id: str = "default") -> str:
          lower = message.lower()
          best_intent = "general"
          best_score = 0
          for intent, keywords in _INTENT_RULES:
              score = sum(1 for kw in keywords if kw in lower)
              if score > best_score:
                  best_score = score
                  best_intent = intent
          if best_score == 0:
              best_intent = self._context_intent(session_id)
          return best_intent
  
      def _context_intent(self, session_id: str) -> str:
          history = self._sessions.get(session_id)
          if not history:
              return "general"
          for msg in reversed(history):
              if msg.role == "user" and msg.intent and msg.intent != "general":
                  return msg.intent
          return "general"
  
      # -- Channel data fetch --
  
      def _fetch_channel_data(self, intent: str) -> Tuple[Dict[str, Any], List[str]]:
          sources: List[str] = []
          data: Dict[str, Any] = {}
          channel_name = _INTENT_CHANNEL_MAP.get(intent)
          if channel_name and channel_name in self._channel_registry:
              ch = self._channel_registry[channel_name]
              try:
                  status = ch.get_status() if hasattr(ch, "get_status") else {}
                  data.update(status)
                  # Flatten nested dicts so template fillers can find keys like wind_speed
                  for v in list(status.values()):
                      if isinstance(v, dict):
                          data.update(v)
                  sources.append(channel_name)
              except Exception as exc:
                  logger.warning("Failed to get status from %s: %s", channel_name, exc)
                  data["_error"] = str(exc)
          if intent == "general":
              data, sources = self._fetch_overview()
          return data, sources
  
      def _fetch_overview(self) -> Tuple[Dict[str, Any], List[str]]:
          sources: List[str] = []
          overview: Dict[str, Any] = {"channel_ok": 0, "channel_total": 0}
          for ch_name, ch in self._channel_registry.items():
              overview["channel_total"] += 1
              try:
                  st = ch.get_status() if hasattr(ch, "get_status") else {}
                  status_val = st.get("status", "unknown")
                  if status_val in ("ok", "running", ChannelStatus.OK):
                      overview["channel_ok"] += 1
                  sources.append(ch_name)
              except Exception:
                  pass
          overview["summary"] = f"{overview['channel_ok']}/{overview['channel_total']} channels healthy."
          return overview, sources
  
      # -- Reply generation --
  
      def _build_reply(self, intent: str, data: Dict[str, Any], lang: str = "zh") -> str:
          fillers = self._extract_fillers(intent, data)
          template = _REPLY_TEMPLATES.get(intent, _REPLY_TEMPLATES["general"])
          try:
              reply = template.format_map(_SafeFormatDict(fillers))
          except Exception:
              reply = template
          if lang == "en":
              reply = self._translate_key_terms(reply)
          return reply
  
      def _extract_fillers(self, intent: str, data: Dict[str, Any]) -> Dict[str, Any]:
          d = _SafeFormatDict(data)
          extractors = {
              "navigation": lambda: {
                  "course": d.get("course", d.get("heading", "--")),
                  "speed": d.get("speed", d.get("sog", "--")),
                  "lat": d.get("latitude", d.get("lat", "--")),
             
  ```
  
  (后续文件因 token 预算已省略)
  
  ## 要求
  1. 分析任务需求，拆解为可执行的子步骤
  2. 识别技术风险和依赖关系
  3. 为后续研究人员、架构师、开发者提供清晰的指导
  4. 输出一份结构化的任务分解文档 (Markdown 格式)
  
  ## ⚠️ 重要提示
  系统已自动预加载项目文件结构和相关源文件（见下方 📂 项目上下文）。
  请基于**实际存在的文件**进行分析，不要猜测文件名。
  
  项目根目录: /Users/panglaohu/Downloads/DoubleBoatClawSystem
  后端: src/backend/ (Python FastAPI)
  前端: src/frontend/ (HTML + JS)
  
  
  项目根目录: /Users/panglaohu/Downloads/AgentsGroup2026
  后端: src/backend/ (Python FastAPI)
  前端: src/frontend/ (HTML + JS)
  
────────────────────────────────────────────────────────────
⚡ 使用 DeepSeek V4 直连 (64K 输出, 流式)...

🔗 API: api.deepseek.com | 模型: deepseek-v4-pro
────────────────────────────────────────────────────────────

# 指纹计算模块 — 任务分解与开发规划

**PM:** AgentsGroup2026 项目组  
**状态:** 待开发  
**对象:** 全栈开发、架构师、研究员  

---

## 1. 业务背景与目标

在 **AgentsGroup2026** 系统中，需要持续监控智能体的行为一致性，用于 A/B 测试、异常检测与演化评估。当前 `ab_testing` 模块已经定义了 `behavior_fingerprint_mutation_rate` 等指标，但缺少一个稳定、可复现的 **指纹计算模块**。

本任务要求实现：

1. **模板提取**  
   从 Agent 配置、提示词、工具调用序列等静态/半静态信息中抽取“骨架”，排除动态噪声。

2. **动态变量剔除**  
   识别并消除时间戳、随机种子、临时会话 ID、内存地址等运行时变量。

3. **精确哈希**  
   对处理后的规范化数据进行确定性哈希（SHA-256）生成唯一指纹。

4. **自检与稳定性监控埋点**  
   提供指纹自检能力（如多次计算应一致），并向监控系统上报稳定性指标。

---

## 2. 模块定位与架构概览

拟在 `src/backend/monitoring/` 下新增 **指纹计算引擎**，复用现有监控基础设施。

```
src/backend/monitoring/
├── fingerprint_builder.py          # 核心：模板提取、剔除、哈希
├── fingerprint_monitor.py          # 自检 + 稳定性监控埋点
└── models.py (已存在)              # 扩展监控模型，增加指纹相关指标
```

**依赖关系：**
- 读取 `agents/ab_testing.py`、`agents/models.py`、`agents/team_store.py` 中的 Agent 配置与行为快照。
- 输出指纹给 `ab_testing` 用于变异率计算。
- 通过 `monitoring/collector.py` 上报稳定性指标。

---

## 3. 子任务分解

以下 5 个子任务按依赖顺序排列，每个子任务均包含明确的输入、输出、技术要求和回归测试点。

### 3.1 架构设计与接口定义

**负责人:** 架构师（可兼研究员）  
**预估工时:** 0.5 人天  
**前置依赖:** 无  
**输出物:**
- `fingerprint_interface.py` 或集成于 `models.py` 中的协议定义
- 数据流图更新（Markdown）

**具体内容：**
```python
class FingerprintSource(TypedDict):
    agent_id: str
    system_prompt: str
    tool_signatures: List[str]  # 工具名+参数签名
    skill_ids: List[str]
    permissions: List[str]
    channels: List[str]
    team_id: str
    model_config_snapshot: dict
    # 以及其他可配置静态字段

class FingerprintResult:
    hash_value: str
    source_hash: str         # 源数据规范化后的哈希
    excluded_dynamics: List[str]  # 被剔除的动态变量名
    template_version: int    # 模板提取算法的版本号
```

**注意：** 确保接口同时兼容同步调用（给任务引擎）和异步上报（给监控）。

---

### 3.2 模板提取模块

**负责人:** 开发者  
**预估工时:** 1 人天  
**输入:** AgentProfile, AgentTeam 等模型对象或序列化 JSON  
**输出:** 规范化字典 `normalized_template`（顺序确定、无动态值）

**功能点：**
1. **白名单字段提取**  
   仅从 `AgentProfile` 中选取稳定字段：`agent_id`, `system_prompt`, `skills`, `permissions`, `channels`, `model_id`, `team_id`, `personality.traits`, `response_style` 等。  
   忽略 `description`（可能人为修改频繁）、`metadata` 中的非结构化字段。

2. **排序与标准化**  
   - 所有列表字段（如 `skills`, `channels`）按字母排序；  
   - 字典字段按键排序后递归处理；  
   - 去除冗余空白、统一缩进（可选）。

3. **版本标记**  
   返回的模板必须包含 `template_version`，当字段选择逻辑变化时可递增，以便追踪。

**验收标准：**  
- 对同一 Agent 多次调用返回完全相同的字典（序列化后 SHA256 一致）。  
- 对仅有 `description`、`temperature` 等变化的 Agent，模板保持一致。

---

### 3.3 动态变量剔除

**负责人:** 开发者  
**预估工时:** 0.75 人天  
**输入:** 从运行日志或事件中采集的原始数据（如工具调用序列、响应时间序列）  
**输出:** 清洗后、无噪音的规范化数据列表

**处理策略：**
1. **时间戳归一化**  
   将所有 `datetime`、`timestamp(ms)` 统一替换为固定占位符：`"<TS>"`。

2. **随机值剔除**  
   匹配 UUID、random seed、non‑deterministic IDs（如 `session_id`, `trace_id`） → 替换为 `"<RAND>"`。

3. **可配置剔除规则**  
   通过字典配置需剔除的字段路径，例如：
   ```python
   EXCLUDE_PATHS = [
       ("execution_id",),
       ("context", "request_id"),
   ]
   ```

4. **保留结构骨架**  
   即使值被替换，列表长度、嵌套层级仍应保留，以维持结构指纹。

**验收标准：**  
- 同一事件的多次采样（时间不同、随机种子不同）产生完全一致的清洗后结构。  
- 剔除列表可审计（��过 `FingerprintResult.excluded_dynamics` 记录）。

---

### 3.4 精确哈希计算

**负责人:** 开发者  
**预估工时:** 0.5 人天  
**输入:** 规范化后的模板 + 清洗后的动态数据  
**输出:** SHA‑256 指纹 (`FingerprintResult.hash_value`)

**技术要求：**
- 使用标准库 `hashlib.sha256`，确保跨平台一致性。
- 输入数据必须序列化为 **规范 JSON**：`json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(',', ':'))`。
- 支持两种模式：
  - `fingerprint = sha256(normalized_template_json)`
  - `fingerprint = sha256(normalized_template_json + dynamic_skeleton_json)` （组合指纹）
- 若输入数据量过大，可采用流式分块更新摘要（但暂不强制，因为数据量微小）。

**验收标准：**
- 相同输入 → 相同哈希。
- 跨 Python 3.10/3.11/3.12 环境输出一致。

---

### 3.5 自检与稳定性监控埋点

**负责人:** 开发者  
**预估工时:** 1 人天  
**输入:** 指纹生成函数  
**输出:** 自检器 + 指标上报

**详细设计：**
1. **内置自检**  
   - `FingerprintBuilder` 提供 `check_stability()` 方法，在同一 Agent 配置下连续调用 `compute()` 3 次，并比较哈希值。
   - 若任意两次不一致，记录错误详情。
   - 结果通过 `fingerprint_builder.stability_check` 属性提供最近一次自检状态。

2. **监控指标集成**  
   复用 `monitoring/collector.py` 的能力，上报以下指标：
   - `fingerprint_compute_duration_ms` (gauge)
   - `fingerprint_stability_failures_total` (counter)
   - `fingerprint_template_version` (gauge)
   - `fingerprint_cache_hit_ratio` (可选，若实现缓存)
   
3. **定期主动探测**  
   在 `fingerprint_monitor.py` 中实现一个后台任务（轻量 asyncio），每隔 5 分钟对系统中所有活跃 Agent 执行一次稳定性检查，并将结果记入指标。

**验收标准：**
- 运行自检后，若模板稳定，`stability_failures_total` 不增加。
- 通过 Prometheus 端点 `/metrics` 可观察到新增指标。

---

## 4. 集成与测试计划

| 阶段 | 内容 | 负责人 | 工时 |
|------|------|--------|------|
| **单元测试** | 使用 pytest，针对每个子模块编写测试（模板提取、剔除、哈希、自检） | 开发者 | 0.75 |
| **集成测试** | 端到端：取 `ai_coding_team` 中的 Agent，计算指纹，多次调用确保一致 | 开发者 | 0.5 |
| **压力/稳定性** | 并发调用计算指纹（多协程），验证无竞态、哈希一致 | 测试工程师 | 0.5 |
| **监控验证** | 启动系统，观察 `/metrics` 并确认指标上报 | 开发者+测试 | 0.25 |

## 5. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| AgentProfile 字段变化导致模板漂移 | 指纹大面积失效，A/B 测试失真 | ① 使用明确的“模板版本号” ② 在 CI 中增加快照测试，检测字段增减 |
| 动态剔除遗漏某些随机值 | 指纹不稳定 | ① 提供可配置的剔除规则表 ② 通过监控指标 `stability_failures_total` 尽早发现 |
| 哈希计算与现有 A/B 测试不兼容 | 旧的 `mutation_rate` 计算逻辑需要修改 | 提前与 ab_testing 模块负责人对齐输出格式，保持向后兼容 |
| 自检任务占用资源过多 | 系统抖动 | 仅对活跃 Agent 采样，加入随机抖动（jitter），限制并发数 |

## 6. 开发流程与里程碑

1. **接口冻结**（Day 0.5）  
   架构师与研究员完成接口定义，并与前后端对齐。

2. **MVP 实现**（Day 2）  
   开发者完成 3.2–3.4，实现单次指纹计算并通过单元测试。

3. **监控集成**（Day 3）  
   完成 3.5，嵌入监控指标与自检任务。

4. **集成测试 + 文档**（Day 3.5）  
   联调 `ab_testing`，更新相关文档，交付。

## 7. 交付物清单

- [ ] `src/backend/monitoring/fingerprint_builder.py`（含模板、剔除、哈希）
- [ ] `src/backend/monitoring/fingerprint_monitor.py`（自检 + 埋点）
- [ ] `src/backend/monitoring/models.py` 补充（指纹相关数据结构）
- [ ] `src/backend/tests/test_fingerprint.py` 单元测试
- [ ] 集成测试用例
- [ ] 更新 `startup_validator.py` 中的健康检查（如果有需要）
- [ ] 监控指标接入文档（Prometheus 指标说明）

---

请研发团队按此规划推进，如有阻塞及时同步。

────────────────────────────────────────────────────────────
✅ deepseek-v4-pro 完成
