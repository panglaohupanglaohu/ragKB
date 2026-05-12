# PM分解 — project_manager

任务: 实现侵入式溯因与维度断路器/修复模板绑定，触发告警后自动生成专项 Backlog 并冻结非关键调用
步骤: pm_decompose
Agent: build_pm

---

📋 任务: 65c1db92-524
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
  实现侵入式溯因与维度断路器/修复模板绑定，触发告警后自动生成专项 Backlog 并冻结非关键调用
  Developer + Tester
  
  ## 📂 项目上下文 (系统自动预加载)
  
  ### 项目文件结构 (src/ 目录)
  ```
  src/frontend/agent-team-config.html
  src/frontend/datacenter-ratchet-evolution.html
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
  src/backend/channels/marine_base.py
  src/backend/channels/openclaw_sync.py
  src/backend/channels/openclaw_sync.py.bak
  src/backend/channels/system_evolution.py
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
  src/docs/agent_handoffs/23cb267e-4e0_executor_started_20260503T114540.md
  src/docs/agent_handoffs/38e22004-b64_architecture_20260503T045011.md
  src/docs/agent_handoffs/38e22004-b64_pm_decompose_20260503T044921.md
  src/docs/agent_handoffs/38e22004-b64_research_20260503T044941.md
  src/docs/agent_handoffs/38e22004-b64_task_init_20260503T044856.md
  src/docs/agent_handoffs/3bde709e-2fe_executor_started_20260507T031444.md
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
  src/docs/agent_handoffs/6f911ba3-822_architecture_20260507T003740.md
  src/docs/agent_handoffs/6f911ba3-822_deploy_FAILED_20260507T004337.md
  src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T003806.md
  src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T004113.md
  src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T004235.md
  src/docs/agent_handoffs/6f911ba3-822_executor_started_20260507T003435.md
  src/docs/agent_handoffs/6f911ba3-822_pm_decompose_20260507T003510.md
  src/docs/agent_handoffs/6f911ba3-822_research_20260507T003550.md
  src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T003827.md
  src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T004134.md
  src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T004311.md
  src/docs/agent_handoffs/7c934759-39e_architecture_20260505T010014.md
  src/docs/agent_handoffs/7c934759-39e_develop_20260505T010359.md
  src/docs/agent_handoffs/7c934759-39e_develop_20260505T012357.md
  src/docs/agent_handoffs/7c934759-39e_develop_FAILED_20260505T011447.md
  src/docs/agent_handoffs/7c934759-39e_executor_started_20260505T005814.md
  src/docs/agent_handoffs/7c934759-39e_pm_decompose_20260505T005849.md
  src/docs/agent_handoffs/7c934759-39e_research_20260505T005919.md
  src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T011016.md
  src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T011949.md
  src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T012853.md
  src/docs/agent_handoffs/8665633b-cad_executor_started_20260507T031444.md
  src/docs/agent_handoffs/8a5071c5-834_architecture_20260507T003655.md
  src/docs/agent_handoffs/8a5071c5-834_deploy_FAILED_20260507T004051.md
  src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T003716.md
  src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T003903.md
  src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T004005.md
  src/docs/agent_handoffs/8a5071c5-834_executor_started_20260507T003435.md
  src/docs/agent_handoffs/8a5071c5-834_pm_decompose_20260507T003510.md
  src/docs/agent_handoffs/8a5071c5-834_research_20260507T003540.md
  src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T003737.md
  src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T003929.md
  src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T004031.md
  src/docs/agent_handoffs/a77bd3b9-2db_architecture_20260507T003625.md
  src/docs/agent_handoffs/a77bd3b9-2db_deploy_FAILED_20260507T004102.md
  src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T003646.md
  src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T003838.md
  src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T004005.md
  src/docs/agent_handoffs/a77bd3b9-2db_executor_started_20260507T003435.md
  src/docs/agent_handoffs/a77bd3b9-2db_pm_decompose_20260507T003515.md
  src/docs/agent_handoffs/a77bd3b9-2db_research_20260507T003545.md
  src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T003712.md
  src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T003904.md
  src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T004042.md
  src/docs/agent_handoffs/ba3b66b1-a77_architecture_20260505T154317.md
  src/docs/agent_handoffs/ba3b66b1-a77_deploy_FAILED_20260505T154903.md
  src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154353.md
  src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154600.md
  src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154807.md
  src/docs/agent_handoffs/ba3b66b1-a77_executor_started_20260505T153921.md
  src/docs/agent_handoffs/ba3b66b1-a77_pm_decompose_20260505T153951.md
  src/docs/agent_handoffs/ba3b66b1-a77_research_20260505T154041.md
  src/docs/agent_handoffs/ba3b66b1-a77_test_FAILED_20260505T154424.md
  ... (共 257 个 src/ 文件)
  
  ```
  
  ### 文件: `src/backend/agent_team_api.py`
  ```py
  # -*- coding: utf-8 -*-
  """
  Agent Team API Routes - 双团队管理 REST API
  
  提供构建团队 & 执行团队的状态查询、KPI 考核、
  任务分配、报告查询等端点。挂载至 FastAPI 的 router。
  """
  
  from __future__ import annotations
  
  from fastapi import APIRouter, HTTPException
  from pydantic import BaseModel
  from typing import Any, Dict, List, Optional
  
  router = APIRouter(prefix="/api/v1/agent-teams", tags=["Agent Teams"])
  
  
  # ---------------------------------------------------------------------------
  # 全局引用（在 main.py startup 时注入）
  # ---------------------------------------------------------------------------
  _build_team = None
  _execution_team = None
  _scheduler = None
  _evolution_engine = None
  
  
  def set_teams(build_team, execution_team, scheduler, evolution_engine=None):
      """在应用启动时由 main.py 调用，注入团队实例."""
      global _build_team, _execution_team, _scheduler, _evolution_engine
      _build_team = build_team
      _execution_team = execution_team
      _scheduler = scheduler
      _evolution_engine = evolution_engine
  
  
  # ---------------------------------------------------------------------------
  # Request / Response Models
  # ---------------------------------------------------------------------------
  
  class TaskAssignment(BaseModel):
      agent_id: str
      task: str
  
  class FeedbackSubmission(BaseModel):
      category: str = "optimization"
      severity: str = "medium"
      title: str
      detail: str
  
  
  # ---------------------------------------------------------------------------
  # Scheduler
  # ---------------------------------------------------------------------------
  
  @router.get("/scheduler/status")
  async def scheduler_status():
      if not _scheduler:
          raise HTTPException(503, "Scheduler not initialized")
      return _scheduler.get_status()
  
  
  @router.post("/scheduler/report")
  async def scheduler_generate_report():
      if not _scheduler:
          raise HTTPException(503, "Scheduler not initialized")
      return _scheduler.generate_report_now()
  
  
  @router.post("/scheduler/tick")
  async def scheduler_tick_once():
      """手动触发一次调度 tick (调试用)."""
      if not _scheduler:
          raise HTTPException(503, "Scheduler not initialized")
      return _scheduler.tick_once()
  
  
  # ---------------------------------------------------------------------------
  # Build Team
  # ---------------------------------------------------------------------------
  
  @router.get("/build/status")
  async def build_team_status():
      if not _build_team:
          raise HTTPException(503, "Build team not initialized")
      return _build_team.get_status()
  
  
  @router.get("/build/kpis")
  async def build_team_kpis():
      if not _build_team:
          raise HTTPException(503, "Build team not initialized")
      return _build_team.get_agent_kpis()
  
  
  @router.get("/build/agents/{agent_id}")
  async def build_agent_detail(agent_id: str):
      if not _build_team:
          raise HTTPException(503, "Build team not initialized")
      agent = _build_team.agents.get(agent_id)
      if not agent:
          raise HTTPException(404, f"Agent '{agent_id}' not found")
      return agent.to_dict()
  
  
  @router.post("/build/assign")
  async def build_assign_task(body: TaskAssignment):
      if not _build_team:
          raise HTTPException(503, "Build team not initialized")
      ok = _build_team.assign_task(body.agent_id, body.task)
      if not ok:
          raise HTTPException(404, f"Agent '{body.agent_id}' not found")
      return {"status": "assigned", "agent_id": body.agent_id, "task": body.task}
  
  
  @router.get("/build/reports")
  async def build_reports(limit: int = 10):
      if not _build_team:
          raise HTTPException(503, "Build team not initialized")
      reports = _build_team.hourly_reports[-limit:]
      return [r.to_dict() for r in reports]
  
  
  @router.get("/build/issues")
  async def build_issues():
      if not _build_team:
          raise HTTPException(503, "Build team not initialized")
      return _build_team.issue_backlog
  
  
  # ---------------------------------------------------------------------------
  # Execution Team
  # ---------------------------------------------------------------------------
  
  @router.get("/execution/status")
  async def execution_team_status():
      if not _execution_team:
          raise HTTPException(503, "Execution team not initialized")
      return _execution_team.get_status()
  
  
  @router.get("/execution/agents/{agent_id}")
  async def execution_agent_detail(agent_id: str):
      if not _execution_team:
          raise HTTPException(503, "Execution team not initialized")
      agent = _execution_team.agents.get(agent_id)
      if not agent:
          raise HTTPException(404, f"Agent '{agent_id}' not found")
      return agent.to_dict()
  
  
  @router.get("/execution/reports")
  async def execution_reports(limit: int = 10):
      if not _execution_team:
          raise HTTPException(503, "Execution team not initialized")
      reports = _execution_team.execution_reports[-limit:]
      return [r.to_dict() for r in reports]
  
  
  @router.get("/execution/feedback")
  async def execution_feedback():
      if not _execution_team:
          raise HTTPException(503, "Execution team not initialized")
      return [item.to_dict() for item in _execution_team.feedback_queue]
  
  
  @router.post("/execution/feedback")
  async def submit_feedback(body: FeedbackSubmission):
      if not _execution_team:
          raise HTTPException(503, "Execution team not initialized")
      item = _execution_team.submit_feedback(
          category=body.category,
          severity=body.severity,
          title=body.title,
          detail=body.detail,
      )
      return item.to_dict()
  
  
  # ---------------------------------------------------------------------------
  # Combined
  # ---------------------------------------------------------------------------
  
  @router.get("/overview")
  async def teams_overview():
      """一站式获取双团队全局概览."""
      result: Dict[str, Any] = {}
      if _build_team:
          bs = _build_team.get_status()
          result["build_team"] = {
              "health": bs["health"],
              "agent_count": bs["agent_count"],
              "metrics": bs["metrics"],
          }
      if _execution_team:
          es = _execution_team.get_status()
          result["execution_team"] = {
              "health": es["health"],
              "agent_count": es["agent_count"],
              "metrics": es["metrics"],
          }
      if _scheduler:
          result["scheduler"] = _scheduler.get_status()
      if _evolution_engine:
          result["evolution"] = _evolution_engine.get_status()
      return result
  
  
  # ---------------------------------------------------------------------------
  # System Evolution (自我演进引擎)
  # ---------------------------------------------------------------------------
  
  @router.get("/evolution/status")
  async def evolution_status():
      """获取自我演进引擎状态。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.get_status()
  
  
  @router.get("/evolution/summary")
  async def evolution_summary():
      """获取演进项汇总。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.get_evolution_summary()
  
  
  @router.get("/evolution/items")
  async def evolution_items(status: Optional[str] = None):
      """获取演进项列表，可按状态过滤。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.get_evolution_items(status=status)
  
  
  @router.get("/evolution/rules")
  async def evolution_rules():
      """获取审查规则列表。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return [r.to_dict() for r in _evolution_engine.audit_rules]
  
  
  @router.post("/evolution/audit")
  async def evolution_run_audit():
      """手动触发一次审查。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.run_full_audit()
  
  
  @router.post("/evolution/cycle")
  async def evolution_run_cycle():
      """运行完整演进周期（审查→派发→验证→关闭）。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.run_evolution_cycle()
  
  
  @router.post("/evolution/dispatch")
  async def evolution_dispatch():
      """派发所有待处理演进项给 Build 团队。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.dispatch_all_pending()
  
  
  @router.post("/evolution/verify")
  async def evolution_verify():
      """验证所有待验证项。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.verify_all_pending()
  
  
  @router.get("/evolution/items/{item_id}")
  async def evolution_item_detail(item_id: str):
      """获取单个演进项详情。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      item = _evolution_engine.evolution_items.get(item_id)
      if not item:
          raise HTTPException(404, f"Item '{item_id}' not found")
      return item.to_dict()
  
  
  @router.post("/evolution/items/{item_id}/progress")
  async def evolution_mark_progress(item_id: str):
      """标记演进项为进行中。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      ok = _evolution_engine.mark_in_progress(item_id)
      if not ok:
          raise HTTPException(404, f"Item '{item_id}' not found")
      return {"status": "ok", "item_id": item_id, "new_status": "in_progress"}
  
  
  @router.post("/evolution/items/{item_id}/complete")
  async def evolution_mark_complete(item_id: str):
      """标记演进项构建完成，进入待验证。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      ok = _evolution_engine.mark_build_complete(item_id)
      if not ok:
          raise HTTPException(404, f"Item '{item_id}' not found")
      return {"status": "ok", "item_id": item_id, "new_status": "verify_pending"}
  
  
  @router.post("/evolution/close-verified")
  async def evolution_close_verified():
      """关闭所有已验证通过的演进项。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      closed = _evolution_engine.close_verified()
      return {"closed": closed, "count": len(closed)}
  
  
  @router.post("/evolution/close")
  async def evolution_close():
      """关闭所有已验证通过的演进项 (close-verified 别名)。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      closed = _evolution_engine.close_verified()
      return {"closed": closed, "count": len(closed)}
  
  
  @router.get("/evolution/history")
  async def evolution_audit_history():
      """获取审查历史记录。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      raw = _evolution_engine.get_audit_history()
      # Normalize field names for frontend (expects timestamp, total)
      result = []
      for h in raw:
          entry = dict(h)
          entry.setdefault("timestamp", entry.pop("time", None))
          entry.setdefault("total", (entry.get("passed") or 0) + (entry.get("failed") or 0) + (entry.get("skipped") or 0))
          result.append(entry)
      return result
  
  
  @router.get("/evolution/analytics")
  async def evolution_analytics():
      """获取演进分析数据 (域覆盖、严重度分布、趋势)。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      summary = _evolution_engine.get_evolution_summary()
      history = _evolution_engine.get_audit_history()
      status = _evolution_engine.get_status()
  
      return {
          "summary": summary,
          "history": history,
          "stats": status.get("stats", {}),
          "items_by_status": status.get("items_by_status", {}),
          "rules_count": status.get("audit_rules_count", 0),
      }
  
  
  # ---------------------------------------------------------------------------
  # Phase 3: 业界标准化改进 API
  # ---------------------------------------------------------------------------
  
  @router.get("/evolution/compliance-rating")
  async def evolution_compliance_rating():
      """获取 DNV CII 风格 A~E 合规评级。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      data = _evolution_engine.get_compliance_rating()
      # Add aliases expected by frontend
      data["grade"] = data.get("rating", "?")
      data["description"] = data.get("rating_label", "")
      escalation = _evolution_engine.get_escalation_status()
      if escalation.get("escalated_count", 0) > 0:
          data["escalation_tier"] = "corrective"
      else:
          data["escalation_tier"] = "normal"
      return data
  
  
  @router.post("/evolution/compliance-rating/calculate")
  async def evolution_calculate_rating():
      """重新计算合规评级 (运行快速审查)。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.calculate_compliance_rating()
  
  
  @router.get("/evolution/checklist")
  async def evolution_checklist(level: Optional[str] = None):
      """获取 ClassNK 双层自查清单 (company/ship)。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.get_checklist(level=level)
  
  
  @router.get("/evolution/zones")
  async def evolution_zones():
      """获取所有合规区域。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.get_all_zones()
  
  
  @router.get("/evolution/zones/active")
  async def evolution_active_zones():
      """获取当前激活的合规区域。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.get_active_zones()
  
  
  @router.post("/evolution/zones/update-position")
  async def evolution_update_position(lat: float = 0.0, lon: float = 0.0):
      """更新船舶位置，自动检测合规区域进入/离开。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.update_vessel_position(lat, lon)
  
  
  @router.get("/evolution/escalation")
  async def evolution_escalation():
      """获取失败升级状态 (DNV SEEMP Part III 风格)。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.get_escalation_status()
  
  
  @router.get("/evolution/trend")
  async def evolution_trend():
      """获取合规评级趋势分析。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      data = _evolution_engine.get_trend_analysis()
      # Frontend expects improvement_rate
      delta = data.get("trend_delta", 0.0)
      data["improvement_rate"] = round(delta, 1)
      return data
  
  
  @router.get("/evolution/monitoring")
  async def evolution_monitoring():
      """获取连续监控状态。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      data = _evolution_engine.get_monitoring_status()
      # Frontend expects 'active' bool and 'last_check' timestamp
      data["active"] = True
      if _evolution_engine._last_monitoring_time:
          from datetime import datetime as _dt
          data["last_check"] = _dt.fromtimestamp(_evolution_engine._last_monitoring_time).isoformat()
      else:
          data["last_check"] = None
      return data
  
  
  @router.get("/evolution/audit-trail")
  async 
  ```
  
  ### 文件: `src/backend/agents/agent_toolbox.py`
  ```py
  """AgentToolbox — function-calling tools for code-aware agents.
  
  Gives Developer / QA agents the ability to read, grep, write, and execute code
  in the project so they don't have to hallucinate file contents.
  
  All tool calls are scoped to the project root and write operations are
  restricted to a safe allowlist (src/, tests/, docs/, config/, public/).
  
  Each tool returns a JSON-serializable dict suitable for OpenAI/DeepSeek
  function-calling protocol.
  """
  from __future__ import annotations
  
  import json
  import logging
  import os
  import re
  import shlex
  import subprocess
  import time
  from pathlib import Path
  from typing import Any, Dict, List, Optional, Tuple
  
  logger = logging.getLogger("AgentToolbox")
  
  PROJECT_ROOT = Path(__file__).resolve().parents[3]  # src/backend/agents/ -> root
  ALLOWED_WRITE_PREFIXES = ("src/", "tests/", "docs/", "config/", "public/",
                             "storage/agent_workspaces/", "storage/pipeline_runs/")
  MAX_FILE_BYTES = 256 * 1024   # 256KB per read
  MAX_GREP_HITS = 200
  MAX_EXEC_OUTPUT = 32 * 1024   # 32KB stdout/stderr cap
  
  
  # ═════════════════════════════════════════════════════════════════
  # OpenAI / DeepSeek function-calling tool schema (V4 supports this)
  # ═════════════════════════════════════════════════════════════════
  
  TOOL_SCHEMA: List[Dict[str, Any]] = [
      {
          "type": "function",
          "function": {
              "name": "read_file",
              "description": (
                  "读取项目里某个文件的内容。优先使用此工具理解现有代码，再基于实际代码做修改。"
                  "只能读取项目根目录下的文件。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "path": {
                          "type": "string",
                          "description": "项目相对路径，如 src/backend/channels/marine_base.py",
                      },
                      "start_line": {"type": "integer", "description": "起始行 (1-based, 可选)", "default": 1},
                      "end_line": {"type": "integer", "description": "结束行 (1-based, 可选)", "default": 0},
                  },
                  "required": ["path"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "grep",
              "description": (
                  "在项目中按正则搜索文本。用于查找类/函数/枚举值的真实定义位置。"
                  "返回每个匹配的文件路径、行号、行内容。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "pattern": {"type": "string", "description": "正则表达式"},
                      "include": {
                          "type": "string",
                          "description": "glob 限定，如 src/backend/**/*.py",
                          "default": "**/*",
                      },
                      "max_hits": {"type": "integer", "default": 50},
                  },
                  "required": ["pattern"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "list_files",
              "description": "列出某个目录下的所有文件（递归）。",
              "parameters": {
                  "type": "object",
                  "properties": {
                      "path": {"type": "string", "description": "项目相对目录"},
                      "max_depth": {"type": "integer", "default": 3},
                  },
                  "required": ["path"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "write_file",
              "description": (
                  "向项目写入或新建文件。只能写入 src/, tests/, docs/, config/, public/ 下。"
                  "如果目标已存在，旧内容会先备份为 .bak。优先创建新文件而非整文件覆盖大文件。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "path": {"type": "string", "description": "项目相对路径"},
                      "content": {"type": "string", "description": "完整文件内容"},
                      "create_only": {
                          "type": "boolean",
                          "description": "为 true 时仅在文件不存在时写入",
                          "default": False,
                      },
                  },
                  "required": ["path", "content"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "patch_file",
              "description": (
                  "对已有文件做精准搜索-替换。比 write_file 安全，因为它要求你先看到原文。"
                  "search 必须是文件中存在的、唯一的连续片段。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "path": {"type": "string"},
                      "search": {"type": "string", "description": "要被替换的原文片段（必须唯一）"},
                      "replace": {"type": "string", "description": "替换为的新内容"},
                  },
                  "required": ["path", "search", "replace"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "run_python",
              "description": (
                  "在项目 venv 中执行一段 Python 代码（cwd=src/backend）。"
                  "用于验证 import 是否成功、检查类的属性等。最长执行 30s。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "code": {"type": "string", "description": "要执行的 Python 代码"},
                      "timeout": {"type": "integer", "default": 30},
                  },
                  "required": ["code"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "run_pytest",
              "description": (
                  "运行 pytest，可指定路径或 -k 表达式。仅 QA agent 使用。"
                  "返回最后 60 行输出。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "target": {"type": "string", "description": "测试路径或 -k 表达式", "default": ""},
                      "timeout": {"type": "integer", "default": 120},
                  },
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "finish",
              "description": (
                  "声明任务完成。Agent 调用此工具表示完成本步骤的所有工作，并附上简短总结。"
                  "调用后循环终止。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "summary": {"type": "string", "description": "本步骤完成情况的简短总结"},
                      "files_changed": {
                          "type": "array",
                          "items": {"type": "string"},
                          "description": "本步骤修改/新建的文件路径列表",
                          "default": [],
                      },
                  },
                  "required": ["summary"],
              },
          },
      },
  ]
  
  
  def _safe_path(rel: str) -> Path:
      """Resolve a project-relative path, refusing escapes."""
      if not rel:
          raise ValueError("empty path")
      p = (PROJECT_ROOT / rel).resolve()
      try:
          p.relative_to(PROJECT_ROOT)
      except ValueError:
          raise PermissionError(f"path escapes project root: {rel}")
      return p
  
  
  def _is_allowed_write(rel: str) -> bool:
      rel = rel.replace("\\", "/")
      return any(rel.startswith(p) for p in ALLOWED_WRITE_PREFIXES)
  
  
  # ═════════════════════════════════════════════════════════════════
  # Tool implementations
  # ═════════════════════════════════════════════════════════════════
  
  def tool_read_file(path: str, start_line: int = 1, end_line: int = 0) -> Dict[str, Any]:
      try:
          p = _safe_path(path)
          if not p.is_file():
              return {"ok": False, "error": f"not a file: {path}"}
          size = p.stat().st_size
          if size > MAX_FILE_BYTES * 4:
              return {
                  "ok": False,
                  "error": f"file too large ({size}B). Use grep to find the relevant section first.",
              }
          text = p.read_text(encoding="utf-8", errors="replace")
          lines = text.splitlines()
          total = len(lines)
          if end_line and end_line > 0:
              lines = lines[max(0, start_line - 1):end_line]
          elif start_line > 1:
              lines = lines[start_line - 1:]
          out = "\n".join(lines)
          if len(out) > MAX_FILE_BYTES:
              out = out[:MAX_FILE_BYTES] + "\n…(truncated)"
          return {"ok": True, "path": path, "total_lines": total, "content": out}
      except Exception as e:
          return {"ok": False, "error": str(e)}
  
  
  def tool_grep(pattern: str, include: str = "**/*", max_hits: int = 50) -> Dict[str, Any]:
      try:
          regex = re.compile(pattern)
      except re.error as e:
          return {"ok": False, "error": f"bad regex: {e}"}
      max_hits = min(max_hits, MAX_GREP_HITS)
      hits: List[Dict[str, Any]] = []
      for fp in PROJECT_ROOT.glob(include):
          if not fp.is_file():
              continue
          # Skip irrelevant
          rel = str(fp.relative_to(PROJECT_ROOT))
          if any(seg in rel for seg in ("/node_modules/", "/.git/", "/__pycache__/", "/venv/", ".bak")):
              continue
          try:
              with fp.open("r", encoding="utf-8", errors="replace") as f:
                  for i, line in enumerate(f, 1):
                      if regex.search(line):
                          hits.append({"path": rel, "line": i, "text": line.rstrip()[:200]})
                          if len(hits) >= max_hits:
                              return {"ok": True, "hits": hits, "truncated": True}
          except Exception:
              continue
      return {"ok": True, "hits": hits, "truncated": False}
  
  
  def tool_list_files(path: str, max_depth: int = 3) -> Dict[str, Any]:
      try:
          p = _safe_path(path)
          if not p.is_dir():
              return {"ok": False, "error": f"not a directory: {path}"}
          out: List[str] = []
          base_depth = len(p.parts)
          for root, dirs, files in os.walk(p):
              depth = len(Path(root).parts) - base_depth
              if depth > max_depth:
                  dirs[:] = []
                  continue
              dirs[:] = [d for d in dirs
                         if not d.startswith(".")
                         and d not in ("node_modules", "__pycache__", "venv")]
              for f in files:
                  if f.endswith((".pyc", ".bak")):
                      continue
                  rel = str((Path(root) / f).relative_to(PROJECT_ROOT))
                  out.append(rel)
                  if len(out) >= 500:
                      return {"ok": True, "files": out, "truncated": True}
          return {"ok": True, "files": out, "truncated": False}
      except Exception as e:
          return {"ok": False, "error": str(e)}
  
  
  def tool_write_file(path: str, content: str, create_only: bool = False) -> Dict[str, Any]:
      try:
          if not _is_allowed_write(path):
              return {"ok": False, "error": f"write denied (outside allowed dirs): {path}"}
          p = _safe_path(path)
          if p.exists() and create_only:
              return {"ok": False, "error": f"file exists and create_only=True: {path}"}
          # Shrink-replace guard
          if p.is_file():
              old_size = p.stat().st_size
              if old_size > 2048 and len(content) < old_size * 0.5:
                  return {
                      "ok": False,
                      "error": (
                          f"shrink-replace blocked: new {len(content)}B "
                          f"< 50% of existing {old_size}B. "
                          f"Use patch_file for incremental edits, or write a new file."
                      ),
                  }
              # Backup
              bak = p.with_suffix(p.suffix + ".bak")
              try:
                  bak.write_bytes(p.read_bytes())
              except Exception:
                  pass
          p.parent.mkdir(parents=True, exist_ok=True)
          p.write_text(content, encoding="utf-8")
          return {"ok": True, "path": path, "bytes": len(content), "created": not p.exists()}
      except Exception as e:
          return {"ok": False, "error": str(e)}
  
  
  def tool_patch_file(path: str, search: str, replace: str) -> Dict[str, Any]:
      try:
          if not _is_allowed_write(path):
              return {"ok": False, "error": f"write denied: {path}"}
          p = _safe_path(path)
          if not p.is_file():
              return {"ok": False, "error": f"file not found: {path}"}
          text = p.read_text(encoding="utf-8")
          cnt = text.count(search)
          if cnt == 0:
              return {"ok": False, "error": "search pattern not found in file"}
          if cnt > 1:
              return {
                  "ok": False,
                  "error": f"search pattern matches {cnt} times — must be unique. Add more context.",
              }
          new_text = text.replace(search, replace, 1)
          bak = p.with_suffix(p.suffix + ".bak")
          try:
              bak.write_text(text, encoding="utf-8")
          except Exception:
              pass
          p.write_text(new_text, encoding="utf-8")
          return {"ok": True, "path": path, "old_bytes": len(text), "new_bytes": len(new_text)}
      except Exception as e:
          return {"ok": False, "error": str(e)}
  
  
  def _run_subprocess(cmd: List[str], cwd: Path, timeout: int) -> Dict[str, Any]:
      start = time.time()
      try:
          proc = subprocess.run(
              cmd, cwd=str(cwd), capture_output=True, text=True,
              timeout=timeout,
              env={**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
          )
          elapsed = time.time() - start
          out = proc.stdout or ""
          err = proc.stderr or ""
          if len(out) > MAX_EXEC_OUTPUT:
              out = "…(truncated)\n" + out[-MAX_EXEC_OUTPUT:]
          if len(err) > MAX_EXEC_OUTPUT:
              err = "…(truncated)\n" + err[-MAX_EXEC_OUTPUT:]
          return {
              "ok": True,
              "exit_code": proc.returncode,
              "stdout": out,
              "stderr": err,
              "elapsed_sec": round(elapsed, 2),
          }
      except subprocess.TimeoutExpired:
          return {"ok": False, "error": f"timeout after {timeout}s"}
      except Exception as e:
          return {"ok": False, "error": str(e)}
  
  
  def tool_run_python(code: str, timeout: int = 30) -> Dict[str, Any]:
      venv_py = PROJECT_ROOT / "venv" / "bin" / "python"
      py = str(venv_py) if venv_py.exists() else "python3"
      cwd = PROJECT_ROOT / "src" / "backend"
      return _run_subprocess([py, "-c", code], cwd, timeout)
  
  
  def tool_run_pytest(target: str = "", timeout: int = 120) -> Dict[str, Any]:
      venv_py = PROJECT_ROOT / "venv" / "bin" / "python"
      py = str(venv_py) if venv_py.exists() else "python3"
      args = [py, "-m", "pytest", "-q", "--tb=short", "--maxfail=5"]
      if target:
          if target.startswith("-k") or "::" in target or target.endswith(".py"):
              if target.startswith("-k"):
                  args += target.split(maxsplit=1)
              else:
                  args.append(target)
          else:
              args += ["-k", target]
      return _run_subprocess(args, PROJECT_ROOT, timeout)
  
  
  # ═════════════════════════════════════════════════════════════════
  # Dispatcher
  # ═════════════════════════════════════════════════════════════════
  
  _DISPATCH = {
      "read_file": l
  ```
  
  ### 文件: `src/backend/agents/models.py`
  ```py
  # -*- coding: utf-8 -*-
  """AgentsGroup2026 Agent Team Framework — Core Data Models.
  
  Inspired by Clawith platform architecture:
  - AgentTeam = Company (team-level resource sharing)
  - AgentProfile = Employee (individual agent with personality/skills/permissions)
  - ModelConfig = Model Pool entry
  - ToolDefinition = Tool catalog entry
  - SkillDefinition = Skill catalog entry
  """
  
  from __future__ import annotations
  
  import uuid
  from dataclasses import dataclass, field
  from datetime import datetime, timezone
  from enum import Enum
  from typing import Any, Dict, List, Optional
  
  
  # ── Enums ──────────────────────────────────────────────────────────────────
  
  
  class AgentState(Enum):
      """Agent lifecycle states."""
  
      IDLE = "idle"
      WORKING = "working"
      PAUSED = "paused"
      ERROR = "error"
      STOPPED = "stopped"
  
  
  class ToolCategory(Enum):
      """Tool classification categories."""
  
      GENERAL = "general"
      BROWSER = "browser"
      CODE_EXECUTION = "code_execution"
      COMMUNICATION = "communication"
      FILE_OPERATION = "file_operation"
      TRIGGERS = "triggers"
      DISCOVERY = "discovery"
      DIGITAL_TWIN = "digital_twin"
      # Hermes-style tool categories
      WEB = "web"
      VISION = "vision"
      MEMORY = "memory"
      SKILLS = "skills"
      DELEGATION = "delegation"
  
  
  class SkillCategory(Enum):
      """Skill classification categories."""
  
      GENERAL = "general"
      DIGITAL_TWIN = "digital_twin"
      AUTOMATION = "automation"
      # Hermes-style skill categories
      RESEARCH = "research"
      DOMAIN_KNOWLEDGE = "domain_knowledge"
  
  
  class Visibility(Enum):
      """Visibility level for teams/agents."""
  
      PUBLIC = "public"
      PRIVATE = "private"
      INTERNAL = "internal"
  
  
  class AccessLevel(Enum):
      """Permission access levels."""
  
      READ = "read"
      WRITE = "write"
      ADMIN = "admin"
  
  
  class AgentTemplateType(Enum):
      """Predefined agent template types."""
  
      RESEARCHER = "researcher"
      DEVELOPER = "developer"
      ANALYST = "analyst"
      ENGINEER = "engineer"
      COORDINATOR = "coordinator"
      CUSTOM = "custom"
      # Hermes-style agent types
      HERMES_RESEARCHER = "hermes_researcher"
      HERMES_DEVELOPER = "hermes_developer"
      HERMES_CREATIVE = "hermes_creative"
  
  
  # ── Dataclasses ────────────────────────────────────────────────────────────
  
  
  @dataclass
  class ModelConfig:
      """LLM model configuration entry."""
  
      model_id: str = ""
      provider: str = "anthropic"
      name: str = "claude-sonnet-4-20250514"
      max_tokens: int = 65536
      temperature: float = 0.7
      is_default: bool = False
      enabled: bool = True
      api_key: str = ""
      api_base_url: str = ""
  
      def __post_init__(self) -> None:
          if not self.model_id:
              self.model_id = str(uuid.uuid4())[:8]
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "model_id": self.model_id,
              "provider": self.provider,
              "name": self.name,
              "max_tokens": self.max_tokens,
              "temperature": self.temperature,
              "is_default": self.is_default,
              "enabled": self.enabled,
              "api_key": ("****" + self.api_key[-4:]) if len(self.api_key) >= 4 else ("****" if self.api_key else ""),
              "api_base_url": self.api_base_url,
              "has_api_key": bool(self.api_key),
          }
  
  
  @dataclass
  class ToolDefinition:
      """Tool catalog entry."""
  
      tool_id: str = ""
      name: str = ""
      description: str = ""
      category: ToolCategory = ToolCategory.BROWSER
      enabled: bool = True
      requires_approval: bool = False
      parameters: Dict[str, Any] = field(default_factory=dict)
      icon: str = "🔧"
      config_schema: Dict[str, Any] = field(default_factory=dict)
      config: Dict[str, Any] = field(default_factory=dict)
      is_default: bool = False
      source: str = "builtin"
  
      def __post_init__(self) -> None:
          if not self.tool_id:
              self.tool_id = str(uuid.uuid4())[:8]
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "tool_id": self.tool_id,
              "name": self.name,
              "description": self.description,
              "category": self.category.value,
              "enabled": self.enabled,
              "requires_approval": self.requires_approval,
              "parameters": self.parameters,
              "icon": self.icon,
              "config_schema": self.config_schema,
              "config": self.config,
              "is_default": self.is_default,
              "source": self.source,
          }
  
  
  @dataclass
  class SkillDefinition:
      """Skill catalog entry."""
  
      skill_id: str = ""
      name: str = ""
      description: str = ""
      category: SkillCategory = SkillCategory.GENERAL
      required: bool = False
      enabled: bool = True
      icon: str = "⚡"
      config_schema: Dict[str, Any] = field(default_factory=dict)
      config: Dict[str, Any] = field(default_factory=dict)
      is_default: bool = False
      source: str = "builtin"
      slug: str = ""
      required_tools: List[str] = field(default_factory=list)
      instructions: str = ""
  
      def __post_init__(self) -> None:
          if not self.skill_id:
              self.skill_id = str(uuid.uuid4())[:8]
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "skill_id": self.skill_id,
              "name": self.name,
              "description": self.description,
              "category": self.category.value,
              "required": self.required,
              "enabled": self.enabled,
              "icon": self.icon,
              "config_schema": self.config_schema,
              "config": self.config,
              "is_default": self.is_default,
              "source": self.source,
              "slug": self.slug,
              "required_tools": self.required_tools,
              "has_instructions": bool(self.instructions),
          }
  
  
  @dataclass
  class AgentPersonality:
      """Agent personality and behavior configuration."""
  
      tone: str = "professional"
      language: str = "zh-CN"
      expertise_areas: List[str] = field(default_factory=list)
      response_style: str = "concise"
      creativity: float = 0.5
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "tone": self.tone,
              "language": self.language,
              "expertise_areas": self.expertise_areas,
              "response_style": self.response_style,
              "creativity": self.creativity,
          }
  
  
  @dataclass
  class ToolsetDistribution:
      """Hermes-style probabilistic toolset distribution.
  
      Each toolset has a % probability of being available per turn.
      Inspired by NousResearch/hermes-agent toolset_distributions.py.
      """
  
      name: str = "default"
      description: str = ""
      toolsets: Dict[str, int] = field(default_factory=dict)
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "name": self.name,
              "description": self.description,
              "toolsets": self.toolsets,
          }
  
  
  @dataclass
  class HermesAgentConfig:
      """Hermes-style agent configuration — extends AgentProfile with
      learning loop, memory, skills, toolsets, and context management.
  
      Inspired by NousResearch/hermes-agent architecture:
      - Closed learning loop (skills from experience)
      - Persistent memory across sessions
      - Toolset distributions for probabilistic tool access
      - SOUL.md persona
      - Context files (AGENTS.md, HERMES.md)
      - Session search (cross-session recall)
      - Delegate/subagent parallelization
      """
  
      # Agent loop parameters
      max_iterations: int = 90
      iteration_budget: int = 90
  
      # Toolset distribution (Hermes-style probabilistic tool selection)
      toolset_distribution: ToolsetDistribution = field(
          default_factory=lambda: ToolsetDistribution(name="default")
      )
      enabled_toolsets: List[str] = field(default_factory=list)
      disabled_toolsets: List[str] = field(default_factory=list)
  
      # Memory & learning
      memory_enabled: bool = True
      session_search_enabled: bool = True
      skill_auto_create: bool = True
      soul_md: str = ""
      context_files: List[str] = field(default_factory=list)
  
      # Delegation
      can_delegate: bool = False
      max_subagents: int = 3
  
      # Platform
      platform: str = "cli"
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "max_iterations": self.max_iterations,
              "iteration_budget": self.iteration_budget,
              "toolset_distribution": self.toolset_distribution.to_dict(),
              "enabled_toolsets": self.enabled_toolsets,
              "disabled_toolsets": self.disabled_toolsets,
              "memory_enabled": self.memory_enabled,
              "session_search_enabled": self.session_search_enabled,
              "skill_auto_create": self.skill_auto_create,
              "soul_md": self.soul_md,
              "context_files": self.context_files,
              "can_delegate": self.can_delegate,
              "max_subagents": self.max_subagents,
              "platform": self.platform,
          }
  
  
  @dataclass
  class AgentPermission:
      """Agent access permission."""
  
      resource: str = ""
      access_level: AccessLevel = AccessLevel.READ
      channels: List[str] = field(default_factory=list)
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "resource": self.resource,
              "access_level": self.access_level.value,
              "channels": self.channels,
          }
  
  
  @dataclass
  class AgentChannelConfig:
      """Channel subscription configuration for an agent."""
  
      channel_name: str = ""
      subscribe: bool = True
      publish: bool = False
      priority: int = 0
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "channel_name": self.channel_name,
              "subscribe": self.subscribe,
              "publish": self.publish,
              "priority": self.priority,
          }
  
  
  @dataclass
  class AgentProfile:
      """Individual agent profile — the Employee equivalent."""
  
      agent_id: str = ""
      name: str = ""
      role: str = ""
      description: str = ""
      template_type: AgentTemplateType = AgentTemplateType.CUSTOM
      state: AgentState = AgentState.IDLE
      model_id: str = ""
      system_prompt: str = ""
      personality: AgentPersonality = field(default_factory=AgentPersonality)
      permissions: List[AgentPermission] = field(default_factory=list)
      channels: List[AgentChannelConfig] = field(default_factory=list)
      tools: List[str] = field(default_factory=list)
      skills: List[str] = field(default_factory=list)
      metadata: Dict[str, Any] = field(default_factory=dict)
      created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
      # Hermes-style agent config (optional — non-None means Hermes mode)
      hermes_config: Optional[HermesAgentConfig] = None
  
      def __post_init__(self) -> None:
          if not self.agent_id:
              self.agent_id = str(uuid.uuid4())[:8]
  
      @property
      def is_hermes_agent(self) -> bool:
          return self.hermes_config is not None
  
      def to_dict(self) -> Dict[str, Any]:
          d = {
              "agent_id": self.agent_id,
              "name": self.name,
              "role": self.role,
              "description": self.description,
              "template_type": self.template_type.value,
              "state": self.state.value,
              "model_id": self.model_id,
              "system_prompt": self.system_prompt,
              "personality": self.personality.to_dict(),
              "permissions": [p.to_dict() for p in self.permissions],
              "channels": [c.to_dict() for c in self.channels],
              "tools": self.tools,
              "skills": self.skills,
              "metadata": self.metadata,
              "created_at": self.created_at,
              "is_hermes_agent": self.is_hermes_agent,
          }
          if self.hermes_config is not None:
              d["hermes_config"] = self.hermes_config.to_dict()
          return d
  
  
  @dataclass
  class AgentTeam:
      """Agent team — the Company equivalent. Holds shared resources."""
  
      team_id: str = ""
      name: str = ""
      description: str = ""
      visibility: Visibility = Visibility.PRIVATE
      agents: Dict[str, AgentProfile] = field(default_factory=dict)
      models: Dict[str, ModelConfig] = field(default_factory=dict)
      tools: Dict[str, ToolDefinition] = field(default_factory=dict)
      skills: Dict[str, SkillDefinition] = field(default_factory=dict)
      metadata: Dict[str, Any] = field(default_factory=dict)
      created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
  
      def __post_init__(self) -> None:
          if not self.team_id:
              self.team_id = str(uuid.uuid4())[:8]
  
      def add_agent(self, agent: AgentProfile) -> None:
          self.agents[agent.agent_id] = agent
  
      def remove_agent(self, agent_id: str) -> Optional[AgentProfile]:
          return self.agents.pop(agent_id, None)
  
      def get_agent(self, agent_id: str) -> Optional[AgentProfile]:
          return self.agents.get(agent_id)
  
      def add_model(self, model: ModelConfig) -> None:
          self.models[model.model_id] = model
  
      def remove_model(self, model_id: str) -> Optional[ModelConfig]:
          return self.models.pop(model_id, None)
  
      def get_model(self, model_id: str) -> Optional[ModelConfig]:
          return self.models.get(model_id)
  
      def add_tool(self, tool: ToolDefinition) -> None:
          self.tools[tool.tool_id] = tool
  
      def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
          return self.tools.get(tool_id)
  
      def add_skill(self, skill: SkillDefinition) -> None:
          self.skills[skill.skill_id] = skill
  
      def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
          return self.skills.get(skill_id)
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "team_id": self.team_id,
              "name": self.name,
              "description": self.description,
              "visibility": self.visibility.value,
              "agents": {k: v.to_dict() for k, v in self.agents.items()},
              "models": {k: v.to_dict() for k, v in self.models.items()},
              "tools": {k: v.to_dict() for k, v in self.tools.items()},
              "skills": {k: v.to_dict() for k, v in self.skills.items()},
              "metadata": self.metadata,
              "created_at": self.created_at,
          }
  
  ```
  
  ### 文件: `src/backend/agents/plaza_engine.py`
  ```py
  # -*- coding: utf-8 -*-
  """智能体广场引擎 — 讨论编排与多 Agent 协同.
  
  核心编排逻辑:
  1. Moderator（主持人壁龛）提出子话题，引导讨论方向
  2. 每轮: 各参与者按座席层级依次发言（内圈→中圈→外圈）
  3. Moderator 总结本轮关键观点
  4. 最终轮: Moderator 生成全局总结 + 关键结论
  
  消息通过 asyncio.Queue 实时推送给 SSE 订阅者。
  """
  
  from __future__ import annotations
  
  import asyncio
  import json
  import logging
  import re
  from datetime import datetime, timezone
  from typing import Any, AsyncIterator, Callable, Dict, List, Optional
  from uuid import uuid4
  
  from .plaza import (
      Discussion, DiscussionStatus, NicheRole, Participant,
      Plaza, PlazaMessage, SeatTier, PRESET_TOPICS,
  )
  from .plaza_store import PlazaStore
  
  logger = logging.getLogger(__name__)
  
  _ROUND_SPEAKER_LIMIT = 5
  _EXCHANGES_PER_ROUND = 2  # 每轮内交锋次数
  _SPEAKERS_PER_EXCHANGE = 3  # 每次交锋参与人数
  _CORE_ROLE_PRIORITY = {
      "architect": 0,
      "researcher": 1,
      "developer": 2,
      "qa_engineer": 3,
      "qa": 3,
      "tester": 3,
      "devops": 4,
      "project_manager": 5,
      "documentation": 6,
  }
  
  
  class PlazaEngine:
      """广场引擎 — 管理广场、参与者和讨论编排."""
  
      def __init__(self):
          self._store = PlazaStore()
          self._plazas: Dict[str, Plaza] = self._store.load_all()
          self._sse_queues: Dict[str, List[asyncio.Queue]] = {}  # discussion_id → queues
          self._discussion_locks: Dict[str, asyncio.Lock] = {}
          self._chat_fn: Optional[Callable] = None  # ChatHarness.chat reference
  
      def set_chat_fn(self, fn: Callable):
          """注入 ChatHarness.chat 异步函数."""
          self._chat_fn = fn
  
      def _get_agent_profile(self, agent_id: str):
          """从 TeamManager 获取完整 AgentProfile，用于注入个性."""
          try:
              from agents.api import _team_manager
              if _team_manager:
                  for team in _team_manager.list_teams():
                      agent = team.get_agent(agent_id)
                      if agent:
                          return agent
          except Exception:
              pass
          return None
  
      def _build_agent_system_prompt(self, participant: Participant) -> str:
          """根据 AgentProfile 构建有个性的 system prompt."""
          profile = self._get_agent_profile(participant.agent_id)
          if profile:
              expertise = "、".join(profile.personality.expertise_areas) if profile.personality.expertise_areas else ""
              traits = "、".join(profile.metadata.get("traits", [])) if profile.metadata else ""
              parts = [
                  f"你是 {profile.name}，职责: {profile.role}。",
                  f"专长: {expertise}。" if expertise else "",
                  f"性格特质: {traits}。" if traits else "",
                  f"你的工作方式: {profile.system_prompt}" if profile.system_prompt else "",
                  f"\n你正在一个智能体广场的讨论中发言。",
                  f"请用自然的方式说话，像一个真实的专业人士在开会讨论。",
                  f"可以表达观点、提出建议、回应他人，说话要有内容、有依据。",
                  f"不需要客套寒暄，但要说人话，不要像电报一样压缩。",
              ]
              return "".join(p for p in parts if p)
          # 回退到基础信息
          return (
              f"你是 {participant.agent_name}，职责: {participant.role}。"
              f"你正在一个智能体广场的讨论中发言。"
              f"请用自然的方式说话，像一个真实的专业人士在开会讨论。"
              f"可以表达观点、提出建议、回应他人，说话要有内容、有依据。"
          )
  
      # ── 广场 CRUD ──────────────────────────────────────────
  
      def create_plaza(self, name: str, description: str = "") -> Plaza:
          plaza = Plaza(name=name, description=description)
          self._plazas[plaza.id] = plaza
          self._store.save_plaza(plaza)
          logger.info(f"🏛️ 广场创建: {name} ({plaza.id})")
          return plaza
  
      def get_plaza(self, plaza_id: str) -> Optional[Plaza]:
          return self._plazas.get(plaza_id)
  
      def list_plazas(self) -> List[Plaza]:
          return list(self._plazas.values())
  
      def delete_plaza(self, plaza_id: str) -> bool:
          if plaza_id in self._plazas:
              del self._plazas[plaza_id]
              self._store.delete_plaza(plaza_id)
              return True
          return False
  
      # ── 参与者管理 ──────────────────────────────────────────
  
      def add_participant(
          self, plaza_id: str, agent_id: str, agent_name: str = "",
          role: str = "", team_id: str = "",
          seat_tier: SeatTier = SeatTier.MIDDLE,
          niche_role: NicheRole = NicheRole.OBSERVER,
      ) -> Optional[Participant]:
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return None
          # 分配壁龛编号 (动态扩展)
          used_niches = {p.niche_index for p in plaza.participants.values() if p.niche_index >= 0}
          niche_index = len(used_niches)
          # 自动扩展壁龛数
          if niche_index >= plaza.niche_count:
              plaza.niche_count = niche_index + 1
          p = Participant(
              agent_id=agent_id, agent_name=agent_name, role=role,
              team_id=team_id, seat_tier=seat_tier, niche_role=niche_role,
              niche_index=niche_index,
          )
          plaza.participants[agent_id] = p
          self._store.save_plaza(plaza)
          logger.info(f"🪑 参与者加入广场 {plaza_id}: {agent_name} (壁龛 #{niche_index})")
          return p
  
      def remove_participant(self, plaza_id: str, agent_id: str) -> bool:
          plaza = self._plazas.get(plaza_id)
          if plaza and agent_id in plaza.participants:
              del plaza.participants[agent_id]
              self._store.save_plaza(plaza)
              return True
          return False
  
      # ── 讨论管理 ──────────────────────────────────────────
  
      def create_discussion(
          self, plaza_id: str, topic: str, description: str = "",
          moderator_agent_id: str = "", max_rounds: int = 5,
      ) -> Optional[Discussion]:
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return None
          disc = Discussion(
              plaza_id=plaza_id, topic=topic, description=description,
              moderator_agent_id=moderator_agent_id, max_rounds=max_rounds,
          )
          plaza.discussions[disc.id] = disc
          self._store.save_plaza(plaza)
          logger.info(f"💬 讨论创建: {topic[:40]} ({disc.id})")
          return disc
  
      def get_discussion(self, plaza_id: str, discussion_id: str) -> Optional[Discussion]:
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return None
          return plaza.discussions.get(discussion_id)
  
      def list_discussions(self, plaza_id: str) -> List[Discussion]:
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return []
          return list(plaza.discussions.values())
  
      def delete_discussion(self, plaza_id: str, discussion_id: str) -> bool:
          plaza = self._plazas.get(plaza_id)
          if not plaza or discussion_id not in plaza.discussions:
              return False
          del plaza.discussions[discussion_id]
          self._sse_queues.pop(discussion_id, None)
          self._store.save_plaza(plaza)
          return True
  
      def reset_discussion(self, plaza_id: str, discussion_id: str) -> Optional[Discussion]:
          """重置已结束讨论，保留话题本身以便重新讨论。"""
          disc = self.get_discussion(plaza_id, discussion_id)
          if not disc:
              return None
          disc.status = DiscussionStatus.OPEN
          disc.current_round = 0
          disc.messages.clear()
          disc.summary = ""
          disc.key_conclusions.clear()
          disc.plan.clear()
          disc.assigned_team_id = ""
          disc.started_at = None
          disc.ended_at = None
          plaza = self._plazas.get(plaza_id)
          if plaza:
              self._store.save_plaza(plaza)
          return disc
  
      # ── SSE 订阅管理 ──────────────────────────────────────
  
      def subscribe(self, discussion_id: str) -> asyncio.Queue:
          q: asyncio.Queue = as
  ```
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
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

