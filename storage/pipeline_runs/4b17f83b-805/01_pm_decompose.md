# PM分解 — project_manager

任务: 建设 CI 强制验收用例：原子写入崩溃恢复测试、全链路 trace context 透传一致性测试、降级路径触发与健康状态验证
步骤: pm_decompose
Agent: build_pm

---

📋 任务: 4b17f83b-805
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
  建设 CI 强制验收用例：原子写入崩溃恢复测试、全链路 trace context 透传一致性测试、降级路径触发与健康状态验证
  测试工程师
  
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
  src/docs/agent_handoffs/6f911ba3-822_executor_started_20260507T003435.md
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
  src/docs/agent_handoffs/8a5071c5-834_executor_started_20260507T003435.md
  src/docs/agent_handoffs/ba3b66b1-a77_architecture_20260505T154317.md
  src/docs/agent_handoffs/ba3b66b1-a77_deploy_FAILED_20260505T154903.md
  src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154353.md
  src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154600.md
  src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154807.md
  src/docs/agent_handoffs/ba3b66b1-a77_executor_started_20260505T153921.md
  src/docs/agent_handoffs/ba3b66b1-a77_pm_decompose_20260505T153951.md
  src/docs/agent_handoffs/ba3b66b1-a77_research_20260505T154041.md
  src/docs/agent_handoffs/ba3b66b1-a77_test_FAILED_20260505T154424.md
  src/docs/agent_handoffs/ba3b66b1-a77_test_FAILED_20260505T154631.md
  src/docs/agent_handoffs/ba3b66b1-a77_test_FAILED_20260505T154838.md
  src/docs/agent_handoffs/ba472f30-1a6_executor_started_20260507T003435.md
  src/docs/agent_handoffs/d553cde7-ee1_executor_started_20260506T101306.md
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
  ... (共 172 个 src/ 文件)
  
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
  
  ### 文件: `src/frontend/js/nav-sidebar.js`
  ```js
  /**
   * AgentsGroup2026 — Shared Navigation Sidebar
   * Injects OpenBridge-compliant sidebar navigation into any page.
   * Usage: <script src="/js/nav-sidebar.js" data-active="captain"></script>
   */
  (function () {
    'use strict';
  
    const NAV_ITEMS = [
      { id: 'captain',    icon: '⚓', label: 'nav.captain',    href: '/captain-cockpit-new.html' },
      { id: 'navigation', icon: '航', label: 'nav.navigation', href: '/navigation.html' },
      { id: 'dp',         icon: '定', label: 'nav.dp',         href: '/dp-control.html' },
      { id: 'thruster',   icon: '推', label: 'nav.thruster',   href: '/thruster-control.html' },
      { id: 'monitor',    icon: '监', label: 'nav.monitor',    href: '/worldmonitor-map.html' },
      { id: 'cms',        icon: '健', label: 'nav.cms',        href: '/cms-health.html' },
      { id: 'hmi',        icon: '台', label: 'nav.hmi',        href: '/hmi-console.html' },
      { id: 'offshore',   icon: '工', label: 'nav.offshore',   href: '/offshore-ops.html' },
      { id: 'weather',    icon: '海', label: 'nav.weather',    href: '/weather-ocean.html' },
      { id: 'crew',       icon: '员', label: 'nav.crew',       href: '/crew-management.html' },
      { sep: true },
      { id: 'sim',        icon: '练', label: 'nav.sim',        href: '/sim-training.html' },
      { id: 'energy',     icon: '能', label: 'nav.energy',     href: '/energy-compliance.html' },
      { id: 'datacenter', icon: '数', label: 'nav.datacenter', href: '/marine-datacenter.html' },
      { id: 'safety',     icon: '安', label: 'nav.safety',     href: '/safety-emergency.html' },
      { id: 'shore',      icon: '岸', label: 'nav.shore',      href: '/ship-shore.html' },
      { sep: true },
      { id: 'twin',       icon: '孪', label: 'nav.twin',       href: '/digital-twin.html' },
      { id: 'agents',     icon: '智', label: 'nav.agents',     href: '/agent-team-config.html' },
      { id: 'plaza',      icon: '⊙', label: 'nav.plaza',      href: '/plaza.html' },
      { id: 'tasks',      icon: '任', label: 'nav.tasks',      href: '/tasks.html' },
      { id: 'evolution',  icon: '演', label: 'nav.evolution',  href: '/system-evolution.html' },
      { id: 'kb',         icon: '知', label: 'nav.kb',         href: '/knowledge-base.html' },
      { id: 'llm-config', icon: '配', label: 'nav.llm-config', href: '/poseidon-config.html' },
    ];
  
    const THEMES = ['day', 'dusk', 'night', 'bright'];
  
    function getActiveId() {
      const script = document.querySelector('script[data-active]');
      return script ? script.getAttribute('data-active') : '';
    }
  
    function getCurrentTheme() {
      return document.documentElement.getAttribute('data-obc-theme') || 'dusk';
    }
  
    function setTheme(theme) {
      document.documentElement.setAttribute('data-obc-theme', theme);
      localStorage.setItem('ob-theme', theme);
    }
  
    function initTheme() {
      const saved = localStorage.getItem('ob-theme');
      if (saved && THEMES.includes(saved)) {
        setTheme(saved);
      } else {
        setTheme('dusk');
      }
    }
  
    function _t(key) {
      return (window.PX_I18N && window.PX_I18N.t) ? window.PX_I18N.t(key) : key;
    }
  
    function buildSidebar() {
      const activeId = getActiveId();
      const sidebar = document.createElement('nav');
      sidebar.className = 'ob-sidebar';
      sidebar.setAttribute('role', 'navigation');
      sidebar.setAttribute('aria-label', 'Main Navigation');
  
      // Brand
      const brand = document.createElement('div');
      brand.className = 'ob-nav-brand';
      brand.textContent = 'PX';
      brand.title = 'AgentsGroup2026';
      sidebar.appendChild(brand);
  
      // Nav items container
      const items = document.createElement('div');
      items.className = 'ob-nav-items';
  
      NAV_ITEMS.forEach(item => {
        if (item.sep) {
          const sep = document.createElement('div');
          sep.className = 'ob-nav-sep';
          items.appendChild(sep);
          return;
        }
  
        const a = document.createElement('a');
        a.className = 'ob-nav-item' + (item.id === activeId ? ' active' : '');
        a.href = item.href;
        a.setAttribute('data-nav-i18n', item.label);
        a.setAttribute('data-tooltip', _t(item.label));
  
        const icon = document.createElement('span');
        icon.className = 'ob-nav-icon';
        icon.textContent = item.icon;
        icon.setAttribute('aria-hidden', 'true');
  
        const label = document.createElement('span');
        label.className = 'ob-nav-label';
        label.textContent = _t(item.label);
  
        a.appendChild(icon);
        a.appendChild(label);
        items.appendChild(a);
      });
  
      sidebar.appendChild(items);
  
      // Footer with language toggle + theme switcher
      const footer = document.createElement('div');
      footer.className = 'ob-nav-footer';
  
      // Language toggle button
      const langWrap = document.createElement('div');
      langWrap.style.cssText = 'padding: 4px 6px;';
      const langBtn = document.createElement('button');
      langBtn.className = 'ob-theme-btn';
      langBtn.id = 'px-lang-btn';
      langBtn.style.cssText = 'width:100%;font-size:11px;letter-spacing:1px;';
      const curLang = (window.PX_I18N && window.PX_I18N.getLang) ? window.PX_I18N.getLang() : 'zh';
      langBtn.textContent = curLang === 'zh' ? '中/EN' : 'EN/中';
      langBtn.title = 'Switch Language';
      langBtn.addEventListener('click', () => {
        if (window.PX_I18N && window.PX_I18N.toggleLang) {
          window.PX_I18N.toggleLang();
          // Update sidebar labels
          sidebar.querySelectorAll('[data-nav-i18n]').forEach(a => {
            const key = a.getAttribute('data-nav-i18n');
            const translated = _t(key);
            a.setAttribute('data-tooltip', translated);
            const lbl = a.querySelector('.ob-nav-label');
            if (lbl) lbl.textContent = translated;
          });
        }
      });
      langWrap.appendChild(langBtn);
      footer.appendChild(langWrap);
  
      // Theme switcher
      const themeWrap = document.createElement('div');
      themeWrap.style.cssText = 'padding: 4px 6px;';
  
      const themeSwitch = document.createElement('div');
      themeSwitch.className = 'ob-theme-switch';
      themeSwitch.style.cssText = 'flex-direction: column;';
  
      const currentTheme = getCurrentTheme();
      const themeLabels = { day: '日', dusk: '暮', night: '夜', bright: '明' };
  
      THEMES.forEach(t => {
        const btn = document.createElement('button');
        btn.className = 'ob-theme-btn' + (t === currentTheme ? ' active' : '');
        btn.textContent = themeLabels[t];
        btn.title = t.charAt(0).toUpperCase() + t.slice(1);
        btn.addEventListener('click', () => {
          setTheme(t);
          themeSwitch.querySelectorAll('.ob-theme-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
        });
        themeSwitch.appendChild(btn);
      });
  
      themeWrap.appendChild(themeSwitch);
      footer.appendChild(themeWrap);
      sidebar.appendChild(footer);
  
      return sidebar;
    }
  
    function buildTopbar(title, subtitle) {
      const topbar = document.createElement('header');
      topbar.className = 'ob-topbar';
  
      const titleWrap = document.createElement('div');
      titleWrap.style.cssText = 'display:flex;align-items:baseline;gap:4px;min-width:0;';
  
      const h1 = document.createElement('span');
      h1.className = 'ob-topbar-title';
      h1.textContent = title || document.title;
      titleWrap.appendChild(h1);
  
      if (subtitle) {
        const sub = document.createElement('span');
        sub.className = 'ob-topbar-subtitle';
        sub.textContent = subtitle;
        titleWrap.appendChild(sub);
      }
  
      topbar.appendChild(titleWrap);
  
      // Right: clock + connection status
      const actions = document.createElement('div');
      actions.className = 'ob-topbar-actions';
  
      const connDot = document.createElement('span');
      connDot.className = 'ob-dot';
      connDot.id = 'ob-conn-dot';
      connDot.title = 'Backend connection';
      actions.appendChild(connDot);
  
      const clock = document.createElement('span');
      clock.className = 'ob-clock';
      clock.id = 'ob-clock';
      actions.appendChild(clock);
  
      topbar.appendChild(actions);
  
      return topbar;
    }
  
    function updateClock() {
      const el = document.getElementById('ob-clock');
      if (!el) return;
      const now = new Date();
      const utc = now.toISOString().slice(11, 19);
      el.textContent = utc + ' UTC';
    }
  
    function checkBackend() {
      const dot = document.getElementById('ob-conn-dot');
      if (!dot) return;
      fetch('/health', { signal: AbortSignal.timeout(3000) })
        .then(r => {
          dot.className = r.ok ? 'ob-dot ob-dot-ok' : 'ob-dot ob-dot-warning';
          dot.title = r.ok ? 'Backend connected' : 'Backend error';
        })
        .catch(() => {
          dot.className = 'ob-dot ob-dot-alarm';
          dot.title = 'Backend offline';
        });
    }
  
    /**
     * Initialize navigation shell.
     * Wraps existing <body> content in the OpenBridge layout.
     */
    function init() {
      initTheme();
  
      const pageTitle = document.querySelector('meta[name="ob-title"]');
      const pageSubtitle = document.querySelector('meta[name="ob-subtitle"]');
      const title = pageTitle ? pageTitle.content : document.title;
      const subtitle = pageSubtitle ? pageSubtitle.content : '';
  
      // Check if already wrapped
      if (document.querySelector('.ob-app')) return;
  
      // Create shell
      const app = document.createElement('div');
      app.className = 'ob-app';
  
      const sidebar = buildSidebar();
      const main = document.createElement('div');
      main.className = 'ob-main';
  
      const topbar = buildTopbar(title, subtitle);
  
      const content = document.createElement('div');
      content.className = 'ob-content';
  
      // Move existing body children into content
      while (document.body.firstChild) {
        // Skip our own script tag
        if (document.body.firstChild === document.currentScript) {
          document.body.removeChild(document.body.firstChild);
          continue;
        }
        content.appendChild(document.body.firstChild);
      }
  
      main.appendChild(topbar);
      main.appendChild(content);
      app.appendChild(sidebar);
      app.appendChild(main);
      document.body.appendChild(app);
  
      // Start clock + health check
      updateClock();
      setInterval(updateClock, 1000);
      checkBackend();
      setInterval(checkBackend, 10000);
    }
  
    // Run when DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  })();
  
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
  
              # 注册广场监控 Channel
              try:
                  from monitoring.plaza_monitor import PlazaMonitorChannel
                  from channels.marine_base import get_default_registry
  
                  monitor_ch = PlazaMonitorChannel()
                  registry = get_default_registry()
                  registry.register(monitor_ch)
                  monitor_ch.initialize()
  
                  # 注入到 plaza_routes
                  from agents.plaza_routes import set_plaza_monitor
                  set_plaza_monitor(monitor_ch)
  
                  logger.info("✅ PlazaMonitorChannel registered & injected")
              except Exception as me:
                  logger.warning(f"⚠️ PlazaMonitorChannel registration failed: {me}")
  
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
              
  ```
  
  ### 文件: `src/backend/monitoring/__init__.py`
  ```py
  # -*- coding: utf-8 -*-
  """
  智能体广场实时监控与自动化质量保障系统 — 监控模块
  
  基于统一 traceId 的全链路可观测体系，支持：
  - W3C Trace Context 标准
  - P0/P1/P2 三级埋点字段分层采集
  - 自适应采样（基于 anomalyScore 动态调整）
  - 本地缓冲与异步上报
  - 降级场景全量采集
  - ConfigMap 热更新采样策略
  """
  
  from __future__ import annotations
  
  from .models import (
      TraceSpan,
      TraceContext,
      SpanPriority,
      SamplingDecision,
      SamplingConfig,
      MonitoringMetrics,
      PlazaEventType,
      TelemetryRecord,
  )
  from .sampler import AdaptiveSampler
  from .collector import TraceCollector
  from .plaza_monitor import PlazaMonitorChannel
  
  __all__ = [
      "TraceSpan",
      "TraceContext",
      "SpanPriority",
      "SamplingDecision",
      "SamplingConfig",
      "MonitoringMetrics",
      "PlazaEventType",
      "TelemetryRecord",
      "AdaptiveSampler",
      "TraceCollector",
      "PlazaMonitorChannel",
  ]
  
  ```
  
  ### 文件: `src/backend/monitoring/collector.py`
  ```py
  # -*- coding: utf-8 -*-
  """
  Trace 采集器 — 本地缓冲 + 异步上报.
  
  负责:
  1. 接收 TraceSpan 并做采样决策
  2. 本地缓冲已采样数据
  3. 异步批量上报
  4. 降级场景强制全量采集
  """
  
  from __future__ import annotations
  
  import asyncio
  import json
  import logging
  import os
  from datetime import datetime, timezone
  from typing import Any, Callable, Dict, List, Optional
  
  from .models import (
      MonitoringMetrics,
      SamplingConfig,
      SpanPriority,
      TelemetryRecord,
      TraceSpan,
  )
  from .sampler import AdaptiveSampler
  
  logger = logging.getLogger(__name__)
  
  
  class TraceCollector:
      """Trace 采集器 — 本地缓冲 + 异步上报.
  
      使用 asyncio 实现非阻塞采集，支持自定义上报回调函数。
      """
  
      def __init__(
          self,
          sampler: Optional[AdaptiveSampler] = None,
          config: Optional[SamplingConfig] = None,
          upload_callback: Optional[Callable[[List[Dict[str, Any]]], None]] = None,
      ):
          self._sampler = sampler or AdaptiveSampler(config or SamplingConfig())
          self._upload_callback = upload_callback
          self._buffer: List[Dict[str, Any]] = []
          self._p2_buffer: List[Dict[str, Any]] = []
          self._metrics = MonitoringMetrics()
          self._running = False
          self._flush_task: Optional[asyncio.Task] = None
          self._lock = asyncio.Lock()
  
          # 用于 CI/CD 校验的遥测记录
          self._telemetry_records: List[TelemetryRecord] = []
  
      @property
      def sampler(self) -> AdaptiveSampler:
          return self._sampler
  
      @property
      def metrics(self) -> MonitoringMetrics:
          return self._metrics
  
      @property
      def config(self) -> SamplingConfig:
          return self._sampler.config
  
      def update_config(self, config_dict: dict):
          """热更新采样策略."""
          self._sampler.update_from_dict(config_dict)
          logger.info(f"📋 采集器配置已更新: {config_dict}")
  
      async def start(self):
          """启动异步刷新任务."""
          if self._running:
              return
          self._running = True
          self._flush_task = asyncio.create_task(self._flush_loop())
          logger.info("📡 TraceCollector 已启动")
  
      async def stop(self):
          """停止采集器并刷新剩余数据."""
          self._running = False
          if self._flush_task:
              self._flush_task.cancel()
              try:
                  await self._flush_task
              except asyncio.CancelledError:
                  pass
          await self._flush_now()
          logger.info("📡 TraceCollector 已停止")
  
      async def record(self, span: TraceSpan) -> bool:
          """记录一个 TraceSpan.
  
          流程:
          1. 采样决策
          2. 如果采样 → 加入缓冲
          3. 更新指标
  
          Returns:
              True 如果被采样并加入缓冲
          """
          decision = self._sampler.decide(span)
          self._metrics.total_spans += 1
  
          if not decision.should_sample:
              return False
  
          # 更新指标
          self._metrics.sampled_spans += 1
          if decision.priority == SpanPriority.P0:
              self._metrics.p0_spans += 1
          elif decision.priority == SpanPriority.P1:
              self._metrics.p1_spans += 1
          else:
              self._metrics.p2_spans += 1
  
          if span.status in ("error", "critical"):
              self._metrics.error_spans += 1
  
          if span.event_type == "fallback_triggered":
              self._metrics.fallback_count += 1
  
          # 更新平均异常评分和耗时
          n = self._metrics.total_spans
          self._metrics.avg_anomaly_score += (
              span.anomaly_score - self._metrics.avg_anomaly_score
          ) / n
          self._metrics.avg_duration_ms += (
              span.duration_ms - self._metrics.avg_duration_ms
          ) / n
  
          # 降级场景或高异常 → 全量采集
          include_all = (
              self._sampler.config.degradation_mode
              or span.anomaly_score >= self._sampler.config.anomaly_threshold_high
              or span.event_type == "fallback_triggered"
          )
  
          span_dict = span.to_dict(include_all=include_all)
  
          # 记录遥测记录（用于 CI/CD 校验）
          p0_fields = list(span.get_p0_fields().keys())
          p1_fields = list(span.get_p1_fields().keys())
          p2_fields = list(span.get_p2_fields().keys())
          all_expected = p0_fields + (p1_fields if include_all else []) + (p2_fields if include_all else [])
          fields_present = [k for k in all_expected if k in span_dict]
          fields_missing = [k for k in all_expected if k not in span_dict]
  
          record = TelemetryRecord(
              trace_id=span.trace_id,
              span_id=span.span_id,
              event_type=span.event_type,
              timestamp=span.timestamp,
              sampled=True,
              priority=decision.priority.value,
              fields_present=fields_present,
              fields_missing=fields_missing,
              anomaly_score=span.anomaly_score,
              status=span.status,
              duration_ms=span.duration_ms,
          )
          self._telemetry_records.append(record)
  
          # 加入缓冲
          async with self._lock:
              if decision.priority == SpanPriority.P2:
                  self._p2_buffer.append(span_dict)
              else:
                  self._buffer.append(span_dict)
  
              # 缓冲上限保护
              max_size = self._sampler.config.max_buffer_size
              if len(self._buffer) > max_size:
                  overflow = self._buffer[:-max_size]
                  self._buffer = self._buffer[-max_size:]
                  logger.warning(f"⚠️ 缓冲溢出，丢弃 {len(overflow)} 条记录")
  
          return True
  
      async def _flush_loop(self):
          """定时刷新循环."""
          interval = self._sampler.config.flush_interval_s
          while self._running:
              try:
                  await asyncio.sleep(interval)
                  await self._flush_now()
              except asyncio.CancelledError:
                  break
              except Exception as e:
                  logger.error(f"❌ 刷新循环异常: {e}")
  
      async def _flush_now(self):
          """立即刷新缓冲数据."""
          async with self._lock:
              if not self._buffer and not self._p2_buffer:
                  return
              batch = list(self._buffer)
              p2_batch = list(self._p2_buffer)
              self._buffer.clear()
              self._p2_buffer.clear()
  
          all_data = batch + p2_batch
          if not all_data:
              return
  
          self._metrics.last_flush_timestamp = datetime.now(timezone.utc).isoformat()
          self._metrics.buffer_usage_pct = 0.0
  
          if self._upload_callback:
              try:
                  if asyncio.iscoroutinefunction(self._upload_callback):
                      await self._upload_callback(all_data)
                  else:
                      self._upload_callback(all_data)
                  logger.debug(f"📤 上报 {len(all_data)} 条追踪数据")
              except Exception as e:
                  logger.error(f"❌ 上报失败: {e}")
                  # 上报失败重新入队
                  async with self._lock:
                      self._buffer.extend(batch)
                      self._p2_buffer.extend(p2_batch)
          else:
              logger.debug(f"📤 (无回调) 缓冲 {len(all_data)} 条追踪数据")
  
      async def flush(self) -> int:
          """手动触发刷新，返回刷新的记录数."""
          await self._flush_now()
          return len(self._buffer) + len(self._p2_buffer)
  
      def get_telemetry_records(
          self, limit: int = 100, status_filter: Optional[str] = None
      ) -> List[Dict[str, Any]]:
          """获取遥测记录（用于 CI/CD 门禁校验）."""
          records = self._telemetry_records[-limit:]
          if status_filter:
              records = [r for r in records if r.status == status_filter]
          return [r.to_dict() for r in records]
  
      def get_metrics(self) -> Dict[str, Any]:
          """获取当前指标."""
          self._metrics.buffer_usage_pct = round(
              (len(self._buffer) + len(self._p2_buffer))
              / max(self._sampler.config.max_buffer_size, 1) * 100,
              2,
          )
          return self._metrics.to_dict()
  
      def get_sampler_stats(self) -> dict:
          """获取采样器统计."""
          return self._sampler.get_stats()
  
  ```
  
  ### 文件: `src/backend/monitoring/models.py`
  ```py
  # -*- coding: utf-8 -*-
  """
  监控数据模型 — 全链路追踪与埋点字段定义
  
  遵循 W3C Trace Context 标准，定义 P0/P1/P2 三级埋点字段。
  """
  
  from __future__ import annotations
  
  import enum
  import uuid
  from dataclasses import dataclass, field
  from datetime import datetime, timezone
  from typing import Any, Dict, List, Optional
  
  
  class SpanPriority(str, enum.Enum):
      """埋点优先级 — P0 实时必采 / P1 条件采样 / P2 离线批量."""
      P0 = "P0"  # 实时必采
      P1 = "P1"  # 条件采样
      P2 = "P2"  # 离线批量
  
  
  class PlazaEventType(str, enum.Enum):
      """广场事件类型."""
      DISCUSSION_CREATED = "discussion_created"
      DISCUSSION_STARTED = "discussion_started"
      DISCUSSION_ENDED = "discussion_ended"
      PARTICIPANT_JOINED = "participant_joined"
      PARTICIPANT_LEFT = "participant_left"
      MESSAGE_SENT = "message_sent"
      MODERATOR_SUMMARY = "moderator_summary"
      PLAN_ASSIGNED = "plan_assigned"
      SSE_STREAM_STARTED = "sse_stream_started"
      SSE_STREAM_ENDED = "sse_stream_ended"
      FALLBACK_TRIGGERED = "fallback_triggered"
      ERROR_OCCURRED = "error_occurred"
      LLM_CALL_STARTED = "llm_call_started"
      LLM_CALL_COMPLETED = "llm_call_completed"
      LLM_CALL_FAILED = "llm_call_failed"
      SAMPLING_ADJUSTED = "sampling_adjusted"
      DEGRADATION_ACTIVATED = "degradation_activated"
  
  
  @dataclass
  class TraceContext:
      """W3C Trace Context — 全链路追踪上下文."""
      trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:32])
      span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
      parent_span_id: Optional[str] = None
      sampled: bool = True
      trace_flags: str = "01"  # W3C trace flags
  
      def to_w3c_traceparent(self) -> str:
          """生成 W3C traceparent 头: version-trace_id-span_id-flags."""
          return f"00-{self.trace_id}-{self.span_id}-{self.trace_flags}"
  
      @classmethod
      def from_w3c_traceparent(cls, traceparent: str) -> Optional["TraceContext"]:
          """从 W3C traceparent 解析."""
          parts = traceparent.split("-")
          if len(parts) != 4:
              return None
          return cls(
              trace_id=parts[1],
              span_id=parts[2],
              trace_flags=parts[3],
          )
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "trace_id": self.trace_id,
              "span_id": self.span_id,
              "parent_span_id": self.parent_span_id,
              "sampled": self.sampled,
              "trace_flags": self.trace_flags,
          }
  
  
  @dataclass
  class TraceSpan:
      """单个追踪 Span — 代表一次操作/事件的完整追踪信息.
  
      P0 字段 (实时必采):
          trace_id, span_id, parent_span_id, event_type, timestamp,
          anomaly_score, status, duration_ms, source
  
      P1 字段 (条件采样):
          model_version, gpu_power_w, cpu_usage_pct, memory_mb,
          token_count, latency_p99_ms, agent_id, session_id
  
      P2 字段 (离线批量):
          node_pue, thermal_sensor_c, energy_kwh, carbon_g,
          network_rtt_ms, disk_iops, container_restart_count
      """
      # ── 核心字段 (P0) ─
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

好的，作为 AgentsGroup2026 系统的项目经理 (PM)，我将对“建设 CI 强制验收用例”这一任务进行详细分解和规划。

---

## 任务分解文档: CI 强制验收用例建设

**项目名称:** AgentsGroup2026
**任务负责人:** 测试工程师
**项目经理:** PM (AgentsGroup2026)
**创建日期:** 2024-05-24

### 1. 任务概述

本任务旨在为 AgentsGroup2026 系统建立三个关键的 CI 强制验收用例，以确保系统核心功能的稳定性和可靠性。这些用例将作为代码合入主分支前的“门禁”，防止引入回归性缺陷。

**核心验收用例:**
1.  **原子写入崩溃恢复测试:** 验证系统在数据写入过程中发生崩溃后，能够恢复到一致状态，不丢失数据。
2.  **全链路 Trace Context 透传一致性测试:** 验证 W3C Trace Context 在系统各服务/组件间传递时，`trace_id` 和 `span_id` 保持一致。
3.  **降级路径触发与健康状态验证:** 验证系统在依��服务故障时，能正确触发降级逻辑，并保持整体健康状态。

### 2. 需求分析与技术风险识别

#### 2.1 原子写入崩溃恢复测试

-   **需求分析:** 系统在写入关键数据（如任务状态、团队配置、演进记录）时，必须保证操作的原子性。如果写入过程中进程崩溃，重启后数据应处于一个已知的、一致的状态（要么全部写入成功，要么全部未写入），不能出现“部分写入”的脏数据。
-   **技术风险:**
    -   **存储层依赖:** 需要明确系统当前使用的存储机制（如文件、SQLite、内存���。从项目文件看，`task_store.py`, `team_store.py`, `session_store.py` 等可能涉及数据持久化。如果使用文件存储，实现原子写入（如写临时文件再 `rename`）相对简单；如果使用内存，则需考虑持久化策略。
    -   **并发写入:** 测试需要模拟并发写入场景下的崩溃，确保锁机制或事务机制有效。
    -   **状态恢复:** 崩溃恢复后，系统需要能正确重建内部状态（如从持久化存储重新加载），测试需要验证这一点。

#### 2.2 全链路 Trace Context 透传一致性测试

-   **需求分析:** 系统已定义 `TraceContext` 和 `TraceSpan` 模型（见 `monitoring/models.py`），并遵循 W3C Trace Context 标准。CI 用例需要验证，当一个请求（如一次 LLM 调用、一个广场讨论）穿越多个组件（如 `main.py` -> `agent_team_api.py` -> `plaza_engine.py` -> `chat_harness.py`）时，`trace_id` 和 `parent_span_id` 能被正确创建和传递。
-   **技术风险:**
    -   **透传机制缺失:** 代码中可能尚未在所有关键路径上实现 `traceparent` 头的传递。需要检查 `main.py` 中的路由处理、`agent_team_api.py` 中的 API 调用、`plaza_engine.py` 中的事件处理等是否都集成了 `TraceContext`。
    -   **异步任务:** 对于 `asyncio.create_task` 启动的后台任务，需要确保 `TraceContext` 能被正确传播到新任务中。
    -   **外部调用:** 如果系统调用外部 LLM API，需要验证 `traceparent` 头是否被附加到 HTTP 请求中。

#### 2.3 降级路径触发与健康状态验证

-   **需求分析:** 系统应具备优雅降级能力。例如，当 LLM 服务不可用时，`bridge_chat` 应能回退到模板回复；当 `plaza_engine` 的某个组件故障时，广场功能应能降级运行。CI 用例需要模拟这些故障，并验证降级路径被正确触发，同时系统的 `/api/v1/health` 端点应返回正确的健康状态（如 `services` 字段中对应服务状态为 `false`）。
-   **技术风险:**
    -   **故障注入:** 需要一种机制来模拟依赖服务故障（如 Mock LLM 服务、停止某个内部组件）。这可能需要修改测试环境或使用依赖注入。
    -   **健康检查定义:** 需要明确“健康”的定义。`HealthResponse` 模型中的 `services` 字典是一个好的起点。测试需要验证，当某个服务降级时，其对应的 `services` 状态是否为 `false`，而整体 `status` 是否仍为 `ok`（或 `degraded`）。
    -   **降级逻辑覆盖:** 需要识别所有可能的降级路径。从 `main.py` 的 `startup` 函数看，`BridgeChatChannel` 和 `SystemEvolutionChannel` 的初始化失败是被 `try...except` 捕获的，这是一种降级。需要确保其他关键路径也有类似处理。

### 3. 任务分解与子步骤

| 子任务 ID | 子任务名称 | 详细描述 | 依赖 | 预期产出 |
| :--- | :--- | :--- | :--- | :--- |
| **T1** | **原子写入崩溃恢复测试** | | | |
| T1.1 | 识别关键写入路径 | 分析 `task_store.py`, `team_store.py`, `session_store.py` 等，确定哪些写入操作需要原子性保证。 | 无 | 一份关键写入路径列表。 |
| T1.2 | 实现崩溃模拟辅助函数 | 编写一个测试工具函数，能在指定代码行（如 `write()` 调用后）模拟进程崩溃（如 `os._exit(1)`）。 | T1.1 | `test_helpers.py` 中的 `simulate_crash_after_write()` 函数。 |
| T1.3 | 编写崩溃恢复测试用例 | 1. 执行一个原子写入操作。 <br>2. 在写入中途（如写临时文件后，重命名前）调用崩溃模拟函数。 <br>3. 重启系统（或重新初始化存储模块）。 <br>4. 验证数据处于一致状态（如任务不存在或完全存在，无脏数据）。 | T1.2 | `test_crash_recovery.py` 文件，包含多个测试用例。 |
| T1.4 | 集成到 CI 流程 | 将 `test_crash_recovery.py` 添加到 CI 配置（如 `pytest` 命令）中，作为强制验收步骤。 | T1.3 | CI 配置文件（如 `.gitlab-ci.yml`, `Jenkinsfile`）更新。 |
| **T2** | **全链路 Trace Context 透传一致性测试** | | | |
| T2.1 | 分析 Trace Context 传播路径 | 梳理从 HTTP 请求进入（`main.py`）到最终 LLM 调用或事件处理��完整调用链，标记出所有需要传递 `traceparent` 的点。 | 无 | 一份 Trace Context 传播路径图或文档。 |
| T2.2 | 实现 Trace Context 注入/提取中间件 | 如果尚未实现，编写一个 FastAPI 中间件，从入站请求中提取 `traceparent` 头，并注入到 `request.state` 中。同时，为出站 HTTP 请求（如调用 LLM）添加 `traceparent` 头。 | T2.1 | `monitoring/middleware.py` 文件。 |
| T2.3 | 编写 Trace Context 透传测试用例 | 1. 发起一个模拟请求，并携带一个已知的 `traceparent` 头。 <br>2. 使用 Mock 对象拦截所有内部调用（如 `ChatHarness.chat`）。 <br>3. 验证所有被拦截的调用都接收到了正确的 `trace_id` 和 `parent_span_id`。 | T2.2 | `test_trace_context.py` 文件。 |
| T2.4 | 集成到 CI 流程 | 将 `test_trace_context.py` 添加到 CI 配置中。 | T2.3 | CI 配置文件更新。 |
| **T3** | **降级路径触发与健康状态验证** | | | |
| T3.1 | 识别所有降级路径 | 分析代码，找出所有 `try...except` 块和条件判断，这些是降级逻辑的入口。例如，`main.py` 中 `BridgeChatChannel` 初始化失败、`_agent_llm_chat` 函数返回 `None` 等。 | 无 | 一份降级路径清单。 |
| T3.2 | 实现故障注入机制 | 创建一个测试配置或环境变量，允许在测试中禁用特定服务（如 `DISABLE_LLM=true`）。或者，使用 `unittest.mock` 来模拟服务故障。 | T3.1 | 测试配置或 Mock 策略。 |
| T3.3 | 编写降级与健康检查测试用例 | 1. 通过配置或 Mock 模拟一个服务故障（如 LLM 不可用）。 <br>2. 调用相关 API（如 `/api/v1/bridge-chat/send`）。 <br>3. 验证 API 返回了降级响应（如模板回复）。 <br>4. 调用 `/api/v1/health` 端点。 <br>5. 验证 `services` 中对应服务的状态为 `false`，且整体 `status` 为 `ok` 或 `degraded`。 | T3.2 | `test_degradation.py` 文件。 |
| T3.4 | 集成到 CI 流程 | 将 `test_degradation.py` 添加到 CI 配置中。 | T3.3 | CI 配置文件更新。 |

### 4. 依赖关系与执行顺序

-   **T1 (原子写入)** 和 **T2 (Trace Context)** 之间没有强依赖关系，可以并行开发。
-   **T3 (降级路径)** 依赖于 **T3.1 (识别降级路径)** 的完成，但 T3.1 本身是一个分析任务，可以快速完成。
-   所有子任务的 **T.x.4 (集成到 CI)** 步骤都依赖于其对应的测试用例编写完成。
-   **建议执行顺序:**
    1.  **并行启动:** T1.1, T2.1, T3.1 (分析阶段)
    2.  **并行开发:** T1.2, T2.2, T3.2 (工具/机制实现)
    3.  **并行开发:** T1.3, T2.3, T3.3 (测试用例编写)
    4.  **最终集成:** T1.4, T2.4, T3.4 (CI 配置)

### 5. 对后续角色的指导

-   **研究人员 (Research Agent):**
    -   请深入研究 `monitoring/models.py` 中的 `TraceContext` 和 `TraceSpan` 模型，确认其完整性和与 W3C 标准的兼容性。
    -   分析 `task_store.py`, `team_store.py` 等文件的写入逻辑，评估当前实现是否具备原子性。如果使用文件存储，研究 `os.rename` 的原子性保证。
    -   调研 Python `asyncio` 中 `contextvars` 的使用，为 T2.2 中异步任务的 Trace Context 传播提供最佳实践。

-   **架构师 (Architecture Agent):**
    -   基于 T2.1 的分析结果，设计一个清晰的 Trace Context 传播架构图，明确各组件（API 网关、业务服务、后台任务）的职责。
    -   为 T3.1 的降级路径设计一个统一的降级策略模式（如“断路器”模式），确保降级逻辑的一致性和可测试性。
    -   评估 T1.1 中识别的关键写入路径，如果当前实现不满足原子性，请设计一个改进方案（如引入 WAL 或事务性文件写入）。

-   **开发者 (Developer Agent):**
    -   根据 T1.2 和 T1.3 的要求，实现崩溃模拟辅助函数和测试用例。注意测试需要在隔离环境中运行，避免影响开发数据。
    -   根据 T2.2 和 T2.3 的要求，实现 Trace Context 中间件和测试用例。确保中间件不影响现有请求处理逻辑。
    -   根据 T3.2 和 T3.3 的要求，实现故障注入机制和测试用例。优先使用 Mock 对象，避免修改生产代码。

────────────────────────────────────────────────────────────
✅ deepseek-chat 完成
