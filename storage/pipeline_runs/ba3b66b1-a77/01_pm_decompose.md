# PM分解 — project_manager

任务: [广场计划] 如何把 OpenClaw 智能体接入现有团队体系，并输出可直接派发的执行计划
步骤: pm_decompose
Agent: build_pm

---

📋 任务: ba3b66b1-a77
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
  [广场计划] 如何把 OpenClaw 智能体接入现有团队体系，并输出可直接派发的执行计划
  ## 技术概要
  以**可逆性系数 R** 动态控制 OpenClaw 决策权限，R 阈值由事故回放标定（取恢复成本中位数 0.3 分位）。首次上线采用**免疫接种**——让越权操作在原子化回滚中真实发生，用微创代价暴露误判率，废除影子模式。回滚窗口需绑定**全链路延迟热力梯度断层**，而非静态分位，避免回滚本身成为级联故障源。最大风险是梯度断层标定滞后于拓扑演进，首要动作是搭建事故回放预演环境并输出 R 阈值初版。
  
  ## 加权结论 (P0→P1→P2)
  - [P0] 权限采用 R 系数动态函数，通过免疫接种获取真实误判率，回滚原子性必须基于全拓扑最大超时包络线校准 | Architect, Developer, 技术研究员 | 直接决定智能体决策卡位能否从“拟像指标”进入生产有效治理
  - [P1] 回滚窗口验证必须覆盖尾延迟引发的死锁脉冲场景，防止治愈机制退化为致病原 | Tester | 是级联安全的唯一质量门禁，否则免疫接种实验无法通过
  - [P2] 将免疫接种期间的资源开销纳入可观测成本面板，作为后续能耗优化的输入，不阻塞主上线
  
  ## 执行计划
  | 序号 | 任务 | 负责角色 | 优先级 | 依赖 | 预期产出 |
  |---|---|---|---|---|---|
  | 1 | 构建事故回放预演环境，回放过去 6 个月事故，计算恢复成本中位数并标定 R 阈值（0.3 分位） | Developer | P0 | 历史事故记录齐全 | R 系数阈值配置文件 |
  | 2 | 设计免疫接种机制：封装越权操作为原子化事务，内置全链路最大超时包络线校准的自动回滚 | Architect, 技术研究员 | P0 | 任务 1 的 R 阈值 | 免疫接种执行器与回滚窗口标定逻辑 |
  | 3 | 开发实时拓扑发现与延迟热力梯度断层监控，动态输出裁剪后的回滚窗口参数 | 全栈开发 | P0 | 流式拓扑感知组件 | 动态回滚窗口校准模块 |
  | 4 | 在预演环境对免疫接种进行级联容忍度测试，重点注入尾延迟死锁脉冲，验证下游超时不击穿 | Tester | P1 | 任务 2, 3 | 级联安全门禁报告 |
  | 5 | 设定从免疫接种到正式裁决的切换标准（累积误判率<阈值，连续 *N* 次无害），执行切换并冻结 R 边界 | Architect, Developer | P0 | 任务 4 通过 | 正式裁决切换方案与值班手册 |
  
  ## 补充观察
  免疫接种期间可旁路采集 GPU/CPU 能耗信号，记入成本面板供后续优化，不挤占主交付。
  
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
  src/docs/agent_handoffs/d87c964b-c06_architecture_20260503T045321.md
  src/docs/agent_handoffs/d87c964b-c06_pm_decompose_20260503T045236.md
  src/docs/agent_handoffs/d87c964b-c06_research_20260503T045251.md
  src/docs/agent_handoffs/d87c964b-c06_task_init_20260503T045211.md
  src/docs/agent_handoffs/dbf24d0c-5cc_architecture_20260503T235205.md
  src/docs/agent_handoffs/dbf24d0c-5cc_deploy_FAILED_20260504T012356.md
  src/docs/agent_handoffs/dbf24d0c-5cc_develop_20260503T235646.md
  src/docs/agent_handoffs/dbf24d0c-5cc_develop_20260504T004702.md
  src/docs/agent_handoffs/dbf24d0c-5cc_develop_FAILED_20260504T001109.md
  src/docs/agent_handoffs/dbf24d0c-5cc_executor_started_20260503T234950.md
  src/docs/agent_handoffs/dbf24d0c-5cc_pm_decompose_20260503T235020.md
  src/docs/agent_handoffs/dbf24d0c-5cc_research_20260503T235105.md
  src/docs/agent_handoffs/dbf24d0c-5cc_test_FAILED_20260504T000157.md
  src/docs/agent_handoffs/dbf24d0c-5cc_test_FAILED_20260504T002112.md
  src/docs/agent_handoffs/dbf24d0c-5cc_test_FAILED_20260504T012326.md
  src/docs/agent_handoffs/dd0e3569-eb0_architecture_20260503T114837.md
  src/docs/agent_handoffs/dd0e3569-eb0_deploy_FAILED_20260503T121257.md
  src/docs/agent_handoffs/dd0e3569-eb0_develop_20260503T115309.md
  src/docs/agent_handoffs/dd0e3569-eb0_develop_FAILED_20260503T120023.md
  src/docs/agent_handoffs/dd0e3569-eb0_develop_FAILED_20260503T120906.md
  src/docs/agent_handoffs/dd0e3569-eb0_executor_started_20260503T114547.md
  src/docs/agent_handoffs/dd0e3569-eb0_pm_decompose_20260503T114622.md
  src/docs/agent_handoffs/dd0e3569-eb0_research_20260503T114712.md
  src/docs/agent_handoffs/dd0e3569-eb0_test_20260503T115557.md
  src/docs/agent_handoffs/dd0e3569-eb0_test_FAILED_20260503T120434.md
  src/docs/agent_handoffs/dd0e3569-eb0_test_FAILED_20260503T121242.md
  src/docs/workflow_artifacts/1ce78c0e-062_architecture.md
  src/docs/workflow_artifacts/1ce78c0e-062_deploy.md
  src/docs/workflow_artifacts/1ce78c0e-062_develop.md
  src/docs/workflow_artifacts/1ce78c0e-062_pm_decompose.md
  src/docs/workflow_artifacts/1ce78c0e-062_research.md
  src/docs/workflow_artifacts/1ce78c0e-062_test.md
  src/docs/workflow_artifacts/38e22004-b64_architecture.md
  src/docs/workflow_artifacts/38e22004-b64_pm_decompose.md
  src/docs/workflow_artifacts/38e22004-b64_research.md
  src/docs/workflow_artifacts/7c934759-39e_architecture.md
  src/docs/workflow_artifacts/7c934759-39e_deploy.md
  src/docs/workflow_artifacts/7c934759-39e_develop.md
  src/docs/workflow_artifacts/7c934759-39e_pm_decompose.md
  src/docs/workflow_artifacts/7c934759-39e_research.md
  src/docs/workflow_artifacts/7c934759-39e_test.md
  src/docs/workflow_artifacts/d87c964b-c06_architecture.md
  src/docs/workflow_artifacts/d87c964b-c06_pm_decompose.md
  src/docs/workflow_artifacts/d87c964b-c06_research.md
  src/docs/workflow_artifacts/dbf24d0c-5cc_architecture.md
  src/docs/workflow_artifacts/dbf24d0c-5cc_deploy.md
  src/docs/workflow_artifacts/dbf24d0c-5cc_develop.md
  src/docs/workflow_artifacts/dbf24d0c-5cc_pm_decompose.md
  src/docs/workflow_artifacts/dbf24d0c-5cc_research.md
  src/docs/workflow_artifacts/dbf24d0c-5cc_test.md
  src/docs/workflow_artifacts/dd0e3569-eb0_architecture.md
  src/docs/workflow_artifacts/dd0e3569-eb0_deploy.md
  src/docs/workflow_artifacts/dd0e3569-eb0_develop.md
  src/docs/workflow_artifacts/dd0e3569-eb0_pm_decompose.md
  src/docs/workflow_artifacts/dd0e3569-eb0_research.md
  ... (共 151 个 src/ 文件)
  
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
  
  
  @router.get("/evolution/history")
  async def evolution_audit_history():
      """获取审查历史记录。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.get_audit_history()
  
  
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
      return _evolution_engine.get_compliance_rating()
  
  
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
      return {
          "active_zones": _evolution_engine.get_active_zones(),
          "activated_rules": _evolution_engine.get_zone_activated_rules(),
          "vessel_position": _evolution_engine._vessel_position,
      }
  
  
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
      return _evolution_engine.get_trend_analysis()
  
  
  @router.get("/evolution/monitoring")
  async def evolution_monitoring():
      """获取连续监控状态。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.get_monitoring_status()
  
  
  @router.get("/evolution/audit-trail")
  async def evolution_audit_trail(event_type: Optional[str] = None, limit: int = 50):
      """获取审计轨迹日志。"""
      if not _evolution_engine:
          raise HTTPException(404, "Evolution engine not registered")
      return _evolution_engine.get_audit_trail(event_type=event_type, limit=limit)
  
  
  __all__ = ["router", "set_teams"]
  
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
  _EXCHANGES_PER_ROUND = 3  # 每轮内交锋次数 — 模拟辩论短交锋
  _SPEAKERS_PER_EXCHANGE = 2  # 每次交锋参与人数
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
          self._chat_fn: Optional[Callable] = None  # ChatHarness.chat reference
  
      def set_chat_fn(self, fn: Callable):
          """注入 ChatHarness.chat 异步函数."""
          self._chat_fn = fn
  
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
          q: asyncio.Queue = asyncio.Queue()
          self._sse_queues.setdefault(discussion_id, []).append(q)
          return q
  
      def unsubscribe(self, discussion_id: str, q: asyncio.Queue):
          qs = self._sse_queues.get(discussion_id, [])
          if q in qs:
              qs.remove(q)
  
      async def _broadcast(self, discussion_id: str, event: Dict[str, Any]):
          """向所有 SSE 订阅者推送事件."""
          for q in self._sse_queues.get(discussion_id, []):
              try:
                  q.put_nowait(event)
              except asyncio.QueueFull:
                  pass
  
      # ── 核心讨论编排 ──────────────────────────────────────
  
      async def run_discussion(
          self, plaza_id: str, discussion_id: str,
      ) -> Optional[Discussion]:
          """运行一场完整的广场讨论.
  
          编排流程 (向心结构):
          1. Moderator 开场: 阐述话题，提出第一轮子问题
          2. 每轮:
             a. 各参与者按座席层级依次发言 (内→中→外)
             b. Moderator 总结本轮观点
          3. 最终轮: Moderator 生成全局总结 + 关键结论
          """
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return None
          disc = plaza.discussions.get(discussion_id)
          if not disc:
              return None
          if disc.status not in (DiscussionStatus.OPEN,):
              return disc
  
          disc.status = DiscussionStatus.IN_PROGRESS
          disc.started_at = datetime.now(timezone.utc).isoformat()
  
          # Give event loop a chance to process SSE client connections
          await asyncio.sleep(0.1)
  
          await self._broadcast(disc.id, {
              "type": "discussion_start",
              "discussion_id": disc.id,
              "topic": disc.topic,
          })
  
          participants = list(plaza.participants.values())
          moderator = None
          speakers = []
  
          # 找到 moderator
          if disc.moderator_agent_id:
              moderator = plaza.participants.get(disc.moderator_agent_id)
          if not moderator and participants:
              moderator = participants[0]
              disc.moderator_agent_id = moderator.agent_id
  
          # 按座席层级排序发言者 (内→中→外)
          tier_order = {SeatTier.INNER: 0, SeatTier.MIDDLE: 1, SeatTier.OUTER: 2}
          speakers = sorted(
              [p for p in participants if p.agent_id != moderator.agent_id],
              key=lambda p: (
                  tier_order.get(p.seat_tier, 1),
                  self._role_priority(p),
                  p.niche_index,
              ),
          ) if moderator else participants
  
          if not self._chat_fn:
              # 无 LLM 时使用模拟回复
              await self._run_simulated(disc, moderator, speakers)
              return disc
  
          # ── 开场: Moderator 引导话题 ──
          opening_prompt = (
              f"你是本场讨论的议事长（主持人）。\n"
              f"讨论话题: 「{disc.topic}」\n"
              f"{f'话题描述: {disc.description}' if disc.description else ''}\n"
              f"{f'讨论目标: {disc.goal}' if disc.goal else ''}\n"
              f"参与者: {', '.join(p.agent_name or p.agent_id for p in speakers)}\n\n"
              f"请开场，像技术辩论赛主持人一样推进讨论:\n"
              f"- 只用 2-3 句，短句表达，不要长篇铺陈\n"
              f"- 先点明主问题，再抛出第一个最关键的技术追问\n"
              f"- 问题要直接指向可执行方案、风险或约束，而不是泛泛而谈"
          )
          opening = await self._agent_speak(
              disc, moderator, opening_prompt, round_number=0,
              niche_role="moderator",
          )
  
          # ── 多轮讨论 (辩论式交锋) ──
          for round_num in range(1, disc.max_rounds + 1):
              disc.current_round = round_num
              await self._broadcast(disc.id, {
                  "type": "round_start", "round": round_num,
                  "max_rounds": disc.max_rounds,
              })
  
              round_speakers = self._select_round_speakers(speakers, round_num)
              # 每轮多次短交锋，模拟辩论赛节奏
              exchanges = _EXCHANGES_PER_ROUND if disc.max_rounds <= 2 else 2
              for ex_idx in range(exchanges):
                  # 轮转选人: 每次交锋选不同子集
                  ex_speakers = self._pick_exchange_speakers(
                      round_speakers, ex_idx, _SPEAKERS_PER_EXCHANGE,
                  )
                  for speaker in ex_speakers:
                      # 获取最近 5 条作为即时上下文 (短窗口促进针锋相对)
                      recent = self._format_recent(disc, limit=5)
                      speak_prompt = (
                          f"你正在参与关于「{disc.topic}」的快速辩论。\n"
                          f"你是 {speaker.agent_name}（{speaker.role}）。"
                          f"第 {round_num} 轮，第 {ex_idx+1} 次交锋。\n\n"
                          f"刚才的交锋:\n{recent}\n\n"
                          f"规则——像苏格拉底辩论+伯里克利演说:\n"
                          f"- 只说 1-2 句话，30-60 字，一次只推进一个论点\n"
                          f"- 必须回应上一条的关键词或判断，然后补你的核心依据\n"
                          f"- 不要复述背景、不要客套、不要写标题或列表\n"
                          f"- 追求深度和锋利，给出可落地的指标、约束或机制\n"
                          f"- 像在辩论赛里被限时 15 秒，有哲思但极度凝练"
                      )
                      await self._agent_speak(
                          disc, speaker, speak_prompt, round_number=round_num,
                          niche_role=speaker.niche_role.value,
                      )
  
              # Moderator 收束本轮 (非最后一轮时)
              if round_num < disc.max_rounds:
                  summary_prompt = (
                      f"你是主持人。第 {round_num} 轮 {exchanges} 次交锋已结束。\n\n"
                      f"本轮讨论:\n{self._format_round_messages(disc, round_num)}\n\n"
                      f"请像辩论赛主持人一样收束:\n"
                      f"- 1 句话点出本轮最有价值的共识或分歧\n"
                      f"- 1 个尖锐追问推动下一轮收敛到可执行方案\n"
                      f"- 总共不超过 2 句，40 字以内"
                  )
                  await self._agent_speak(
                      disc, moderator, summary_prompt, round_number=round_num,
                      niche_role="moderator",
                  )
  
          # ── 最终总结 ──
          disc.status = DiscussionStatus.SUMMARIZING
          await self._broadcast(disc.id, {"type": "summarizing"})
  
          final_prompt = (
              f"你是议事长。关于「{disc.topic}」的讨论已经完成 {disc.max_rounds} 轮。\n"
              f"{f'讨论目标: {disc.goal}' if disc.goal else ''}\n\n"
              f"完整讨论记录:\n{self._format_history(disc)}\n\n"
              f"请生成可直接派发任务的技术型概要。核心原则——有取舍、有权重:\n"
              f"- build/构建/开发/架构/部署相关发言 = 权重最高(P0级)，这些人要真正动手执行\n"
              f"- 测试/QA/安全相关 = 中等权重(P1级)，是质量门禁\n"
              f"- 能耗/外围优化/观察类 = 低权重(P2级)，仅作为补充参考，绝不挤占主篇幅\n"
              f"- 如果能耗建议不影响主目标上线，就放到最后1行带过\n\n"
              f"输出结构 (严格按此格式，不要自由发挥):\n"
              f"## 技术概要\n"
              f"4-6 句写清: 主目标、核心方案、关键约束、最大风险、首要动作\n"
              f"必须是接到这份概要的人能直接开工的技术描述\n\n"
              f"## 加权结论 (P0→P1→P2)\n"
              f"- [P0] 结论 | 主要支持角色 | 为什么重要\n"
              f"- [P1] ...\n"
              f"- [P2] 仅保留 1 条最相关的低权重建议\n\n"
              f"## 执行计划\n"
              f"| 序号 | 任务 | 负责角色 | 优先级 | 依赖 | 预期产出 |\n"
              f"|---|---|---|---|---|---|\n"
              f"列出 3-5 个任务，按优先级排序\n\n"
              f"## 补充观察\n"
              f"1 句话带过能耗/外围建议即可\n\n"
              f"请用 Markdown 输出，简洁有力，能直接作为任务单下发。"
          )
          disc.summary = await self._generate_agent_content(
              moderator,
              final_prompt,
          )
          closing_msg = PlazaMessage(
              discussion_id=disc.id,
              agent_id=moderator.agent_id,
              agent_name=moderator.agent_name or moderator.agent_id,
              role=moderator.role,
              niche_role="moderator",
              content=self._build_closing_brief(disc.summary),
              round_number=disc.max_rounds + 1,
              metadata={"summary_kind": "closing_brief"},
          )
          disc.messages.append(closing_msg)
          await self._broadcast(disc.id, {
              "type": "message",
              "message": closing_msg.to_dict(),
          })
          disc.status = DiscussionStatus.CLOSED
          disc.ended_at = datetime.now(timezone.utc).isoformat()
  
          await self._broadcast(disc.id, {
              "type": "discussion_end",
              "summary": disc.summary,
          })
  
          # 持久化讨论结果
          self._store.save_plaza(plaza)
  
          logger.info(
              f"✅ 讨论完成: {disc.topic[:30]} — "
              f"{len(disc.messages)} 条消息, {disc.max_rounds} 轮"
          )
          return disc
  
      async def _agent_speak(
          self, disc: Discussion, participant: Participant,
          prompt: str, round_number: int, niche_role: str = "",
      ) -> Optional[PlazaMessage]:
          """让一个 Agent 在广场中发言."""
          content = await self._generate_agent_content(participant, prompt)
          content = self._shape_debate_message(
              content,
              is_moderator=(niche_role == "moderator"),
          )
  
          msg = PlazaMessage(
              discussion_id=disc.id,
              agent_id=participant.agent_id,
              agent_name=participant.agent_name or participant.agent_id,
              role=participant.role,
              niche_role=niche_role or participant.niche_role.value,
              content=content,
              round_number=round_number,
          )
          disc.messages.append(msg)
  
          await self._broadcast(disc.id, {
              "type": "message",
              "message": msg.to_dict(),
          })
          return msg
  
      async def _generate_agent_content(
          self,
          participant: Participant,
          prompt: str,
      ) -> str:
          try:
              result = await self._chat_fn(
                  prompt,
                  agent_id=participant.agent_id,
                  system_prompt=(
                      f"你是 {participant.agent_name}，角色: {participant.role}。"
                      f"你在智能体广场辩论中发
  ```
  
  ### 文件: `src/backend/agents/plaza_routes.py`
  ```py
  # -*- coding: utf-8 -*-
  """智能体广场 API 路由 + SSE 实时推送."""
  
  from __future__ import annotations
  
  import asyncio
  import json
  import logging
  from typing import Any, Dict, List, Optional
  
  from fastapi import APIRouter, HTTPException, status
  from fastapi.responses import StreamingResponse
  from pydantic import BaseModel, Field
  
  from .plaza import PRESET_TOPICS, SeatTier, NicheRole
  from .plaza_engine import get_plaza_engine
  
  logger = logging.getLogger(__name__)
  router = APIRouter(prefix="/plaza", tags=["Plaza"])
  
  
  # ── Request Models ────────────────────────────────────────
  
  class CreatePlazaRequest(BaseModel):
      name: str = Field(..., min_length=1, max_length=100)
      description: str = Field(default="", max_length=500)
  
  
  class AddParticipantRequest(BaseModel):
      agent_id: str
      agent_name: str = ""
      role: str = ""
      team_id: str = ""
      seat_tier: str = Field(default="middle")
      niche_role: str = Field(default="observer")
  
  
  class CreateDiscussionRequest(BaseModel):
      topic: str = Field(..., min_length=1, max_length=200)
      description: str = Field(default="", max_length=500)
      goal: str = Field(default="", max_length=500)
      moderator_agent_id: str = ""
      max_rounds: int = Field(default=3, ge=1, le=10)
  
  
  class SetVisualModeRequest(BaseModel):
      mode: str = Field(default="modern")  # modern | rome_320ad | senedd
  
  
  # ── 广场 CRUD ──────────────────────────────────────────────
  
  @router.post("", summary="创建广场", status_code=status.HTTP_201_CREATED)
  async def create_plaza(req: CreatePlazaRequest) -> Dict[str, Any]:
      engine = get_plaza_engine()
      plaza = engine.create_plaza(req.name, req.description)
      return plaza.to_dict(include_details=True)
  
  
  @router.get("", summary="列出所有广场")
  async def list_plazas() -> List[Dict[str, Any]]:
      engine = get_plaza_engine()
      return [p.to_dict() for p in engine.list_plazas()]
  
  
  @router.get("/presets", summary="获取预设话题模板")
  async def get_preset_topics() -> List[Dict[str, str]]:
      return PRESET_TOPICS
  
  
  @router.get("/{plaza_id}", summary="获取广场详情")
  async def get_plaza(plaza_id: str) -> Dict[str, Any]:
      engine = get_plaza_engine()
      plaza = engine.get_plaza(plaza_id)
      if not plaza:
          raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
      return plaza.to_dict(include_details=True)
  
  
  @router.delete("/{plaza_id}", summary="删除广场")
  async def delete_plaza(plaza_id: str) -> Dict[str, str]:
      engine = get_plaza_engine()
      if not engine.delete_plaza(plaza_id):
          raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
      return {"status": "deleted"}
  
  
  @router.put("/{plaza_id}/visual-mode", summary="切换视觉模式")
  async def set_visual_mode(plaza_id: str, req: SetVisualModeRequest) -> Dict[str, Any]:
      engine = get_plaza_engine()
      plaza = engine.get_plaza(plaza_id)
      if not plaza:
          raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
      if req.mode not in ("modern", "rome_320ad", "senedd"):
          raise HTTPException(status.HTTP_400_BAD_REQUEST, "无效的视觉模式")
      plaza.visual_mode = req.mode
      return {"status": "updated", "visual_mode": plaza.visual_mode}
  
  
  # ── 参与者管理 ──────────────────────────────────────────────
  
  @router.post("/{plaza_id}/participants", summary="添加参与者", status_code=201)
  async def add_participant(plaza_id: str, req: AddParticipantRequest) -> Dict[str, Any]:
      engine = get_plaza_engine()
      try:
          tier = SeatTier(req.seat_tier)
      except ValueError:
          tier = SeatTier.MIDDLE
      try:
          niche = NicheRole(req.niche_role)
      except ValueError:
          niche = NicheRole.OBSERVER
      p = engine.add_participant(
          plaza_id, req.agent_id, req.agent_name, req.role, req.team_id,
          tier, niche,
      )
      if not p:
          raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
      return p.to_dict()
  
  
  @router.delete("/{plaza_id}/participants/{agent_id}", summary="移除参与者")
  async def remove_participant(plaza_id: str, agent_id: str) -> Dict[str, str]:
      engine = get_plaza_engine()
      if not engine.remove_participant(plaza_id, agent_id):
          raise HTTPException(status.HTTP_404_NOT_FOUND, "参与者不存在")
      return {"status": "removed"}
  
  
  @router.post("/{plaza_id}/participants/batch", summary="批量添加参与者", status_code=201)
  async def batch_add_participants(
      plaza_id: str, participants: List[AddParticipantRequest]
  ) -> List[Dict[str, Any]]:
      engine = get_plaza_engine()
      results = []
      for req in participants:
          try:
              tier = SeatTier(req.seat_tier)
          except ValueError:
              tier = SeatTier.MIDDLE
          try:
              niche = NicheRole(req.niche_role)
          except ValueError:
              niche = NicheRole.OBSERVER
          p = engine.add_participant(
              plaza_id, req.agent_id, req.agent_name, req.role, req.team_id,
              tier, niche,
          )
          if p:
              results.append(p.to_dict())
      return results
  
  
  # ── 讨论管理 ──────────────────────────────────────────────
  
  @router.post("/{plaza_id}/discussions", summary="创建讨论", status_code=201)
  async def create_discussion(
      plaza_id: str, req: CreateDiscussionRequest,
  ) -> Dict[str, Any]:
      engine = get_plaza_engine()
      disc = engine.create_discussion(
          plaza_id, req.topic, req.description,
          req.moderator_agent_id, req.max_rounds,
      )
      if disc:
          disc.goal = req.goal
      if not disc:
          raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
      return disc.to_dict()
  
  
  @router.get("/{plaza_id}/discussions", summary="列出讨论")
  async def list_discussions(plaza_id: str) -> List[Dict[str, Any]]:
      engine = get_plaza_engine()
      return [d.to_dict() for d in engine.list_discussions(plaza_id)]
  
  
  @router.get("/{plaza_id}/discussions/{disc_id}", summary="获取讨论详情")
  async def get_discussion(plaza_id: str, disc_id: str) -> Dict[str, Any]:
      engine = get_plaza_engine()
      disc = engine.get_discussion(plaza_id, disc_id)
      if not disc:
          raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")
      return disc.to_dict(include_messages=True)
  
  
  @router.get("/{plaza_id}/discussions/{disc_id}/summary", summary="获取讨论总结")
  async def get_discussion_summary(plaza_id: str, disc_id: str) -> Dict[str, Any]:
      engine = get_plaza_engine()
      disc = engine.get_discussion(plaza_id, disc_id)
      if not disc:
          raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")
      return {
          "discussion_id": disc.id,
          "topic": disc.topic,
          "status": disc.status.value,
          "summary": disc.summary,
          "key_conclusions": disc.key_conclusions,
          "message_count": len(disc.messages),
          "rounds": disc.current_round,
          "plan": disc.plan,
          "goal": disc.goal,
          "assigned_team_id": disc.assigned_team_id,
      }
  
  
  @router.delete("/{plaza_id}/discussions/{disc_id}", summary="删除讨论")
  async def delete_discussion(plaza_id: str, disc_id: str) -> Dict[str, str]:
      engine = get_plaza_engine()
      if not engine.delete_discussion(plaza_id, disc_id):
          raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")
      return {"status": "deleted", "discussion_id": disc_id}
  
  
  # ── 自动入座 (所有团队智能体) ──────────────────────────────
  
  @router.post("/{plaza_id}/auto-seat", summary="全部智能体自动入座", status_code=200)
  async def auto_seat_all_agents(plaza_id: str) -> Dict[str, Any]:
      """从所有团队拉取智能体自动入座广场，按团队分区."""
      engine = get_plaza_engine()
      plaza = engine.get_plaza(plaza_id)
      if not plaza:
          raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
  
      # 获取 TeamManager
      try:
          from agents.api import _team_manager
      except ImportError:
          raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "TeamManager 不可用")
  
      added = []
      teams = _team_manager.list_teams() if _team_manager else []
      for team in teams:
          agents = team.agents
          if isinstance(agents, dict):
              agents = list(agents.values())
          for a in agents:
              if a.agent_id in plaza.participants:
                  continue
              p = engine.add_participant(
                  plaza_id, a.agent_id, a.name or a.agent_id,
                  a.role or "", team.team_id,
                  SeatTier.MIDDLE, NicheRole.OBSERVER,
              )
              if p:
                  added.append(p.to_dict())
  
      return {"added": len(added), "total": len(plaza.participants), "participants": added}
  
  
  # ── 计划指派给团队 ──────────────────────────────────────────
  
  class AssignPlanRequest(BaseModel):
      team_id: str
      task_name: str = ""
      task_description: str = ""
  
  
  @router.post("/{plaza_id}/discussions/{disc_id}/assign", summary="将讨论计划指派给团队")
  async def assign_plan_to_team(
      plaza_id: str, disc_id: str, req: AssignPlanRequest,
  ) -> Dict[str, Any]:
      engine = get_plaza_engine()
      disc = engine.get_discussion(plaza_id, disc_id)
      if not disc:
          raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")
  
      disc.assigned_team_id = req.team_id
  
      # 尝试创建任务
      try:
          from agents.task_engine import get_task_engine, AgentTask
          te = get_task_engine()
          task_name = req.task_name or f"[广场计划] {disc.topic[:50]}"
          task_desc = req.task_description or disc.summary or disc.topic
          task = AgentTask(
              team_id=req.team_id,
              title=task_name,
              description=task_desc,
              metadata={"source": "plaza", "discussion_id": disc.id, "plaza_id": plaza_id},
          )
          import asyncio
          submitted = await te.submit_task(task)
          return {"status": "assigned", "team_id": req.team_id, "task_id": submitted.task_id}
      except Exception as e:
          logger.warning(f"创建任务失败: {e}")
          return {"status": "assigned_no_task", "team_id": req.team_id, "error": str(e)}
  
  
  # ── 讨论→任务批量派发 ──────────────────────────────────────
  
  class DispatchTasksRequest(BaseModel):
      team_id: str = Field(..., min_length=1)
  
  
  @router.post("/{plaza_id}/discussions/{disc_id}/dispatch", summary="从讨论结论自动拆解并派发任务")
  async def dispatch_tasks_from_discussion(
      plaza_id: str, disc_id: str, req: DispatchTasksRequest,
  ) -> Dict[str, Any]:
      """解析讨论总结中的行动计划，为每个步骤创建独立任务并提交到 TaskEngine."""
      engine = get_plaza_engine()
      disc = engine.get_discussion(plaza_id, disc_id)
      if not disc:
          raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")
      if not disc.summary:
          raise HTTPException(status.HTTP_400_BAD_REQUEST, "讨论尚无总结，请先完成讨论")
  
      # 用 LLM 解析总结 → 任务列表
      from .chat_harness import get_chat_harness
      harness = get_chat_harness()
      parse_prompt = (
          "你是任务拆解助手。请分析以下讨论总结，提取可执行的任务列表。\n"
          "严格按照 JSON 数组格式输出，每项包含: title, description, priority (1-3, 1最高)\n"
          "优先使用‘执行计划’和‘加权结论’中的 P0/P1 信息；‘补充观察’默认不要转成任务，除非它是上线必需动作。\n"
          "只输出 JSON 数组，不要任何其他文字。\n\n"
          f"讨论话题: {disc.topic}\n\n"
          f"讨论总结:\n{disc.summary}\n"
      )
      try:
          llm_reply = await harness.chat(parse_prompt, system="你是一个任务拆解专家，只输出JSON。")
          # 提取 JSON 数组
          import re
          json_match = re.search(r'\[.*\]', llm_reply, re.DOTALL)
          if not json_match:
              raise ValueError("LLM 未返回有效 JSON 数组")
          tasks_data = json.loads(json_match.group())
      except Exception as e:
          logger.warning(f"LLM 任务拆解失败: {e}，回退为单任务")
          tasks_data = [{
              "title": f"[广场计划] {disc.topic[:50]}",
              "description": disc.summary,
              "priority": 2,
          }]
  
      # 批量提交任务
      from .task_engine import get_task_engine, AgentTask
      te = get_task_engine()
      created_tasks = []
      for i, td in enumerate(tasks_data[:10]):  # 最多 10 个任务
          task = AgentTask(
              team_id=req.team_id,
              title=str(td.get("title", f"任务 {i+1}"))[:120],
              description=str(td.get("description", ""))[:2000],
              priority=int(td.get("priority", 2)),
              metadata={
                  "source": "plaza_dispatch",
                  "discussion_id": disc.id,
                  "plaza_id": plaza_id,
                  "sequence": i,
              },
          )
          await te.submit_task(task)
          created_tasks.append(task.to_dict())
  
      disc.assigned_team_id = req.team_id
      engine._store.save_plaza(engine._plazas[plaza_id])
  
      return {
          "status": "dispatched",
          "team_id": req.team_id,
          "task_count": len(created_tasks),
          "tasks": created_tasks,
      }
  
  
  # ── 启动讨论 + SSE 流 ──────────────────────────────────────
  
  @router.post("/{plaza_id}/discussions/{disc_id}/start", summary="启动讨论")
  async def start_discussion(plaza_id: str, disc_id: str) -> Dict[str, Any]:
      engine = get_plaza_engine()
      disc = engine.get_discussion(plaza_id, disc_id)
      if not disc:
          raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")
      if disc.status == "closed":
          disc = engine.reset_discussion(plaza_id, disc_id)
      elif disc.status != "open":
          raise HTTPException(status.HTTP_400_BAD_REQUEST, f"讨论状态为 {disc.status}，无法启动")
  
      # 在后台运行讨论
      asyncio.create_task(engine.run_discussion(plaza_id, disc_id))
      return {"status": "started", "discussion_id": disc_id}
  
  
  @router.get("/{plaza_id}/discussions/{disc_id}/stream", summary="SSE 实时消息流")
  async def stream_discussion(plaza_id: str, disc_id: str):
      """Server-Sent Events 实时推送讨论消息.
  
      通过穹顶 Oculus 高速数据通道实时传输讨论流。
      """
      engine = get_plaza_engine()
      disc = engine.get_discussion(plaza_id, disc_id)
      if not disc:
          raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")
  
      q = engine.subscribe(disc_id)
  
      async def event_stream():
          try:
              # 先推送已有消息（支持中途接入）
              for msg in disc.messages:
                  yield f"data: {json.dumps({'type': 'message', 'message': msg.to_dict()}, ensure_ascii=False)}\n\n"
  
              # 推送当前状态
              yield f"data: {json.dumps({'type': 'status', 'status': disc.status.value}, ensure_ascii=False)}\n\n"
  
              # 实时推送新消息
              while True:
                  try:
                      event = await asyncio.wait_for(q.get(), timeout=30.0)
                      yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                      if event.get("type") == "discussion_end":
                          break
                  except asyncio.TimeoutError:
                      yield f"data: {json.dumps({'type': 'heartbeat'}, ensure_ascii=False)}\n\n"
          finally:
              engine.unsubscribe(disc_id, q)
  
      return StreamingResponse(
          event_stream(),
          media_type="text/event-stream",
          headers={
              "Cache-Control": "no-cache",
              "Connection": "keep-alive",
              "X-Accel-Buffering": "no",
          },
      )
  
  
  # ══════════════════════════════════════════════════════════════
  # 监控与遥测 API
  # ══════════════════════════════════════════════════════════════
  
  # 全局监控 Channel 引用（在 main.py startup 时注入）
  _plaza_monitor_channel = None
  
  
  def set_plaza_monitor(channel):
      """注入 PlazaMonitorChannel 实例."""
      global _plaza_monitor_channel
      _plaza_monitor_channel = channel
  
  
  @router.get("/monitoring/status", summary="获取监控状态")
  async def monitoring_status() -> Dict[str, Any]:
      """获取广场监控 Channel 状态."""
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
              instr
  ```
  
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

# 任务分解文档：OpenClaw 智能体接入现有团队体系

## 1. 任务概述

**目标**：将 OpenClaw 智能体安全、可控地接入现有 Agent 团队体系，通过可逆性系数 R 动态控制决策权限，采用免疫接种策略验证系统可靠性。

**核心约束**：
- 首次上线必须经历真实越权操作（免疫接种），废除影子模式
- 回滚窗口绑定全链路延迟热力梯度断层，而非静态分位
- R 阈值由事故回放标定（恢复成本中位数 0.3 分位）

## 2. 任务分解

### 2.1 阶段一：基础设施搭建（P0）

#### 任务 1.1：构建事故回放预演环境
- **负责角色**：Developer
- **依赖**：历史事故记录齐全
- **具体步骤**：
  1. 分析现有 `src/backend/monitoring/` 目录下的监控组件（`collector.py`, `models.py`, `sampler.py`）
  2. 利用 `src/backend/channels/openclaw_sync.py` 作为 OpenClaw 同步通道基础
  3. 搭建独立的事故回放沙箱环境
  4. 回放过去 6 个月事故记录
  5. 计算恢复成本中位数并标定 R 阈值（0.3 分位）
- **预期产出**：`R 系数阈值配置文件`（JSON/YAML 格式）

#### 任务 1.2：设计免疫接种机制
- **负责角色**：Architect, 技术研究员
- **依赖**：任务 1.1 的 R 阈值
- **具体步骤**：
  1. 封装越权操作为原子化事务
  2. 内置全链路最大超时包络线校准的自动回滚
  3. 参考 `src/backend/agents/execution_registry.py` 的执行注册机制
  4. 设计回滚窗口标定逻辑
- **预期产出**：`免疫接种执行器` 与 `回滚窗口标定逻辑`

#### 任务 1.3：开发实时拓扑发现与延迟热力梯度断层监控
- **负责角色**：全栈开发
- **依赖**：流式拓扑感知组件
- **具体步骤**：
  1. 基于 `src/backend/monitoring/plaza_monitor.py` 扩展监控能力
  2. 实现实时拓扑发现模块
  3. 开发延迟热力梯度断层监控
  4. 动态输出裁剪后的回滚窗口参数
- **预期产出**：`动态回滚窗口校准模块`

### 2.2 阶段二：验证与测试（P1）

#### 任务 2.1：级联容忍度测试
- **负责角色**：Tester
- **依赖**：任务 1.2, 1.3
- **具体步骤**：
  1. 在预演环境对免疫接种进行级联容忍度测试
  2. 重点注入尾延迟死锁脉冲场景
  3. 验证下游超时不击穿
  4. 生成级联安全门禁报告
- **预期产出**：`级联安全门禁报告`

### 2.3 阶段三：上线与切换（P0）

#### 任务 3.1：设定切换标准并执行
- **负责角色**：Architect, Developer
- **依赖**：任务 2.1 通过
- **具体步骤**：
  1. 设定从免疫接种到正式裁决的切换标准
  2. 累积误判率 < 阈值
  3. 连续 N 次无害操作
  4. 执行切换并冻结 R 边界
- **预期产出**：`正式裁决切换方案` 与 `值班手册`

### 2.4 阶段四：可观测性建设（P2）

#### 任务 4.1：资源开销监控
- **负责角色**：Developer
- **依赖**：任务 1.2
- **具体步骤**：
  1. 旁路采集 GPU/CPU 能耗信号
  2. 记入成本面板
  3. 作为后续能耗优化的输入
- **预期产出**：`可观测成本面板`

## 3. 技术风险与缓解措施

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 梯度断层标定滞后于拓扑演进 | 回滚窗口不准确 | 实时拓扑发现模块需支持动态更新，设置告警阈值 |
| 尾延迟死锁脉冲导致级联故障 | 系统稳定性受损 | 级联容忍度测试必须覆盖极端场景 |
| 免疫接种期间资源开销过大 | 影响正常业务 | P2 任务监控资源开销，设置资源上限 |
| 历史事故记录不完整 | R 阈值标定偏差 | 建立事故记录完整性检查机制 |

## 4. 依赖关系图

```
任务 1.1 (事故回放环境)
    ↓
任务 1.2 (免疫接种设计) ← 依赖任务 1.1 的 R 阈值
    ↓
任务 1.3 (拓扑发现与梯度监控) ← 独立开发，与 1.2 并行
    ↓
任务 2.1 (级联容忍度测试) ← 依赖任务 1.2 和 1.3
    ↓
任务 3.1 (切换标准与执行) ← 依赖任务 2.1 通过
    ↓
任务 4.1 (资源开销监控) ← 依赖任务 1.2，可并行
```

## 5. 现有代码资源分析

### 5.1 可直接复用的组件

1. **`src/backend/channels/openclaw_sync.py`**：OpenClaw 同步通道，可作为通信基础
2. **`src/backend/monitoring/collector.py`**：监控数据采集器
3. **`src/backend/monitoring/plaza_monitor.py`**：广场监控，可扩展为拓扑监控
4. **`src/backend/agents/execution_registry.py`**：执行注册，可用于免疫接种执行器

### 5.2 需要扩展的组件

1. **事故回放引擎**：需新建，基于现有监控数据
2. **R 系数计算模块**：需新建，基于恢复成本分析
3. **延迟热力梯度断层检测**：需在 `plaza_monitor.py` 基础上扩展
4. **原子化回滚事务**：需新建，参考 `execution_registry.py` 模式

## 6. 执行计划时间线

| 阶段 | 任务 | 预计工时 | 优先级 |
|------|------|----------|--------|
| 基础设施 | 1.1 事故回放环境 | 3 天 | P0 |
| 基础设施 | 1.2 免疫接种设计 | 5 天 | P0 |
| 基础设施 | 1.3 拓扑发现与梯度监控 | 4 天 | P0 |
| 验证测试 | 2.1 级联容忍度测试 | 3 天 | P1 |
| 上线切换 | 3.1 切换标准与执行 | 2 天 | P0 |
| 可观测性 | 4.1 资源开销监控 | 2 天 | P2 |

## 7. 后续指导

### 7.1 对架构师的指导
- 重点设计免疫接种的原子化事务模型
- 确保回滚窗口绑定全链路延迟热力梯度断层
- 参考 `src/backend/agents/execution_registry.py` 的事务管理机制

### 7.2 对开发者的指导
- 优先完成事故回放预演环境搭建
- 利用现有 `openclaw_sync.py` 作为通信通道
- 监控模块基于 `plaza_monitor.py` 扩展

### 7.3 对测试人员的指导
- 级联容忍度测试必须覆盖尾延迟死锁脉冲场景
- 验证回滚窗口的准确性
- 生成可量化的安全门禁报告

### 7.4 对技术研究员的指导
- 研究 R 系数动态函数的数学模型
- 分析恢复成本中位数的统计特性
- 评估免疫接种策略的有效性指标

────────────────────────────────────────────────────────────
✅ deepseek-chat 完成