🔗 API: api.deepseek.com | 模型: deepseek-chat
────────────────────────────────────────────────────────────

# 任务分解与规划：侵入式溯因与维度断路器/修复模板绑定

## 1. 任务需求分析

### 1.1 核心目标
实现一个告警驱动的自动化响应系统，当系统触发告警时：
1. **侵入式溯因**：自动分析告警根因
2. **维度断路器绑定**：将告警与断路器机制关联
3. **修复模板绑定**：自动匹配修复方案
4. **自动生成专项 Backlog**：创建修复任务
5. **冻结非关键调用**：降低系统负载

### 1.2 关键概念定义

| 概念 | 定义 |
|------|------|
| **侵入式溯因** | 在系统运行时主动注入探测点，收集上下文数据用于根因分析 |
| **维度断路器** | 按功能维度（如API、数据库、缓存）划分的熔断机制 |
| **修复模板** | 预定义的修复方案模板，包含修复步骤和验证条件 |
| **专项 Backlog** | 针对特定告警生成的临时任务队列 |
| **非关键调用冻结** | 临时暂停非核心功能的调用以保护系统 |

## 2. 技术风险评估

### 2.1 依赖关系分析

```
┌─────────────────────────────────────────────────────────────┐
│                    现有系统组件依赖图                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  monitoring/collector.py ──→ monitoring/models.py           │
│       ↓                                                     │
│  monitoring/plaza_monitor.py ──→ agents/plaza_engine.py     │
│       ↓                                                     │
│  agents/agent_loop.py ──→ agents/agent_toolbox.py           │
│       ↓                                                     │
│  agents/task_engine.py ──→ agents/task_store.py             │
│       ↓                                                     │
│  channels/system_evolution.py ──→ agent_team_api.py         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 主要风险

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| 侵入式探测可能影响性能 | 高 | 使用采样率控制，异步非阻塞 |
| 断路器误触发导致服务降级 | 高 | 配置阈值可调，手动覆盖机制 |
| 修复模板匹配不准确 | 中 | 多级匹配策略，人工确认环节 |
| Backlog与现有任务系统冲突 | 中 | 独立命名空间，隔离管理 |
| 冻结调用影响用户体验 | 中 | 白名单机制，关键API豁免 |

## 3. 任务分解结构

### 3.1 总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    告警响应系统架构                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ 告警检测  │───→│ 侵入式    │───→│ 维度      │───→│ 修复      │  │
│  │ (现有)    │    │ 溯因引擎  │    │ 断路器    │    │ 模板匹配  │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│       │              │              │              │            │
│       ▼              ▼              ▼              ▼            │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ 告警队列  │    │ 溯因结果  │    │ 断路器    │    │ 修复      │  │
│  │ (增强)    │    │ 缓存      │    │ 状态管理  │    │ 方案库    │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│       │              │              │              │            │
│       └──────────────┴──────────────┴──────────────┘            │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              自动化响应编排器                               │    │
│  │  ├─ 生成专项 Backlog                                      │    │
│  │  ├─ 冻结非关键调用                                        │    │
│  │  └─ 触发修复流程                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 子任务分解

#### 子任务 1：侵入式溯因引擎 (Invasive Abduction Engine)

**文件路径**: `src/backend/monitoring/abduction_engine.py`

**功能描述**:
- 接收告警事件，自动注入探测点
- 收集相关维度的上下文数据
- 执行根因分析算法
- 输出结构化溯因报告

**接口定义**:
```python
class AbductionEngine:
    async def analyze_alert(self, alert: AlertEvent) -> AbductionResult
    async def inject_probe(self, dimension: str, probe_config: ProbeConfig)
    async def collect_context(self, alert_id: str) -> ContextSnapshot
    def get_abduction_result(self, alert_id: str) -> Optional[AbductionResult]
