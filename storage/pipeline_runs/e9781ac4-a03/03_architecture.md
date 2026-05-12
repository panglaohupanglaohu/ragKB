# 架构设计 — architect

任务: CI/CD 集成 schema 迁移与端到端自动化测试：迁移脚本作为部署 Job 自动执行，评估器边界用例覆盖，审核流竞态与断网场景测试，烟雾测试验证索引就绪与 SkillStore 完整性。
步骤: architecture
Agent: build_architect

---

📋 任务: e9781ac4-a03
🤖 Agent: Architect (architect)
📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
🔧 执行方式: DeepSeek API (直连)
⏱️ 超时: 1200s
────────────────────────────────────────────────────────────
📝 提示词:
  你是 AgentsGroup2026 系统的 Architect (architect)。
  请执行以下开发任务:
  
  你是系统架构师。请为以下任务设计技术方案:
  
  ## 任务
  CI/CD 集成 schema 迁移与端到端自动化测试：迁移脚本作为部署 Job 自动执行，评估器边界用例覆盖，审核流竞态与断网场景测试，烟雾测试验证索引就绪与 SkillStore 完整性。
  Deployer, 测试工程师
  
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
  src/docs/agent_handoffs/11e9b4b9-283_executor_started_20260509T074916.md
  src/docs/agent_handoffs/11e9b4b9-283_pm_decompose_20260509T075116.md
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
  src/docs/agent_handoffs/21ef94ba-2b6_executor_started_20260509T074916.md
  src/docs/agent_handoffs/21ef94ba-2b6_pm_decompose_20260509T075106.md
  src/docs/agent_handoffs/232eac0a-e93_executor_started_20260509T073231.md
  src/docs/agent_handoffs/23cb267e-4e0_executor_started_20260503T114540.md
  src/docs/agent_handoffs/2da416d2-cdf_executor_started_20260509T074916.md
  src/docs/agent_handoffs/2da416d2-cdf_pm_decompose_20260509T075121.md
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
  src/docs/agent_handoffs/3f9494e1-96d_executor_started_20260509T074916.md
  src/docs/agent_handoffs/3f9494e1-96d_pm_decompose_20260509T075056.md
  src/docs/agent_handoffs/3f9494e1-96d_research_20260509T075256.md
  src/docs/agent_handoffs/415e549a-116_executor_started_20260509T073231.md
  src/docs/agent_handoffs/4601c322-51d_executor_started_20260509T075153.md
  src/docs/agent_handoffs/4601c322-51d_pipeline_complete_20260509T075233.md
  ... (共 532 个 src/ 文件)
  
  ```
  
  ### 文件: `src/backend/startup_check.py`
  ```py
  # -*- coding: utf-8 -*-
  """
  Startup Check Middleware - 启动时自动执行验证
  
  在 FastAPI 应用启动后自动运行验证检查，
  将结果记录到日志和 /api/v1/startup-check 端点。
  """
  
  from __future__ import annotations
  
  import asyncio
  import logging
  from typing import Any, Dict, Optional
  
  from fastapi import APIRouter
  
  from startup_validator import StartupValidator, ValidationReport
  
  logger = logging.getLogger("startup_check")
  
  # 全局验证报告
  _last_report: Optional[Dict[str, Any]] = None
  _check_router = APIRouter(prefix="/api/v1", tags=["Startup Check"])
  
  
  @_check_router.get("/startup-check")
  async def get_startup_check():
      """获取最近一次启动验证结果"""
      if _last_report is None:
          return {
              "status": "not_run",
              "message": "启动验证尚未执行",
          }
      return {
          "status": "completed",
          "report": _last_report,
      }
  
  
  async def run_startup_check(base_url: str = "http://localhost:8080"):
      """在应用启动后运行验证"""
      global _last_report
  
      logger.info("🔍 执行启动验证...")
      validator = StartupValidator(base_url)
      try:
          report = await validator.run_all()
          _last_report = report.to_dict()
  
          if report.failed > 0:
              logger.warning(
                  f"⚠️ 启动验证完成: {report.failed}/{report.total_checks} 项失败"
              )
              for check in report.checks:
                  if check.status.value == "fail":
                      logger.warning(f"  ❌ {check.name}: {check.error}")
          elif report.warnings > 0:
              logger.info(
                  f"⚠️ 启动验证完成: {report.warnings} 项警告"
              )
          else:
              logger.info(f"✅ 启动验证通过: 全部 {report.total_checks} 项检查通过")
  
          return report
      finally:
          await validator.close()
  
  
  def get_startup_check_router() -> APIRouter:
      """获取启动检查路由"""
      return _check_router
  
  
  __all__ = ["run_startup_check", "get_startup_check_router", "get_startup_check"]
  
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
  
  ### 文件: `src/backend/tests/__init__.py`
  ```py
  # -*- coding: utf-8 -*-
  """AgentsGroup2026 Test Pipeline — 自动化测试流水线.
  
  覆盖:
  - 单元测试: 数据模型、核心算法、工具函数
  - 集成测试: FastAPI 路由、团队管理 API
  - A/B 测试验证: EWMA 阈值、Lamport 时钟、流量染色
  """
  
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
  
  ### 文件: `src/backend/agents/tts_routes.py`
  ```py
  # -*- coding: utf-8 -*-
  """TTS route — Edge-TTS (Microsoft Neural) as primary engine.
  
  Edge-TTS provides free, high-quality neural voices with natural emotion.
  GPT-SoVITS is kept as optional fallback for custom voice cloning.
  """
  
  from __future__ import annotations
  
  import json
  import logging
  import os
  import re
  import signal
  import subprocess
  from pathlib import Path
  from typing import Optional
  
  import httpx
  from fastapi import APIRouter, HTTPException
  from fastapi.responses import Response
  from pydantic import BaseModel
  
  logger = logging.getLogger(__name__)
  
  router = APIRouter(tags=["tts"])
  
  # ── Config ────────────────────────────────────────────────────────────────────
  _config_path = Path(__file__).resolve().parents[3] / "config" / "settings.json"
  
  
  def _load_tts_config() -> dict:
      """Re-read settings.json for live config."""
      try:
          with open(_config_path, "r", encoding="utf-8") as f:
              return json.load(f).get("tts", {})
      except Exception:
          return {}
  
  
  # ── Edge-TTS voice pool (male-only fallback voices) ─────────────────────────
  VOICE_POOL = [
      {"voice": "zh-CN-YunxiNeural", "style": "lively", "desc": "活泼阳光男声"},
      {"voice": "zh-CN-YunjianNeural", "style": "passionate", "desc": "热情成熟男声"},
      {"voice": "zh-CN-YunyangNeural", "style": "professional", "desc": "专业新闻男声"},
  ]
  
  VOICE_PROFILE_RULES = [
      (("pm", "项目经理"), {"voice": "zh-CN-YunyangNeural", "rate": "+3%", "pitch": "-2Hz"}),
      (("architect", "架构", "architect"), {"voice": "zh-CN-YunjianNeural", "rate": "+2%", "pitch": "-4Hz"}),
      (("researcher", "研究员", "research"), {"voice": "zh-CN-YunxiNeural", "rate": "+4%", "pitch": "+0Hz"}),
      (("developer", "开发", "全栈"), {"voice": "zh-CN-YunjianNeural", "rate": "+8%", "pitch": "+1Hz"}),
      (("tester", "测试"), {"voice": "zh-CN-YunyangNeural", "rate": "+4%", "pitch": "-1Hz"}),
      (("deployer", "运维", "部署"), {"voice": "zh-CN-YunyangNeural", "rate": "+6%", "pitch": "-3Hz"}),
      (("doc", "writer", "文档"), {"voice": "zh-CN-YunxiNeural", "rate": "+1%", "pitch": "+1Hz"}),
      (("policy", "watchdog", "forecast", "thermal", "pue", "darwin"), {"voice": "zh-CN-YunjianNeural", "rate": "+5%", "pitch": "-2Hz"}),
  ]
  
  DEFAULT_VOICE = "zh-CN-YunxiNeural"
  DEFAULT_RATE = "+8%"
  DEFAULT_PITCH = "+0Hz"
  
  # Track GPT-SoVITS subprocess (optional)
  _tts_process: Optional[subprocess.Popen] = None
  
  
  # ── Request models ─────────────────────────────────────────────────────────────
  
  class TTSRequest(BaseModel):
      text: str
      text_lang: str = "zh"
      speed_factor: float = 1.0
      voice: str = ""
      agent_name: str = ""
      rate: str = ""
      pitch: str = ""
  
  
  def _voice_for_agent(agent_name: str) -> str:
      """Deterministic voice assignment based on agent name hash."""
      if not agent_name:
          return DEFAULT_VOICE
      h = sum(ord(c) for c in agent_name)
      return VOICE_POOL[h % len(VOICE_POOL)]["voice"]
  
  
  def _profile_for_agent(agent_name: str) -> dict:
      lowered = (agent_name or "").lower()
      for keywords, profile in VOICE_PROFILE_RULES:
          if any(keyword in lowered for keyword in keywords):
              return profile
      return {
          "voice": _voice_for_agent(agent_name),
          "rate": DEFAULT_RATE,
          "pitch": DEFAULT_PITCH,
      }
  
  
  def _speechify_text(text: str) -> str:
      """Normalize LLM output into something that sounds spoken instead of written."""
      spoken = text.strip()
      spoken = re.sub(r"`([^`]+)`", r"\1", spoken)
      spoken = re.sub(r"\*\*([^*]+)\*\*", r"\1", spoken)
      spoken = re.sub(r"\*([^*]+)\*", r"\1", spoken)
      spoken = re.sub(r"^[\-•\d.\s]+", "", spoken, flags=re.MULTILINE)
      spoken = spoken.replace("SLA", "服务等级目标")
      spoken = spoken.replace("CI/CD", "持续集成和持续部署")
      spoken = spoken.replace("traceId", "追踪标识")
      spoken = spoken.replace("WebSocket", "Web Socket")
      spoken = re.sub(r"\s*[:：]\s*", "，", spoken)
      spoken = re.sub(r"\s*[;；]\s*", "。", spoken)
      spoken = re.sub(r"\n+", "。", spoken)
      spoken = re.sub(r"[ ]{2,}", " ", spoken)
      spoken = re.sub(r"[。]{2,}", "。", spoken)
      return spoken.strip("。 ") + "。"
  
  
  def _rate_to_percent(rate: str) -> int:
      match = re.match(r"([+-]?\d+)%", (rate or "").strip())
      if not match:
          return 0
      return int(match.group(1))
  
  
  def _prefer_faster_rate(base_rate: str, computed_rate: str) -> str:
      if _rate_to_percent(computed_rate) > _rate_to_percent(base_rate):
          return computed_rate
      return base_rate
  
  
  def _rate_for_text(text: str, base_speed: float = 1.0) -> str:
      """Compute natural speaking rate for conversational discussion."""
      length = len(text.replace(" ", ""))
      if length < 20:
          pct = 8
      elif length < 60:
          pct = 12
      elif length < 150:
          pct = 18
      else:
          pct = 22
      pct += int((base_speed - 1.0) * 25)
      pct = max(-10, min(30, pct))
      return f"+{pct}%" if pct >= 0 else f"{pct}%"
  
  
  # ── Edge-TTS synthesis ─────────────────────────────────────────────────────────
  
  async def _edge_tts_synthesize(text: str, voice: str, rate: str, pitch: str) -> bytes:
      """Call edge-tts library to synthesize text to MP3 bytes."""
      import edge_tts
  
      communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
      audio_chunks = []
      async for chunk in communicate.stream():
          if chunk["type"] == "audio":
              audio_chunks.append(chunk["data"])
  
      if not audio_chunks:
          raise RuntimeError("Edge-TTS returned no audio data")
      return b"".join(audio_chunks)
  
  
  # ── GPT-SoVITS fallback ───────────────────────────────────────────────────────
  
  async def _gptsovits_synthesize(text: str, cfg: dict, speed: float) -> Optional[bytes]:
      """Fallback to local GPT-SoVITS if available."""
      api_url = cfg.get("api_url", "http://127.0.0.1:9880")
      payload = {
          "text": text,
          "text_lang": cfg.get("text_lang", "zh"),
          "ref_audio_path": cfg.get("ref_audio_path", ""),
          "prompt_text": cfg.get("prompt_text", ""),
          "prompt_lang": cfg.get("prompt_lang", "zh"),
          "speed_factor": speed,
          "media_type": "wav",
          "streaming_mode": False,
          "text_split_method": "cut5",
          "batch_size": 1,
          "temperature": 1.0,
          "top_k": 15,
          "top_p": 1.0,
          "parallel_infer": True,
          "repetition_penalty": 1.35,
      }
      try:
          async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=5.0)) as client:
              resp = await client.post(f"{api_url}/tts", json=payload)
              if resp.status_code == 200:
                  return resp.content
      except Exception as e:
          logger.debug(f"GPT-SoVITS fallback failed: {e}")
      return None
  
  
  # ── Main TTS endpoint ─────────────────────────────────────────────────────────
  
  @router.post("/tts")
  async def tts_synthesize(req: TTSRequest):
      """Synthesize speech using Edge-TTS (primary) or GPT-SoVITS (fallback)."""
      cfg = _load_tts_config()
      engine = cfg.get("engine", "edge-tts")
  
      text = req.text.strip()
      if not text:
          raise HTTPException(400, "text is required")
  
      spoken_text = _speechify_text(text)
      profile = _profile_for_agent(req.agent_name)
  
      voice = req.voice or profile["voice"]
      computed_rate = _rate_for_text(spoken_text, req.speed_factor)
      rate = req.rate or _prefer_faster_rate(profile["rate"], computed_rate)
      pitch = req.pitch or profile["pitch"] or DEFAULT_PITCH
  
      # Try Edge-TTS first
      if engine != "gpt-sovits-only":
          try:
              audio_data = await _edge_tts_synthesize(spoken_text, voice, rate, pitch)
              return Response(
                  content=audio_data,
                  media_type="audio/mpeg",
                  headers={"Cache-Control": "no-cache", "X-TTS-Engine": "edge-tts", "X-TTS-Voice": voice},
              )
          except Exception as e:
              logger.warning(f"Edge-TTS failed: {e}, trying GPT-SoVITS fallback")
  
      # Fallback to GPT-SoVITS
      if cfg.get("ref_audio_path"):
          audio_data = await _gptsovits_synthesize(spoken_text, cfg, req.speed_factor)
          if audio_data:
              return Response(
                  content=audio_data,
                  media_type="audio/wav",
                  headers={"Cache-Control": "no-cache", "X-TTS-Engine": "gpt-sovits"},
              )
  
      raise HTTPException(503, "All TTS engines unavailable")
  
  
  # ── Config endpoints ──────────────────────────────────────────────────────────
  
  @router.get("/tts/config")
  async def tts_get_config():
      """Return current TTS config."""
      cfg = _load_tts_config()
      return {
          "engine": cfg.get("engine", "edge-tts"),
          "api_url": cfg.get("api_url", "http://127.0.0.1:9880"),
          "ref_audio_path": cfg.get("ref_audio_path", ""),
          "text_lang": cfg.get("text_lang", "zh"),
          "speed_factor": cfg.get("speed_factor", 1.0),
          "edge_voice": cfg.get("edge_voice", DEFAULT_VOICE),
          "edge_rate": cfg.get("edge_rate", DEFAULT_RATE),
          "voice_pool": VOICE_POOL,
      }
  
  
  class TTSConfigUpdate(BaseModel):
      engine: str = "edge-tts"
      api_url: str = "http://127.0.0.1:9880"
      ref_audio_path: str = ""
      prompt_text: str = ""
      prompt_lang: str = "zh"
      text_lang: str = "zh"
      speed_factor: float = 1.0
      edge_voice: str = DEFAULT_VOICE
      edge_rate: str = DEFAULT_RATE
  
  
  @router.put("/tts/config")
  async def tts_update_config(body: TTSConfigUpdate):
      """Update TTS config in settings.json."""
      try:
          with open(_config_path, "r", encoding="utf-8") as f:
              settings = json.load(f)
      except Exception:
          settings = {}
  
      settings["tts"] = {
          **settings.get("tts", {}),
          "engine": body.engine,
          "api_url": body.api_url,
          "ref_audio_path": body.ref_audio_path,
          "prompt_text": body.prompt_text,
          "prompt_lang": body.prompt_lang,
          "text_lang": body.text_lang,
          "speed_factor": body.speed_factor,
          "edge_voice": body.edge_voice,
          "edge_rate": body.edge_rate,
      }
      with open(_config_path, "w", encoding="utf-8") as f:
          json.dump(settings, f, ensure_ascii=False, indent=2)
      return {"status": "saved"}
  
  
  @router.get("/tts/status")
  async def tts_status():
      """Check TTS service availability."""
      global _tts_process
      cfg = _load_tts_config()
  
      edge_ok = False
      try:
          import edge_tts  # noqa: F401
          edge_ok = True
      except ImportError:
          pass
  
      gptsovits_ok = False
      api_url = cfg.get("api_url", "http://127.0.0.1:9880")
      try:
          async with httpx.AsyncClient(timeout=3.0) as client:
              resp = await client.get(f"{api_url}/")
              gptsovits_ok = resp.status_code < 500
      except Exception:
          pass
  
      pid = None
      if _tts_process and _tts_process.poll() is None:
          pid = _tts_process.pid
  
      return {
          "engine": cfg.get("engine", "edge-tts"),
          "edge_tts": {"available": edge_ok, "voice": cfg.get("edge_voice", DEFAULT_VOICE)},
          "gpt_sovits": {"online": gptsovits_ok, "api_url": api_url, "pid": pid},
      }
  
  
  @router.get("/tts/voices")
  async def tts_list_voices():
      """List available Edge-TTS voices."""
      return {"voices": VOICE_POOL, "default": DEFAULT_VOICE}
  
  
  # ── GPT-SoVITS process management ─────────────────────────────────────────────
  
  @router.post("/tts/start")
  async def tts_start_service():
      """Start GPT-SoVITS subprocess (optional)."""
      global _tts_process
      if _tts_process and _tts_process.poll() is None:
          return {"status": "already_running", "pid": _tts_process.pid}
  
      gpt_sovits_dir = Path.home() / "GPT-SoVITS"
      venv_python = gpt_sovits_dir / "venv" / "bin" / "python"
      if not venv_python.exists():
          raise HTTPException(404, "GPT-SoVITS venv not found")
  
      try:
          _tts_process = subprocess.Popen(
              [str(venv_python), "api_v2.py", "-a", "127.0.0.1", "-p", "9880",
               "-c", "GPT_SoVITS/configs/tts_infer.yaml"],
              cwd=str(gpt_sovits_dir),
              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
              preexec_fn=os.setsid,
          )
          return {"status": "started", "pid": _tts_process.pid}
      except Exception as e:
          raise HTTPException(500, str(e))
  
  
  @router.post("/tts/stop")
  async def tts_stop_service():
      """Stop GPT-SoVITS subprocess."""
      global _tts_process
      if _tts_process and _tts_process.poll() is None:
          os.killpg(os.getpgid(_tts_process.pid), signal.SIGTERM)
          _tts_process = None
          return {"status": "stopped"}
      return {"status": "not_running"}
  
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
              AgentChannelConfig(channel_name="coding_bus", subscribe=True, pub
  ```
  
  (后续文件因 token 预算已省略)
  
  
  ## 前序步骤的产出 (递进式摘要)
  
  ### 步骤 01: pm_decompose
  任务: CI/CD 集成 schema 迁移与端到端自动化测试：迁移脚本作为部署 Job 自动执行，评估器边界用例覆盖，审核流竞态与断网场景测试，烟雾测试验证索引就绪与 SkillStore 完整性。
  步骤: pm_decompose
  📋 任务: e9781ac4-a03
  🤖 Agent: PM (project_manager)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ────────────────────────────────────────────────────────────
  你是 AgentsGroup2026 系统的 PM (project_manager)。
  你是项目经理 (PM)。请对以下任务进行分解和规划:
  CI/CD 集成 schema 迁移与端到端自动化测试：迁移脚本作为部署 Job 自动执行，评估器边界用例覆盖，审核流竞态与断网场景测试，烟雾测试验证索引就绪与 SkillStore 完整性。
  ## 📂 项目上下文 (系统自动预加载)
  ### 项目文件结构 (src/ 目录)
  ### 文件: `src/backend/startup_check.py`
  ### 文件: `src/backend/startup_validator.py`
  ### 文件: `src/backend/tests/__init__.py`
  **子任务拆解:**
    - *目标**：建立一套完整的 CI/CD 流水线，能够在部署阶段自动执行 schema 迁移脚本，并通过分层自动化测试（评估器边界覆盖、审核流竞态/断网场景、烟雾测试）保证系统的数据一致性、稳定性和关键路径完整性。
    - 可重放的 schema 迁移脚本（集成为部署 Job 自动执行）
    - 评估器（EWMA 阈值引擎、A/B 测试相关组件）边界用例测试套件
    - 审核流（任务审核/配置变更审核）在并发竞态与网络中断下的健壮性测试
    - 烟雾测试套件（验证服务启动后索引就绪、SkillStore 完整性）
    - CI/CD 配置文件（如 GitHub Actions / Jenkinsfile）更新，串联上述步骤
    - *涉及角色**：Deployer（部署工程师）、测试工程师
    - **后端框架**：Python FastAPI（`src/backend/main.py`）
  
  ### 步骤 02: research (完整产出)
  
  # 研究分析 — researcher
  
  任务: CI/CD 集成 schema 迁移与端到端自动化测试：迁移脚本作为部署 Job 自动执行，评估器边界用例覆盖，审核流竞态与断网场景测试，烟雾测试验证索引就绪与 SkillStore 完整性。
  步骤: research
  Agent: build_researcher
  
  ---
  
  📋 任务: e9781ac4-a03
  🤖 Agent: Researcher (researcher)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ⏱️ 超时: 1200s
  ────────────────────────────────────────────────────────────
  📝 提示词:
    你是 AgentsGroup2026 系统的 Researcher (researcher)。
    请执行以下开发任务:
    
    你是技术研究员。请对以下任务进行技术调研:
    
    ## 任务
    CI/CD 集成 schema 迁移与端到端自动化测试：迁移脚本作为部署 Job 自动执行，评估器边界用例覆盖，审核流竞态与断网场景测试，烟雾测试验证索引就绪与 SkillStore 完整性。
    Deployer, 测试工程师
    
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
    src/docs/agent_handoffs/11e9b4b9-283_executor_started_20260509T074916.md
    src/docs/agent_handoffs/11e9b4b9-283_pm_decompose_20260509T075116.md
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
    src/docs/agent_handoffs/21ef94ba-2b6_executor_started_20260509T074916.md
    src/docs/agent_handoffs/21ef94ba-2b6_pm_decompose_20260509T075106.md
    src/docs/agent_handoffs/232eac0a-e93_executor_started_20260509T073231.md
    src/docs/agent_handoffs/23cb267e-4e0_executor_started_20260503T114540.md
    src/docs/agent_handoffs/2da416d2-cdf_executor_started_20260509T074916.md
    src/docs/agent_handoffs/2da416d2-cdf_pm_decompose_20260509T075121.md
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
    src/docs/agent_handoffs/3f9494e1-96d_executor_started_20260509T074916.md
    src/docs/agent_handoffs/3f9494e1-96d_pm_decompose_20260509T075056.md
    src/docs/agent_handoffs/3f9494e1-96d_research_20260509T075256.md
    src/docs/agent_handoffs/415e549a-116_executor_started_20260509T073231.md
    src/docs/agent_handoffs/4601c322-51d_executor_started_20260509T075153.md
    src/docs/agent_handoffs/4601c322-51d_pipeline_complete_20260509T075233.md
    ... (共 532 个 src/ 文件)
    
    ```
    
    ### 文件: `src/backend/startup_check.py`
    ```py
    # -*- coding: utf-8 -*-
    """
    Startup Check Middleware - 启动时自动执行验证
    
    在 FastAPI 应用启动后自动运行验证检查，
    将结果记录到日志和 /api/v1/startup-check 端点。
    """
    
    from __future__ import annotations
    
    import asyncio
    import logging
    from typing import Any, Dict, Optional
    
    from fastapi import APIRouter
    
    from startup_validator import StartupValidator, ValidationReport
    
    logger = logging.getLogger("startup_check")
    
    # 全局验证报告
    _last_report: Optional[Dict[str, Any]] = None
    _check_router = APIRouter(prefix="/api/v1", tags=["Startup Check"])
    
    
    @_check_router.get("/startup-check")
    async def get_startup_check():
        """获取最近一次启动验证结果"""
        if _last_report is None:
            return {
                "status": "not_run",
                "message": "启动验证尚未执行",
            }
        return {
            "status": "completed",
            "report": _last_report,
        }
    
    
    async def run_startup_check(base_url: str = "http://localhost:8080"):
        """在应用启动后运行验证"""
        global _last_report
    
        logger.info("🔍 执行启动验证...")
        validator = StartupValidator(base_url)
        try:
            report = await validator.run_all()
            _last_report = report.to_dict()
    
            if report.failed > 0:
                logger.warning(
                    f"⚠️ 启动验证完成: {report.failed}/{report.total_checks} 项失败"
                )
                for check in report.checks:
                    if check.status.value == "fail":
                        logger.warning(f"  ❌ {check.name}: {check.error}")
            elif report.warnings > 0:
                logger.info(
                    f"⚠️ 启动验证完成: {report.warnings} 项警告"
                )
            else:
                logger.info(f"✅ 启动验证通过: 全部 {report.total_checks} 项检查通过")
    
            return report
        finally:
            await validator.close()
    
    
    def get_startup_check_router() -> APIRouter:
        """获取启动检查路由"""
        return _check_router
    
    
    __all__ = ["run_startup_check", "get_startup_check_router", "get_startup_check"]
    
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
    
    ### 文件: `src/backend/tests/__init__.py`
    ```py
    # -*- coding: utf-8 -*-
    """AgentsGroup2026 Test Pipeline — 自动化测试流水线.
    
    覆盖:
    - 单元测试: 数据模型、核心算法、工具函数
    - 集成测试: FastAPI 路由、团队管理 API
    - A/B 测试验证: EWMA 阈值、Lamport 时钟、流量染色
    """
    
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
            # ── Build Team / Researcher skills ───────────────────────
  ...(截断)
  
  ## ⚠️ 重要提示
  上方 📂 项目上下文 包含了任务相关的实际源文件。
  请基于这些文件设计方案，不要引用不存在的文件。
  
  ## 要求
  1. 基于调研结果和实际源码，设计详细技术方案
  2. 明确指出需要修改的文件和具体修改内容
  3. 定义接口规范（如有新增 API）
  4. 为开发工程师提供逐步实施指南
  
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

# 技术方案设计：CI/CD 集成 Schema 迁移与端到端自动化测试

## 1. 概述

### 1.1 目标
建立一套完整的 CI/CD 流水线，实现在部署阶段自动执行 **schema 迁移脚本**，并通过分层自动化测试（**评估器边界覆盖**、**审核流竞态/断网场景**、**烟雾测试**）保证系统的数据一致性、关键路径稳定性和服务完整性。

### 1.2 当前系统现状
- 后端基于 Python FastAPI，数据多使用文件存储（JSON 文件/目录），如 `TeamStore`、`TaskStore`、`SkillRegistry` 等。
- 已有 `StartupValidator` 执行基本健康检查、端点可达性验证。
- 现有测试套件覆盖单元测试、集成测试和部分 A/B 测试验证，使用 pytest + fixture。
- 系统有 `evolution_engine`（演进引擎）、任务审核流程、A/B 测试模块（EWMA 阈值、Lamport 时钟）等关键组件。
- 前端为静态 HTML/JS，后端直接提供静态文件。

### 1.3 涉及角色
- **Deployer（部署工程师）**：负责迁移脚本实现、CI/CD 配置、构建与部署流程编排。
- **测试工程师**：负责边界用例设计、竞态与断网场景测试用例编写、烟雾测试扩展。

### 1.4 关键交付物
1. **可重放的 Schema 迁移脚本**：集成 CI/CD，支持升级和回滚。
2. **评估器边界测试套件**：覆盖 EWMA 阈值引擎、A/B 指标异常边界。
3. **审核流竞态与断网测试套件**：覆盖任务审核、配置变更审核的并发和网络中断场景。
4. **烟雾测试增强**：在现有 `StartupValidator` 基础上增加索引就绪、SkillStore 完整性检查。
5. **CI/CD 配置更新**：串联上述所有步骤的流水线定义（GitHub Actions / Jenkinsfile 风格）。

---

## 2. 架构设计

### 2.1 整体流程
```
[Code Commit] → CI Pipeline → [Build] → [Test] → [Deploy Job] → [Smoke Test]
                                                 ↓
                                          Schema Migration
                                          (自动执行)
```
- CI 阶段运行单元测试、评估器边界测试、审核流竞态/断网测试。
- 部署 Job 在应用启动前运行迁移脚本，确保数据格式与当前版本兼容。
- 部署后立即执行烟雾测试，验证服务状态和关键数据完整性。

### 2.2 关键模块设计

#### 2.2.1 Schema 迁移框架
**为什么需要？**  
系统多采用 JSON 文件存储，当数据模型变化（如 `TeamProfile` 新增字段、`Task` 结构调整）时，必须更新已持久化的数据文件，否则读取失败或逻辑错误。

**设计思路**  
- 类似 Alembic，维护一个版本号记录（`schema_version.json`）和一系列迁移脚本（按版本号命名）。
- 迁移脚本实现 `upgrade()` 和可选的 `downgrade()` 方法。
- 启动时执行“待运行”的迁移，保持幂等性。
- CI/CD 中在启动应用前运行 `migrate` 命令。

**数据结构**  
```
data/
├── schema_version.json    // {"version": 2, "applied_migrations": [...]}
└── ...                    // 其他业务数据文件
src/backend/migrations/
├── __init__.py
├── base.py                // 迁移基类
├── runner.py              // 迁移执行器
└── versions/
    ├── 001_add_team_meta.py
    └── 002_skill_registry_refactor.py
```

#### 2.2.2 评估器边界测试
**针对组件**  
`src/backend/agents/ab_testing.py` 中的 `EWMAThresholdEngine`、`LamportClock`、`ABTestMetrics` 等。

**边界测试覆盖点**
- EWMA 权重边界（alpha=0, alpha=1, alpha 负值）
- 阈值溢出（指标超出浮点数范围）
- Lamport 时钟在并发更新下的正确性
- 流量染色标记的极限长度
- A/B 指标突变（瞬间跳变到极大/极小值）

**实现方式**  
在 `src/backend/tests/` 下新增 `test_ab_testing_boundary.py`，利用已有 fixture 扩展用例。

#### 2.2.3 审核流竞态与断网测试
**审核流指哪些？**  
- 任务审核：TaskEngine 中的任务状态变更（如从 `review` 到 `approved`）
- 配置变更审核：Agent/Team 配置修改需要审批（可能体现在 `team_manager` 或 `agent_team_api` 中）

**竞态场景**
- 多个审核者对同一任务并发审批
- 审核与任务执行并发（审核通过同时任务开始执行）
- 依赖链状态快速切换

**断网场景**
- 审核过程中 API 调用超时/网络断开后恢复，确保数据一致性
- 使用 `respx` 或 mock 网络层模拟部分成功（HTTP 500/Timeout）

**实现方式**  
- 增加 `test_audit_flow_race.py`，使用 `asyncio` 并发 + `unittest.mock` 或 `pytest-asyncio` 控制并发流程。
- 增加 `test_audit_flow_network.py`，使用 `httpx.MockTransport` 或 `respx` 模拟网络异常。

#### 2.2.4 烟雾测试（索引就绪 & SkillStore 完整性）
**扩展点**  
现有 `StartupValidator` 已检查健康、API、前端等，我们扩展以下检查：
- **索引就绪**：验证数据库中关键查询索引（如果使用文件存储，则检查关键文件存在且可解析，如 TeamStore 加载成功）。
- **SkillStore 完整性**：`SkillRegistry` 加载默认技能后，检查必要技能是否存在（如 `complex_task_executor`、`skill_creator`），并验证技能定义完整性（非空 instruction、合法 category、必需工具列表非空等）。

**实现**  
- 新增 `_check_file_stores()`：遍历 `TeamStore`、`TaskStore`、`SkillStore` 等，确认文件可读且结构有效。
- 增强 `_check_agent_config()` 或新增 `_check_skillstore()`。
- 可以通过 CLI 工具 `validate_startup.py` 调用 `StartupValidator` 并指定额外检查项。

---

## 3. 详细设计

### 3.1 Schema 迁移机制
**基类** (`src/backend/migrations/base.py`)
```python
class Migration:
    version: int
    description: str
    def upgrade(self) -> None: ...
    def downgrade(self) -> None: ...  # 可选，支持回滚
```

**执行器** (`src/backend/migrations/runner.py`)
- 从 `data/schema_version.json` 读取当前版本。
- 扫描 `versions/` 目录，按版本号排序，执行未应用的 `upgrade()`。
- 更新 `schema_version.json`。
- 提供 CLI 入口：`python -m migrations.runner`，可带 `--downgrade` 参数。

**CI 集成**  
在部署脚本（如 `deploy.sh` 或 CI step）中：
```bash
python -m migrations.runner  # 自动升级到最新
```

**回滚方案**  
CI 支持回滚步骤：执行 `downgrade` 到指定版本，然后重新部署旧版本代码。

### 3.2 CI/CD Pipeline 配置
**推荐 GitHub Actions 示例**：
```yaml
name: CI/CD Pipeline
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      app:
        image: agentsgroup:test
        ports: ["8080:8080"]
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Unit & Integration Tests
        run: pytest src/backend/tests/test_ab_testing.py test_models test_task_engine test_team_manager
      - name: Boundary Tests
        run: pytest src/backend/tests/test_ab_testing_boundary.py
      - name: Audit Race Condition Tests
        run: pytest src/backend/tests/test_audit_flow_race.py
      - name: Audit Network Failure Tests
        run: pytest src/backend/tests/test_audit_flow_network.py
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Run Schema Migration
        run: python -m migrations.runner
      - name: Deploy Application
        run: docker-compose up -d
      - name: Smoke Tests
        run: python -m scripts.validate_startup --smoke --check-skillstore --check-index
```

### 3.3 测试用例设计细则

#### 3.3.1 评估器边界测试 (`test_ab_testing_boundary.py`)
| 场景 | 输入/操作 | 预期结果 |
|------|-----------|----------|
| EWMA alpha 边界 | alpha=0.0 | 权重无效，降级为简单平均或报错 |
| EWMA alpha 边界 | alpha=1.0 | 完全忽略历史值 |
| 负值指标 | false_upgrade_rate = -0.1 | 抛出异常或自动钳位 |
| 极大值 | resource_increase_pct = 1e10 | 不导致溢出，EWMA 计算正确 |
| Lamport 并发更新 | 两个节点同时 tick | 最终时间戳一致，无冲突 |
| 流量标签长度>1KB | 染色标记超长 | 正常截断或拒绝 |

#### 3.3.2 审核流竞态测试 (`test_audit_flow_race.py`)
- **并发审批同一任务**：两个 approve 请求同时到达，任务状态只升级一次。
- **审批与删除并发**：审批请求同时执行任务删除，最终状态要么 approved 要么 deleted，不出现双活。
- **依赖任务状态快速变更**：任务 A 依赖 B，B 被快速 approve 两次，A 不应被重复触发。

实现使用 `asyncio.gather` 或 `ThreadPoolExecutor` + `TestClient` 并发。

#### 3.3.3 断网测试 (`test_audit_flow_network.py`)
- **审核 API 超时**：mock `/approve` 端点随机返回 504，重试后最终一致。
- **网络中断期间状态更新**：模拟网络断开后，本地任务状态仅写入本地，恢复后同步正常。

可使用 `pytest-httpx` 或直接 mock `httpx.AsyncClient` 的请求方法。

#### 3.3.4 烟雾测试增强
**索引就绪检查**：
```python
async def _check_file_stores(self) -> CheckResult:
    # load TeamStore from disk
    try:
        store = TeamStore()
        teams = store.list_teams()
        # 检查至少存在一个团队（如默认团队）
        if not teams:
            return CheckResult(name="team_store_index", status=CheckStatus.WARN,
                               detail="No teams found, index may be empty")
    except Exception as e:
        return CheckResult(name="team_store_index", status=CheckStatus.FAIL,
                           error=str(e))
    return CheckResult(name="team_store_index", status=CheckStatus.PASS)
```
**SkillStore 完整性**：
```python
async def _check_skillstore(self) -> CheckResult:
    from agents.skill_registry import SkillRegistry, get_default_skills
    registry = SkillRegistry()
    registry.load_defaults()
    required_skills = ["complex_task_executor", "skill_creator", "mcp_installer"]
    missing = [s for s in required_skills if s not in registry._skills]
    if missing:
        return CheckResult(name="skillstore", status=CheckStatus.FAIL,
                           error=f"Missing required skills: {missing}")
    # 验证每个技能 instruction 不为空
    for sid, skill in registry._skills.items():
        if not skill.instructions or len(skill.instructions) < 10:
            return CheckResult(name="skillstore", status=CheckStatus.FAIL,
                               error=f"Skill {sid} has invalid instructions")
    return CheckResult(name="skillstore", status=CheckStatus.PASS,
                       detail=f"All {len(registry._skills)} skills valid")
```
将上述方法加入 `StartupValidator.run_all()`。

---

## 4. 文件变更清单

### 4.1 新增文件
| 文件路径 | 说明 |
|----------|------|
| `src/backend/migrations/__init__.py` | 包初始化 |
| `src/backend/migrations/base.py` | 迁移基类 |
| `src/backend/migrations/runner.py` | 迁移执行器及 CLI |
| `src/backend/migrations/versions/001_add_team_meta.py` | 示例迁移 |
| `src/backend/migrations/versions/002_skill_registry_refactor.py` | 示例迁移 |
| `src/backend/tests/test_ab_testing_boundary.py` | 评估器边界测试 |
| `src/backend/tests/test_audit_flow_race.py` | 审核流竞态测试 |
| `src/backend/tests/test_audit_flow_network.py` | 审核流断网测试 |
| `.github/workflows/ci-cd.yml` | CI/CD 配置（如使用 GitHub Actions） |
| `scripts/deploy.sh` | 部署脚本（可选，如果不用 Docker） |

### 4.2 修改文件
| 文件路径 | 修改内容 |
|----------|----------|
| `src/backend/startup_validator.py` | 增加 `_check_file_stores()`、`_check_skillstore()` 方法，并在 `run_all()` 中调用 |
| `src/backend/startup_check.py` | 无直接修改，但启动时支持 CLI 参数 `--smoke` 调用增强检查 |
| `src/backend/scripts/validate_startup.py` | 增加命令行参数 `--check-skillstore`、`--check-index`，传递给 `StartupValidator` |
| `src/backend/tests/conftest.py` | 增加共享 fixture：并发测试 mock client、skill_registry 等 |
| `src/backend/agents/skill_registry.py` | 可选：增加 `validate()` 方法，供烟雾测试调用 |
| `src/backend/main.py` | 集成 migration runner，启动时自动执行迁移（通过环境变量控制） |

---

## 5. 接口规范（新增/变更）

### 5.1 烟雾测试增强返回
`GET /api/v1/startup-check` 响应新增字段：
```json
{
  "status": "completed",
  "report": {
    "timestamp": 1234567890.0,
    "total_checks": 10,
    "passed": 9,
    "failed": 0,
    "warnings": 1,
    "checks": [
      // ... 原有检查项 ...
      {
        "name": "team_store_index",
        "status": "pass",
        "detail": "1 team loaded",
        "duration_ms": 12.3
      },
      {
        "name": "skillstore",
        "status": "pass",
        "detail": "All 35 skills valid",
        "duration_ms": 8.1
      }
    ],
    "summary": "⚠️ 1/10 checks have warnings"
  }
}
```

### 5.2 迁移状态 API（可选，方便调试）
`GET /api/v1/migration-status`（新增路由）
- 返回当前 schema 版本和已应用迁移列表。
- 仅部署/调试时使用，生产环境可关闭。

---

## 6. 逐步实施指南

### Step 1: 建立迁移框架 （Deployer）
1. 创建 `src/backend/migrations/` 目录及 `base.py`。
2. 实现 `MigrationRunner`，支持发现和执行迁移。
3. 在 `main.py` 中添加启动逻辑（检查环境变量 `AUTO_MIGRATE=true`）。
4. 为当前数据模型创建第一个迁移（版本 001），确保幂等性。
5. 测试：手动执行迁移，检查 `schema_version.json` 更新。

### Step 2: 编写 CI/CD 配置 （Deployer）
1. 根据仓库选择 CI 工具（GitHub Actions / Jenkins）。
2. 定义流水线阶段：Build → Test → Deploy → Smoke。
3. 在 Deploy 阶段前添加迁移执行步骤。
4. 在 Smoke 测试步骤调用 `validate_startup.py --smoke` 并断言退出码。

### Step 3: 评估器边界测试 （测试工程师）
1. 新增 `test_ab_testing_boundary.py`，使用现有 fixture 扩展边界用例。
2. 运行测试，修复 ab_testing 模块暴露的边界问题（如缺少输入校验）。
3. 集成到 CI 测试阶段。

### Step 4: 审核流竞态与断网测试 （测试工程师）
1. 分析 TaskEngine 和审核相关 API 的实现，找出共享状态。
2. 编写竞态测试，使用 `asyncio.gather` 模拟并发请求。
3. 编写断网测试，mock HTTP 层注入超时/错误。
4. 调试直至通过，确保不引入数据不一致。
5. 加入 CI 测试阶段。

### Step 5: 烟雾测试扩展 （测试工程师 + Deployer）
1. 在 `StartupValidator` 中新增 `_check_file_stores` 和 `_check_skillstore` 方法。
2. 更新 `validate_startup.py` CLI 参数。
3. 本地执行一次烟雾测试，确认通过。
4. 集成到 CI 的 Deploy 后阶段。

### Step 6: 端到端验证 （全体）
1. 模拟一次代码变更（例如修改 Team 结构），编写对应迁移。
2. Push 到仓库，观察 CI 流水线自动执行测试、执行迁移、部署、烟雾测试。
3. 验证流水线报告和系统状态。

---

## 7. 风险与注意事项
- **文件锁冲突**：迁移执行时，应用可能同时启动。解决方案：在迁移脚本执行完成后再启动应用服务（容器编排中通过依赖控制）。
- **迁移回滚**：确保关键迁移提供 `downgrade()` 方法，并在 CI 中支持手动触发回滚。
- **测试环境依赖**：竞态测试可能需要更高资源，CI 环境需保证足够并发能力。
- **技能定义变更**：SkillStore 完整性检查需与技能定义同步更新，避免因新增必选技能导致烟雾测试误报。

---

此方案确保从代码提交到最终部署的全过程自动化，覆盖了架构师需要关注的各层测试和部署可靠性。开发工程师可依据上述逐步实施指南开展工作。

────────────────────────────────────────────────────────────
✅ deepseek-v4-pro 完成
