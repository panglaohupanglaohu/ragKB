# 测试验证 — qa_engineer

任务: CI/CD 集成 schema 迁移与端到端自动化测试：迁移脚本作为部署 Job 自动执行，评估器边界用例覆盖，审核流竞态与断网场景测试，烟雾测试验证索引就绪与 SkillStore 完整性。
步骤: test
Agent: build_tester

---

📋 任务: e9781ac4-a03
🤖 Agent: Tester (qa_engineer)
📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
🔧 执行方式: DeepSeek API (直连)
⏱️ 超时: 1200s
────────────────────────────────────────────────────────────
📝 提示词:
  你是 AgentsGroup2026 系统的 Tester (qa_engineer)。
  请执行以下开发任务:
  
  你是 QA 测试工程师 (DeepSeek V4 + 工具循环模式)。
  你**已经被赋予真正的测试工具能力**: read_file / grep / run_python / run_pytest。
  禁止凭空判定 — 所有结论必须来自工具的真实输出。
  
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
  
  ### 步骤 02: research
  任务: CI/CD 集成 schema 迁移与端到端自动化测试：迁移脚本作为部署 Job 自动执行，评估器边界用例覆盖，审核流竞态与断网场景测试，烟雾测试验证索引就绪与 SkillStore 完整性。
  Agent: build_researcher
  📋 任务: e9781ac4-a03
  🤖 Agent: Researcher (researcher)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ────────────────────────────────────────────────────────────
  你是 AgentsGroup2026 系统的 Researcher (researcher)。
  你是技术研究员。请对以下任务进行技术调研:
  CI/CD 集成 schema 迁移与端到端自动化测试：迁移脚本作为部署 Job 自动执行，评估器边界用例覆盖，审核流竞态与断网场景测试，烟雾测试验证索引就绪与 SkillStore 完整性。
  ## 📂 项目上下文 (系统自动预加载)
  ### 项目文件结构 (src/ 目录)
  ### 文件: `src/backend/startup_check.py`
  ### 文件: `src/backend/startup_validator.py`
  ### 文件: `src/backend/tests/__init__.py`
  **关键决策:**
    - - `src/backend/scripts/migrate.py` – schema 迁移脚本
  - `src/backend/tests/test_evolution_race.py` – 审核流竞态/断网测试
  
  （注：新增文件符合项目 `src/backend/scripts/` 和 `tests/` 目录结构，且任务明确要求此类测试，故予推荐）
  **变更文件 (10):**
    - `src/backend/channels/system_evolution.py`
    - `src/backend/startup_validator.py`
    - `src/backend/tests/test_evolution_race.py`
    - `src/backend/channels/evolution_executor.py`
    - `src/backend/scripts/migrate.py`
    - `src/backend/startup_check.py`
    - `src/backend/agents/plaza_routes.py`
    - `src/backend/tests/conftest.py`
    - `src/backend/tests/test_ab_testing.py`
    - `src/backend/agents/skill_registry.py`
  
  ### 步骤 03: architecture
  任务: CI/CD 集成 schema 迁移与端到端自动化测试：迁移脚本作为部署 Job 自动执行，评估器边界用例覆盖，审核流竞态与断网场景测试，烟雾测试验证索引就绪与 SkillStore 完整性。
  步骤: architecture
  Agent: build_architect
  📋 任务: e9781ac4-a03
  🤖 Agent: Architect (architect)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ────────────────────────────────────────────────────────────
  你是 AgentsGroup2026 系统的 Architect (architect)。
  你是系统架构师。请为以下任务设计技术方案:
  CI/CD 集成 schema 迁移与端到端自动化测试：迁移脚本作为部署 Job 自动执行，评估器边界用例覆盖，审核流竞态与断网场景测试，烟雾测试验证索引就绪与 SkillStore 完整性。
  ## 📂 项目上下文 (系统自动预加载)
  ### 项目文件结构 (src/ 目录)
  ### 文件: `src/backend/startup_check.py`
  ### 文件: `src/backend/startup_validator.py`
  **变更文件 (1):**
    - `src/backend/agents/ab_testing.py`
  **接口规范:**
    - (直连)
    - 应用启动后自动运行验证检查，
    - 端点可用性验证
    - 端点可用性
    - 端点"""
  
  ### 步骤 04: develop (完整产出)
  
  # 代码开发 — developer
  
  任务: CI/CD 集成 schema 迁移与端到端自动化测试：迁移脚本作为部署 Job 自动执行，评估器边界用例覆盖，审核流竞态与断网场景测试，烟雾测试验证索引就绪与 SkillStore 完整性。
  步骤: develop
  Agent: build_developer
  
  ---
  
  📋 任务: e9781ac4-a03
  🤖 Agent: Developer (developer)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ⏱️ 超时: 1200s
  ────────────────────────────────────────────────────────────
  📝 提示词:
    你是 AgentsGroup2026 系统的 Developer (developer)。
    请执行以下开发任务:
    
    你是开发工程师 (DeepSeek V4 + 工具循环模式)。
    你**已经被赋予真正的工具能力**: read_file / grep / list_files / write_file / patch_file / run_python。
    禁止凭空想象 — 所有写代码前必须先用工具读真实代码。
    
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
                instructions="## 阻塞解决\n\n1. 分析
  ...(截断)
  
  ## 推荐工作流（严格遵守）
  **Step 1**: 用 grep / read_file 检查 Developer 写的新文件
  **Step 2**: 对每个新 .py 文件，跑 `run_python(code='from <module> import <name>')` 验证 import 通
  **Step 3**: 对涉及到的 channel，跑 `run_python(code='from channels.X import Y; obj=Y(); print(obj.process_event({}))')` 测试核心方法
  **Step 4**: 跑 `run_pytest(target='-k <module-name>')` 看相关测试是否通过
  **Step 5**: 调用 finish 给出结论：
    - summary 必须以 `## 验证结论 PASS` 或 `## 验证结论 FAIL` 结尾
    - files_changed 通常为空（QA 不写代码）
  
  ## 判定标准
  - import 失败 → BLOCKER → FAIL
  - 单元测试失败 → BLOCKER → FAIL
  - 仅 lint/style 问题 → MINOR → PASS
  
  项目根目录: /Users/panglaohu/Downloads/DoubleBoatClawSystem
  
  
  项目根目录: /Users/panglaohu/Downloads/AgentsGroup2026
  后端: src/backend/ (Python FastAPI)
  前端: src/frontend/ (HTML + JS)
  
────────────────────────────────────────────────────────────
🛠 使用 DeepSeek V4 工具循环模式 (read/grep/write/exec)...

🔗 API: https://api.deepseek.com/v1
模型: deepseek-v4-pro
角色: qa_engineer
────────────────────────────────────────────────────────────

🚀 工具集: read_file, grep, list_files, run_python, run_pytest, finish


🧠 turn#0 (6.76s, 0字, 1个工具调用)
🔧 调用工具: list_files({"path": "src/backend", "max_depth": 3})
   ✅ list_files: 83 files

🧠 turn#1 (23.01s, 102字, 3个工具调用)
🔧 调用工具: read_file({"path": "src/backend/scripts/migrate.py"})
   ✅ read_file: 541 lines, 16828 chars
🔧 调用工具: read_file({"path": "src/backend/tests/test_evolution_race.py"})
   ✅ read_file: 569 lines, 19056 chars
🔧 调用工具: read_file({"path": "src/backend/tests/test_gate_evaluator.py"})
   ✅ read_file: 290 lines, 8980 chars

🧠 turn#2 (9.48s, 98字, 3个工具调用)
🔧 调用工具: read_file({"path": "src/backend/agents/gate_evaluator.py"})
   ✅ read_file: 243 lines, 7007 chars
🔧 调用工具: read_file({"path": "src/backend/agents/review_models.py"})
   ✅ read_file: 184 lines, 6717 chars
🔧 调用工具: read_file({"path": "src/backend/channels/evolution_executor.py"})
   ✅ read_file: 271 lines, 9325 chars

🧠 turn#3 (18.7s, 71字, 1个工具调用)
🔧 调用工具: run_python({"code": "\nimport sys\nsys.path.insert(0, 'src/backend')\n\n# Test imports for new files\nresults = []\n\ntry:\n    from agents.review_models import GateEvalua)
   ✅ run_python: exit=0, 0.26s

🧠 turn#4 (25.46s, 63字, 1个工具调用)
🔧 调用工具: run_python({"code": "\nimport sys\nsys.path.insert(0, 'src/backend')\n\nresults = []\n\n# Skill modules\ntry:\n    from agents.skill_store import SkillStore\n    results.a)
   ✅ run_python: exit=0, 0.1s

🧠 turn#5 (11.99s, 61字, 3个工具调用)
🔧 调用工具: read_file({"path": "src/backend/agents/skill_extractor.py", "start_line": 1, "end_line": 30})
   ✅ read_file: 548 lines, 952 chars
🔧 调用工具: read_file({"path": "src/backend/agents/merge_models.py", "start_line": 1, "end_line": 30})
   ✅ read_file: 195 lines, 1120 chars
🔧 调用工具: read_file({"path": "src/backend/channels/marine_base.py", "start_line": 1, "end_line": 50})
   ✅ read_file: 467 lines, 1087 chars

🧠 turn#6 (12.14s, 73字, 3个工具调用)
🔧 调用工具: grep({"pattern": "^class \\w+", "include": "src/backend/agents/skill_extractor.py"})
   ✅ grep: 3 hits
🔧 调用工具: grep({"pattern": "^class \\w+", "include": "src/backend/agents/merge_models.py"})
   ✅ grep: 6 hits
🔧 调用工具: grep({"pattern": "from channels.marine_base import", "include": "src/backend/monitoring/*.py"})
   ✅ grep: 3 hits

🧠 turn#7 (14.42s, 0字, 2个工具调用)
🔧 调用工具: read_file({"end_line": 35, "path": "src/backend/monitoring/trace_bridge.py", "start_line": 22})
   ✅ read_file: 429 lines, 314 chars
🔧 调用工具: read_file({"end_line": 35, "path": "src/backend/monitoring/fingerprint_bypass.py", "start_line": 24})
   ✅ read_file: 371 lines, 228 chars

🧠 turn#8 (9.05s, 0字, 2个工具调用)
🔧 调用工具: grep({"pattern": "^class \\w+", "include": "src/backend/channels/marine_base.py"})
   ✅ grep: 6 hits
🔧 调用工具: grep({"pattern": "ChannelEvent", "include": "src/backend/channels/marine_base.py"})
   ✅ grep: 0 hits

🧠 turn#9 (9.78s, 110字, 1个工具调用)
🔧 调用工具: run_pytest({"target": "src/backend/tests/test_gate_evaluator.py -v", "timeout": 60})
   ✅ run_pytest: exit=4, 0.53s

🧠 turn#10 (4.41s, 40字, 1个工具调用)
🔧 调用工具: run_pytest({"target": "src/backend/tests/test_gate_evaluator.py", "timeout": 60})
   ✅ run_pytest: exit=1, 0.41s

🧠 turn#11 (7.54s, 67字, 2个工具调用)
🔧 调用工具: run_pytest({"target": "src/backend/tests/test_evolution_race.py", "timeout": 60})
   ✅ run_pytest: exit=1, 3.78s
🔧 调用工具: run_pytest({"target": "src/backend/tests/test_fingerprint.py", "timeout": 60})
   ✅ run_pytest: exit=0, 0.43s

🧠 turn#12 (14.44s, 36字, 2个工具调用)
🔧 调用工具: run_pytest({"target": "src/backend/tests/test_merge_plugin.py", "timeout": 60})
   ✅ run_pytest: exit=1, 0.41s
🔧 调用工具: run_pytest({"target": "src/backend/tests/test_template_variants.py", "timeout": 60})
   ✅ run_pytest: exit=1, 0.43s

🧠 turn#13 (12.3s, 65字, 2个工具调用)
🔧 调用工具: run_pytest({"target": "src/backend/tests/test_ab_testing.py", "timeout": 60})
   ✅ run_pytest: exit=0, 0.37s
🔧 调用工具: run_python({"code": "\nimport sys\nsys.path.insert(0, 'src/backend')\n\n# Test that migrate.py can be imported and basic functions work\nfrom scripts.migrate import Migrat)
   ✅ run_python: exit=1, 0.04s

🧠 turn#14 (6.23s, 54字, 2个工具调用)
🔧 调用工具: grep({"include": "src/backend/scripts/migrate.py", "pattern": "^class \\w+"})
   ✅ grep: 2 hits
🔧 调用工具: grep({"include": "src/backend/scripts/migrate.py", "pattern": "^def \\w+"})
   ✅ grep: 16 hits

🧠 turn#15 (12.08s, 46字, 4个工具调用)
🔧 调用工具: run_pytest({"target": "src/backend/tests/test_agent_toolbox.py", "timeout": 60})
   ✅ run_pytest: exit=1, 0.95s
🔧 调用工具: run_pytest({"target": "src/backend/tests/test_models.py", "timeout": 60})
   ✅ run_pytest: exit=1, 0.39s
🔧 调用工具: run_pytest({"target": "src/backend/tests/test_task_engine.py", "timeout": 60})
   ✅ run_pytest: exit=1, 0.57s
🔧 调用工具: run_pytest({"target": "src/backend/tests/test_team_manager.py", "timeout": 60})
   ✅ run_pytest: exit=1, 0.4s

🧠 turn#16 (43.57s, 71字, 1个工具调用)
🔧 调用工具: finish({"summary": "## 验证结论: FAIL\n\n### 通过项:\n- ✅ `agents.review_models/gate_evaluator/review_service/review_routes/domain_events/event_bus/audit_store` — 全部 import 通)

🏁 循环结束: finish_called (turn #16)

✅ 完成 (17 轮迭代)
修改文件 0 个: 

📋 总结:
## 验证结论: FAIL

### 通过项:
- ✅ `agents.review_models/gate_evaluator/review_service/review_routes/domain_events/event_bus/audit_store` — 全部 import 通过
- ✅ `agents.skill_store/skill_indexer/skill_querier/similarity_engine/fingerprint` — import 通过
- ✅ `test_fingerprint.py` — 77/77 全部通过
- ✅ `test_ab_testing.py` — 53/53 全部通过 (预存)
- ✅ `test_gate_evaluator.py` — 26/27 通过
- ✅ `test_template_variants.py` — 52/53 通过
- ✅ `scripts/migrate.py` — 模块可导入，核心函数 `run_migrations/rollback_migrations/show_status` 存在

### 失败项 (BLOCKER):
- ❌ **`ChannelEvent` 不存在于 `channels/marine_base.py`** — `monitoring/trace_bridge.py` 和 `monitoring/fingerprint_bypass.py` 均尝试 `from channels.marine_base import ChannelEvent`，但 `marine_base.py` 仅有 `ChannelStatus/ChannelPriority/ChannelHealth/ChannelMetrics/MarineChannel`。这会导致两个监控模块完全无法加载，属于 BLOCKER 级缺陷。
- ❌ `test_evolution_race.py` — 5/20 失败: `test_callback_race_condition` (0 回调)、`test_concurrent_discovery_dispatch`/`test_full_pipeline_concurrent` (TypeError: 'dict' object can't be awaited)、`test_evolution_item_status_transition_race` (unexpected keyword 'domain')、`test_plaza_store_index_ready` (PlazaStore 无 get_indices 属性)
- ❌ `test_merge_plugin.py` — 5/37 失败: 聚类/去重逻辑相关断言失败
- ❌ `test_gate_evaluator.py` — 1/27 失败: `test_evaluate_from_dict` 访问不存在的 `entity_id` 属性
- ⚠️ 预存测试退化: `test_models.py` (5 fail)、`test_task_engine.py` (5 fail)、`test_team_manager.py` (3 fail) — 多为 API 签名变更导致

### 风险评估:
`ChannelEvent` 缺失是 **部署阻断级缺陷** — 任何引用 `trace_bridge` 或 `fingerprint_bypass` 的启动流程都会崩