```

**依赖**:
- `monitoring/models.py` - AlertEvent 模型
- `monitoring/collector.py` - 数据收集接口
- `agents/agent_toolbox.py` - 工具调用能力

**测试要点**:
- 告警接收与解析
- 探测点注入与数据收集
- 根因分析准确性
- 并发告警处理

---

#### 子任务 2：维度断路器管理器 (Dimension Circuit Breaker Manager)

**文件路径**: `src/backend/monitoring/circuit_breaker.py`

**功能描述**:
- 按维度管理断路器状态（CLOSED/OPEN/HALF_OPEN）
- 绑定告警到对应维度断路器
- 提供断路器状态查询和手动控制
- 支持断路器阈值配置

**接口定义**:
```python
class DimensionCircuitBreaker:
    async def register_dimension(self, dimension: str, config: BreakerConfig)
    async def on_alert(self, alert: AlertEvent, dimension: str) -> BreakerState
    async def trip_breaker(self, dimension: str) -> bool
    async def reset_breaker(self, dimension: str) -> bool
    def get_breaker_status(self, dimension: str) -> Optional[BreakerState]
    def get_all_breakers(self) -> Dict[str, BreakerState]
```

**依赖**:
- `monitoring/models.py` - 断路器状态模型
- `agents/plaza_monitor.py` - 监控数据源

**测试要点**:
- 断路器状态转换
- 告警触发断路器
- 阈值配置生效
- 手动覆盖功能

---

#### 子任务 3：修复模板库与匹配引擎 (Repair Template Library & Matcher)

**文件路径**: `src/backend/monitoring/repair_templates.py`

**功能描述**:
- 管理修复模板的CRUD
- 根据溯因结果匹配最佳修复模板
- 支持模板参数化
- 提供模板执行状态跟踪

**接口定义**:
```python
class RepairTemplateManager:
    async def create_template(self, template: RepairTemplate) -> str
    async def match_template(self, result: AbductionResult) -> Optional[RepairTemplate]
    async def execute_template(self, template_id: str, params: Dict) -> ExecutionResult
    def list_templates(self, filters: Dict) -> List[RepairTemplate]
    def get_template(self, template_id: str) -> Optional[RepairTemplate]
