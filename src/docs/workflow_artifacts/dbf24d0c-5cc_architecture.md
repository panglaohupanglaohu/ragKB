# 架构设计 — architect

任务: [广场计划] 设计并实现一套智能体广场实时监控与自动化质量保障系统
步骤: architecture
Agent: build_architect

---

📋 任务: dbf24d0c-5cc
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
  [广场计划] 设计并实现一套智能体广场实时监控与自动化质量保障系统
  好的，作为项目经理，我已整合各位专家的意见，形成最终总结与执行计划。
  
  ---
  
  ### 最终总结与执行计划
  
  #### 1. 讨论概要
  
  经过多轮讨论，团队已就智能体广场的实时监控与自动化质量保障系统达成共识。核心方案是建立一套基于统一 `traceId` 的全链路可观测体系，并采用**自适应采样与优先级分层**策略来平衡数据全面性与系统性能。该方案明确了P0/P1/P2三级埋点字段，并集成了CI/CD门禁、降级场景强制采集及混沌工程验证等机制，确保系统在高压与故障场景下的稳定性和可追溯性。
  
  #### 2. 关键结论
  
  1.  **统一追踪与多维埋点**：采用W3C Trace Context标准，`traceId` 需贯穿API网关、WebSocket、K8s Sidecar全链路。埋点字段扩展至模型版本、异常评分、能耗、热传感器等元数据，实现多维链路完整性校验。
  2.  **自适应采样与优先级分层**：将埋点字段分为P0（实时必采，如`traceId`, `eventType`, `anomalyScore`）、P1（条件采样，如`gpuPowerW`, `modelVersion`）、P2（离线批量，如`nodePUE`）。采样率基于`anomalyScore`动态调整，并通过ConfigMap热更新。
  3.  **CI/CD集成门禁**：流水线中集成多项门禁，包括：采样率压测（P99延迟增量<5%）、采样一致性校验（同一traceId采样标记一致）、字段完整性校验（缺失P0字段阻断发布）、以及能耗/热采样门禁，确保发布质量。
  4.  **降级场景全量采集**：当触发`fallback_triggered`等降级事件时，强制全量采集该链路所有字段（包括P2），确保故障链路数据完整，便于根因分析。
  5.  **混沌工程验证**：在CI/CD中注入随机故障与流量突增，验证自适应采样策略在极端情况下的正确性与稳定性，确保P0字段100%采集且性能开销可控。
  
  #### 3. 执行计划
  
  **任务1：核心框架与埋点开发**
  *   **任务名称**: 实现全链路追踪与自适应采样框架
  *   **负责角色**: 全栈开发、Architect
  *   **预期产出**:
      *   完成W3C Trace Context在API网关、WebSocket、K8s Sidecar中的集成。
      *   开发自适应采样决策模块，支持基于`anomalyScore`的动态采样率调整。
      *   实现P0/P1/P2三级埋点字段的采集、本地缓冲与异步上报逻辑。
      *   交付可运行的代码库及技术设计文档。
  
  **任务2：CI/CD流水线集成与门禁开发**
  *   **任务名称**: 集成监控门禁与自动化测试
  *   **负责角色**: Deployer、Tester、Policy Engine
  *   **预期产出**:
      *   在CI/CD流水线中集成采样率压测门禁、字段完整性校验门禁、能耗/热采样门禁。
      *   开发采样一致性校验脚本，用于端到端测试。
      *   编写Playwright混沌工程测试用例，模拟异常与流量突增，验证采样策略。
      *   交付CI/CD流水线配置文件、测试脚本及门禁规则文档。
  
  **任务3：配置管理与文档化**
  *   **任务名称**: 建立采样策略配置中心与Schema Registry
  *   **负责角色**: Doc Writer、Deployer
  *   **预期产出**:
      *   搭建基于ConfigMap的采样策略动态配置中心，支持热更新。
      *   建立采样策略Schema Registry，强制每次更新携带`schemaVersion`。
      *   编写采样策略的版本管理、部署检查清单及故障报告模板。
      *   交付配置中心使用指南、Schema Registry规范及运维手册。
  
  #### 4. 建议指派团队
  
  建议将上述任务指派给 **Build团队** 执行，并由 **SRE团队** 提供架构与运维支持。项目经理将负责协调资源、跟踪进度，并确保最终交付物符合技术任务书要求。
  
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
  src/backend/agents/session_store.py
  src/backend/agents/skill_registry.py
  src/backend/agents/task_engine.py
  src/backend/agents/team_manager.py
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
  src/backend/channels/__init__.py
  src/backend/channels/bridge_chat.py
  src/backend/channels/marine_base.py
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
  src/docs/agent_handoffs/d87c964b-c06_architecture_20260503T045321.md
  src/docs/agent_handoffs/d87c964b-c06_pm_decompose_20260503T045236.md
  src/docs/agent_handoffs/d87c964b-c06_research_20260503T045251.md
  src/docs/agent_handoffs/d87c964b-c06_task_init_20260503T045211.md
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
  src/docs/workflow_artifacts/d87c964b-c06_architecture.md
  src/docs/workflow_artifacts/d87c964b-c06_pm_decompose.md
  src/docs/workflow_artifacts/d87c964b-c06_research.md
  src/docs/workflow_artifacts/dd0e3569-eb0_architecture.md
  src/docs/workflow_artifacts/dd0e3569-eb0_deploy.md
  src/docs/workflow_artifacts/dd0e3569-eb0_develop.md
  src/docs/workflow_artifacts/dd0e3569-eb0_pm_decompose.md
  src/docs/workflow_artifacts/dd0e3569-eb0_research.md
  src/docs/workflow_artifacts/dd0e3569-eb0_test.md
  ```
  
  ### 文件: `src/frontend/js/i18n.js`
  ```js
  /**
   * AgentsGroup2026 — i18n Internationalization Module v2
   * DOM text-walker approach: walks all text nodes and replaces Chinese↔English.
   * Usage: <script src="/js/i18n.js"></script>
   * Pages can extend via: PX_I18N.addTexts({ '中文': 'English', ... })
   */
  (function () {
    'use strict';
  
    const LANGS = ['zh', 'en'];
    const STORAGE_KEY = 'px-lang';
  
    /* ── Shared text map: zh → en ── */
    const TEXT_MAP = new Map([
      // ─── Index / Home page ───
      ['深海远洋双体船舶智能综合信息系统', 'Deep-Sea Ocean-Going Catamaran Intelligent Information System'],
      ['船长中控台', 'Captain Cockpit'],
      ['智能导航', 'Smart Navigation'],
      ['数据中心孪生', 'DC Digital Twin'],
      ['态势感知', 'Situation Awareness'],
      ['船岸通信', 'Ship-Shore Link'],
      ['气象海况', 'Weather & Sea'],
      ['海上作业', 'Offshore Operations'],
      ['进入系统', 'Enter System'],
  
      // ─── Page titles ───
      ['船长智能中控台', 'Captain Cockpit'],
      ['船长驾驶舱', 'Captain Cockpit'],
      ['导航与操纵', 'Navigation & Maneuvering'],
      ['动力定位', 'DP Control'],
      ['推进控制', 'Thruster Control'],
      ['全船监控', 'Full Ship Monitor'],
      ['设备健康', 'CMS Health'],
      ['控制台', 'HMI Console'],
      ['海工特种作业', 'Offshore Operations'],
      ['海工特種作业', 'Offshore Operations'],
      ['气象海洋', 'Weather & Ocean'],
      ['船员管理', 'Crew Management'],
      ['仿真训练', 'Simulation & Training'],
      ['能效合规', 'Energy Compliance'],
      ['船载数据中心', 'Marine Datacenter'],
      ['安全应急', 'Safety & Emergency'],
      ['船岸协同', 'Ship-Shore Sync'],
      ['数字孪生', 'Digital Twin'],
      ['智能体', 'AI Agents'],
      ['系统自我演进', 'System Self-Evolution'],
      ['系统演进', 'System Evolution'],
      ['知识库', 'Knowledge Base'],
      ['系统配置', 'System Configuration'],
      ['全球船舶监控平台', 'Global Ship Monitoring'],
      ['船舶避免碰撞增强现实系统', 'Ship Collision Avoidance AR System'],
  
      // ─── Nav sidebar ───
      ['船长总览', 'Captain'],
      ['导航', 'Navigation'],
      ['全船监控', 'Monitor'],
      ['海工作业', 'Offshore Ops'],
      ['船员管理', 'Crew Mgmt'],
  
      // ─── Common status / UI ───
      ['正常', 'Normal'],
      ['报警', 'Alarm'],
      ['警告', 'Warning'],
      ['离线', 'Offline'],
      ['在线', 'Online'],
      ['已连接', 'Connected'],
      ['待命', 'Standby'],
      ['就绪', 'Ready'],
      ['待确认', 'Pending'],
      ['已执行', 'Executed'],
      ['已确认', 'Confirmed'],
      ['已接收', 'Received'],
      ['已批准', 'Approved'],
      ['已提交', 'Submitted'],
      ['有效', 'Valid'],
      ['即将到期', 'Expiring Soon'],
      ['检修中', 'Under Maintenance'],
      ['加载中', 'Loading'],
      ['初始化中', 'Initializing'],
      ['搜索', 'Search'],
      ['保存', 'Save'],
      ['取消', 'Cancel'],
      ['确认', 'Confirm'],
      ['关闭', 'Close'],
      ['刷新', 'Refresh'],
      ['导出', 'Export'],
      ['状态', 'Status'],
      ['设置', 'Settings'],
      ['提交', 'Submit'],
      ['返回', 'Back'],
      ['折叠', 'Collapse'],
      ['全屏', 'Fullscreen'],
      ['隐藏', 'Hide'],
      ['开始', 'Start'],
      ['暂停', 'Pause'],
      ['重置', 'Reset'],
      ['清空', 'Clear'],
      ['添加', 'Add'],
      ['保存配置', 'Save Config'],
      ['刷新全部', 'Refresh All'],
  
      // ─── Captain cockpit ───
      ['快捷指令', 'Quick Commands'],
      ['拋錨', 'Drop Anchor'],
      ['抛锚', 'Drop Anchor'],
      ['响笛', 'Sound Horn'],
      ['紧急停车', 'Emergency Stop'],
      ['信号灯', 'Signal Light'],
      ['信号燈', 'Signal Light'],
      ['航行日志', 'Navigation Log'],
      ['航行日誌', 'Navigation Log'],
      ['系统设置', 'System Settings'],
      ['性能报告', 'Performance Report'],
      ['气象更新', 'Weather Update'],
      ['操作日志', 'Operation Log'],
      ['操作日誌', 'Operation Log'],
      ['操作人', 'Operator'],
      ['事件', 'Event'],
      ['结果', 'Result'],
      ['完成', 'Complete'],
      ['大副', 'Chief Officer'],
      ['轮机长', 'Chief Engineer'],
      ['船长', 'Captain'],
      ['调整航向', 'Adjust Heading'],
      ['主机转速', 'M/E RPM'],
      ['确认航线', 'Confirm Route'],
      ['您好', 'Hello'],
      ['当前航行状态如何', 'Current navigation status?'],
      ['当前航速', 'Current Speed'],
      ['航向', 'Heading'],
      ['主机功率', 'M/E Power'],
      ['子系统全部在线', 'All subsystems online'],
      ['抵达下一航路点', 'ETA next waypoint'],
      ['首页', 'Home'],
      ['中控台', 'Control Center'],
      ['广播', 'Broadcast'],
  
      // ─── Safety & Emergency ───
      ['消防区域矩阵', 'Fire Zone Matrix'],
      ['救生设备清单', 'Life Saving Equipment'],
      ['应急预案', 'Emergency Plans'],
      ['集合站点', 'Muster Stations'],
      ['正常区域', 'Normal Zones'],
      ['注意区域', 'Caution Zones'],
      ['报警区域', 'Alarm Zones'],
      ['救生设备', 'Life Saving Equip.'],
      ['预案就绪', 'Plans Ready'],
      ['设备', 'Equipment'],
      ['数量', 'Qty'],
      ['容量', 'Capacity'],
      ['检验日期', 'Inspection Date'],
      ['救生艇', 'Lifeboat'],
      ['救生筏', 'Life Raft'],
      ['救生圈', 'Life Buoy'],
      ['救生衣', 'Life Jacket'],
      ['发光', 'Illuminated'],
      ['烟雾', 'Smoke Signal'],
      ['火灾', 'Fire'],
      ['弃船', 'Abandon Ship'],
      ['人落水', 'Man Overboard'],
      ['碰撞', 'Collision'],
      ['搁浅', 'Grounding'],
      ['进水', 'Flooding'],
      ['污染', 'Pollution'],
      ['医疗', 'Medical'],
      ['机舱', 'Engine Room'],
      ['货舱', 'Cargo Hold'],
      ['住舱', 'Accommodation'],
      ['驾驶', 'Bridge'],
      ['甲板', 'Deck'],
      ['左舷甲板', 'Port Deck'],
      ['右舷甲板', 'Starboard Deck'],
      ['驾驶台', 'Bridge'],
      ['机舱控制室', 'Engine Control Room'],
      ['人已到', 'Arrived'],
  
      // ─── Ship-Shore ───
      ['通信链路', 'Communication Links'],
      ['数据同步', 'Data Sync'],
      ['岸基指令历史', 'Shore Command History'],
      ['远程数据流', 'Remote Data Flow'],
      ['上行', 'Uplink'],
      ['下行', 'Downlink'],
      ['延迟', 'Latency'],
      ['航行数据', 'Navigation Data'],
      ['实时', 'Real-time'],
      ['岸基', 'Shore'],
      ['云存储', 'Cloud Storage'],
      ['云存儲', 'Cloud Storage'],
      ['视频监控', 'Video Monitor'],
      ['視频监控', 'Video Monitor'],
      ['岸基指令', 'Shore Command'],
      ['船端', 'Ship-side'],
      ['时间', 'Time'],
      ['来源', 'Source'],
      ['指令', 'Command'],
      ['航速调整', 'Speed Adjustment'],
      ['进港航道确认', 'Port Channel Confirm'],
      ['台风预警转发', 'Typhoon Alert Forward'],
      ['优化建议下发', 'Optimization Advice'],
      ['沿海', 'Coastal'],
      ['双频', 'Dual Freq'],
  
      // ─── Simulation & Training ───
      ['综合评分', 'Overall Score'],
      ['綜合評分', 'Overall Score'],
      ['训练次数', 'Training Count'],
      ['本月', 'This Month'],
      ['累计时长', 'Total Duration'],
      ['船员排名', 'Crew Ranking'],
      ['场景配置', 'Scenario Config'],
      ['训练场景', 'Training Scenario'],
      ['故障注入', 'Fault Injection'],
      ['训练日志', 'Training Log'],
      ['训练日誌', 'Training Log'],
      ['能力评估雷达图', 'Competency Radar'],
      ['能力評估雷达图', 'Competency Radar'],
      ['成绩详情', 'Score Details'],
      ['成績详情', 'Score Details'],
      ['评分趋势', 'Score Trend'],
      ['評分趨勢', 'Score Trend'],
      ['避碰判断', 'Collision Avoidance'],
      ['导航精度', 'Navigation Accuracy'],
      ['通信规范', 'Communication Standards'],
      ['应急反应', 'Emergency Response'],
      ['操纵技能', 'Maneuvering Skills'],
      ['团队协作', 'Teamwork'],
      ['平均反应时间', 'Avg. Response Time'],
      ['天气', 'Weather'],
      ['海况', 'Sea State'],
      ['交通密度', 'Traffic Density'],
      ['能见度', 'Visibility'],
      ['模拟时间', 'Simulation Time'],
      ['主机故障', 'M/E Failure'],
      ['舵机故障', 'Rudder Lock'],
      ['雷达故障', 'Radar Fail'],
      ['通信中断', 'Comms Down'],
      ['电力丧失', 'Blackout'],
      ['优秀', 'Excellent'],
      ['合格', 'Pass'],
      ['失败', 'Fail'],
      ['晴朗', 'Clear'],
      ['多云', 'Cloudy'],
      ['暴雨', 'Storm'],
      ['台风', 'Typhoon'],
      ['轻浪', 'Slight'],
      ['大浪', 'Rough'],
      ['狂浪', 'Very Rough'],
      ['狂涛', 'High'],
      ['蒲氏风级', 'Beaufort Scale'],
      ['评价', 'Grade'],
      ['右舷让路避让', 'Starboard Give-way'],
      ['雷达标绘', 'Radar Plotting'],
      ['联络确认', 'Communication Confirm'],
      ['狭水道右舷通行', 'Narrow Channel Starboard'],
      ['应急舵切换', 'Emergency Steering Switch'],
      ['追越船避让', 'Overtaking Avoidance'],
      ['避碰', 'COLREG Avoidance'],
      ['分道通航', 'TSS'],
      ['港口进出', 'Port Entry/Exit'],
      ['应急操纵', 'Emergency Maneuvering'],
      ['锚泊作业', 'Anchoring Ops'],
  
      // ─── System Evolution ───
      ['达尔文棘轮', 'Darwin Ratchet'],
      ['自然选择', 'Natural Selection'],
      ['棘轮机制', 'Ratchet Mechanism'],
      ['演进时间线', 'Evolution Timeline'],
      ['初始化棘轮引擎中', 'Initializing Ratchet Engine'],
      ['演进流水线', 'Evolution Pipeline'],
      ['演进操作', 'Evolution Ops'],
      ['演进趋势', 'Evolution Trend'],
      ['域覆盖雷达', 'Domain Radar'],
      ['审查热力图', 'Audit Heatmap'],
      ['合规评级', 'Compliance Rating'],
      ['合规区域', 'Compliance Zones'],
      ['升级仪表板', 'Upgrade Dashboard'],
      ['双重检查单', 'Double Checklist'],
      ['公司级', 'Company Level'],
      ['船舶级', 'Vessel Level'],
      ['审计轨迹', 'Audit Trail'],
      ['审查规则库', 'Audit Rules'],
      ['演进条目', 'Evolution Entries'],
      ['审查历史', 'Audit History'],
      ['运行审查', 'Runtime Audit'],
      ['派发', 'Dispatch'],
      ['验证', 'Verify'],
      ['完整周期', 'Full Cycle'],
      ['已锁定的演化特性只增不减', 'Locked traits only grow, never regress'],
      ['永不回退', 'Never Rollback'],
      ['系统自我演进引擎就绪', 'Self-Evolution Engine Ready'],
      ['正在加载演进数据', 'Loading evolution data'],
      ['活跃', 'Active'],
  
      // ─── Thruster Control ───
      ['机舱综合状态', 'Engine Room Overview'],
      ['机舱綜合狀态', 'Engine Room Overview'],
      ['功率趋势', 'Power Trend'],
      ['功率趨勢', 'Power Trend'],
      ['振动频谱', 'Vibration Spectrum'],
      ['振动频譜', 'Vibration Spectrum'],
      ['缸温分布', 'Cylinder Temp Distribution'],
      ['缸溫分布', 'Cylinder Temp Distribution'],
      ['燃油流量', 'Fuel Flow'],
      ['能效指标', 'Efficiency Indicators'],
      ['额定', 'Rated'],
      ['负荷', 'Load'],
      ['燃油压力', 'Fuel Pressure'],
      ['排气温度', 'Exhaust Temp'],
      ['振动水平', 'Vibration Level'],
      ['舱底水位', 'Bilge Water Level'],
      ['推进效率', 'Propulsion Efficiency'],
      ['总运行时', 'Total Runtime'],
      ['下次保养', 'Next Maintenance'],
      ['高级控制', 'Advanced Control'],
      ['限值', 'Limit'],
      ['滑油温度', 'Lube Oil Temp'],
      ['冷却水温', 'Cooling Water Temp'],
      ['车钟', 'Telegraph'],
      ['车鐘', 'Telegraph'],
  
      // ─── Weather & Ocean ───
      ['风场', 'Wind Field'],
      ['風场', 'Wind Field'],
      ['海浪谱', 'Wave Spectrum'],
      ['海浪譜', 'Wave Spectrum'],
      ['海况综合', 'Sea Conditions'],
      ['海況綜合', 'Sea Conditions'],
      ['道格拉斯海况', 'Douglas Sea State'],
      ['蒲福风级', 'Beaufort Scale'],
      ['气温', 'Air Temp'],
      ['水温', 'Water Temp'],
      ['气压', 'Pressure'],
      ['湿度', 'Humidity'],
      ['洋流', 'Current'],
      ['涌浪', 'Swell'],
      ['表面流速', 'Surface Current Speed'],
      ['流向', 'Current Direction'],
      ['涌浪评估', 'Swell Assessment'],
      ['适航', 'Seaworthy'],
      ['潮汐', 'Tide'],
      ['当前潮高', 'Current Tide Height'],
      ['气象预警', 'Weather Warning'],
      ['大风蓝色预警', 'Blue Gale Warning'],
      ['天气窗口', 'Weather Window'],
      ['可作业', 'Operable'],
      ['航线天气评估', 'Route Weather Assessment'],
      ['良好', 'Good'],
      ['预报', 'Forecast'],
      ['方向', 'Direction'],
      ['风速', 'Wind Speed'],
      ['风向', 'Wind Dir'],
      ['浪高', 'Wave Height'],
  
      // ─── Offshore Operations ───
      ['作业状态', 'Operation Status'],
      ['作业狀态', 'Operation Status'],
      ['作业类型', 'Operation Type'],
      ['起重吊装', 'Crane Lifting'],
      ['许可状态', 'Permit Status'],
      ['許可狀态', 'Permit Status'],
      ['作业区域', 'Work Zone'],
      ['客户', 'Client'],
      ['起重机状态', 'Crane Status'],
      ['起重机狀态', 'Crane Status'],
      ['臂仰角', 'Boom Angle'],
      ['回转角', 'Slew Angle'],
      ['吃钩高度', 'Hook Height'],
      ['吃鉤高度', 'Hook Height'],
      ['环境条件', 'Environment Conditions'],
      ['环境條件', 'Environment Conditions'],
      ['作业限制', 'Op. Limits'],
      ['未超限', 'Within Limits'],
      ['安全检查单', 'Safety Checklist'],
      ['安全检查單', 'Safety Checklist'],
      ['系统状态确认', 'System Status Confirmed'],
      ['系统狀态确认', 'System Status Confirmed'],
      ['通信链路测试', 'Comms Link Test'],
      ['通信链路测試', 'Comms Link Test'],
      ['人员就位确认', 'Personnel Positioned'],
      ['气象窗口核实', 'Weather Window Verified'],
      ['应急预案就绪', 'Emergency Plan Ready'],
      ['应急预案就緒', 'Emergency Plan Ready'],
      ['吊具检验合格', 'Rigging Inspection Pass'],
      ['吊具检驗合格', 'Rigging Inspection Pass'],
      ['安全区域清场', 'Safety Zone Cleared'],
      ['平台东南侧', 'Platform SE Side'],
      ['平台東南側', 'Platform SE Side'],
  
      // ─── Crew Management ───
      ['总船员', 'Total Crew'],
      ['当值', 'On Watch'],
      ['休息', 'Off Watch'],
      ['疲劳预警', 'Fatigue Alert'],
      ['疲勞预警', 'Fatigue Alert'],
      ['证书到期', 'Certificate Expiring'],
      ['证書到期', 'Certificate Expiring'],
      ['船员花名册', 'Crew Roster'],
      ['船员花名冊', 'Crew Roster'],
      ['休息时间合规', 'Work/Rest Compliance'],
      ['休息时間合规', 'Work/Rest Compliance'],
      ['疲劳风险', 'Fatigue Risk'],
      ['疲勞風险', 'Fatigue Risk'],
      ['船舶评分', 'Vessel Score'],
      ['高风险人员', 'High Risk Personnel'],
      ['达标', 'Compliant'],
      ['证书监控', 'Certificate Monitor'],
      ['证書监控', 'Certificate Monitor'],
      ['应急演练记录', 'Emergency Drill Records'],
      ['值班安排', 'Watch Schedule'],
      ['当前班次', 'Current Watch'],
      ['甲班', 'Watch A'],
      ['下次换班', 'Next Changeover'],
      ['大管轮', 'Second Engineer'],
      ['水手长', 'Bosun'],
      ['机工', 'Motorman'],
  
      // ─── Energy Compliance ───
      ['当前', 'Current'],
      ['年度评级', 'Annual Rating'],
      ['年度轨迹', 'Annual Trajectory'],
      ['实时追踪', 'Real-time Tracking'],
      ['月度燃油消耗', 'Monthly Fuel Consumption'],
      ['排放监测', 'Emissions Monitoring'],
      ['二氧化碳', 'CO₂'],
      ['年度申报', 'Annual Declaration'],
      ['硫氧化物', 'SOx'],
      ['氮氧化物', 'NOx'],
      ['颗粒物', 'Particulate Matter'],
      ['合规文档', 'Compliance Documents'],
      ['文档名称', 'Document Name'],
      ['编号', 'Number'],
      ['有效期', 'Validity'],
      ['更新日期', 'Update Date'],
      ['审核机构', 'Audit Authority'],
      ['技术档案', 'Technical File'],
      ['改善方案', 'Improvement Plan'],
      ['国际能效证书', 'International Energy Cert.'],
      ['排放合规声明', 'Emission Compliance Decl.'],
      ['年报', 'Annual Report'],
      ['合规', 'Compliant'],
  
      // ─── Navigation ───
      ['电子海图', 'ECDIS'],
      ['航线路径点', 'Route Waypoints'],
      ['气象数据', 'Weather Data'],
      ['叠加层', 'Overlays'],
      ['目标', 'Targets'],
      ['雷达回波', 'Radar Echo'],
      ['安全等深线', 'Safety Contour'],
      ['追踪', 'Tracking'],
      ['航线进度', 'Route Progress'],
      ['航速', 'Speed'],
  
      // ─── Knowledge Base ───
      ['文档', 'Documents'],
      ['向量', 'Vectors'],
      ['领域', 'Domains'],
      ['領域', 'Domains'],
      ['全部', 'All'],
      ['法规', 'Regulations'],
      ['程序', 'Procedures'],
      ['技术', 'Technical'],
      ['培训', 'Training'],
      ['清单', 'Checklist'],
      ['清單', 'Checklist'],
      ['添加知识文档', 'Add Knowledge Document'],
      ['标题', 'Title'],
      ['标題', 'Title'],
      ['类别', 'Category'],
      ['类別', 'Category'],
      ['标签', 'Tags'],
      ['标籤', 'Tags'],
      ['逗号分隔', 'Comma separated'],
      ['内容', 'Content'],
      ['內容', 'Content'],
  
      // ─── Config page ───
      ['船舶信息', 'Ship Info'],
      ['船名', 'Ship Name'],
      ['船型', 'Ship Type'],
      ['穿浪双体船', 'Wave-Piercing Catamaran'],
      ['集装箱船', 'Container Ship'],
      ['散货船', 'Bulk Carrier'],
      ['油轮', 'Tanker'],
      ['总吨', 'Gross Tonnage'],
      ['功能开关', 'Feature Toggles'],
      ['决策辅助', 'Decision Aid'],
      ['決策輔助', 'Decision Aid'],
      ['启用', 'Enable'],
      ['自动避碰', 'Auto COLREG'],
      ['气象航线优化', 'Weather Route Optimization'],
      ['船员疲劳监控', 'Crew Fatigue Monitor'],
      ['船员疲勞监控', 'Crew Fatigue Monitor'],
      ['闭环审查', 'Closed-loop Audit'],
      ['构建', 'Build'],
      ['数据存储', 'Data Storage'],
      ['数据存儲', 'Data Storage'],
      ['访问控制', 'Access Control'],
      ['认证', 'Authentication'],
      ['端口控制', 'Port Control'],
      ['未授权', 'Unauthorized'],
      ['审查日志', 'Audit Log'],
      ['審查日誌', 'Audit Log'],
      ['记录所有系统配置变更', 'Log all config changes'],
      ['系统运行状态', 'System Runtime Status'],
      ['系统运行狀态', 'System Runtime Status'],
      ['运行时间', 'Uptime'],
      ['使用率', 'Usage'],
      ['内存使用', 'Memory Usage'],
      ['健康', 'Healt
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
  
  ### 文件: `src/backend/main.py`
  ```py
  # -*- coding: utf-8 -*-
  """
  AgentsGroup2026 — Standalone Agent Management + Evolution + Chat Server
  
  A self-contained FastAPI application extracted from AgentsGroup2026 that provides:
    - Agent team management (create/configure/manage agents)
    - System evolution engine (audit → dispatch → verify → close)
    - Bridge chat (LLM-powered conversational interface)
    - OpenClaw integration (connect external agents)
  
  Usage:
      cd src/backend && python main.py --port 8080
  """
  
  from __future__ import annotations
  
  import argparse
  import json
  import logging
  import os
  import sys
  from pathlib import Path
  from typing import Any, Dict, Optional
  
  import uvicorn
  from fastapi import FastAPI, HTTPException
  from fastapi.middleware.cors import CORSMiddleware
  from fastapi.staticfiles import StaticFiles
  from pydantic import BaseModel
  
  # ── Logging ──
  logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s  %(message)s")
  logger = logging.getLogger("agentsgroup")
  
  # ── App ──
  app = FastAPI(
      title="AgentsGroup2026",
      description="Standalone Agent Management, Evolution & Chat Platform",
      version="1.0.0",
  )
  
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  
  
  # ══════════════════════════════════════════════════════════════════
  # Request / Response Models
  # ══════════════════════════════════════════════════════════════════
  
  class BridgeChatRequest(BaseModel):
      message: str
      session_id: str = "default"
      lang: str = "zh"
      agent_id: str = "default_agent"
      source: str = "bridge_chat"
  
  
  class HealthResponse(BaseModel):
      status: str = "ok"
      version: str = "1.0.0"
      services: Dict[str, bool] = {}
  
  
  class LoginRequest(BaseModel):
      username: str
      password: str
  
  
  class RegisterRequest(BaseModel):
      username: str
      password: str
  
  
  # ══════════════════════════════════════════════════════════════════
  # Global State
  # ══════════════════════════════════════════════════════════════════
  
  _team_manager = None
  _chat_channel = None
  
  
  # ══════════════════════════════════════════════════════════════════
  # Startup
  # ══════════════════════════════════════════════════════════════════
  
  @app.on_event("startup")
  async def startup():
      """Initialize all subsystems."""
      global _team_manager, _chat_channel
  
      logger.info("🚀 AgentsGroup2026 starting...")
  
      # 1. Register channels (evolution + chat)
      try:
          from channels.marine_base import get_default_registry
          from channels.system_evolution import SystemEvolutionChannel
          from channels.bridge_chat import BridgeChatChannel
  
          registry = get_default_registry()
  
          # System Evolution
          evo = SystemEvolutionChannel()
          registry.register(evo)
          evo.initialize()
          logger.info("✅ SystemEvolutionChannel registered")
  
          # Bridge Chat
          channel_registry = {}
          for ch_name in registry.list_channels():
              ch = registry.get(ch_name)
              if ch:
                  channel_registry[ch_name] = ch
          _chat_channel = BridgeChatChannel(channel_registry=channel_registry)
          registry.register(_chat_channel)
          _chat_channel.initialize()
          logger.info("✅ BridgeChatChannel registered")
      except Exception as e:
          logger.warning(f"⚠️ Channel registration failed: {e}")
  
      # 2. Agent Team API (evolution endpoints)
      try:
          from agent_team_api import router as agent_team_router, set_teams
          from channels.marine_base import get_default_registry
  
          registry = get_default_registry()
          evo_engine = registry.get("system_evolution")
          set_teams(
              build_team=None,
              execution_team=None,
              scheduler=None,
              evolution_engine=evo_engine,
          )
          app.include_router(agent_team_router)
          logger.info("✅ Agent Team API mounted (/api/v1/agent-teams)")
      except Exception as e:
          logger.warning(f"⚠️ Agent Team API failed: {e}")
  
      # 3. Agent Config API (teams, agents, tools, skills, tasks, sessions)
      try:
          from agents.api import router as agent_config_router, init_agent_config
          from agents.team_manager import TeamManager
          from agents.teams.build_team import create_build_team
  
          _team_manager = TeamManager()
          build_team_obj = create_build_team()
          _team_manager._teams[build_team_obj.team_id] = build_team_obj
  
          # AI 编程团队
          try:
              from agents.teams.ai_coding_team import create_ai_coding_team
              ai_coding_obj = create_ai_coding_team()
              _team_manager._teams[ai_coding_obj.team_id] = ai_coding_obj
          except Exception:
              pass
  
          # Try energy team (optional)
          try:
              from agents.teams.energy_team import create_energy_team
              energy_team_obj = create_energy_team()
              _team_manager._teams[energy_team_obj.team_id] = energy_team_obj
          except Exception:
              pass
  
          init_agent_config(_team_manager)
          app.include_router(agent_config_router)
          logger.info(
              "✅ Agent Config API mounted (/api/v1/agent-config) "
              f"— teams: {len(_team_manager.list_teams())}, "
              f"agents: {sum(len(t.agents) for t in _team_manager.list_teams())}"
          )
  
          # 4. 智能体广场 API
          try:
              from agents.plaza_routes import router as plaza_router
              from agents.plaza_engine import get_plaza_engine
              from agents.chat_harness import ChatHarness
  
              plaza_engine = get_plaza_engine()
              # 注入 ChatHarness.chat 函数
              from agents.api import get_chat_harness
              harness = get_chat_harness()
              plaza_engine.set_chat_fn(harness.chat)
  
              app.include_router(plaza_router, prefix="/api/v1/agent-config")
              logger.info("✅ 智能体广场 API mounted (/api/v1/agent-config/plaza)")
          except Exception as e:
              logger.warning(f"⚠️ Plaza API failed: {e}")
  
          # 4b. TTS 语音合成代理 (GPT-SoVITS)
          try:
              from agents.tts_routes import router as tts_router
              app.include_router(tts_router, prefix="/api/v1")
              logger.info("✅ TTS API mounted (/api/v1/tts)")
          except Exception as e:
              logger.warning(f"⚠️ TTS API failed: {e}")
  
      except Exception as e:
          logger.warning(f"⚠️ Agent Config API failed: {e}")
  
      # 5. 启动验证路由
      try:
          from startup_check import get_startup_check_router
          app.include_router(get_startup_check_router())
          logger.info("✅ Startup Check API mounted (/api/v1/startup-check)")
      except Exception as e:
          logger.warning(f"⚠️ Startup Check API failed: {e}")
  
      logger.info("🎉 AgentsGroup2026 ready")
  
      # 6. 异步执行启动验证（不阻塞启动）
      try:
          import asyncio
          from startup_check import run_startup_check
  
          async def _delayed_check():
              await asyncio.sleep(2)  # 等待所有服务就绪
              await run_startup_check(base_url="http://localhost:8080")
  
          asyncio.create_task(_delayed_check())
          logger.info("🔍 Startup validation scheduled (delayed 2s)")
      except Exception as e:
          logger.warning(f"⚠️ Startup validation scheduling failed: {e}")
  
  
  # ══════════════════════════════════════════════════════════════════
  # Auth
  # ══════════════════════════════════════════════════════════════════
  
  import hashlib
  import secrets
  
  # Default users (in production, use a proper database)
  _USERS = {
      "admin": hashlib.sha256("admin123".encode()).hexdigest(),
  }
  _TOKENS: Dict[str, str] = {}
  
  
  @app.post("/api/v1/auth/register")
  async def register(req: RegisterRequest):
      """Register a new user."""
      username = req.username.strip()
      if not username or len(username) < 2:
          raise HTTPException(status_code=400, detail="用户名至少需要2个字符")
      if len(req.password) < 4:
          raise HTTPException(status_code=400, detail="密码至少需要4个字符")
      if username in _USERS:
          raise HTTPException(status_code=409, detail="该用户名已被注册")
      _USERS[username] = hashlib.sha256(req.password.encode()).hexdigest()
      token = secrets.token_hex(32)
      _TOKENS[token] = username
      logger.info(f"✅ New user registered: {username}")
      return {"token": token, "username": username}
  
  
  @app.post("/api/v1/auth/login")
  async def login(req: LoginRequest):
      """Simple token-based login."""
      pwd_hash = hashlib.sha256(req.password.encode()).hexdigest()
      if req.username not in _USERS or _USERS[req.username] != pwd_hash:
          raise HTTPException(status_code=401, detail="用户名或密码错误")
      token = secrets.token_hex(32)
      _TOKENS[token] = req.username
      return {"token": token, "username": req.username}
  
  
  @app.get("/api/v1/auth/me")
  async def auth_me(authorization: str = ""):
      """Check current auth status."""
      token = authorization.replace("Bearer ", "") if authorization else ""
      if token in _TOKENS:
          return {"username": _TOKENS[token], "authenticated": True}
      return {"username": "guest", "authenticated": False}
  
  
  # ══════════════════════════════════════════════════════════════════
  # Health & Info
  # ══════════════════════════════════════════════════════════════════
  
  @app.get("/api/v1/health")
  async def health():
      """Health check endpoint."""
      from channels.marine_base import get_default_registry
      registry = get_default_registry()
      return HealthResponse(
          status="ok",
          version="1.0.0",
          services={
              "evolution": registry.get("system_evolution") is not None,
              "bridge_chat": registry.get("bridge_chat") is not None,
              "agent_config": _team_manager is not None,
          },
      )
  
  
  @app.get("/api/v1/info")
  async def info():
      """System info endpoint for external integrations."""
      return {
          "name": "AgentsGroup2026",
          "version": "1.0.0",
          "description": "Standalone Agent Management, Evolution & Chat Platform",
          "capabilities": ["agent_management", "system_evolution", "chat", "openclaw_integration"],
          "api_prefix": "/api/v1",
          "endpoints": {
              "agent_config": "/api/v1/agent-config",
              "agent_teams": "/api/v1/agent-teams",
              "evolution": "/api/v1/agent-teams/evolution",
              "chat": "/api/v1/bridge-chat",
              "health": "/api/v1/health",
          },
      }
  
  
  # ══════════════════════════════════════════════════════════════════
  # Bridge Chat endpoints
  # ══════════════════════════════════════════════════════════════════
  
  async def _agent_llm_chat(
      message: str,
      session_id: str = "default",
      agent_id: str = "default_agent",
  ) -> Optional[Dict[str, Any]]:
      """Try LLM chat with agent context. Returns None if LLM is unavailable."""
      try:
          from agents.chat_harness import get_chat_harness
          from agents.api import _team_manager as tm
      except ImportError:
          return None
  
      harness = get_chat_harness()
      agent_prompt = ""
      agent_name = agent_id
  
      if tm:
          for team in tm.list_teams():
              agent = team.get_agent(agent_id)
              if agent:
                  agent_prompt = agent.system_prompt or ""
                  agent_name = agent.name or agent_id
                  break
  
      ctx_lines = []
      if agent_prompt:
          ctx_lines.append(agent_prompt)
      else:
          ctx_lines.append(f"你是 AgentsGroup2026 系统的智能体 {agent_name}。")
      ctx_lines.append("回答时简洁专业，可中英文混合。")
      ctx_lines.append("如果用户请求涉及系统改进，请提出具体可执行的建议。")
      system_prompt = "\n".join(ctx_lines)
  
      try:
          result = await harness.chat(
              message,
              agent_id=agent_id,
              session_id=f"chat_{session_id}",
              system_prompt=system_prompt,
          )
          if result.error:
              return None
          reply = result.response.strip()
          if not reply:
              return None
  
          urgency = "normal"
          urgent_kw = ["紧急", "严重", "critical", "urgent", "emergency", "error"]
          if any(kw in reply.lower() for kw in urgent_kw):
              urgency = "high"
  
          return {
              "reply": reply,
              "urgency": urgency,
              "source": "agent_llm",
              "agent_id": agent_id,
              "agent_name": agent_name,
              "model": result.model,
              "provider": result.provider,
              "latency_ms": round(result.latency_ms, 1),
              "session_id": session_id,
          }
      except Exception as exc:
          logger.debug("Agent LLM chat failed: %s", exc)
          return None
  
  
  @app.post("/api/v1/bridge-chat/send")
  async def bridge_chat_send(payload: BridgeChatRequest):
      """Handle chat message — LLM first, template fallback.
  
      When the user mentions task/build keywords, automatically creates
      a task for the build team via TaskEngine.
      """
      # Try LLM chat
      llm_result = await _agent_llm_chat(payload.message, payload.session_id, agent_id=payload.agent_id)
  
      # Auto-create task when message mentions build/task keywords
      task_id = None
      msg_text = (payload.message or "").strip()
      _build_keywords = [
          "build团队", "Build团队", "build team", "开发任务", "开发团队",
          "构建团队", "提交任务", "分配任务", "创建任务", "新建任务",
          "改进系统", "优化系统", "修复", "升级", "重构",
      ]
      _is_build_request = any(kw in msg_text for kw in _build_keywords)
  
      if _is_build_request and len(msg_text) >= 4:
          try:
              from agents.api import _te
              from agents.task_engine import AgentTask
  
              title = msg_text.split("\n")[0][:120]
              task_description = msg_text
              if llm_result and llm_result.get("reply"):
                  task_description = (
                      f"{msg_text}\n\n---\n\n"
                      f"## Agent 分析建议 (参考)\n\n{llm_result['reply']}\n"
                  )
  
              engine = _te()
              if not engine._running:
                  await engine.start()
  
              task = AgentTask(
                  agent_id="build_pm",
                  team_id="build_system",
                  title=title,
                  description=task_description,
                  priority=2,
                  metadata={
                      "source": "bridge_chat",
                      "session_id": payload.session_id,
                      "agent_id": payload.agent_id,
                  },
              )
              await engine.submit_task(task)
              task_id = task.task_id
              logger.info(f"[Chat] Created task {task_id}: {title[:40]}")
          except Exception as e:
              logger.warning(f"[Chat] Task creation failed: {e}")
              if llm_result:
                  llm_result["pipeline_error"] = f"任务创建失败: {str(e)[:200]}"
  
      if llm_result:
          if task_id:
              llm_result["task_id"] = task_id
          return llm_result
  
      # Fallback to template-based bridge_chat channel
      try:
          from channels.marine_base import get_default_registry
  
          registry = get_default_registry()
          chat_ch = registry.get("bridge_chat")
          if not chat_ch:
          
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
  from datetime import datetime, timezone
  from typing import Any, AsyncIterator, Callable, Dict, List, Optional
  from uuid import uuid4
  
  from .plaza import (
      Discussion, DiscussionStatus, NicheRole, Participant,
      Plaza, PlazaMessage, SeatTier, PRESET_TOPICS,
  )
  
  logger = logging.getLogger(__name__)
  
  
  class PlazaEngine:
      """广场引擎 — 管理广场、参与者和讨论编排."""
  
      def __init__(self):
          self._plazas: Dict[str, Plaza] = {}
          self._sse_queues: Dict[str, List[asyncio.Queue]] = {}  # discussion_id → queues
          self._chat_fn: Optional[Callable] = None  # ChatHarness.chat reference
  
      def set_chat_fn(self, fn: Callable):
          """注入 ChatHarness.chat 异步函数."""
          self._chat_fn = fn
  
      # ── 广场 CRUD ──────────────────────────────────────────
  
      def create_plaza(self, name: str, description: str = "") -> Plaza:
          plaza = Plaza(name=name, description=description)
          self._plazas[plaza.id] = plaza
          logger.info(f"🏛️ 广场创建: {name} ({plaza.id})")
          return plaza
  
      def get_plaza(self, plaza_id: str) -> Optional[Plaza]:
          return self._plazas.get(plaza_id)
  
      def list_plazas(self) -> List[Plaza]:
          return list(self._plazas.values())
  
      def delete_plaza(self, plaza_id: str) -> bool:
          if plaza_id in self._plazas:
              del self._plazas[plaza_id]
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
          logger.info(f"🪑 参与者加入广场 {plaza_id}: {agent_name} (壁龛 #{niche_index})")
          return p
  
      def remove_participant(self, plaza_id: str, agent_id: str) -> bool:
          plaza = self._plazas.get(plaza_id)
          if plaza and agent_id in plaza.participants:
              del plaza.participants[agent_id]
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
              key=lambda p: tier_order.get(p.seat_tier, 1),
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
              f"请开场: 简要阐述话题的背景和意义，明确讨论目标，然后提出第一个引导性问题。"
          )
          opening = await self._agent_speak(
              disc, moderator, opening_prompt, round_number=0,
              niche_role="moderator",
          )
  
          # ── 多轮讨论 ──
          for round_num in range(1, disc.max_rounds + 1):
              disc.current_round = round_num
              await self._broadcast(disc.id, {
                  "type": "round_start", "round": round_num,
                  "max_rounds": disc.max_rounds,
              })
  
              # 每个参与者发言
              prev_messages = self._format_history(disc)
              for speaker in speakers:
                  speak_prompt = (
                      f"你正在参与一场关于「{disc.topic}」的讨论。\n"
                      f"你的角色: {speaker.agent_name} ({speaker.role})\n"
                      f"当前是第 {round_num}/{disc.max_rounds} 轮。\n\n"
                      f"之前的讨论内容:\n{prev_messages}\n\n"
                      f"请根据你的专业背景发表观点。注意:\n"
                      f"- 回应之前的讨论内容，可以赞同、补充或提出不同见解\n"
                      f"- 言之有物，提供具体的技术细节或实践经验\n"
                      f"- 控制在 200 字以内"
                  )
                  await self._agent_speak(
                      disc, speaker, speak_prompt, round_number=round_num,
                      niche_role=speaker.niche_role.value,
                  )
                  prev_messages = self._format_history(disc)
  
              # Moderator 总结本轮
              if round_num < disc.max_rounds:
                  summary_prompt = (
                      f"你是主持人。第 {round_num} 轮讨论已结束。\n\n"
                      f"本轮讨论内容:\n{self._format_round_messages(disc, round_num)}\n\n"
                      f"请简要总结本轮的关键观点 (3 句以内)，"
                      f"然后提出下一轮的引导性问题。"
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
              f"请生成最终总结和执行计划:\n"
              f"1. 讨论概要 (3-5 句)\n"
              f"2. 关键结论 (列出 3-5 个要点)\n"
              f"3. 执行计划:\n"
              f"   - 列出 2-4 个具体可执行的任务步骤\n"
              f"   - 每个步骤包含: 任务名称、负责角色、预期产出\n"
              f"4. 建议指派给哪个团队执行\n\n"
              f"请用结构化格式输出。"
          )
          summary_msg = await self._agent_speak(
              disc, moderator, final_prompt, round_number=disc.max_rounds + 1,
              niche_role="moderator",
          )
          disc.summary = summary_msg.content if summary_msg else ""
          disc.status = DiscussionStatus.CLOSED
          disc.ended_at = datetime.now(timezone.utc).isoformat()
  
          await self._broadcast(disc.id, {
              "type": "discussion_end",
              "summary": disc.summary,
          })
  
          logger.info(
              f"✅ 讨论完成: {disc.topic[:30]} — "
              f"{len(disc.messages)} 条消息, {disc.max_rounds} 轮"
          )
          re
  ```
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  
  ## 前序步骤的产出 (递进式摘要)
  
  ### 步骤 01: pm_decompose
  任务: [广场计划] 设计并实现一套智能体广场实时监控与自动化质量保障系统
  步骤: pm_decompose
  📋 任务: dbf24d0c-5cc
  🤖 Agent: PM (project_manager)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ────────────────────────────────────────────────────────────
  你是 AgentsGroup2026 系统的 PM (project_manager)。
  你是项目经理 (PM)。请对以下任务进行分解和规划:
  [广场计划] 设计并实现一套智能体广场实时监控与自动化质量保障系统
  好的，作为项目经理，我已整合各位专家的意见，形成最终总结与执行计划。
  经过多轮讨论，团队已就智能体广场的实时监控与自动化质量保障系统达成共识。核心方案是建立一套基于统一 `traceId` 的全链路可观测体系，并采用**自适应采样与优先级分层**策略来平衡数据全面性与系统性能。该方案明确了P0/P1/P2三级埋点字段，并集成了CI/CD门禁、降级场景强制采集及混沌工程验证等机制，确保系统在高压与故障场景下的稳定性和可追溯性。
  1.  **统一追踪与多维埋点**：采用W3C Trace Context标准，`traceId` 需贯穿API网关、WebSocket、K8s Sidecar全链路。埋点字段扩展至模型版本、异常评分、能耗、热传感器等元数据，实现多维链路完整性校验。
  2.  **自适应采样与优先级分层**：将埋点字段分为P0（实时必采，如`traceId`, `eventType`, `anomalyScore`）、P1（条件采样，如`gpuPowerW`, `modelVersion`）、P2（离线批量，如`nodePUE`）。采样率基于`anomalyScore`动态调整，并通过ConfigMap热更新。
  3.  **CI/CD集成门禁**：流水线中集成多项门禁，包括：采样率压测（P99延迟增量<5%）、采样一致性校验（同一traceId采样标记一致）、字段完整性校验（缺失P0字段阻断发布）、以及能耗/热采样门禁，确保发布质量。
  **子任务拆解:**
    - *项目名称:** 广场计划 (Plaza Project)
    - *项目经理:** AgentsGroup2026 PM
    - *版本:** 1.0
    - *日期:** 2024-05-24
    - *技术风险与依赖:**
    - **风险:** 在K8s Sidecar中集成W3C Trace Context可能需要对现有Istio/Envoy配置进行修改，存在兼容性问题。
    - **依赖:** WP1.1 是 WP1.2 和 WP1.3 的前提。WP1.4 依赖 WP1.3 的埋点框架。
    - *技术风险与依赖:**
  
  ### 步骤 02: research (完整产出)
  
  # 研究分析 — researcher
  
  任务: [广场计划] 设计并实现一套智能体广场实时监控与自动化质量保障系统
  步骤: research
  Agent: build_researcher
  
  ---
  
  📋 任务: dbf24d0c-5cc
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
    [广场计划] 设计并实现一套智能体广场实时监控与自动化质量保障系统
    好的，作为项目经理，我已整合各位专家的意见，形成最终总结与执行计划。
    
    ---
    
    ### 最终总结与执行计划
    
    #### 1. 讨论概要
    
    经过多轮讨论，团队已就智能体广场的实时监控与自动化质量保障系统达成共识。核心方案是建立一套基于统一 `traceId` 的全链路可观测体系，并采用**自适应采样与优先级分层**策略来平衡数据全面性与系统性能。该方案明确了P0/P1/P2三级埋点字段，并集成了CI/CD门禁、降级场景强制采集及混沌工程验证等机制，确保系统在高压与故障场景下的稳定性和可追溯性。
    
    #### 2. 关键结论
    
    1.  **统一追踪与多维埋点**：采用W3C Trace Context标准，`traceId` 需贯穿API网关、WebSocket、K8s Sidecar全链路。埋点字段扩展至模型版本、异常评分、能耗、热传感器等元数据，实现多维链路完整性校验。
    2.  **自适应采样与优先级分层**：将埋点字段分为P0（实时必采，如`traceId`, `eventType`, `anomalyScore`）、P1（条件采样，如`gpuPowerW`, `modelVersion`）、P2（离线批量，如`nodePUE`）。采样率基于`anomalyScore`动态调整，并通过ConfigMap热更新。
    3.  **CI/CD集成门禁**：流水线中集成多项门禁，包括：采样率压测（P99延迟增量<5%）、采样一致性校验（同一traceId采样标记一致）、字段完整性校验（缺失P0字段阻断发布）、以及能耗/热采样门禁，确保发布质量。
    4.  **降级场景全量采集**：当触发`fallback_triggered`等降级事件时，强制全量采集该链路所有字段（包括P2），确保故障链路数据完整，便于根因分析。
    5.  **混沌工程验证**：在CI/CD中注入随机故障与流量突增，验证自适应采样策略在极端情况下的正确性与稳定性，确保P0字段100%采集且性能开销可控。
    
    #### 3. 执行计划
    
    **任务1：核心框架与埋点开发**
    *   **任务名称**: 实现全链路追踪与自适应采样框架
    *   **负责角色**: 全栈开发、Architect
    *   **预期产出**:
        *   完成W3C Trace Context在API网关、WebSocket、K8s Sidecar中的集成。
        *   开发自适应采样决策模块，支持基于`anomalyScore`的动态采样率调整。
        *   实现P0/P1/P2三级埋点字段的采集、本地缓冲与异步上报逻辑。
        *   交付可运行的代码库及技术设计文档。
    
    **任务2：CI/CD流水线集成与门禁开发**
    *   **任务名称**: 集成监控门禁与自动化测试
    *   **负责角色**: Deployer、Tester、Policy Engine
    *   **预期产出**:
        *   在CI/CD流水线中集成采样率压测门禁、字段完整性校验门禁、能耗/热采样门禁。
        *   开发采样一致性校验脚本，用于端到端测试。
        *   编写Playwright混沌工程测试用例，模拟异常与流量突增，验证采样策略。
        *   交付CI/CD流水线配置文件、测试脚本及门禁规则文档。
    
    **任务3：配置管理与文档化**
    *   **任务名称**: 建立采样策略配置中心与Schema Registry
    *   **负责角色**: Doc Writer、Deployer
    *   **预期产出**:
        *   搭建基于ConfigMap的采样策略动态配置中心，支持热更新。
        *   建立采样策略Schema Registry，强制每次更新携带`schemaVersion`。
        *   编写采样策略的版本管理、部署检查清单及故障报告模板。
        *   交付配置中心使用指南、Schema Registry规范及运维手册。
    
    #### 4. 建议指派团队
    
    建议将上述任务指派给 **Build团队** 执行，并由 **SRE团队** 提供架构与运维支持。项目经理将负责协调资源、跟踪进度，并确保最终交付物符合技术任务书要求。
    
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
    src/backend/agents/session_store.py
    src/backend/agents/skill_registry.py
    src/backend/agents/task_engine.py
    src/backend/agents/team_manager.py
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
    src/backend/channels/__init__.py
    src/backend/channels/bridge_chat.py
    src/backend/channels/marine_base.py
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
    src/docs/agent_handoffs/d87c964b-c06_architecture_20260503T045321.md
    src/docs/agent_handoffs/d87c964b-c06_pm_decompose_20260503T045236.md
    src/docs/agent_handoffs/d87c964b-c06_research_20260503T045251.md
    src/docs/agent_handoffs/d87c964b-c06_task_init_20260503T045211.md
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
    src/docs/workflow_artifacts/d87c964b-c06_architecture.md
    src/docs/workflow_artifacts/d87c964b-c06_pm_decompose.md
    src/docs/workflow_artifacts/d87c964b-c06_research.md
    src/docs/workflow_artifacts/dd0e3569-eb0_architecture.md
    src/docs/workflow_artifacts/dd0e3569-eb0_deploy.md
    src/docs/workflow_artifacts/dd0e3569-eb0_develop.md
    src/docs/workflow_artifacts/dd0e3569-eb0_pm_decompose.md
    src/docs/workflow_artifacts/dd0e3569-eb0_research.md
    src/docs/workflow_artifacts/dd0e3569-eb0_test.md
    ```
    
    ### 文件: `src/frontend/js/i18n.js`
    ```js
    /**
     * AgentsGroup2026 — i18n Internationalization Module v2
     * DOM text-walker approach: walks all text nodes and replaces Chinese↔English.
     * Usage: <script src="/js/i18n.js"></script>
     * Pages can extend via: PX_I18N.addTexts({ '中文': 'English', ... })
     */
    (function () {
      'use strict';
    
      const LANGS = ['zh', 'en'];
      const STORAGE_KEY = 'px-lang';
    
      /* ── Shared text map: zh → en ── */
      const TEXT_MAP = new Map([
        // ─── Index / Home page ───
        ['深海远洋双体船舶智能综合信息系统', 'Deep-Sea Ocean-Going Catamaran Intelligent Information System'],
        ['船长中控台', 'Captain Cockpit'],
        ['智能导航', 'Smart Navigation'],
        ['数据中心孪生', 'DC Digital Twin'],
        ['态势感知', 'Situation Awareness'],
        ['船岸通信', 'Ship-Shore Link'],
        ['气象海况', 'Weather & Sea'],
        ['海上作业', 'Offshore Operations'],
        ['进入系统', 'Enter System'],
    
        // ─── Page titles ───
        ['船长智能中控台', 'Captain Cockpit'],
        ['船长驾驶舱', 'Captain Cockpit'],
        ['导航与操纵', 'Navigation & Maneuvering'],
        ['动力定位', 'DP Control'],
        ['推进控制', 'Thruster Control'],
        ['全船监控', 'Full Ship Monitor'],
        ['设备健康', 'CMS Health'],
        ['控制台', 'HMI Console'],
        ['海工特种作业', 'Offshore Operations'],
        ['海工特種作业', 'Offshore Operations'],
        ['气象海洋', 'Weather & Ocean'],
        ['船员管理', 'Crew Management'],
        ['仿真训练', 'Simulation & Training'],
        ['能效合规', 'Energy Compliance'],
        ['船载数据中心', 'Marine Datacenter'],
        ['安全应急', 'Safety & Emergency'],
        ['船岸协同', 'Ship-Shore Sync'],
        ['数字孪生', 'Digital Twin'],
        ['智能体', 'AI Agents'],
        ['系统自我演进', 'System Self-Evolution'],
        ['系统演进', 'System Evolution'],
        ['知识库', 'Knowledge Base'],
        ['系统配置', 'System Configuration'],
        ['全球船舶监控平台', 'Global Ship Monitoring'],
        ['船舶避免碰撞增强现实系统', 'Ship Collision Avoidance AR System'],
    
        // ─── Nav sidebar ───
        ['船长总览', 'Captain'],
        ['导航', 'Navigation'],
        ['全船监控', 'Monitor'],
        ['海工作业', 'Offshore Ops'],
        ['船员管理', 'Crew Mgmt'],
    
        // ─── Common status / UI ───
        ['正常', 'Normal'],
        ['报警', 'Alarm'],
        ['警告', 'Warning'],
        ['离线', 'Offline'],
        ['在线', 'Online'],
        ['已连接', 'Connected'],
        ['待命', 'Standby'],
        ['就绪', 'Ready'],
        ['待确认', 'Pending'],
        ['已执行', 'Executed'],
        ['已确认', 'Confirmed'],
        ['已接收', 'Received'],
        ['已批准', 'Approved'],
        ['已提交', 'Submitted'],
        ['有效', 'Valid'],
        ['即将到期', 'Expiring Soon'],
        ['检修中', 'Under Maintenance'],
        ['加载中', 'Loading'],
        ['初始化中', 'Initializing'],
        ['搜索', 'Search'],
        ['保存', 'Save'],
        ['取消', 'Cancel'],
        ['确认', 'Confirm'],
        ['关闭', 'Close'],
        ['刷新', 'Refresh'],
        ['导出', 'Export'],
        ['状态', 'Status'],
        ['设置', 'Settings'],
        ['提交', 'Submit'],
        ['返回', 'Back'],
        ['折叠', 'Collapse'],
        ['全屏', 'Fullscreen'],
        ['隐藏', 'Hide'],
        ['开始', 'Start'],
        ['暂停', 'Pause'],
        ['重置', 'Reset'],
        ['清空', 'Clear'],
        ['添加', 'Add'],
        ['保存配置', 'Save Config'],
        ['刷新全部', 'Refresh All'],
    
        // ─── Captain cockpit ───
        ['快捷指令', 'Quick Commands'],
        ['拋錨', 'Drop Anchor'],
        ['抛锚', 'Drop Anchor'],
        ['响笛', 'Sound Horn'],
        ['紧急停车', 'Emergency Stop'],
        ['信号灯', 'Signal Light'],
        ['信号燈', 'Signal Light'],
        ['航行日志', 'Navigation Log'],
        ['航行日誌', 'Navigation Log'],
        ['系统设置', 'System Settings'],
        ['性能报告', 'Performance Report'],
        ['气象更新', 'Weather Update'],
        ['操作日志', 'Operation Log'],
        ['操作日誌', 'Operation Log'],
        ['操作人', 'Operator'],
        ['事件', 'Event'],
        ['结果', 'Result'],
        ['完成', 'Complete'],
        ['大副', 'Chief Officer'],
        ['轮机长', 'Chief Engineer'],
        ['船长', 'Captain'],
        ['调整航向', 'Adjust Heading'],
        ['主机转速', 'M/E RPM'],
        ['确认航线', 'Confirm Route'],
        ['您好', 'Hello'],
        ['当前航行状态如何', 'Current navigation status?'],
        ['当前航速', 'Current Speed'],
        ['航向', 'Heading'],
        ['主机功率', 'M/E Power'],
        ['子系统全部在线', 'All subsystems online'],
        ['抵达下一航路点', 'ETA next waypoint'],
        ['首页', 'Home'],
        ['中控台', 'Control Center'],
        ['广播', 'Broadcast'],
    
        // ─── Safety & Emergency ───
        ['消防区域矩阵', 'Fire Zone Matrix'],
        ['救生设备清单', 'Life Saving Equipment'],
        ['应急预案', 'Emergency Plans'],
        ['集合站点', 'Muster Stations'],
        ['正常区域', 'Normal Zones'],
        ['注意区域', 'Caution Zones'],
        ['报警区域', 'Alarm Zones'],
        ['救生设备', 'Life Saving Equip.'],
        ['预案就绪', 'Plans Ready'],
        ['设备', 'Equipment'],
        ['数量', 'Qty'],
        ['容量', 'Capacity'],
        ['检验日期', 'Inspection Date'],
        ['救生艇', 'Lifeboat'],
        ['救生筏', 'Life Raft'],
        ['救生圈', 'Life Buoy'],
        ['救生衣', 'Life Jacket'],
        ['发光', 'Illuminated'],
        ['烟雾', 'Smoke Signal'],
        ['火灾', 'Fire'],
        ['弃船', 'Abandon Ship'],
        ['人落水', 'Man Overboard'],
        ['碰撞', 'Collision'],
        ['搁浅', 'Grounding'],
        ['进水', 'Flooding'],
        ['污染', 'Pollution'],
        ['医疗', 'Medical'],
        ['机舱', 'Engine Room'],
        ['货舱', 'Cargo Hold'],
        ['住舱', 'Accommodation'],
        ['驾驶', 'Bridge'],
        ['甲板', 'Deck'],
        ['左舷甲板', 'Port Deck'],
        ['右舷甲板', 'Starboard Deck'],
        ['驾驶台', 'Bridge'],
        ['机舱控制室', 'Engine Control Room'],
        ['人已到', 'Arrived'],
    
        // ─── Ship-Shore ───
        ['通信链路', 'Communication Links'],
        ['数据同步', 'Data Sync'],
        ['岸基指令历史', 'Shore Command History'],
        ['远程数据流', 'Remote Data Flow'],
        ['上行', 'Uplink'],
        ['下行', 'Downlink'],
        ['延迟', 'Latency'],
        ['航行数据', 'Navigation Data'],
        ['实时', 'Real-time'],
        ['岸基', 'Shore'],
        ['云存储', 'Cloud Storage'],
        ['云存儲', 'Cloud Storage'],
        ['视频监控', 'Video Monitor'],
        ['視频监控', 'Video Monitor'],
        ['岸基指令', 'Shore Command'],
        ['船端', 'Ship-side'],
        ['时间', 'Time'],
        ['来源', 'Source'],
        ['指令', 'Command'],
        ['航速调整', 'Speed Adjustment'],
        ['进港航道确认', 'Port Channel Confirm'],
        ['台风预警转发', 'Typhoon Alert Forward'],
        ['优化建议下发', 'Optimization Advice'],
        ['沿海', 'Coastal'],
        ['双频', 'Dual Freq'],
    
        // ─── Simulation & Training ───
        ['综合评分', 'Overall Score'],
        ['綜合評分', 'Overall Score'],
        ['训练次数', 'Training Count'],
        ['本月', 'This Month'],
        ['累计时长', 'Total Duration'],
        ['船员排名', 'Crew Ranking'],
        ['场景配置', 'Scenario Config'],
        ['训练场景', 'Training Scenario'],
        ['故障注入', 'Fault Injection'],
        ['训练日志', 'Training Log'],
        ['训练日誌', 'Training Log'],
        ['能力评估雷达图', 'Competency Radar'],
        ['能力評估雷达图', 'Competency Radar'],
        ['成绩详情', 'Score Details'],
        ['成績详情', 'Score Details'],
        ['评分趋势', 'Score Trend'],
        ['評分趨勢', 'Score Trend'],
        ['避碰判断', 'Collision Avoidance'],
        ['导航精度', 'Navigation Accuracy'],
        ['通信规范', 'Communication Standards'],
        ['应急反应', 'Emergency Response'],
        ['操纵技能', 'Maneuvering Skills'],
        ['团队协作', 'Teamwork'],
        ['平均反应时间', 'Avg. Response Time'],
        ['天气', 'Weather'],
        ['海况', 'Sea State'],
        ['交通密度', 'Traffic Density'],
        ['能见度', 'Visibility'],
        ['模拟时间', 'Simulation Time'],
        ['主机故障', 'M/E Failure'],
        ['舵机故障', 'Rudder Lock'],
        ['雷达故障', 'Radar Fail'],
        ['通信中断', 'Comms Down'],
        ['电力丧失', 'Blackout'],
        ['优秀', 'Excellent'],
        ['合格', 'Pass'],
        ['失败', 'Fail'],
        ['晴朗', 'Clear'],
        ['多云', 'Cloudy'],
        ['暴雨', 'Storm'],
        ['台风', 'Typhoon'],
        ['轻浪', 'Slight'],
        ['大浪', 'Rough'],
        ['狂浪', 'Very Rough'],
        ['狂涛', 'High'],
        ['蒲氏风级', 'Beaufort Scale'],
        ['评价', 'Grade'],
        ['右舷让路避让', 'Starboard Give-way'],
        ['雷达标绘', 'Radar Plotting'],
        ['联络确认', 'Communication Confirm'],
        ['狭水道右舷通行', 'Narrow Channel Starboard'],
        ['应急舵切换', 'Emergency Steering Switch'],
        ['追越船避让', 'Overtaking Avoidance'],
        ['避碰', 'COLREG Avoidance'],
        ['分道通航', 'TSS'],
        ['港口进出', 'Port Entry/Exit'],
        ['应急操纵', 'Emergency Maneuvering'],
        ['锚泊作业', 'Anchoring Ops'],
    
        // ─── System Evolution ───
        ['达尔文棘轮', 'Darwin Ratchet'],
        ['自然选择', 'Natural Selection'],
        ['棘轮机制', 'Ratchet Mechanism'],
        ['演进时间线', 'Evolution Timeline'],
        ['初始化棘轮引擎中', 'Initializing Ratchet Engine'],
        ['演进流水线', 'Evolution Pipeline'],
        ['演进操作', 'Evolution Ops'],
        ['演进趋势', 'Evolution Trend'],
        ['域覆盖雷达', 'Domain Radar'],
        ['审查热力图', 'Audit Heatmap'],
        ['合规评级', 'Compliance Rating'],
        ['合规区域', 'Compliance Zones'],
        ['升级仪表板', 'Upgrade Dashboard'],
        ['双重检查单', 'Double Checklist'],
        ['公司级', 'Company Level'],
        ['船舶级', 'Vessel Level'],
        ['审计轨迹', 'Audit Trail'],
        ['审查规则库', 'Audit Rules'],
        ['演进条目', 'Evolution Entries'],
        ['审查历史', 'Audit History'],
        ['运行审查', 'Runtime Audit'],
        ['派发', 'Dispatch'],
        ['验证', 'Verify'],
        ['完整周期', 'Full Cycle'],
        ['已锁定的演化特性只增不减', 'Locked traits only grow, never regress'],
        ['永不回退', 'Never Rollback'],
        ['系统自我演进引擎就绪', 'Self-Evolution Engine Ready'],
        ['正在加载演进数据', 'Loading evolution data'],
        ['活跃', 'Active'],
    
        // ─── Thruster Control ───
        ['机舱综合状态', 'Engine Room Overview'],
        ['机舱綜合狀态', 'Engine Room Overview'],
        ['功率趋势', 'Power Trend'],
        ['功率趨勢', 'Power Trend'],
        ['振动频谱', 'Vibration Spectrum'],
        ['振动频譜', 'Vibration Spectrum'],
        ['缸温分布', 'Cylinder Temp Distribution'],
        ['缸溫分布', 'Cylinder Temp Distribution'],
        ['燃油流量', 'Fuel Flow'],
        ['能效指标', 'Efficiency Indicators'],
        ['额定', 'Rated'],
        ['负荷', 'Load'],
        ['燃油压力', 'Fuel Pressure'],
        ['排气温度', 'Exhaust Temp'],
        ['振动水平', 'Vibration Level'],
        ['舱底水位', 'Bilge Water Level'],
        ['推进效率', 'Propulsion Efficiency'],
        ['总运行时', 'Total Runtime'],
        ['下次保养', 'Next Maintenance'],
        ['高级控制', 'Advanced Control'],
        ['限值', 'Limit'],
        ['滑油温度', 'Lube Oil Temp'],
        ['冷却水温', 'Cooling Water Temp'],
        ['车钟', 'Telegraph'],
        ['车鐘', 'Telegraph'],
    
        // ─── Weather & Ocean ───
        ['风场', 'Wind Field'],
        ['風场', 'Wind Field'],
        ['海浪谱', 'Wave Spectrum'],
        ['海浪譜', 'Wave Spectrum'],
        ['海况综合', 'Sea Conditions'],
        ['海況綜合', 'Sea Conditions'],
        ['道格拉斯海况', 'Douglas Sea State'],
        ['蒲福风级', 'Beaufort Scale'],
        ['气温', 'Air Temp'],
        ['水温', 'Water Temp'],
        ['气压', 'Pressure'],
        ['湿度', 'Humidity'],
        ['洋流', 'Current'],
        ['涌浪', 'Swell'],
        ['表面流速', 'Surface Current Speed'],
        ['流向', 'Current Direction'],
        ['涌浪评估', 'Swell Assessment'],
        ['适航', 'Seaworthy'],
        ['潮汐', 'Tide'],
        ['当前潮高', 'Current Tide Height'],
        ['气象预警', 'Weather Warning'],
        ['大风蓝色预警', 'Blue Gale Warning'],
        ['天气窗口', 'Weather Window'],
        ['可作业', 'Operable'],
        ['航线天气评估', 'Route Weather Assessment'],
        ['良好', 'Good'],
        ['预报', 'Forecast'],
        ['方向', 'Direction'],
        ['风速', 'Wind Speed'],
        ['风向', 'Wind Dir'],
        ['浪高', 'Wave Height'],
    
        // ─── Offshore Operations ───
        ['作业状态', 'Operation Status'],
        ['作业狀态', 'Operation Status'],
        ['作业类型', 'Operation Type'],
        ['起重吊装', 'Crane Lifting'],
        ['许可状态', 'Permit Status'],
        ['許可狀态', 'Permit Status'],
        ['作业区域', 'Work Zone'],
        ['客户', 'Client'],
        ['起重机状态', 'Crane Status'],
        ['起重机狀态', 'Crane Status'],
        ['臂仰角', 'Boom Angle'],
        ['回转角', 'Slew Angle'],
        ['吃钩高度', 'Hook Height'],
        ['吃鉤高度', 'Hook Height'],
        ['环境条件', 'Environment Conditions'],
        ['环境條件', 'Environment Conditions'],
        ['作业限制', 'Op. Limits'],
        ['未超限', 'Within Limits'],
        ['安全检查单', 'Safety Checklist'],
        ['安全检查單', 'Safety Checklist'],
        ['系统状态确认', 'System Status Confirmed'],
        ['系统狀态确认', 'System Status Confirmed'],
        ['通信链路测试', 'Comms Link Test'],
        ['通信链路测試', 'Comms Link Test'],
        ['人员就位确认', 'Personnel Positioned'],
        ['气象窗口核实', 'Weather Window Verified'],
        ['应急预案就绪', 'Emergency Plan Ready'],
        ['应急预案就緒', 'Emergency Plan Ready'],
        ['吊具检验合格', 'Rigging Inspection Pass'],
        ['吊具检驗合格', 'Rigging Inspection Pass'],
        ['安全区域清场', 'Safety Zone Cleared'],
        ['平台东南侧', 'Platform SE Side'],
        ['平台東南側', 'Platform SE Side'],
    
        // ─── Crew Management ───
        ['总船员', 'Total Crew'],
        ['当值', 'On Watch'],
        ['休息', 'Off Watch'],
        ['疲劳预警', 'Fatigue Alert'],
        ['疲勞预警', 'Fatigue Alert'],
        ['证书到期', 'Certificate Expiring'],
        ['证書到期', 'Certificate Expiring'],
        ['船员花名册', 'Crew Roster'],
        ['船员花名冊', 'Crew Roster'],
        ['休息时间合规', 'Work/Rest Compliance'],
        ['休息时間合规', 'Work/Rest Compliance'],
        ['疲劳风险', 'Fatigue Risk'],
        ['疲勞風险', 'Fatigue Risk'],
        ['船舶评分', 'Vessel Score'],
        ['高风险人员', 'High Risk Personnel'],
        ['达标', 'Compliant'],
        ['证书监控', 'Certificate Monitor'],
        ['证書监控', 'Certificate Monitor'],
        ['应急演练记录', 'Emergency Drill Records'],
        ['值班安排', 'Watch Schedule'],
        ['当前班次', 'Current Watch'],
        ['甲班', 'Watch A'],
        ['下次换班', 'Next Changeover'],
        ['大管轮', 'Second Engineer'],
        ['水手长', 'Bosun'],
        ['机工', 'Motorman'],
    
        // ─── Energy Compliance ───
        ['当前', 'Current'],
        ['年度评级', 'Annual Rating'],
        ['年度轨迹', 'Annual Trajectory'],
        ['实时追踪', 'Real-time Tracking'],
        ['月度燃油消耗', 'Monthly Fuel Consumption'],
        ['排放监测', 'Emissions Monitoring'],
        ['二氧化碳', 'CO₂'],
        ['年度申报', 'Annual Declaration'],
        ['硫氧化物', 'SOx'],
        ['氮氧化物', 'NOx'],
        ['颗粒物', 'Particulate Matter'],
        ['合规文档', 'Compliance Documents'],
        ['文档名称', 'Document Name'],
        ['编号', 'Number'],
        ['有效期', 'Validity'],
        ['更新日期', 'Update Date'],
        ['审核机构', 'Audit Authority'],
        ['技术档案', 'Technical File'],
        ['改善方案', 'Improvement Plan'],
        ['国际能效证书', 'International Energy Cert.'],
        ['排放合规声明', 'Emission Compliance Decl.'],
        ['年报', 'Annual Report'],
        ['合规', 'Compliant'],
    
        // ─── Navigation ───
        ['电子海图', 'ECDIS'],
        ['航线路径点', 'Route Waypoints'],
        ['气象数据', 'Weather Data'],
        ['叠加层', 'Overlays'],
        ['目标', 'Targets'],
        ['雷达回波', 'Radar Echo'],
        ['安全等深线', 'Safety Contour'],
        ['追踪', 'Tracking'],
        ['航线进度', 'Route Progress'],
        ['航速', 'Speed'],
    
        // ─── Knowledge Base ───
        ['文档', 'Documents'],
        ['向量', 'Vectors'],
        ['领域', 'Domains'],
        ['領域', 'Domains'],
        ['全部', 'All'],
        ['法规', 'Regulations'],
        ['程序', 'Procedures'],
        ['技术', 'Technical'],
        ['培训', 'Training'],
        ['清单', 'Checklist'],
        ['清單', 'Checklist'],
        ['添加知识文档', 'Add Knowledge Document'],
        ['标题', 'Title'],
        ['标題', 'Title'],
        ['类别', 'Category'],
        ['类別', 'Category'],
        ['标签', 'Tags'],
        ['标籤', 'Tags'],
        ['逗号分隔', 'Comma separated'],
        ['内容', 'Content'],
        ['內容', 'Content'],
    
        // ─── Config page ───
        ['船舶信息', 'Ship Info'],
        ['船名', 'Ship Name'],
        ['船型', 'Ship Type'],
        ['穿浪双体船', 'Wave-Piercing Catamaran'],
        ['集装箱船', 'Container Ship'],
        ['散货船', 'Bulk Carrier'],
        ['油轮', 'Tanker'],
        ['总吨', 'Gross Tonnage'],
        ['功能开关', 'Feature Toggles'],
        ['决策辅助', 'Decision Aid'],
        ['決策輔助', 'Decision Aid'],
        ['启用', 'Enable'],
        ['自动避碰', 'Auto COLREG'],
        ['气象航线优化', 'Weather Route Optimization'],
        ['船员疲劳监控', 'Crew Fatigue Monitor'],
        ['船员疲勞监控', 'Crew Fatigue Monitor'],
        ['闭环审查', 'Closed-loop Audit'],
        ['构建', 'Build'],
        ['数据存储', 'Data Storage'],
        ['数据存儲', 'Data Storage'],
        ['访问控制', 'Access Control'],
        ['认证', 'Authentication'],
        ['端口控制', 'Port Control'],
        ['未授权', 'Unauthorized'],
        ['审查日志', 'Audit Log'],
        ['審查日誌', 'Audit Log'],
        ['记录所有系统配置变更', 'Log all config changes'],
        ['系统运行状态', 'System Runtime Status'],
        ['系统运行狀态', 'System Runtime Status'],
        ['运行时间', 'Uptime'],
        ['使用率', 'Usage'],
        ['内存使用', 'Memory Usage'],
        ['健康', 'Healt
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
    
    ### 文件: `src/backend/main.py`
    ```py
    # -*- coding: utf-8 -*-
    """
    AgentsGroup2026 — Standalone Agent Management + Evolution + Chat Server
    
    A self-contained FastAPI application extracted from AgentsGroup2026 that provides:
      - Agent team management (create/configure/manage agents)
      - System evolution engine (audit → dispatch → verify → close)
      - Bridge chat (LLM-powered conversational interface)
      - OpenClaw integration (connect external agents)
    
    Usage:
        cd src/backend && python main.py --port 8080
    """
    
    from __future__ import annotations
    
    import argparse
    import json
    import logging
    import os
    import sys
    from pathlib import Path
    from typing import Any, Dict, Optional
    
    import uvicorn
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel
    
    # ── Logging ──
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s  %(message)s")
    logger = logging.getLogger("agentsgroup")
    
    # ── App ──
    app = FastAPI(
        title="AgentsGroup2026",
        description="Standalone Agent Management, Evolution & Chat Platform",
        version="1.0.0",
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    
    # ══════════════════════════════════════════════════════════════════
    # Request / Response Models
    # ══════════════════════════════
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

🔗 API: api.deepseek.com | 模型: deepseek-chat
────────────────────────────────────────────────────────────

好的，作为系统架构师 (Architect)，我已仔细审阅了项目经理的最终总结、研究员的调研报告以及项目现有的代码库。

基于现有 `AgentsGroup2026` 系统的架构（特别是 `plaza_engine.py` 和 `plaza_routes.py` 中已有的讨论编排能力），我将设计一套**轻量级、可落地**的实时监控与自动化质量保障系统。

该方案将充分利用现有组件，避免过度设计，并聚焦于为“智能体广场”的讨论过程提供可观测性和质量保障。

---

### 技术方案: 智能体广场实时监控与自动化质量保障系统

#### 1. 总体架构

我们将采用 **“事件驱动 + 自适应采样 + 门禁验证”** 的架构。核心思路是在现有的 `PlazaEngine` 讨论流程中嵌入监控埋点，通过一个独立的 `MonitorService` 进行数据采集、分析和告警，并在 CI/CD 流水线中集成质量门禁。

```
+-------------------+       +-------------------+       +-------------------+
|   Plaza Frontend  |       |   Plaza Engine    |       |   Monitor Service |
|  (plaza.html)     |<----->|  (plaza_engine.py)|<----->| (NEW: monitor.py) |
+-------------------+       +-------------------+       +-------------------+
        |                           |                           |
        | SSE (实时推送)             | 事件埋点 (P0/P1/P2)        | 数据聚合 & 分析
        |                           |                           |
        v                           v                           v
+-------------------+       +-------------------+       +-------------------+
|   Dashboard       |       |   ConfigMap       |       |   Alert Manager  |
| (实时监控面板)     |       | (采样策略热更新)   |       | (告警 & 门禁)    |
+-------------------+       +-------------------+       +-------------------+
```

#### 2. 核心组件设计

##### 2.1. 监控数据模型 (`src/backend/agents/monitor.py` - 新增)

定义统一的数据结构，用于在广场讨论的各个环节进行埋点。

```python
# src/backend/agents/monitor.py
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid

class Priority(Enum):
    P0 = "P0"  # 实时必采
    P1 = "P1"  # 条件采样
    P2 = "P2"  # 离线批量

class EventType(Enum):
    DISCUSSION_START = "discussion_start"
    AGENT_SPEAK = "agent_speak"
    MODERATOR_SUMMARIZE = "moderator_summarize"
    DISCUSSION_END = "discussion_end"
    FALLBACK_TRIGGERED = "fallback_triggered"  # 降级事件
    ERROR = "error"

@dataclass
class MonitorEvent:
    """监控事件数据模型"""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.DISCUSSION_START
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # P0 字段 (必采)
    plaza_id: str = ""
    discussion_id: str = ""
    agent_id: str = ""
    niche_role: str = ""
    round_number: int = 0
    anomaly_score: float = 0.0  # 异常评分，用于动态采样
    
    # P1 字段 (条件采样)
    model_version: str = ""
    gpu_power_w: float = 0.0
    latency_ms: float = 0.0
    token_count: int = 0
    
    # P2 字段 (离线批量)
    node_pue: float = 0.0
    thermal_sensor_c: float = 0.0
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
```

##### 2.2. 监控服务 (`src/backend/agents/monitor_service.py` - 新增)

负责接收、采样、缓冲和上报监控事件。

```python
# src/backend/agents/monitor_service.py
from __future__ import annotations
import asyncio
import logging
from typing import Dict, List, Optional
from collections import deque
from .monitor import MonitorEvent, Priority, EventType

logger = logging.getLogger(__name__)

class AdaptiveSampler:
    """自适应采样器"""
    def __init__(self, config: Dict = None):
        self.config = config or {
            "base_sample_rate": 0.1,  # 基础采样率 10%
            "anomaly_threshold": 0.7,  # 异常阈值
            "anomaly_sample_rate": 1.0,  # 异常时全采
            "p1_sample_rate": 0.5,  # P1 字段采样率
        }
    
    def should_sample(self, event: MonitorEvent) -> bool:
        """判断是否应该采样"""
        # P0 字段必采
        if event.event_type in [EventType.ERROR, EventType.FALLBACK_TRIGGERED]:
            return True
        
        # 异常评分高时全采
        if event.anomaly_score >= self.config["anomaly_threshold"]:
            return True
        
        # 基于基础采样率
        import random
        return random.random() < self.config["base_sample_rate"]
    
    def should_collect_p1(self, event: MonitorEvent) -> bool:
        """判断是否采集 P1 字段"""
        import random
        return random.random() < self.config["p1_sample_rate"]

class MonitorService:
    """监控服务"""
    def __init__(self):
        self._sampler = AdaptiveSampler()
        self._buffer: deque = deque(maxlen=10000)  # 本地缓冲
        self._report_interval = 60  # 上报间隔（秒）
        self._running = False
        self._metrics: Dict = {
            "total_events": 0,
            "sampled_events": 0,
            "p0_events": 0,
            "p1_events": 0,
            "p2_events": 0,
        }
    
    async def start(self):
        """启动监控服务"""
        self._running = True
        asyncio.create_task(self._periodic_report())
        logger.info("MonitorService started")
    
    async def stop(self):
        """停止监控服务"""
        self._running = False
        await self._flush_buffer()
        logger.info("MonitorService stopped")
    
    async def record_event(self, event: MonitorEvent):
        """记录监控事件"""
        self._metrics["total_events"] += 1
        
        # 自适应采样
        if not self._sampler.should_sample(event):
            return
        
        self._metrics["sampled_events"] += 1
        
        # 判断是否采集 P1/P2 字段
        if event.event_type in [EventType.ERROR, EventType.FALLBACK_TRIGGERED]:
            # 降级场景全量采集
            collect_p1 = True
            collect_p2 = True
        else:
            collect_p1 = self._sampler.should_collect_p1(event)
            collect_p2 = False  # P2 默认离线
        
        # 清理非采集字段
        if not collect_p1:
            event.model_version = ""
            event.gpu_power_w = 0.0
            event.latency_ms = 0.0
            event.token_count = 0
        
        if not collect_p2:
            event.node_pue = 0.0
            event.thermal_sensor_c = 0.0
        
        # 更新指标
        if event.event_type in [EventType.ERROR, EventType.FALLBACK_TRIGGERED]:
            self._metrics["p0_events"] += 1
        if collect_p1:
            self._metrics["p1_events"] += 1
        if collect_p2:
            self._metrics["p2_events"] += 1
        
        # 加入缓冲
        self._buffer.append(event)
        
        # 如果缓冲满，立即上报
        if len(self._buffer) >= self._buffer.maxlen:
            await self._flush_buffer()
    
    async def _periodic_report(self):
        """定期上报"""
        while self._running:
            await asyncio.sleep(self._report_interval)
            await self._flush_buffer()
    
    async def _flush_buffer(self):
        """刷新缓冲（实际可写入日志或发送到外部存储）"""
        if not self._buffer:
            return
        
        events = list(self._buffer)
        self._buffer.clear()
        
        # 实际实现：写入日志、发送到 Kafka、或写入数据库
        logger.info(f"Flushing {len(events)} monitor events")
        for event in events:
            logger.debug(f"MonitorEvent: {event.to_dict()}")
    
    def get_metrics(self) -> Dict:
        """获取监控指标"""
        return {
            **self._metrics,
            "buffer_size": len(self._buffer),
            "sample_rate": round(
                self._metrics["sampled_events"] / max(self._metrics["total_events"], 1) * 100, 2
            ),
        }
    
    def update_config(self, config: Dict):
        """热更新采样配置"""
        self._sampler.config.update(config)
        logger.info(f"Sampler config updated: {config}")

# 全局单例
_monitor_service: Optional[MonitorService] = None

def get_monitor_service() -> MonitorService:
    global _monitor_service
    if _monitor_service is None:
        _monitor_service = MonitorService()
    return _monitor_service
```

##### 2.3. 修改 `PlazaEngine` 以嵌入监控

在 `plaza_engine.py` 的关键流程中插入监控埋点。

**需要修改的文件:** `src/backend/agents/plaza_engine.py`

**具体修改内容:**

1.  **导入 MonitorService:**
    ```python
    from .monitor_service import get_monitor_service, MonitorService
    from .monitor import MonitorEvent, EventType
    ```

2.  **在 `run_discussion` 方法中嵌入埋点:**
    ```python
    async def run_discussion(self, plaza_id: str, discussion_id: str) -> Optional[Discussion]:
        # ... 现有代码 ...
        
        monitor = get_monitor_service()
        
        # 讨论开始事件
        await monitor.record_event(MonitorEvent(
            event_type=EventType.DISCUSSION_START,
            plaza_id=plaza_id,
            discussion_id=discussion_id,
            agent_id=moderator.agent_id if moderator else "",
            niche_role="moderator",
            metadata={"topic": disc.topic}
        ))
        
        # ... 在 _agent_speak 调用后 ...
        async def _agent_speak_with_monitor(disc, participant, prompt, round_number, niche_role):
            # 记录发言前事件
            await monitor.record_event(MonitorEvent(
                event_type=EventType.AGENT_SPEAK,
                plaza_id=plaza_id,
                discussion_id=discussion_id,
                agent_id=participant.agent_id,
                niche_role=niche_role,
                round_number=round_number,
                anomaly_score=0.0,  # 可基于内容计算
                metadata={"prompt_length": len(prompt)}
            ))
            
            # 调用原有的 _agent_speak
            msg = await self._agent_speak(disc, participant, prompt, round_number, niche_role)
            
            # 记录发言后事件（包含延迟等指标）
            if msg:
                await monitor.record_event(MonitorEvent(
                    event_type=EventType.AGENT_SPEAK,
                    plaza_id=plaza_id,
                    discussion_id=discussion_id,
                    agent_id=participant.agent_id,
                    niche_role=niche_role,
                    round_number=round_number,
                    latency_ms=msg.latency_ms if hasattr(msg, 'latency_ms') else 0.0,
                    token_count=msg.token_count if hasattr(msg, 'token_count') else 0,
                ))
            
            return msg
        
        # 将原有的 _agent_speak 调用替换为 _agent_speak_with_monitor
        # ...
        
        # 讨论结束事件
        await monitor.record_event(MonitorEvent(
            event_type=EventType.DISCUSSION_END,
            plaza_id=plaza_id,
            discussion_id=discussion_id,
            agent_id=moderator.agent_id if moderator else "",
            niche_role="moderator",
            round_number=disc.max_rounds,
            metadata={"message_count": len(disc.messages)}
        ))
    ```

3.  **在 `_run_simulated` 方法中嵌入埋点:**
    ```python
    async def _run_simulated(self, disc, moderator, speakers):
        monitor = get_monitor_service()
        # ... 模拟逻辑 ...
        await monitor.record_event(MonitorEvent(
            event_type=EventType.FALLBACK_TRIGGERED,
            discussion_id=disc.id,
            agent_id="simulator",
            metadata={"reason": "LLM unavailable"}
        ))
    ```

##### 2.4. 新增监控 API 端点

**需要修改的文件:** `src/backend/agents/plaza_routes.py`

**具体修改内容:**

```python
# 在 plaza_routes.py 中添加
from .monitor_service import get_monitor_service

@router.get("/plaza/monitor/metrics")
async def get_monitor_metrics():
    """获取监控指标"""
    monitor = get_monitor_service()
    return monitor.get_metrics()

@router.post("/plaza/monitor/config")
async def update_monitor_config(config: Dict):
    """热更新采样配置"""
    monitor = get_monitor_service()
    monitor.update_config(config)
    return {"status": "ok", "config": config}

@router.get("/plaza/monitor/health")
async def monitor_health():
    """监控服务健康检查"""
    monitor = get_monitor_service()
    metrics = monitor.get_metrics()
    return {
        "status": "healthy",
        "sample_rate": metrics["sample_rate"],
        "buffer_size": metrics["buffer_size"],
        "total_events": metrics["total_events"],
    }
```

##### 2.5. 前端监控面板

**需要修改的文件:** `src/frontend/plaza.html` (或新建 `src/frontend/plaza-monitor.html`)

**具体修改内容:**

在现有广场页面中增加一个“监控”标签页或侧边栏，显示实时指标。

```html
<!-- 在 plaza.html 中添加 -->
<div id="monitor-panel" style="display:none;">
    <h3>实时监控</h3>
    <div class="monitor-metrics">
        <div class="metric-card">
            <span class="metric-label">总事件数</span>
            <span id="total-events" class="metric-value">0</span>
        </div>
        <div class="metric-card">
            <span class="metric-label">采样率</span>
            <span id="sample-rate" class="metric-value">0%</span>
        </div>
        <div class="metric-card">
            <span class="metric-label">P0 事件</span>
            <span id="p0-events" class="metric-value">0</span>
        </div>
        <div class="metric-card">
            <span class="metric-label">缓冲大小</span>
            <span id="buffer-size" class="metric-value">0</span>
        </div>
    </div>
</div>

<script>
// 定时刷新监控指标
async function refreshMonitorMetrics() {
    try {
        const response = await fetch('/api/v1/agent-config/plaza/monitor/metrics');
        const metrics = await response.json();
        document.getElementById('total-events').textContent = metrics.total_events;
        document.getElementById('sample-rate').textContent = metrics.sample_rate + '%';
        document.getElementById('p0-events').textContent = metrics.p0_events;
        document.getElementById('buffer-size').textContent = metrics.buffer_size;
    } catch (error) {
        console.error('Failed to fetch monitor metrics:', error);
    }
}

// 每 5 秒刷新一次
setInterval(refreshMonitorMetrics, 5000);
</script>
```

##### 2.6. CI/CD 门禁集成

**需要新增文件:** `src/backend/scripts/ci_gate.py`

```python
# src/backend/scripts/ci_gate.py
"""
CI/CD 门禁检查脚本
在流水线中执行，确保发布质量
"""
import sys
import json
import requests

def check_sampling_rate(base_url: str = "http://localhost:8080"):
    """检查采样率压测结果"""
    response = requests.get(f"{base_url}/api/v1/agent-config/plaza/monitor/metrics")
    metrics = response.json()
    
    # 检查采样率是否在合理范围
    sample_rate = metrics.get("sample_rate", 0)
    if sample_rate < 5 or sample_rate > 50:
        print(f"❌ 采样率异常: {sample_rate}% (期望 5%-50%)")
        return False
    print(f"✅ 采样率正常: {sample_rate}%")
    return True

def check_field_integrity():
    """检查字段完整性"""
    from agents.monitor import MonitorEvent, EventType
    
    # 模拟一个完整事件
    event = MonitorEvent(
        event_type=EventType.DISCUSSION_START,
        plaza_id="test",
        discussion_id="test",
        agent_id="test",
    )
    
    # 检查 P0 字段
    required_fields = ["trace_id", "event_type", "timestamp", "plaza_id", "discussion_id"]
    for field in required_fields:
        if not getattr(event, field, None):
            print(f"❌ 缺少 P0 字段: {field}")
            return False
    
    print("✅ 字段完整性检查通过")
    return True

def check_sampling_consistency():
    """检查采样一致性"""
    from agents.monitor_service import AdaptiveSampler
    
    sampler = AdaptiveSampler()
    from agents.monitor import MonitorEvent, EventType
    
    # 模拟同一 traceId 的多个事件
    trace_id = "test-trace-001"
    events = [
        MonitorEvent(trace_id=trace_id, event_type=EventType.DISCUSSION_START),
        MonitorEvent(trace_id=trace_id, event_type=EventType.AGENT_SPEAK),
        MonitorEvent(trace_id=trace_id, event_type=EventType.DISCUSSION_END),
    ]
    
    # 检查采样标记一致性
    sampled = [sampler.should_sample(e) for e in events]
    if any(sampled) and not all(sampled):
        print(f"❌ 采样不一致: trace_id={trace_id}")
        return False
    
    print("✅ 采样一致性检查通过")
    return True

if __name__ == "__main__":
    checks = [
        ("采样率检查", check_sampling_rate),
        ("字段完整性检查", check_field_integrity),
        ("采样一致性检查", check_sampling_consistency),
    ]
    
    all_passed = True
    for name, func in checks:
        print(f"\n🔍 执行门禁检查: {name}")
        try:
            if not func():
                all_passed = False
        except Exception as e:
            print(f"❌ 检查失败: {e}")
            all_passed = False
    
    if not all_passed:
        print("\n❌ 门禁检查未通过，阻断发布")
        sys.exit(1)
    else:
        print("\n✅ 所有门禁检查通过")
```

#### 3. 接口规范

| 方法 | 路径 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/v1/agent-config/plaza/monitor/metrics` | 获取监控指标 | - | `{total_events, sampled_events, sample_rate, ...}` |
| POST | `/api/v1/agent-config/plaza/monitor/config` | 更新采样配置 | `{base_sample_rate, anomaly_threshold, ...}` | `{status, config}` |
| GET | `/api/v1/agent-config/plaza/monitor/health` | 监控服务健康检查 | - | `{status, sample_rate, buffer_size}` |

#### 4. 实施指南

**步骤 1: 创建监控数据模型**
- 新建 `src/backend/agents/monitor.py`
- 定义 `MonitorEvent` 数据类

**步骤 2: 创建监控服务**
- 新建 `src/backend/agents/monitor_service.py`
- 实现 `AdaptiveSampler` 和 `MonitorService`

**步骤 3: 修改 PlazaEngine**
- 修改 `src/backend/agents/plaza_engine.py`
- 在 `run_discussion` 和 `_run_simulated` 中嵌入监控埋点

**步骤 4: 添加监控 API**
- 修改 `src/backend/agents/plaza_routes.py`
- 添加 `/plaza/monitor/*` 端点

**步骤 5: 更新前端**
- 修改 `src/frontend/plaza.html`
- 添加监控面板和定时刷新逻辑

**步骤 6: 创建 CI/CD 门禁脚本**
- 新建 `src/backend/scripts/ci_gate.py`
- 实现采样率、字段完整性、采样一致性检查

**步骤 7: 配置管理**
- 创建 ConfigMap 模板 `src/backend/configs/monitor-config.yaml`
- 定义采样策略的 Schema Registry

#### 5. 技术风险与缓解措施

| 风险 | 缓解措施 |
|------|----------|
| 埋点影响性能 | 使用异步队列缓冲，P0 字段轻量级采集 |
| 采样策略不当 | 支持 ConfigMap 热更新，可动态调整 |
| 降级场景漏采 | 强制全量采集，确保故障链路完整 |
| 门禁过于严格 | 门禁阈值可配置，支持灰度发布 |

────────────────────────────────────────────────────────────
✅ deepseek-chat 完成
