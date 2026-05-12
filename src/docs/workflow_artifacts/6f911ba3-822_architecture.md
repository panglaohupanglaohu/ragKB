# 架构设计 — architect

任务: 集成配置中心 watch 链路并暴露通道健康指标：对接 etcd/Consul watch，实现配置推送回调，在回调中触发模块级原子更新，上报连接断连次数、推送延迟、加载失败等指标
步骤: architecture
Agent: build_architect

---

📋 任务: 6f911ba3-822
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
  集成配置中心 watch 链路并暴露通道健康指标：对接 etcd/Consul watch，实现配置推送回调，在回调中触发模块级原子更新，上报连接断连次数、推送延迟、加载失败等指标
  Deployer + Architect
  
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
  src/docs/workflow_artifacts/7c934759-39e_test.md
  ... (共 171 个 src/ 文件)
  
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
  
          moderator = self._resolve_moderator(plaza, disc, participants)
          speakers = self._sort_speakers(participants, moderator)
  
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
              f"请开场:\n"
              f"- 用 2-4 句话点明讨论的核心问题\n"
              f"- 直接围绕用户提出的话题展开，不要自行转换或重新解读话题\n"
              f"- 然后向参与者提出第一个需要讨论的具体问题\n"
              f"- 说人话，像一个项目经理在主持会议"
          )
          opening = await self._speak_with_lock(
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
                          f"你正在参与关于「{disc.topic}」的团队讨论。\n"
                          f"你是 {speaker.agent_name}（{speaker.role}）。"
                          f"第 {round_num} 轮，第 {ex_idx+1} 次发言。\n\n"
                          f"刚才的讨论:\n{recent}\n\n"
                          f"发言要求:\n"
                          f"- 结合你的专业背景，给出有实质内容的观点或建议\n"
                          f"- 回应上面讨论中你认为重要的点，然后补充你的看法\n"
                          f"- 可以提出具体的方案、步骤、注意事项\n"
                          f"- 说 3-5 句话，100-200 字左右，不要太短也不要写论文\n"
                          f"- 像在开会发言一样自然表达，不要用列表和标题"
                      )
                      await self._speak_with_lock(
                          disc, speaker, speak_prompt, round_number=round_num,
                          niche_role=speaker.niche_role.value,
                      )
  
              # Moderator 收束本轮 (非最后一轮时)
              if round_num < disc.max_rounds:
                  summary_prompt = (
                      f"你是主持人。第 {round_num} 轮讨论已结束。\n\n"
                      f"本轮讨论:\n{self._format_round_messages(disc, round_num)}\n\n"
                      f"请小结本轮要点:\n"
                      f"- 总结大家达成的共识和仍有分歧的地方\n"
                      f"- 提出下一轮需要重点讨论的问题\n"
                      f"- 用 2-3 句话，自然表达"
                  )
                  await self._speak_with_lock(
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
          # 将最终总结中的执行计划提取到 disc.plan，供前端和派发使用
          disc.plan = {
              "revision_reason": "讨论收敛",
              "revised_at": datetime.now(timezone.utc).isoformat(),
              "content": disc.summary,
          }
          await self._broadcast(disc.id, {"type": "plan_updated", "plan": disc.plan})
  
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
              f"{len(dis
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
              instructions="## 代码重构\n\n1. 识别代码坏味道\n2. 选择重构策略\n3. 小步修改，保持测试绿色\n4
  ```
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  
  ## 前序步骤的产出 (递进式摘要)
  
  ### 步骤 01: pm_decompose
  任务: 集成配置中心 watch 链路并暴露通道健康指标：对接 etcd/Consul watch，实现配置推送回调，在回调中触发模块级原子更新，上报连接断连次数、推送延迟、加载失败等指标
  步骤: pm_decompose
  📋 任务: 6f911ba3-822
  🤖 Agent: PM (project_manager)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ────────────────────────────────────────────────────────────
  你是 AgentsGroup2026 系统的 PM (project_manager)。
  你是项目经理 (PM)。请对以下任务进行分解和规划:
  集成配置中心 watch 链路并暴露通道健康指标：对接 etcd/Consul watch，实现配置推送回调，在回调中触发模块级原子更新，上报连接断连次数、推送延迟、加载失败等指标
  Deployer + Architect
  ## 📂 项目上下文 (系统自动预加载)
  ### 项目文件结构 (src/ 目录)
  ### 文件: `src/frontend/js/i18n.js`
  ### 文件: `src/frontend/js/nav-sidebar.js`
  **变更文件 (1):**
    - `src/backend/main.py`
  **子任务拆解:**
    - *项目名称:** AgentsGroup2026
    - *任务 ID:** TASK-2026-CONFIG-WATCH
    - *负责人:** Deployer + Architect
    - *优先级:** P0 (高)
    - *预计工时:** 5-8 人天
    -  **核心功能:**
    -  **技术选型:**
    -  **约束条件:**
  
  ### 步骤 02: research (完整产出)
  
  # 研究分析 — researcher
  
  任务: 集成配置中心 watch 链路并暴露通道健康指标：对接 etcd/Consul watch，实现配置推送回调，在回调中触发模块级原子更新，上报连接断连次数、推送延迟、加载失败等指标
  步骤: research
  Agent: build_researcher
  
  ---
  
  📋 任务: 6f911ba3-822
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
    集成配置中心 watch 链路并暴露通道健康指标：对接 etcd/Consul watch，实现配置推送回调，在回调中触发模块级原子更新，上报连接断连次数、推送延迟、加载失败等指标
    Deployer + Architect
    
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
    src/docs/workflow_artifacts/7c934759-39e_test.md
    ... (共 171 个 src/ 文件)
    
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
            self, plaza_id: str, agent_id: str,
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

# 技术方案: 集成配置中心 Watch 链路并暴露通道健康指标

## 1. 概述

### 1.1 目标
对接 etcd/Consul 配置中心的 Watch 机制，实现配置变更的实时推送回调，在回调中触发模块级原子更新，并上报连接断连次数、推送延迟、加载失败等健康指标。

### 1.2 范围
- 新增 `src/backend/config_watch/` 模块
- 修改 `src/backend/main.py` 集成启动
- 新增健康指标上报到现有监控系统
- 暴露 REST API 查询通道健康状态

### 1.3 约束
- 使用 Python 3.10+ asyncio
- 兼容现有 FastAPI 框架
- 指标上报复用 `src/backend/monitoring/` 现有基础设施
- 支持 etcd v3 API 和 Consul v1 API

---

## 2. 架构设计

### 2.1 模块结构

```
src/backend/config_watch/
├── __init__.py              # 模块入口，暴露 ConfigWatchManager
├── base.py                  # 抽象基类 ConfigWatchBackend
├── etcd_watch.py            # etcd 实现
├── consul_watch.py          # Consul 实现
├── callback_manager.py      # 回调管理器，触发模块级原子更新
├── health_collector.py      # 健康指标收集器
├── models.py                # 数据模型
└── router.py                # FastAPI 路由（暴露健康状态 API）
```

### 2.2 核心类图

```
ConfigWatchManager (单例)
├── backends: Dict[str, ConfigWatchBackend]
│   ├── EtcdWatchBackend
│   └── ConsulWatchBackend
├── callback_manager: CallbackManager
├── health_collector: HealthCollector
└── start() / stop()

ConfigWatchBackend (ABC)
├── watch_key(key: str, callback: Callable)
├── watch_prefix(prefix: str, callback: Callable)
├── get(key: str) -> Optional[str]
├── health() -> BackendHealth
└── close()

CallbackManager
├── register(module_id: str, updater: ModuleUpdater)
├── unregister(module_id: str)
└── _on_config_change(key: str, old_value, new_value)

HealthCollector
├── record_connect()
├── record_disconnect()
├── record_push_latency(latency_ms: float)
├── record_load_failure(key: str, error: str)
├── get_snapshot() -> ChannelHealthSnapshot
└── reset()
```

### 2.3 数据模型 (`models.py`)

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List, Optional

class BackendHealth(BaseModel):
    backend_type: str  # "etcd" | "consul"
    connected: bool
    last_connect_time: Optional[datetime]
    last_disconnect_time: Optional[datetime]
    connect_count: int = 0
    disconnect_count: int = 0
    last_push_latency_ms: Optional[float]
    avg_push_latency_ms: float = 0.0
    max_push_latency_ms: float = 0.0
    load_failure_count: int = 0
    last_load_failure: Optional[str]
    watched_keys: int = 0

class ChannelHealthSnapshot(BaseModel):
    timestamp: datetime
    backends: Dict[str, BackendHealth]
    overall_status: str  # "healthy" | "degraded" | "unhealthy"

class ConfigChangeEvent(BaseModel):
    key: str
    old_value: Optional[str]
    new_value: Optional[str]
    backend_type: str
    timestamp: datetime
    push_latency_ms: float
```

---

## 3. 详细设计

### 3.1 抽象基类 (`base.py`)

```python
from abc import ABC, abstractmethod
from typing import Callable, Optional, Dict, Any
from .models import BackendHealth

ConfigChangeCallback = Callable[[str, Optional[str], Optional[str]], None]

class ConfigWatchBackend(ABC):
    """配置中心 Watch 后端抽象基类"""
    
    def __init__(self, backend_type: str, endpoints: list, **kwargs):
        self.backend_type = backend_type
        self.endpoints = endpoints
        self._watched_keys: Dict[str, ConfigChangeCallback] = {}
        self._watched_prefixes: Dict[str, ConfigChangeCallback] = {}
    
    @abstractmethod
    async def start(self) -> bool:
        """启动连接并开始 Watch"""
        ...
    
    @abstractmethod
    async def watch_key(self, key: str, callback: ConfigChangeCallback) -> bool:
        """监听单个 key 的变化"""
        ...
    
    @abstractmethod
    async def watch_prefix(self, prefix: str, callback: ConfigChangeCallback) -> bool:
        """监听某个前缀下所有 key 的变化"""
        ...
    
    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """获取当前值"""
        ...
    
    @abstractmethod
    async def health(self) -> BackendHealth:
        """获取后端健康状态"""
        ...
    
    @abstractmethod
    async def close(self):
        """关闭连接"""
        ...
```

### 3.2 etcd 实现 (`etcd_watch.py`)

```python
import asyncio
import logging
from datetime import datetime, timezone
from typing import Callable, Optional, Dict
from typing_extensions import override

import etcd3

from .base import ConfigWatchBackend, ConfigChangeCallback
from .models import BackendHealth

logger = logging.getLogger(__name__)

class EtcdWatchBackend(ConfigWatchBackend):
    """etcd v3 Watch 实现"""
    
    def __init__(self, endpoints: list, **kwargs):
        super().__init__("etcd", endpoints, **kwargs)
        self._client: Optional[etcd3.Etcd3Client] = None
        self._watch_cancel_callbacks: Dict[str, Callable] = {}
        self._watch_task: Optional[asyncio.Task] = None
        self._connected = False
        self._connect_count = 0
        self._disconnect_count = 0
        self._last_connect_time: Optional[datetime] = None
        self._last_disconnect_time: Optional[datetime] = None
        self._push_latencies: list = []
        self._load_failure_count = 0
        self._last_load_failure: Optional[str] = None
    
    async def start(self) -> bool:
        """启动 etcd 客户端连接"""
        try:
            # etcd3 客户端是同步的，在 executor 中运行
            loop = asyncio.get_event_loop()
            self._client = await loop.run_in_executor(
                None, lambda: etcd3.client(
                    host=self.endpoints[0].split(":")[0],
                    port=int(self.endpoints[0].split(":")[1]) if ":" in self.endpoints[0] else 2379
                )
            )
            # 验证连接
            await loop.run_in_executor(None, lambda: self._client.status())
            self._connected = True
            self._connect_count += 1
            self._last_connect_time = datetime.now(timezone.utc)
            logger.info(f"etcd 连接成功: {self.endpoints}")
            return True
        except Exception as e:
            logger.error(f"etcd 连接失败: {e}")
            self._connected = False
            return False
    
    async def watch_key(self, key: str, callback: ConfigChangeCallback) -> bool:
        """监听单个 key"""
        if not self._client:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            # 获取当前值
            old_value = await self.get(key)
            
            # 启动 Watch
            watch_id = await loop.run_in_executor(
                None,
                lambda: self._client.add_watch_callback(
                    key,
                    self._make_watch_callback(key, callback, old_value)
                )
            )
            self._watch_cancel_callbacks[key] = lambda: self._client.cancel_watch(watch_id)
            self._watched_keys[key] = callback
            logger.info(f"etcd watch key: {key}")
            return True
        except Exception as e:
            logger.error(f"etcd watch key 失败 {key}: {e}")
            return False
    
    def _make_watch_callback(self, key: str, callback: ConfigChangeCallback, old_value: Optional[str]):
        """创建 Watch 回调闭包"""
        import time
        
        def _callback(response):
            nonlocal old_value
            try:
                start_time = time.time()
                for event in response.events:
                    new_value = event.value.decode() if event.value else None
                    # 记录推送延迟
                    latency_ms = (time.time() - start_time) * 1000
                    self._push_latencies.append(latency_ms)
                    if len(self._push_latencies) > 100:
                        self._push_latencies.pop(0)
                    
                    # 调用回调
                    callback(key, old_value, new_value)
                    old_value = new_value
            except Exception as e:
                logger.error(f"etcd watch 回调异常 {key}: {e}")
                self._load_failure_count += 1
                self._last_load_failure = str(e)
        
        return _callback
    
    async def watch_prefix(self, prefix: str, callback: ConfigChangeCallback) -> bool:
        """监听前缀"""
        # 类似 watch_key 实现，使用 prefix 参数
        ...
    
    async def get(self, key: str) -> Optional[str]:
        """获取值"""
        if not self._client:
            return None
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, lambda: self._client.get(key)
            )
            if result and result[0]:
                return result[0].decode()
            return None
        except Exception as e:
            logger.error(f"etcd get 失败 {key}: {e}")
            self._load_failure_count += 1
            self._last_load_failure = str(e)
            return None
    
    async def health(self) -> BackendHealth:
        """健康状态"""
        avg_latency = sum(self._push_latencies) / len(self._push_latencies) if self._push_latencies else 0.0
        max_latency = max(self._push_latencies) if self._push_latencies else 0.0
        last_latency = self._push_latencies[-1] if self._push_latencies else None
        
        return BackendHealth(
            backend_type=self.backend_type,
            connected=self._connected,
            last_connect_time=self._last_connect_time,
            last_disconnect_time=self._last_disconnect_time,
            connect_count=self._connect_count,
            disconnect_count=self._disconnect_count,
            last_push_latency_ms=last_latency,
            avg_push_latency_ms=avg_latency,
            max_push_latency_ms=max_latency,
            load_failure_count=self._load_failure_count,
            last_load_failure=self._last_load_failure,
            watched_keys=len(self._watched_keys) + len(self._watched_prefixes)
        )
    
    async def close(self):
        """关闭连接"""
        for cancel in self._watch_cancel_callbacks.values():
            try:
                cancel()
            except Exception:
                pass
        self._watch_cancel_callbacks.clear()
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
        self._connected = False
        self._disconnect_count += 1
        self._last_disconnect_time = datetime.now(timezone.utc)
```

### 3.3 Consul 实现 (`consul_watch.py`)

```python
import asyncio
import logging
from datetime import datetime, timezone
from typing import Callable, Optional, Dict
from typing_extensions import override

import aiohttp
import json

from .base import ConfigWatchBackend, ConfigChangeCallback
from .models import BackendHealth

logger = logging.getLogger(__name__)

class ConsulWatchBackend(ConfigWatchBackend):
    """Consul KV Watch 实现（基于长轮询）"""
    
    def __init__(self, endpoints: list, **kwargs):
        super().__init__("consul", endpoints, **kwargs)
        self._session: Optional[aiohttp.ClientSession] = None
        self._base_url = f"http://{endpoints[0]}/v1" if endpoints else "http://localhost:8500/v1"
        self._watch_tasks: Dict[str, asyncio.Task] = {}
        self._connected = False
        self._connect_count = 0
        self._disconnect_count = 0
        self._last_connect_time: Optional[datetime] = None
        self._last_disconnect_time: Optional[datetime] = None
        self._push_latencies: list = []
        self._load_failure_count = 0
        self._last_load_failure: Optional[str] = None
        self._cached_values: Dict[str, Optional[str]] = {}
    
    async def start(self) -> bool:
        """启动 Consul 连接"""
        try:
            self._session = aiohttp.ClientSession()
            # 验证连接
            async with self._session.get(f"{self._base_url}/status/leader") as resp:
                if resp.status == 200:
                    self._connected = True
                    self._connect_count += 1
                    self._last_connect_time = datetime.now(timezone.utc)
                    logger.info(f"Consul 连接成功: {self._base_url}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Consul 连接失败: {e}")
            self._connected = False
            return False
    
    async def watch_key(self, key: str, callback: ConfigChangeCallback) -> bool:
        """监听单个 key（基于长轮询）"""
        if not self._session:
            return False
        
        # 获取当前值
        old_value = await self.get(key)
        self._cached_values[key] = old_value
        
        # 启动长轮询任务
        task = asyncio.create_task(self._long_poll_key(key, callback))
        self._watch_tasks[key] = task
        self._watched_keys[key] = callback
        logger.info(f"Consul watch key: {key}")
        return True
    
    async def _long_poll_key(self, key: str, callback: ConfigChangeCallback):
        """长轮询监听 key 变化"""
        import time
        index = 0
        
        while True:
            try:
                start_time = time.time()
                params = {"key": key, "index": index, "wait": "300s"}
                async with self._session.get(
                    f"{self._base_url}/kv/{key}",
                    params=params
                ) as resp:
                    if resp.status == 200:
                        # 有变更
                        data = await resp.json()
                        new_value = data[0]["Value"] if data and data[0].get("Value") else None
                        if new_value:
                            new_value = self._base64_decode(new_value)
                        
                        # 更新 index
                        index = int(resp.headers.get("X-Consul-Index", "0"))
                        
                        # 记录推送延迟
                        latency_ms = (time.time() - start_time) * 1000
                        self._push_latencies.append(latency_ms)
                        if len(self._push_latencies) > 100:
                            self._push_latencies.pop(0)
                        
                        # 检查值是否真的变了
                        old_value = self._cached_values.get(key)
                        if new_value != old_value:
                            callback(key, old_value, new_value)
                            self._cached_values[key] = new_value
                    
                    elif resp.status == 404:
                        # key 不存在，继续等待
                        await asyncio.sleep(5)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Consul long poll 异常 {key}: {e}")
                self._load_failure_count += 1
                self._last_load_failure = str(e)
                await asyncio.sleep(5)
    
    def _base64_decode(self, value: str) -> str:
        """Consul 返回 base64 编码的值"""
        import base64
        try:
            return base64.b64decode(value).decode()
        except Exception:
            return value
    
    async def get(self, key: str) -> Optional[str]:
        """获取值"""
        if not self._session:
            return None
        try:
            async with self._session.get(f"{self._base_url}/kv/{key}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data and data[0].get("Value"):
                        return self._base64_decode(data[0]["Value"])
                return None
        except Exception as e:
            logger.error(f"Consul get 失败 {key}: {e}")
            self._load_failure_count += 1
            self._last_load_failure = str(e)
            return None
    
    async def health(self) -> BackendHealth:
        """健康状态"""
        avg_latency = sum(self._push_latencies) / len(self._push_latencies) if self._push_latencies else 0.0
        max_latency = max(self._push_latencies) if self._push_latencies else 0.0
        last_latency = self._push_latencies[-1] if self._push_latencies else None
        
        return BackendHealth(
            backend_type=self.backend_type,
            connected=self._connected,
            last_connect_time=self._last_connect_time,
            last_disconnect_time=self._last_disconnect_time,
            connect_count=self._connect_count,
            disconnect_count=self._disconnect_count,
            last_push_latency_ms=last_latency,
            avg_push_latency_ms=avg_latency,
            max_push_latency_ms=max_latency,
            load_failure_count=self._load_failure_count,
            last_load_failure=self._last_load_failure,
            watched_keys=len(self._watched_keys) + len(self._watched_prefixes)
        )
    
    async def close(self):
        """关闭连接"""
        for task in self._watch_tasks.values():
            task.cancel()
        self._watch_tasks.clear()
        if self._session:
            await self._session.close()
        self._connected = False
        self._disconnect_count += 1
        self._last_disconnect_time = datetime.now(timezone.utc)
```

### 3.4 回调管理器 (`callback_manager.py`)

```python
import asyncio
import logging
from typing import Callable, Dict, Optional, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

ModuleUpdater = Callable[[str, Optional[str], Optional[str]], bool]

class CallbackManager:
    """配置变更回调管理器，触发模块级原子更新"""
    
    def __init__(self):
        self._module_updaters: Dict[str, ModuleUpdater] = {}
        self._key_to_module: Dict[str, str] = {}
        self._update_lock = asyncio.Lock()
    
    def register(self, module_id: str, updater: ModuleUpdater, keys: list = None):
        """注册模块更新器
        
        Args:
            module_id: 模块标识
            updater: 更新函数 (key, old_value, new_value) -> success
            keys: 该模块监听的 key 列表
        """
        self._module_updaters[module_id] = updater
        if keys:
            for key in keys:
                self._key_to_module[key] = module_id
        logger.info(f"注册模块更新器: {module_id}")
    
    def unregister(self, module_id: str):
        """注销模块更新器"""
        self._module_updaters.pop(module_id, None)
        # 清理 key 映射
        keys_to_remove = [k for k, v in self._key_to_module.items() if v == module_id]
        for k in keys_to_remove:
            self._key_to_module.pop(k, None)
    
    async def on_config_change(self, key: str, old_value: Optional[str], new_value: Optional[str]):
        """配置变更回调入口
        
        1. 查找关联模块
        2. 获取模块级锁
        3. 执行原子更新
        4. 记录结果
        """
        module_id = self._key_to_module.get(key)
        if not module_id:
            logger.warning(f"未找到 key {key} 的关联模块")
            return
        
        updater = self._module_updaters.get(module_id)
        if not updater:
            logger.warning(f"未找到模块 {module_id} 的更新器")
            return
        
        async with self._update_lock:
            logger.info(f"触发模块更新: {module_id}, key={key}")
            try:
                # 执行原子更新
                success = updater(key, old_value, new_value)
                if success:
                    logger.info(f"模块 {module_id} 更新成功")
                else:
                    logger.error(f"模块 {module_id} 更新失败")
            except Exception as e:
                logger.error(f"模块 {module_id} 更新异常: {e}")
```

### 3.5 健康指标收集器 (`health_collector.py`)

```python
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from collections import deque

from .models import BackendHealth, ChannelHealthSnapshot

logger = logging.getLogger(__name__)

class HealthCollector:
    """健康指标收集器
    
    收集并聚合各后端的健康指标，提供快照查询。
    同时将指标上报到 monitoring 系统。
    """
    
    def __init__(self):
        self._backends: Dict[str, 'ConfigWatchBackend'] = {}
        self._push_latency_history: Dict[str, deque] = {}
        self._max_history = 1000
    
    def register_backend(self, backend: 'ConfigWatchBackend'):
        """注册后端"""
        self._backends[backend.backend_type] = backend
        self._push_latency_history[backend.backend_type] = deque(maxlen=self._max_history)
    
    def unregister_backend(self, backend_type: str):
        """注销后端"""
        self._backends.pop(backend_type, None)
        self._push_latency_history.pop(backend_type, None)
    
    async def get_snapshot(self) -> ChannelHealthSnapshot:
        """获取当前健康快照"""
        backends_health = {}
        overall_status = "healthy"
        
        for backend_type, backend in self._backends.items():
            try:
                health = await backend.health()
                backends_health[backend_type] = health
                
                # 判断整体状态
                if not health.connected:
                    overall_status = "unhealthy"
                elif health.load_failure_count > 10 or (health.avg_push_latency_ms and health.avg_push_latency_ms > 5000):
                    if overall_status != "unhealthy":
                        overall_status = "degraded"
            except Exception as e:
                logger.error(f"获取 {backend_type} 健康状态失败: {e}")
                backends_health[backend_type] = BackendHealth(
                    backend_type=backend_type,
                    connected=False,
                    last_load_failure=str(e)
                )
                overall_status = "unhealthy"
        
        return ChannelHealthSnapshot(
            timestamp=datetime.now(timezone.utc),
            backends=backends_health,
            overall_status=overall_status
        )
    
    async def report_to_monitoring(self):
        """上报指标到 monitoring 系统"""
        snapshot = await self.get_snapshot()
        
        # 上报到 monitoring collector
        try:
            from src.backend.monitoring.collector import get_collector
            collector = get_collector()
            
            for backend_type, health in snapshot.backends.items():
                collector.gauge(
                    f"config_watch.{backend_type}.connected",
                    1 if health.connected else 0
                )
                collector.gauge(
                    f"config_watch.{backend_type}.connect_count",
                    health.connect_count
                )
                collector.gauge(
                    f"config_watch.{backend_type}.disconnect_count",
                    health.disconnect_count
                )
                if health.avg_push_latency_ms:
                    collector.gauge(
                        f"config_watch.{backend_type}.avg_push_latency_ms",
                        health.avg_push_latency_ms
                    )
                collector.gauge(
                    f"config_watch.{backend_type}.load_failure_count",
                    health.load_failure_count
                )
                collector.gauge(
                    f"config_watch.{backend_type}.watched_keys",
                    health.watched_keys
                )
            
            collector.gauge(
                "config_watch.overall_status",
                0 if snapshot.overall_status == "healthy" else (1 if snapshot.overall_status == "degraded" else 2)
            )
            
            logger.debug(f"健康指标上报完成: {snapshot.overall_status}")
        except Exception as e:
            logger.error(f"健康指标上报失败: {e}")
```

### 3.6 管理器 (`__init__.py`)

```python
import asyncio
import logging
from typing import Dict, Optional, Callable

from .base import ConfigWatchBackend
from .etcd_watch import EtcdWatchBackend
from .consul_watch import ConsulWatchBackend
from .callback_manager import CallbackManager
from .health_collector import HealthCollector
from .models import ChannelHealthSnapshot

logger = logging.getLogger(__name__)

class ConfigWatchManager:
    """配置中心 Watch 管理器（单例）"""
    
    _instance: Optional['ConfigWatchManager'] = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        self.backends: Dict[str, ConfigWatchBackend] = {}
        self.callback_manager = CallbackManager()
        self.health_collector = HealthCollector()
        self._report_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self, config: dict):
        """启动所有配置中心后端
        
        Args:
            config: {
                "etcd": {"endpoints": ["localhost:2379"], ...},
                "consul": {"endpoints": ["localhost:8500"], ...}
            }
        """
        self._running = True
        
        # 启动 etcd
        if "etcd" in config:
            etcd_config = config["etcd"]
            etcd_backend = EtcdWatchBackend(
                endpoints=etcd_config.get("endpoints", ["localhost:2379"]),
                **etcd_config.get("options", {})
            )
            if await etcd_backend.start():
                self.backends["etcd"] = etcd_backend
                self.health_collector.register_backend(etcd_backend)
                logger.info("etcd Watch ���端启动成功")
            else:
                logger.warning("etcd Watch 后端启动失败")
        
        # 启动 Consul
        if "consul" in config:
            consul_config = config["consul"]
            consul_backend = ConsulWatchBackend(
                endpoints=consul_config.get("endpoints", ["localhost:8500"]),
                **consul_config.get("options", {})
            )
            if await consul_backend.start():
                self.backends["consul"] = consul_backend
                self.health_collector.register_backend(consul_backend)
                logger.info("Consul Watch 后端启动成功")
            else:
                logger.warning("Consul Watch 后端启动失败")
        
        # 启动健康指标上报定时任务
        self._report_task = asyncio.create_task(self._periodic_report())
        
        logger.info(f"配置中心 Watch 管理器启动完成，后端: {list(self.backends.keys())}")
    
    async def stop(self):
        """停止所有后端"""
        self._running = False
        
        if self._report_task:
            self._report_task.cancel()
            try:
                await self._report_task
            except asyncio.CancelledError:
                pass
        
        for backend_type, backend in self.backends.items():
            try:
                await backend.close()
                logger.info(f"{backend_type} 后端已关闭")
            except Exception as e:
                logger.error(f"关闭 {backend_type} 后端失败: {e}")
        
        self.backends.clear()
        logger.info("配置中心 Watch 管理器已停止")
    
    async def _periodic_report(self):
        """定时上报健康指标（每 30 秒）"""
        while self._running:
            try:
                await asyncio.sleep(30)
                await self.health_collector.report_to_monitoring()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"定时上报异常: {e}")
    
    async def watch_key(self, key: str, callback: Callable, backend_type: str = "etcd"):
        """监听 key"""
        backend = self.backends.get(backend_type)
        if not backend:
            logger.error(f"后端 {backend_type} 未启动")
            return False
        return await backend.watch_key(key, callback)
    
    async def watch_prefix(self, prefix: str, callback: Callable, backend_type: str = "etcd"):
        """监听前缀"""
        backend = self.backends.get(backend_type)
        if not backend:
            logger.error(f"后端 {backend_type} 未启动")
            return False
        return await backend.watch_prefix(prefix, callback)
    
    async def get_health_snapshot(self) -> ChannelHealthSnapshot:
        """获取健康快照"""
        return await self.health_collector.get_snapshot()
```

### 3.7 FastAPI 路由 (`router.py`)

```python
from fastapi import APIRouter, HTTPException
from . import ConfigWatchManager
from .models import ChannelHealthSnapshot

router = APIRouter(prefix="/api/v1/config-watch", tags=["config-watch"])

@router.get("/health", response_model=ChannelHealthSnapshot)
async def get_config_watch_health():
    """获取配置中心 Watch 通道健康状态"""
    manager = ConfigWatchManager()
    try:
        snapshot = await manager.get_health_snapshot()
        return snapshot
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backends")
async def list_backends():
    """列出已连接的后端"""
    manager = ConfigWatchManager()
    return {"backends": list(manager.backends.keys())}

@router.post("/watch/key")
async def watch_key(key: str, backend_type: str = "etcd"):
    """手动添加 key 监听"""
    manager = ConfigWatchManager()
    success = await manager.watch_key(key, lambda k, o, n: None, backend_type)
    return {"success": success}

@router.post("/watch/prefix")
async def watch_prefix(prefix: str, backend_type: str = "etcd"):
    """手动添加前缀监听"""
    manager = ConfigWatchManager()
    success = await manager.watch_prefix(prefix, lambda k, o, n: None, backend_type)
    return {"success": success}
```

---

## 4. 集成到 main.py

### 4.1 修改 `src/backend/main.py`

```python
# 在文件顶部添加导入
from config_watch import ConfigWatchManager

# 在 app 初始化后添加
app = FastAPI(title="AgentsGroup2026", version="1.0.0")

# 配置中心 Watch 配置
CONFIG_WATCH_CONFIG = {
    "etcd": {
        "endpoints": ["localhost:2379"],
        "options": {
            "timeout": 5,
            "retry_interval": 3
        }
    },
    "consul": {
        "endpoints": ["localhost:8500"],
        "options": {
            "timeout": 5
        }
    }
}

@app.on_event("startup")
async def startup():
    """应用启动"""
    # 启动配置中心 Watch
    config_watch_manager = ConfigWatchManager()
    await config_watch_manager.start(CONFIG_WATCH_CONFIG)
    
    # 注册模块更新器示例
    from config_watch.callback_manager import CallbackManager
    
    def agent_config_updater(key: str, old_value: str, new_value: str) -> bool:
        """Agent 配置更新器"""
        try:
            # 解析新配置
            import json
            config = json.loads(new_value)
            # 执行原子更新
            # ...
            return True
        except Exception as e:
            logger.error(f"Agent 配置更新失败: {e}")
            return False
    
    config_watch_manager.callback_manager.register(
        "agent_config",
        agent_config_updater,
        keys=["/agents/config", "/agents/teams"]
    )
    
    # 注册路由
    from config_watch.router import router as config_watch_router
    app.include_router(config_watch_router)

@app.on_event("shutdown")
async def shutdown():
    """应用关闭"""
    config_watch_manager = ConfigWatchManager()
    await config_watch_manager.stop()
```

---

## 5. 模块级原子更新示例

### 5.1 Agent 团队配置更新器

```python
# src/backend/agents/team_manager.py 中添加

class TeamManager:
    """团队管理器"""
    
    def atomic_update_from_config(self, config_json: str) -> bool:
        """从配置 JSON 执行原子更新
        
        使用版本号确保原子性
        """
        import json
        
        try:
            config = json.loads(config_json)
            version = config.get("version", 0)
            
            # 检查版本号，防止旧配置覆盖新配置
            if version < self._current_config_version:
                logger.warning(f"跳过旧版本配置: {version} < {self._current_config_version}")
                return False
            
            # 备份当前状态
            old_teams = dict(self._teams)
            old_agents = dict(self._agents)
            
            try:
                # 执行更新
                for team_config in config.get("teams", []):
                    team_id = team_config["id"]
                    if team_id in self._teams:
                        self._teams[team_id].update_from_config(team_config)
                    else:
                        self._teams[team_id] = Team.from_config(team_config)
                
                # 移除已删除的团队
                active_ids = {t["id"] for t in config.get("teams", [])}
                for team_id in list(self._teams.keys()):
                    if team_id not in active_ids:
                        del self._teams[team_id]
                
                # 更新版本号
                self._current_config_version = version
                
                logger.info(f"团队配置原子更新成功 (version={version})")
                return True
                
            except Exception:
                # 回滚
                self._teams = old_teams
                self._agents = old_agents
                logger.error("团队配置更新失败，已回滚")
                return False
                
        except json.JSONDecodeError as e:
            logger.error(f"配置 JSON 解析失败: {e}")
            return False
```

---

## 6. 配置示例

### 6.1 etcd 配置

```yaml
# config/etcd.yaml
etcd:
  endpoints:
    - "localhost:2379"
    - "localhost:2380"
  options:
    timeout: 5
    retry_interval: 3
    max_retries: 5
    watch_keys:
      - "/agents/config"
      - "/agents/teams"
      - "/system/features"
    watch_prefixes:
      - "/modules/"
```

### 6.2 Consul 配置

```yaml
# config/consul.yaml
consul:
  endpoints:
    - "localhost:8500"
  options:
    timeout: 5
    datacenter: "dc1"
    watch_keys:
      - "agents/config"
      - "agents/teams"
    watch_prefixes:
      - "modules/"
```

---

## 7. 测试方案

### 7.1 单元测试

```python
# tests/test_config_watch/test_etcd_watch.py
# tests/test_config_watch/test_consul_watch.py
# tests/test_config_watch/test_callback_manager.py
# tests/test_config_watch/test_health_collector.py
```

### 7.2 集成测试

```python
# tests/test_config_watch/test_integration.py

async def test_etcd_watch_integration():
    """测试 etcd Watch 集成"""
    # 启动 etcd 容器（使用 testcontainers）
    # 创建配置
    # 监听 key
    # 修改配置
    # 验证回调触发
    # 验证健康指标
    pass

async def test_consul_watch_integration():
    """测试 Consul Watch 集成"""
    pass

async def test_atomic_update():
    """测试原子更新"""
    # 注册模块更新器
    # 触发配置变更
    # 验证更新成功
    # 验证回滚机制
    pass
```

---

## 8. 实施步骤

### Step 1: 创建模块结构
- 创建 `src/backend/config_watch/` 目录
- 创建 `__init__.py`, `base.py`, `models.py`

### Step 2: 实现后端连接
- 实现 `EtcdWatchBackend` (etcd_watch.py)
- 实现 `ConsulWatchBackend` (consul_watch.py)
- 实现连接/断连重试逻辑

### Step 3: 实现 Watch 机制
- 实现 etcd 的 Watch 回调
- 实现 Consul 的长轮询
- 实现前缀监听

### Step 4: 实现回调管理
- 实现 `CallbackManager`
- 实现模块注册/注销
- 实现原子更新锁

### Step 5: 实现健康指标
- 实现 `HealthCollector`
- 实现指标收集和聚合
- 实现上报到 monitoring

### Step 6: 集成到 main.py
- 添加启动/关闭逻辑
- 注册路由
- 注册模块更新器

### Step 7: 测试
- 单元测试
- 集成测试
- 端到端测试

---

## 9. 依赖

```txt
# requirements.txt 新增
etcd3>=0.12.0
aiohttp>=3.9.0
```

---

## 10. 健康指标 Prometheus 格式

```prometheus
# HELP config_watch_etcd_connected etcd 连接状态
# TYPE config_watch_etcd_connected gauge
config_watch_etcd_connected 1

# HELP config_watch_etcd_connect_count etcd 连接次数
# TYPE config_watch_etcd_connect_count gauge
config_watch_etcd_connect_count 5

# HELP config_watch_etcd_disconnect_count etcd 断连次数
# TYPE config_watch_etcd_disconnect_count gauge
config_watch_etcd_disconnect_count 1

# HELP config_watch_etcd_avg_push_latency_ms etcd 平均推送延迟(ms)
# TYPE config_watch_etcd_avg_push_latency_ms gauge
config_watch_etcd_avg_push_latency_ms 12.5

# HELP config_watch_etcd_load_failure_count etcd 加载失败次数
# TYPE config_watch_etcd_load_failure_count gauge
config_watch_etcd_load_failure_count 0

# HELP config_watch_etcd_watched_keys etcd 监听的 key 数量
# TYPE config_watch_etcd_watched_keys gauge
config_watch_etcd_watched_keys 5

# HELP config_watch_overall_status 整体状态 (0=healthy, 1=degraded, 2=unhealthy)
# TYPE config_watch_overall_status gauge
config_watch_overall_status 0
```

────────────────────────────────────────────────────────────
✅ deepseek-chat 完成