```

**依赖**:
- `agents/agent_toolbox.py` - 执行修复操作
- `agents/task_engine.py` - 任务执行接口

**测试要点**:
- 模板匹配准确性
- 模板参数化执行
- 模板版本管理
- 执行状态跟踪

---

#### 子任务 4：专项 Backlog 生成器 (Special Backlog Generator)

**文件路径**: `src/backend/monitoring/backlog_generator.py`

**功能描述**:
- 根据溯因结果和修复模板生成专项Backlog
- Backlog包含修复步骤、优先级、依赖关系
- 与现有任务系统集成
- 支持Backlog状态跟踪

**接口定义**:
```python
class BacklogGenerator:
    async def generate_backlog(self, alert: AlertEvent, result: AbductionResult) -> SpecialBacklog
    async def update_backlog_status(self, backlog_id: str, status: BacklogStatus)
    def get_backlog(self, backlog_id: str) -> Optional[SpecialBacklog]
    def list_active_backlogs(self) -> List[SpecialBacklog]
    def close_backlog(self, backlog_id: str) -> bool
```

**依赖**:
- `agents/task_store.py` - 任务存储
- `agents/task_engine.py` - 任务执行引擎
- `agent_team_api.py` - API接口

**测试要点**:
- Backlog生成完整性
- 与现有任务系统集成
- 状态转换正确性
- 并发Backlog管理

---

#### 子任务 5：非关键调用冻结器 (Non-Critical Call Freezer)

**文件路径**: `src/backend/monitoring/call_freezer.py`

**功能描述**:
- 定义关键/非关键调用分类
- 根据告警级别自动冻结非关键调用
- 支持白名单机制
- 提供冻结状态查询和手动恢复

**接口定义**:
```python
class CallFreezer:
    async def freeze_non_critical(self, alert: AlertEvent, dimensions: List[str]) -> FreezeResult
    async def restore_calls(self, freeze_id: str) -> bool
    def register_critical_call(self, call_name: str, dimension: str)
    def register_non_critical_call(self, call_name: str, dimension: str)
    def get_freeze_status(self) -> FreezeStatus
    def get_frozen_calls(self) -> List[FrozenCall]
```

**依赖**:
- `agents/agent_loop.py` - Agent调用管理
- `channels/bridge_chat.py` - 通信通道

**测试要点**:
- 冻结/恢复逻辑
- 白名单生效
- 告警级别关联
- 性能影响

---

#### 子任务 6：自动化响应编排器 (Automated Response Orchestrator)

**文件路径**: `src/backend/monitoring/response_orchestrator.py`

**功能描述**:
- 编排整个告警响应流程
- 协调各组件协作
- 提供流程状态监控
- 支持人工干预

**接口定义**:
```python
class ResponseOrchestrator:
    async def handle_alert(self, alert: AlertEvent) -> ResponseResult
    async def cancel_response(self, response_id: str) -> bool
    def get_response_status(self, response_id: str) -> Optional[ResponseStatus]
    def get_response_history(self, filters: Dict) -> List[ResponseRecord]
    def set_manual_intervention(self, response_id: str, action: str)
```

**依赖**:
- 以上所有子任务组件
- `agent_team_api.py` - API暴露
- `channels/system_evolution.py` - 系统演进

**测试要点**:
- 完整流程编排
- 异常处理
- 人工干预机制
- 性能基准

---

#### 子任务 7：API 集成与前端适配

**文件路径**: 
- `src/backend/agent_team_api.py` (扩展)
- `src/frontend/js/agent-team-config.js` (扩展)
- `src/frontend/system-evolution.html` (扩展)

**功能描述**:
- 暴露告警响应相关API
- 前端展示告警状态和响应流程
- 提供手动控制界面

**新增API端点**:
```python
# 在 agent_team_api.py 中新增
@router.get("/monitoring/abduction/status")
@router.get("/monitoring/breakers")
@router.post("/monitoring/breakers/{dimension}/reset")
@router.get("/monitoring/templates")
@router.post("/monitoring/templates")
@router.get("/monitoring/backlogs")
@router.get("/monitoring/freezes")
@router.post("/monitoring/freezes/{freeze_id}/restore")
@router.get("/monitoring/orchestrator/status")
```

**测试要点**:
- API响应正确性
- 前端展示完整性
- 手动控制功能
- 错误处理

---

## 4. 实施路线图

### 4.1 阶段划分

```
阶段1 (基础建设)    阶段2 (核心功能)    阶段3 (集成优化)    阶段4 (测试部署)
    │                    │                    │                    │
    ▼                    ▼                    ▼                    ▼
┌──────────┐       ┌──────────┐       ┌──────────┐       ┌──────────┐
│ 子任务1   │       │ 子任务3   │       │ 子任务6   │       │ 子任务7   │
│ 溯因引擎  │       │ 修复模板  │       │ 编排器    │       │ API集成   │
├──────────┤       ├──────────┤       ├──────────┤       ├──────────┤
│ 子任务2   │       │ 子任务4   │       │ 集成测试  │       │ 性能测试  │
│ 断路��    │       │ Backlog   │       │          │       │          │
├──────────┤       ├──────────┤       │          │       │          │
│ 数据模型  │       │ 子任务5   │       │          │       │          │
│ 定义      │       │ 冻结器    │       │          │       │          │
└──────────┘       └──────────┘       └──────────┘       └──────────┘
```

### 4.2 时间估算

| 阶段 | 子任务 | 预估工时 | 依赖 |
|------|--------|----------|------|
| 阶段1 | 1, 2 | 3天 | 现有监控系统 |
| 阶段2 | 3, 4, 5 | 4天 | 阶段1完成 |
| 阶段3 | 6 | 2天 | 阶段2完成 |
| 阶段4 | 7 | 2天 | 阶段3完成 |
| **总计** | | **11天** | |

## 5. 数据模型设计

### 5.1 新增数据模型

```python
# 在 monitoring/models.py 中新增

@dataclass
class AlertEvent:
    alert_id: str
    source: str  # 告警来源
    severity: str  # critical, high, medium, low
    dimension: str  # 关联维度
    message: str
    timestamp: datetime
    context: Dict[str, Any]

@dataclass
class AbductionResult:
    alert_id: str
    root_cause: str
    confidence: float
    affected_dimensions: List[str]
    evidence: List[EvidenceItem]
    suggested_actions: List[str]
    timestamp: datetime

@dataclass
class BreakerState:
    dimension: str
    state: str  # CLOSED, OPEN, HALF_OPEN
    failure_count: int
    last_failure: Optional[datetime]
    threshold: int
    recovery_timeout: int

@dataclass
class RepairTemplate:
    template_id: str
    name: str
    description: str
    applicable_dimensions: List[str]
    severity_levels: List[str]
    steps: List[RepairStep]
    validation_criteria: List[str]
    version: str

@dataclass
class SpecialBacklog:
    backlog_id: str
    alert_id: str
    template_id: str
    status: str  # PENDING, IN_PROGRESS, COMPLETED, FAILED
    tasks: List[BacklogTask]
    created_at: datetime
    completed_at: Optional[datetime]

@dataclass
class FreezeStatus:
    freeze_id: str
    alert_id: str
    frozen_calls: List[str]
    exempted_calls: List[str]
    status: str  # ACTIVE, RESTORED
    created_at: datetime
    restored_at: Optional[datetime]
```

## 6. 测试策略

### 6.1 单元测试

| 组件 | 测试文件 | 测试重点 |
|------|----------|----------|
| AbductionEngine | `tests/test_abduction_engine.py` | 告警分析、探测注入 |
| CircuitBreaker | `tests/test_circuit_breaker.py` | 状态转换、阈值 |
| RepairTemplate | `tests/test_repair_templates.py` | 匹配逻辑、执行 |
| BacklogGenerator | `tests/test_backlog_generator.py` | 生成完整性、状态 |
| CallFreezer | `tests/test_call_freezer.py` | 冻结/恢复、白名单 |
| Orchestrator | `tests/test_orchestrator.py` | 流程编排、异常 |

### 6.2 集成测试

| 测试场景 | 描述 |
|----------|------|
| 告警→溯因→断路器 | 完整链路测试 |
| 溯因→模板匹配→Backlog | 修复流程测试 |
| 告警→冻结→恢复 | 冻结流程测试 |
| 并发告警处理 | 压力测试 |
| 人工干预覆盖 | 异常流程测试 |

## 7. 开发指导

### 7.1 给开发者的建议

1. **代码风格**：遵循现有项目的 dataclass + async 模式
2. **错误处理**：所有组件需实现优雅降级
3. **日志记录**：使用 `logging.getLogger(__name__)` 统一日志
4. **配置管理**：新增配置项集中在 `config/` 目录
5. **测试先行**：先写测试再实现功能

### 7.2 给测试者的建议

1. **模拟数据**：准备各类告警场景的测试数据
2. **边界测试**：重点关注阈值边界和并发场景
3. **性能基准**：记录各组件响应时间基线
4. **回归测试**：确保不影响现有监控功能

### 7.3 技术债务跟踪

| 项目 | 优先级 | 说明 |
|------|--------|------|
| 溯因算法优化 | 中 | 当前使用规则引擎，后续可引入ML |
| 模板自动学习 | 低 | 从历史修复中自动生成模板 |
| 断路器自适应阈值 | 低 | 根据历史数据动态调整阈值 |
| 前端可视化增强 | 中 | 添加实时流程图展示 |

## 8. 交付物清单

| 交付物 | 类型 | 负责人 |
|--------|------|--------|
| 侵入式溯因引擎 | 代码 | Developer |
| 维度断路器管理器 | 代码 | Developer |
| 修复模板库与匹配引擎 | 代码 | Developer |
| 专项Backlog生成器 | 代码 | Developer |
| 非关键调用冻结器 | 代码 | Developer |
| 自动化响应编排器 | 代码 | Developer |
| API集成与前端适配 | 代码 | Developer |
| 单元测试套件 | 测试 | Tester |
| 集成测试套件 | 测试 | Tester |
| 技术文档 | 文档 | Developer |
| 测试报告 | 文档 | Tester |

────────────────────────────────────────────────────────────
✅ deepseek-chat 完成
