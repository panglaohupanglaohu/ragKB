# 架构设计 — architect

任务: pipeline验证测试
步骤: architecture
Agent: build_architect

---

📋 任务: 17d0eaa2-bd5
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
  pipeline验证测试
  验证QA gate修复: 当QA verdict=PASS时pipeline不应该被阻断
  
  ## 📂 项目上下文 (系统自动预加载)
  
  ### 项目文件结构 (src/ 目录)
  ```
  src/frontend/agent-team-config.html
  src/frontend/index.html
  src/frontend/login.html
  src/frontend/monitoring.html
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
  src/backend/tests/test_evolution_race.py
  src/backend/tests/test_evolution_race.py.bak
  src/backend/tests/test_fingerprint.py
  src/backend/tests/test_fingerprint.py.bak
  src/backend/tests/test_gate_evaluator.py
  src/backend/tests/test_merge_plugin.py
  src/backend/tests/test_merge_plugin.py.bak
  src/backend/tests/test_models.py
  src/backend/tests/test_models.py.bak
  src/backend/tests/test_task_engine.py
  src/backend/tests/test_task_engine.py.bak
  src/backend/tests/test_team_manager.py
  src/backend/tests/test_team_manager.py.bak
  src/backend/tests/test_template_variants.py
  src/backend/tests/test_template_variants.py.bak
  src/backend/agents/__init__.py
  src/backend/agents/ab_testing.py
  src/backend/agents/agent_loop.py
  src/backend/agents/agent_toolbox.py
  src/backend/agents/api.py
  src/backend/agents/api.py.bak
  src/backend/agents/audit_store.py
  src/backend/agents/chat_harness.py
  src/backend/agents/domain_events.py
  src/backend/agents/domain_events.py.bak
  src/backend/agents/event_bus.py
  src/backend/agents/execution_registry.py
  src/backend/agents/fingerprint.py
  src/backend/agents/fingerprint.py.bak
  src/backend/agents/gate_evaluator.py
  src/backend/agents/hermes_research.py
  src/backend/agents/knowledge_base.py
  src/backend/agents/merge_engine.py
  src/backend/agents/merge_models.py
  src/backend/agents/models.py
  src/backend/agents/models.py.bak
  src/backend/agents/plaza.py
  src/backend/agents/plaza_engine.py
  src/backend/agents/plaza_routes.py
  src/backend/agents/plaza_routes.py.bak
  src/backend/agents/plaza_store.py
  src/backend/agents/review_models.py
  src/backend/agents/review_routes.py
  src/backend/agents/review_service.py
  src/backend/agents/session_store.py
  src/backend/agents/similarity_engine.py
  src/backend/agents/skill_extractor.py
  src/backend/agents/skill_indexer.py
  src/backend/agents/skill_querier.py
  src/backend/agents/skill_registry.py
  src/backend/agents/skill_store.py
  src/backend/agents/task_engine.py
  src/backend/agents/task_engine.py.bak
  src/backend/agents/task_store.py
  src/backend/agents/team_manager.py
  src/backend/agents/team_manager.py.bak
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
  src/backend/scripts/migrate.py
  src/backend/scripts/validate_startup.py
  src/backend/scripts/validate_telemetry.py
  src/backend/monitoring/__init__.py
  src/backend/monitoring/__init__.py.bak
  src/backend/monitoring/aggregation_window.py
  src/backend/monitoring/aggregation_window.py.bak
  src/backend/monitoring/collector.py
  src/backend/monitoring/collector.py.bak
  src/backend/monitoring/fingerprint_bypass.py
  src/backend/monitoring/models.py
  src/backend/monitoring/models.py.bak
  src/backend/monitoring/monitoring_routes.py
  src/backend/monitoring/plaza_monitor.py
  src/backend/monitoring/plaza_monitor.py.bak
  src/backend/monitoring/sampler.py
  src/backend/monitoring/trace_bridge.py
  src/backend/channels/__init__.py
  src/backend/channels/bridge_chat.py
  src/backend/channels/evolution_executor.py
  src/backend/channels/marine_base.py
  src/backend/channels/merge_channel.py
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
  src/docs/agent_handoffs/11e9b4b9-283_architecture_20260509T075556.md
  src/docs/agent_handoffs/11e9b4b9-283_deploy_20260509T081242.md
  src/docs/agent_handoffs/11e9b4b9-283_develop_20260509T080722.md
  src/docs/agent_handoffs/11e9b4b9-283_document_20260509T081332.md
  src/docs/agent_handoffs/11e9b4b9-283_executor_started_20260509T074916.md
  src/docs/agent_handoffs/11e9b4b9-283_pipeline_complete_20260509T081332.md
  src/docs/agent_handoffs/11e9b4b9-283_pm_decompose_20260509T075116.md
  src/docs/agent_handoffs/11e9b4b9-283_research_20260509T075401.md
  src/docs/agent_handoffs/11e9b4b9-283_test_20260509T081127.md
  src/docs/agent_handoffs/1356f045-d02_executor_started_20260509T073232.md
  src/docs/agent_handoffs/15554439-6aa_executor_started_20260509T073231.md
  src/docs/agent_handoffs/15a7e2eb-cd1_executor_started_20260509T073232.md
  src/docs/agent_handoffs/18d4b20f-c33_executor_started_20260509T073231.md
  src/docs/agent_handoffs/1aed56ed-eda_executor_started_20260509T073232.md
  src/docs/agent_handoffs/1cc2c0fb-90b_executor_started_20260509T073232.md
  src/docs/agent_handoffs/1ce78c0e-062_architecture_20260503T045804.md
  ... (共 697 个 src/ 文件)
  
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
  
  ### 文件: `src/backend/tests/test_gate_evaluator.py`
  ```py
  # -*- coding: utf-8 -*-
  """测试门禁评估器 — evaluate(context) 纯函数测试.
  
  覆盖:
    - 正常评估 (A/B/C 级)
    - 一票否决 (安全漏洞/破坏性变更/关键测试失败)
    - 边界情况 (0分/100分/缺失字段)
    - 确定性 (相同输入 → 相同输出)
    - 便捷函数 evaluate_from_dict / quick_evaluate
  """
  
  from __future__ import annotations
  
  import pytest
  
  from agents.gate_evaluator import (
      evaluate,
      evaluate_from_dict,
      quick_evaluate,
      _calculate_dimension_scores,
      _compute_weighted_score,
      _map_security_issues_to_score,
      _map_performance_impact,
  )
  from agents.review_models import GateEvaluationContext, GateLevel, GateEvaluationResult
  
  
  class TestGateEvaluator:
      """门禁评估器核心测试."""
  
      # ── 正常评估 ────────────────────────────────────────
  
      def test_evaluate_all_excellent(self):
          """全部优秀 → A级, passed."""
          ctx = GateEvaluationContext(
              entity_id="EVO-1",
              compliance_score=95.0,
              test_pass_rate=100.0,
              code_quality_score=95.0,
              security_issues=0,
              documentation_level=95.0,
              performance_impact=20.0,
          )
          result = evaluate(ctx)
          assert result.level == GateLevel.A
          assert result.passed is True
          assert result.score >= 85.0
          assert len(result.blocked_by) == 0
  
      def test_evaluate_good(self):
          """良好 → B级, passed."""
          ctx = GateEvaluationContext(
              entity_id="EVO-2",
              compliance_score=78.0,
              test_pass_rate=88.0,
              code_quality_score=75.0,
              security_issues=1,
              documentation_level=70.0,
              performance_impact=5.0,
          )
          result = evaluate(ctx)
          assert result.level in (GateLevel.B, GateLevel.C)
          assert result.passed is True
  
      def test_evaluate_moderate(self):
          """基本合规 → C级, passed."""
          ctx = GateEvaluationContext(
              entity_id="EVO-3",
              compliance_score=60.0,
              test_pass_rate=70.0,
              code_quality_score=58.0,
              security_issues=3,
              documentation_level=50.0,
              performance_impact=-5.0,
          )
          result = evaluate(ctx)
          assert result.level in (GateLevel.C, GateLevel.D)
          assert result.passed == (result.level != GateLevel.D)
  
      # ── 一票否决 ────────────────────────────────────────
  
      def test_veto_critical_security(self):
          """严重安全漏洞 → E级, score=0."""
          ctx = GateEvaluationContext(
              entity_id="EVO-sec",
              compliance_score=95.0,
              test_pass_rate=100.0,
              code_quality_score=95.0,
              has_critical_security_issue=True,
          )
          result = evaluate(ctx)
          assert result.level == GateLevel.E
          assert result.passed is False
          assert result.score == 0.0
          assert len(result.blocked_by) > 0
          assert any("安全" in b for b in result.blocked_by)
  
      def test_veto_breaking_change(self):
          """破坏性变更 → E级, score=0."""
          ctx = GateEvaluationContext(
              entity_id="EVO-break",
              compliance_score=90.0,
              has_breaking_change=True,
          )
          result = evaluate(ctx)
          assert result.level == GateLevel.E
          assert result.passed is False
          assert result.score == 0.0
  
      def test_veto_critical_test_failures(self):
          """关键测试失败 → E级, score=0."""
          ctx = GateEvaluationContext(
              entity_id="EVO-fail",
              compliance_score=88.0,
              critical_test_failures=2,
          )
          result = evaluate(ctx)
          assert result.level == GateLevel.E
          assert result.passed is False
          assert result.score == 0.0
  
      def test_multiple_vetos(self):
          """多个否决项同时触发."""
          ctx = GateEvaluationContext(
              entity_id="EVO-multi",
              has_critical_security_issue=True,
              has_breaking_change=True,
              critical_test_failures=1,
          )
          result = evaluate(ctx)
          assert len(result.blocked_by) == 3
  
      # ── 边界情况 ────────────────────────────────────────
  
      def test_zero_scores(self):
          """全0分 → E级."""
          ctx = GateEvaluationContext(entity_id="EVO-zero")
          result = evaluate(ctx)
          assert 0.0 <= result.score <= 40.0
          assert result.level in (GateLevel.D, GateLevel.E)
  
      def test_perfect_scores(self):
          """满分 → A级."""
          ctx = GateEvaluationContext(
              entity_id="EVO-perfect",
              compliance_score=100.0,
              test_pass_rate=100.0,
              code_quality_score=100.0,
              security_issues=0,
              documentation_level=100.0,
              performance_impact=100.0,
          )
          result = evaluate(ctx)
          assert result.level == GateLevel.A
          assert result.score >= 95.0
  
      def test_high_security_issues(self):
          """大量安全问题 → 安全评分归零."""
          ctx = GateEvaluationContext(
              entity_id="EVO-badsec",
              compliance_score=80.0,
              test_pass_rate=90.0,
              code_quality_score=80.0,
              security_issues=10,
          )
          result = evaluate(ctx)
          # 安全占15%权重，大量问题拉低总分
          assert result.score < 70.0
  
      def test_negative_performance(self):
          """严重性能退化."""
          ctx = GateEvaluationContext(
              entity_id="EVO-perf",
              compliance_score=80.0,
              test_pass_rate=90.0,
              code_quality_score=80.0,
              security_issues=0,
              performance_impact=-80.0,
          )
          result = evaluate(ctx)
          # 性能评分应低于50
          assert result.score < 80.0
  
      # ── 确定性 ──────────────────────────────────────────
  
      def test_deterministic(self):
          """相同输入 → 相同输出 (纯函数)."""
          ctx = GateEvaluationContext(
              entity_id="EVO-det",
              compliance_score=75.0,
              test_pass_rate=85.0,
              code_quality_score=70.0,
              security_issues=1,
          )
          results = [evaluate(ctx) for _ in range(20)]
          scores = {r.score for r in results}
          levels = {r.level for r in results}
          assert len(scores) == 1
          assert len(levels) == 1
  
      # ── 便捷函数 ────────────────────────────────────────
  
      def test_evaluate_from_dict(self):
          result = evaluate_from_dict({
              "entity_id": "EVO-dict",
              "compliance_score": 65.0,
              "test_pass_rate": 75.0,
              "code_quality_score": 68.0,
          })
          assert isinstance(result, GateEvaluationResult)
          assert result.entity_id is None  # entity_id 不在 result 中
          assert result.score is not None
  
      def test_quick_evaluate(self):
          result = quick_evaluate(
              entity_id="EVO-quick",
              compliance_score=72.0,
              test_pass_rate=88.0,
              code_quality_score=75.0,
          )
          assert isinstance(result, GateEvaluationResult)
          assert 60.0 <= result.score <= 90.0
  
      def test_quick_evaluate_with_veto(self):
          result = quick_evaluate(
              entity_id="EVO-quick-veto",
              compliance_score=90.0,
              has_critical_security_issue=True,
          )
          assert result.level == GateLevel.E
          assert result.passed is False
  
  
  class TestDimensionScoring:
      """维度评分辅助函数测试."""
  
      def test_security_map_zero(self):
          assert _map_security_issues_to_score(0) == 100.0
  
      def test_security_map_one(self):
          assert 60.0 <= _map_security_issues_to_score(1) <= 80.0
  
      def test_security_map_many(self):
          assert _map_security_issues_to_score(5) == 0.0
          assert _map_security_issues_to_score(10) == 0.0
  
      def test_performance_map_positive(self):
          assert _map_performance_impact(100.0) == 100.0
  
      def test_performance_map_neutral(self):
          assert _map_performance_impact(0.0) == 50.0
  
      def test_performance_map_negative(self):
          assert _map_performance_impact(-100.0) == 0.0
  
      def test_weighted_score(self):
          scores = {
              "compliance_score": 80.0,
              "test_pass_rate": 90.0,
              "code_quality_score": 80.0,
              "security_score": 100.0,
              "documentation_level": 70.0,
              "performance_score": 60.0,
          }
          result = _compute_weighted_score(scores)
          assert 70.0 <= result <= 90.0
  
  
  class TestGateLevel:
      """等级映射测试."""
  
      def test_from_score_A(self):
          assert GateLevel.from_score(95.0) == GateLevel.A
          assert GateLevel.from_score(85.0) == GateLevel.A
  
      def test_from_score_B(self):
          assert GateLevel.from_score(84.9) == GateLevel.B
          assert GateLevel.from_score(70.0) == GateLevel.B
  
      def test_from_score_C(self):
          assert GateLevel.from_score(69.9) == GateLevel.C
          assert GateLevel.from_score(55.0) == GateLevel.C
  
      def test_from_score_D(self):
          assert GateLevel.from_score(54.9) == GateLevel.D
          assert GateLevel.from_score(40.0) == GateLevel.D
  
      def test_from_score_E(self):
          assert GateLevel.from_score(39.9) == GateLevel.E
          assert GateLevel.from_score(0.0) == GateLevel.E
  
  ```
  
  ### 文件: `src/backend/tests/test_template_variants.py`
  ```py
  # -*- coding: utf-8 -*-
  """模板变体注入测试 — Plaza 多模板 XSS、结构完整性及 CSS 一致性验证.
  
  覆盖:
  - 所有 Plaza 模板 (wabisabi, wabisabi-v2, dark, old, main)
  - XSS 注入抵抗 (script/event-handler 不会被嵌入)
  - HTML 结构完整性 (必需 DOM 元素存在)
  - CSS 变量命名一致性
  """
  
  from __future__ import annotations
  
  import html.parser
  import os
  import re
  import json
  from pathlib import Path
  from typing import List, Set
  
  import pytest
  
  
  # ── 模板清单 ────────────────────────────────────────────
  
  FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
  
  PLAZA_TEMPLATES = [
      "plaza.html",
      "plaza-dark.html",
      "plaza-old.html",
      "plaza-wabisabi.html",
      "plaza-wabisabi-v2.html",
  ]
  
  # ── XSS 注入负载 ────────────────────────────────────────
  
  XSS_PAYLOADS = [
      '<script>alert("xss")</script>',
      '<img src=x onerror=alert(1)>',
      '<svg onload=alert(1)>',
      'javascript:alert(1)',
      '<body onload=alert(1)>',
      '"-prompt(1)-"',
      "'-prompt(1)-'",
      '<iframe src="javascript:alert(1)">',
      '<a href="javascript:alert(1)">click</a>',
      '<div onclick="alert(1)">click</div>',
  ]
  
  # ── 必需 DOM 元素 (每个 Plaza 页面应包含的关键结构) ──
  
  REQUIRED_ELEMENTS = [
      "<html",
      "<head",
      "<body",
      "plaza",
      "讨论",  # 讨论管理功能
      "智能体",
  ]
  
  # ── CSS 变量命名规范 ─────────────────────────────────────
  
  CSS_VAR_PATTERN = re.compile(r'--[a-z][a-z0-9-]*', re.IGNORECASE)
  
  # 已知合法的 Plaza CSS 变量前缀
  KNOWN_PREFIXES = [
      '--bg', '--fg', '--card', '--line', '--dim', '--muted',
      '--accent', '--accent-', '--lime', '--gold', '--rose', '--sky',
      '--pink', '--purple', '--cyan', '--amber',
      '--inner', '--mid', '--outer', '--moderator',
      '--niche', '--seat', '--ring',
      '--wabi', '--ando', '--concrete',
      '--font', '--radius', '--shadow',
  ]
  
  
  class TemplateVariant:
      """表示一个 Plaza 模板变体."""
  
      def __init__(self, filename: str):
          self.filename = filename
          self.path = FRONTEND_DIR / filename
          self._content: str = ""
          self._css_vars: Set[str] = set()
          self._loaded = False
  
      def load(self) -> str:
          """加载模板内容."""
          if not self._loaded:
              if self.path.exists():
                  self._content = self.path.read_text(encoding="utf-8")
              else:
                  self._content = ""
              self._loaded = True
          return self._content
  
      @property
      def content(self) -> str:
          return self.load()
  
      @property
      def css_variables(self) -> Set[str]:
          if not self._css_vars and self.content:
              self._css_vars = set(CSS_VAR_PATTERN.findall(self.content))
          return self._css_vars
  
  
  # ════════════════════════════════════════════════════════════
  # 模板加载与基础结构测试
  # ════════════════════════════════════════════════════════════
  
  class TestTemplateLoading:
      """验证所有 Plaza 模板文件存在且可读."""
  
      @pytest.mark.parametrize("template_file", PLAZA_TEMPLATES)
      def test_template_exists(self, template_file):
          """每个模板文件应当存在."""
          path = FRONTEND_DIR / template_file
          assert path.exists(), f"模板文件不存在: {template_file}"
          assert path.stat().st_size > 0, f"模板文件为空: {template_file}"
  
      @pytest.mark.parametrize("template_file", PLAZA_TEMPLATES)
      def test_template_is_valid_html_like(self, template_file):
          """每个模板应包含基本 HTML 结构."""
          variant = TemplateVariant(template_file)
          content = variant.content
          # 检查 HTML doctype 或 html 标签
          has_doctype = "<!DOCTYPE html>" in content or "<!DOCTYPE HTML>" in content.upper()
          has_html_tag = "<html" in content
          has_head_tag = "<head" in content
          has_body_tag = "<body" in content
          assert has_doctype or has_html_tag, f"{template_file}: 缺少 DOCTYPE 或 <html>"
          assert has_head_tag, f"{template_file}: 缺少 <head>"
          assert has_body_tag, f"{template_file}: 缺少 <body>"
  
      @pytest.mark.parametrize("template_file", PLAZA_TEMPLATES)
      def test_template_has_required_elements(self, template_file):
          """每个模板应包含 Plaza 关键功能元素."""
          variant = TemplateVariant(template_file)
          content = variant.content
          # 至少包含 "plaza" 关键词（可变体不同命名）
          plaza_related = any(
              kw in content.lower()
              for kw in ['plaza', '智能体广', '智能体広', '讨论', 'discuss', 'agent']
          )
          assert plaza_related, f"{template_file}: 未发现 Plaza/讨论相关关键词"
  
  
  # ════════════════════════════════════════════════════════════
  # XSS 注入抵抗测试
  # ════════════════════════════════════════════════════════════
  
  class TestTemplateXSSResistance:
      """验证模板不会直接输出 XSS 负载（静态模板层面）."""
  
      @pytest.mark.parametrize("template_file", PLAZA_TEMPLATES)
      def test_no_inline_event_handlers(self, template_file):
          """模板不应包含内联事件处理器 (onclick=, onerror= 等) 用于动态注入点."""
          variant = TemplateVariant(template_file)
          content = variant.content
          # 查找 event handler 模式
          event_pattern = re.compile(r'\bon[a-z]+\s*=\s*["\']', re.IGNORECASE)
          matches = event_pattern.findall(content)
          # 允许少量固有的（如页面切换 onclick），但不应过多
          assert len(matches) < 50, (
              f"{template_file}: 发现 {len(matches)} 个内联事件处理器，"
              f"需审查是否安全: {matches[:10]}"
          )
  
      @pytest.mark.parametrize("template_file", PLAZA_TEMPLATES)
      def test_no_eval_or_innerhtml_direct(self, template_file):
          """模板中不应直接使用 eval() 或 innerHTML 赋值原始用户内容."""
          variant = TemplateVariant(template_file)
          content = variant.content
          # 检查 eval(
          assert "eval(" not in content, (
              f"{template_file}: 发现 eval() 调用"
          )
          # innerHTML 使用是可接受的，但需确认上下文
          # 此处仅报告，不阻断
          inner_html_count = len(re.findall(r'\.innerHTML\s*=', content))
          if inner_html_count > 0:
              # 警告级别：innerHTML 需 textContent 或 DOMPurify 保护
              pass  # 仅记录
  
      @pytest.mark.parametrize("template_file", PLAZA_TEMPLATES)
      def test_no_document_write(self, template_file):
          """模板不应使用 document.write (现代 HTML 规范禁止)."""
          variant = TemplateVariant(template_file)
          content = variant.content
          assert "document.write" not in content, (
              f"{template_file}: 发现 document.write() 调用"
          )
  
  
  # ════════════════════════════════════════════════════════════
  # CSS 变量一致性测试
  # ════════════════════════════════════════════════════════════
  
  class TestCSSVariableConsistency:
      """验证 Plaza 模板间 CSS 变量命名一致性."""
  
      def test_all_templates_have_css_variables(self):
          """所有模板应定义 CSS 自定义变量."""
          for template_file in PLAZA_TEMPLATES:
              variant = TemplateVariant(template_file)
              assert len(variant.css_variables) > 0, (
                  f"{template_file}: 未定义任何 CSS 变量"
              )
  
      def test_css_variable_naming_convention(self):
          """CSS 变量应遵循 --lowercase-with-dashes 命名规范."""
          for template_file in PLAZA_TEMPLATES:
              variant = TemplateVariant(template_file)
              for var in variant.css_variables:
                  # 变量名应为全小写+连字符
                  var_name = var.lstrip('-')
                  assert var_name == var_name.lower(), (
                      f"{template_file}: CSS 变量 {var} 包含大写字符"
                  )
  
      def test_known_prefixes_across_templates(self):
          """跨模板的 CSS 变量应使用已知前缀以保证主题兼容."""
          for template_file in PLAZA_TEMPLATES:
              variant = TemplateVariant(template_file)
              for var in variant.css_variables:
                  var_lower = var.lower()
                  has_known_prefix = any(
                      var_lower.startswith(p) for p in KNOWN_PREFIXES
                  )
                  if not has_known_prefix:
                      # 仅报告，不阻断 (新模板可能引入新前缀)
                      pass
  
      def test_common_variables_across_templates(self):
          """不同模板间应共享一组核心 CSS 变量（允许主题前缀差异）."""
          all_common = None
          for template_file in PLAZA_TEMPLATES:
              variant = TemplateVariant(template_file)
              if all_common is None:
                  all_common = variant.css_variables.copy()
              else:
                  all_common &= variant.css_variables
          # 至少应有基础 UI 变量共享 (如 --dim, --line, --accent, --muted)
          ui_shared = {v for v in (all_common or set())
                       if any(v.startswith('--' + p) for p in
                              ['dim', 'line', 'accent', 'muted', 'text', 'font', 'panel'])}
          assert len(ui_shared) >= 3, (
              f"模板间共享的基础 UI 变量不足 (需要 >=3，实际: {len(ui_shared)})。"
              f"共同变量: {sorted(all_common or [])}"
          )
  
  
  # ════════════════════════════════════════════════════════════
  # 模板内容注入模拟测试
  # ════════════════════════════════════════════════════════════
  
  class TestTemplateInjectionSimulation:
      """模拟动态内容注入到模板中，验证不会产生 XSS."""
  
      SIMPLE_SANITIZER = re.compile(r'[<>&"\']')
  
      @staticmethod
      def simple_escape(text: str) -> str:
          """简单的 HTML 转义 (模拟服务端/前端转义)."""
          return (
              text.replace("&", "&amp;")
              .replace("<", "&lt;")
              .replace(">", "&gt;")
              .replace('"', "&quot;")
              .replace("'", "&#39;")
          )
  
      @pytest.mark.parametrize("template_file", PLAZA_TEMPLATES)
      def test_injection_placeholders_exist(self, template_file):
          """模板应使用占位符（如 {{ }}）或 textContent 而非直接拼接用户输入."""
          variant = TemplateVariant(template_file)
          content = variant.content
          # 检查是否使用了常见的模板占位符
          has_template_syntax = bool(
              re.search(r'\{\{.*?\}\}', content) or  # Mustache/Handlebars
              re.search(r'\$\{.*?\}', content) or     # ES6 template literal (可能危险)
              'textContent' in content or
              'innerText' in content
          )
          # 不强制断言 — 有些模板可能用纯 JS 动态构建
          # 但推荐使用
  
      @pytest.mark.parametrize("payload", XSS_PAYLOADS)
      def test_escaped_payload_not_executable(self, payload):
          """转义后的 XSS 负载应被破坏标签结构，不可执行."""
          escaped = TestTemplateInjectionSimulation.simple_escape(payload)
          # 转义后，HTML 标签结构应被破坏：< 变成 &lt;，> 变成 &gt;
          # 因此不应存在未转义的尖括号标签（<tagname 或 </tagname）
          assert re.search(r'<\w+[\s>]', escaped) is None, (
              f"转义后仍存在未转义的 HTML 开始标签: {escaped}"
          )
          assert re.search(r'</\w+', escaped) is None, (
              f"转义后仍存在未转义的 HTML 结束标签: {escaped}"
          )
          # 不应存在未转义的事件处理器属性 (仅当标签结构完整时才危险)
          # 但这里的 on*= 在 &lt; 之后是安全的 — 只检查标签开始 < 是否被转义即可
          assert '&lt;' in escaped or '<' not in escaped, (
              f"转义后尖括号未正确处理: {escaped}"
          )
  
  
  # ════════════════════════════════════════════════════════════
  # 模板差异/回归测试
  # ════════════════════════════════════════════════════════════
  
  class TestTemplateRegression:
      """验证模板间的关系（主要模板 vs 变体）."""
  
      def test_main_plaza_is_largest(self):
          """主 plaza.html 通常是功能最全的模板."""
          sizes = {}
          for template_file in PLAZA_TEMPLATES:
              variant = TemplateVariant(template_file)
              sizes[template_file] = len(variant.content)
          # plaza.html 应是最复杂的
          main_size = sizes.get("plaza.html", 0)
          for name, size in sizes.items():
              if name != "plaza.html":
                  assert size > 100, f"{name} 文件过小 ({size} bytes)"
  
      def test_no_duplicate_ids_across_templates(self):
          """验证模板不包含重复的 HTML id（在各自上下文内）.
          
          已知问题记录: plaza.html 存在 assign-team 重复（模板内多次引用同一组件）.
          """
          id_pattern = re.compile(r'\bid\s*=\s*["\']([^"\']+)["\']')
          known_duplicates = {'assign-team'}  # plaza.html 已知重复，已在规划修复中
          all_findings = {}
          for template_file in PLAZA_TEMPLATES:
              variant = TemplateVariant(template_file)
              ids = id_pattern.findall(variant.content)
              duplicates = set(i for i in ids if ids.count(i) > 1)
              # 排除已知重复
              new_duplicates = duplicates - known_duplicates
              if new_duplicates:
                  all_findings[template_file] = new_duplicates
          assert len(all_findings) == 0, (
              f"发现新的重复 ID (需修复): {all_findings}"
          )
  
      def test_wabisabi_v2_vs_v1_structure(self):
          """wabisabi-v2 应保留 v1 的关键结构."""
          v1 = TemplateVariant("plaza-wabisabi.html")
          v2 = TemplateVariant("plaza-wabisabi-v2.html")
          # 两者都应包含 wabi-sabi 主题关键词
          v1_content = v1.content.lower()
          v2_content = v2.content.lower()
          assert 'wabi' in v1_content or 'wabi' in v2_content, "wabisabi 变体缺少主题关键词"
  
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
  
  ### 文件: `src/backend/agents/gate_evaluator.py`
  ```py
  # -*- coding: utf-8 -*-
  """门禁评估器 — 无状态纯函数 evaluate(context) → {score, level}.
  
  设计原则:
    - **纯函数**: 零外部依赖、零副作用、零 I/O
    - **确定性**: 相同输入产生相同输出
    - **幂等**: 多次调用结果一致
  
  评分算法:
    综合评分 = 加权平均(维度分数) − 否决项扣分
  
  维度权重 (对标 DNV CII 框架):
    - compliance_score:  25%  (合规评分)
    - test_pass_rate:     20%  (测试通过率)
    - code_quality_score: 20%  (代码质量)
    - security_issues:    15%  (安全扣分 → 线性映射)
    - documentation_level: 10% (文档完善度)
    - performance_impact:  10% (性能影响)
  
  否决项 (一票否决, score 强制 ≤ 39 = E 级):
    - has_critical_security_issue → 自动 E 级
    - has_breaking_change        → 自动 E 级
    - critical_test_failures > 0 → 自动 E 级
  """
  
  from __future__ import annotations
  
  import math
  from datetime import datetime, timezone
  from typing import Dict, List, Tuple
  
  from .review_models import GateEvaluationContext, GateEvaluationResult, GateLevel
  
  
  # ── 维度权重 (sum = 1.0) ────────────────────────────────────
  
  _DIMENSION_WEIGHTS: Dict[str, float] = {
      "compliance_score": 0.25,
      "test_pass_rate": 0.20,
      "code_quality_score": 0.20,
      "security_score": 0.15,          # security_issues 映射为安全分
      "documentation_level": 0.10,
      "performance_score": 0.10,       # performance_impact 映射
  }
  
  # 安全扣分阶梯 (security_issues → security_score)
  _SECURITY_PENALTY_MAP: Dict[int, float] = {
      0: 100.0,
      1: 70.0,
      2: 50.0,
      3: 30.0,
      4: 15.0,
  }
  _SECURITY_PENALTY_DEFAULT = 0.0  # ≥5 → 0 分
  
  # 性能影响映射 (-100~+100 → 0~100)
  #   +100 → 100 (显著优化)
  #     0 →  50 (中性)
  #   -100 →  0 (严重劣化)
  
  
  def evaluate(context: GateEvaluationContext) -> GateEvaluationResult:
      """门禁评估纯函数 — 根据上下文产出评分与等级.
  
      Args:
          context: 评估上下文，包含所有评估维度的量化数据
  
      Returns:
          GateEvaluationResult: {score, level, passed, reasons, warnings, blocked_by}
  
      使用示例:
          ctx = GateEvaluationContext(
              entity_id="EVO-1",
              compliance_score=88.0,
              test_pass_rate=95.0,
              code_quality_score=82.0,
          )
          result = evaluate(ctx)
          pri
  ```
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  
  ## 前序步骤的产出 (递进式摘要)
  
  ### 步骤 01: pm_decompose
  任务: pipeline验证测试
  步骤: pm_decompose
  📋 任务: 17d0eaa2-bd5
  🤖 Agent: PM (project_manager)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ────────────────────────────────────────────────────────────
  你是 AgentsGroup2026 系统的 PM (project_manager)。
  你是项目经理 (PM)。请对以下任务进行分解和规划:
  验证QA gate修复: 当QA verdict=PASS时pipeline不应该被阻断
  ## 📂 项目上下文 (系统自动预加载)
  ### 项目文件结构 (src/ 目录)
  ### 文件: `src/frontend/js/i18n.js`
  ### 文件: `src/backend/tests/test_gate_evaluator.py`
  ### 文件: `src/backend/tests/test_template_variants.py`
  **变更文件 (1):**
    - `src/backend/agents/gate_evaluator.py`
  **子任务拆解:**
    - **目标**：确保当 QA 门禁（Gate）判定为 `PASS`（即 `GateEvaluationResult.passed == True`）时，下游流水线（Pipeline）**不会被阻断**。
    - **背景**：系统中可能存在逻辑错误，导致尽管 QA 给出了“通过”结论，流水线仍然因门禁结果被误判而中断。需要验证这一问题已被修复，或定位残留缺陷。
    - *子任务 0.1** 理解门禁评估器逻辑  
    - 阅读 `src/backend/agents/gate_evaluator.py`，确认 `evaluate()` 函数何时返回 `passed=True`/`passed=False`。  
    - 明确一票否决项（严重安全漏洞、破坏性变更、关键测试失败）会强制 `passed=False`。  
    - 确认当无否决项且综合评分 ≥40 时，结果为通过。  
    - *子任务 0.2** 梳理流水线集成点  
    - 搜索项目中所有引用 `GateEvaluationResult`、`evaluate`、`gate`、`pipeline` 的代码（如 `src/backend/agents/task_engine.py`、`src/backend/channels/merge_channel.py` 等）。  
  
  ### 步骤 02: research (完整产出)
  
  # 研究分析 — researcher
  
  任务: pipeline验证测试
  步骤: research
  Agent: build_researcher
  
  ---
  
  📋 任务: 17d0eaa2-bd5
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
    pipeline验证测试
    验证QA gate修复: 当QA verdict=PASS时pipeline不应该被阻断
    
    ## 📂 项目上下文 (系统自动预加载)
    
    ### 项目文件结构 (src/ 目录)
    ```
    src/frontend/agent-team-config.html
    src/frontend/index.html
    src/frontend/login.html
    src/frontend/monitoring.html
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
    src/backend/tests/test_evolution_race.py
    src/backend/tests/test_evolution_race.py.bak
    src/backend/tests/test_fingerprint.py
    src/backend/tests/test_fingerprint.py.bak
    src/backend/tests/test_gate_evaluator.py
    src/backend/tests/test_merge_plugin.py
    src/backend/tests/test_merge_plugin.py.bak
    src/backend/tests/test_models.py
    src/backend/tests/test_models.py.bak
    src/backend/tests/test_task_engine.py
    src/backend/tests/test_task_engine.py.bak
    src/backend/tests/test_team_manager.py
    src/backend/tests/test_team_manager.py.bak
    src/backend/tests/test_template_variants.py
    src/backend/tests/test_template_variants.py.bak
    src/backend/agents/__init__.py
    src/backend/agents/ab_testing.py
    src/backend/agents/agent_loop.py
    src/backend/agents/agent_toolbox.py
    src/backend/agents/api.py
    src/backend/agents/api.py.bak
    src/backend/agents/audit_store.py
    src/backend/agents/chat_harness.py
    src/backend/agents/domain_events.py
    src/backend/agents/domain_events.py.bak
    src/backend/agents/event_bus.py
    src/backend/agents/execution_registry.py
    src/backend/agents/fingerprint.py
    src/backend/agents/fingerprint.py.bak
    src/backend/agents/gate_evaluator.py
    src/backend/agents/hermes_research.py
    src/backend/agents/knowledge_base.py
    src/backend/agents/merge_engine.py
    src/backend/agents/merge_models.py
    src/backend/agents/models.py
    src/backend/agents/models.py.bak
    src/backend/agents/plaza.py
    src/backend/agents/plaza_engine.py
    src/backend/agents/plaza_routes.py
    src/backend/agents/plaza_routes.py.bak
    src/backend/agents/plaza_store.py
    src/backend/agents/review_models.py
    src/backend/agents/review_routes.py
    src/backend/agents/review_service.py
    src/backend/agents/session_store.py
    src/backend/agents/similarity_engine.py
    src/backend/agents/skill_extractor.py
    src/backend/agents/skill_indexer.py
    src/backend/agents/skill_querier.py
    src/backend/agents/skill_registry.py
    src/backend/agents/skill_store.py
    src/backend/agents/task_engine.py
    src/backend/agents/task_engine.py.bak
    src/backend/agents/task_store.py
    src/backend/agents/team_manager.py
    src/backend/agents/team_manager.py.bak
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
    src/backend/scripts/migrate.py
    src/backend/scripts/validate_startup.py
    src/backend/scripts/validate_telemetry.py
    src/backend/monitoring/__init__.py
    src/backend/monitoring/__init__.py.bak
    src/backend/monitoring/aggregation_window.py
    src/backend/monitoring/aggregation_window.py.bak
    src/backend/monitoring/collector.py
    src/backend/monitoring/collector.py.bak
    src/backend/monitoring/fingerprint_bypass.py
    src/backend/monitoring/models.py
    src/backend/monitoring/models.py.bak
    src/backend/monitoring/monitoring_routes.py
    src/backend/monitoring/plaza_monitor.py
    src/backend/monitoring/plaza_monitor.py.bak
    src/backend/monitoring/sampler.py
    src/backend/monitoring/trace_bridge.py
    src/backend/channels/__init__.py
    src/backend/channels/bridge_chat.py
    src/backend/channels/evolution_executor.py
    src/backend/channels/marine_base.py
    src/backend/channels/merge_channel.py
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
    src/docs/agent_handoffs/11e9b4b9-283_architecture_20260509T075556.md
    src/docs/agent_handoffs/11e9b4b9-283_deploy_20260509T081242.md
    src/docs/agent_handoffs/11e9b4b9-283_develop_20260509T080722.md
    src/docs/agent_handoffs/11e9b4b9-283_document_20260509T081332.md
    src/docs/agent_handoffs/11e9b4b9-283_executor_started_20260509T074916.md
    src/docs/agent_handoffs/11e9b4b9-283_pipeline_complete_20260509T081332.md
    src/docs/agent_handoffs/11e9b4b9-283_pm_decompose_20260509T075116.md
    src/docs/agent_handoffs/11e9b4b9-283_research_20260509T075401.md
    src/docs/agent_handoffs/11e9b4b9-283_test_20260509T081127.md
    src/docs/agent_handoffs/1356f045-d02_executor_started_20260509T073232.md
    src/docs/agent_handoffs/15554439-6aa_executor_started_20260509T073231.md
    src/docs/agent_handoffs/15a7e2eb-cd1_executor_started_20260509T073232.md
    src/docs/agent_handoffs/18d4b20f-c33_executor_started_20260509T073231.md
    src/docs/agent_handoffs/1aed56ed-eda_executor_started_20260509T073232.md
    src/docs/agent_handoffs/1cc2c0fb-90b_executor_started_20260509T073232.md
    src/docs/agent_handoffs/1ce78c0e-062_architecture_20260503T045804.md
    ... (共 697 个 src/ 文件)
    
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
    
    ### 文件: `src/backend/tests/test_gate_evaluator.py`
    ```py
    # -*- coding: utf-8 -*-
    """测试门禁评估器 — evaluate(context) 纯函数测试.
    
    覆盖:
      - 正常评估 (A/B/C 级)
      - 一票否决 (安全漏洞/破坏性变更/关键测试失败)
      - 边界情况 (0分/100分/缺失字段)
      - 确定性 (相同输入 → 相同输出)
      - 便捷函数 evaluate_from_dict / quick_evaluate
    """
    
    from __future__ import annotations
    
    import pytest
    
    from agents.gate_evaluator import (
        evaluate,
        evaluate_from_dict,
        quick_evaluate,
        _calculate_dimension_scores,
        _compute_weighted_score,
        _map_security_issues_to_score,
        _map_performance_impact,
    )
    from agents.review_models import GateEvaluationContext, GateLevel, GateEvaluationResult
    
    
    class TestGateEvaluator:
        """门禁评估器核心测试."""
    
        # ── 正常评估 ────────────────────────────────────────
    
        def test_evaluate_all_excellent(self):
            """全部优秀 → A级, passed."""
            ctx = GateEvaluationContext(
                entity_id="EVO-1",
                compliance_score=95.0,
                test_pass_rate=100.0,
                code_quality_score=95.0,
                security_issues=0,
                documentation_level=95.0,
                performance_impact=20.0,
            )
            result = evaluate(ctx)
            assert result.level == GateLevel.A
            assert result.passed is True
            assert result.score >= 85.0
            assert len(result.blocked_by) == 0
    
        def test_evaluate_good(self):
            """良好 → B级, passed."""
            ctx = GateEvaluationContext(
                entity_id="EVO-2",
                compliance_score=78.0,
                test_pass_rate=88.0,
                code_quality_score=75.0,
                security_issues=1,
                documentation_level=70.0,
                performance_impact=5.0,
            )
            result = evaluate(ctx)
            assert result.level in (GateLevel.B, GateLevel.C)
            assert result.passed is True
    
        def test_evaluate_moderate(self):
            """基本合规 → C级, passed."""
            ctx = GateEvaluationContext(
                entity_id="EVO-3",
                compliance_score=60.0,
                test_pass_rate=70.0,
                code_quality_score=58.0,
                security_issues=3,
                documentation_level=50.0,
                performance_impact=-5.0,
            )
            result = evaluate(ctx)
            assert result.level in (GateLevel.C, GateLevel.D)
            assert result.passed == (result.level != GateLevel.D)
    
        # ── 一票否决 ────────────────────────────────────────
    
        def test_veto_critical_security(self):
            """严重安全漏洞 → E级, score=0."""
            ctx = GateEvaluationContext(
                entity_id="EVO-sec",
                compliance_score=95.0,
                test_pass_rate=100.0,
                code_quality_score=95.0,
                has_critical_security_issue=True,
            )
            result = evaluate(ctx)
            assert result.level == GateLevel.E
            assert result.passed is False
            assert result.score == 0.0
            assert len(result.blocked_by) > 0
            assert any("安全" in b for b in result.blocked_by)
    
        def test_veto_breaking_change(self):
            """破坏性变更 → E级, score=0."""
            ctx = GateEvaluationContext(
                entity_id="EVO-break",
                compliance_score=90.0,
                has_breaking_change=True,
            )
            result = evaluate(ctx)
            assert result.level == GateLevel.E
            assert result.passed is False
            assert result.score == 0.0
    
        def test_veto_critical_test_failures(self):
            """关键测试失败 → E级, score=0."""
            ctx = GateEvaluationContext(
                entity_id="EVO-fail",
                compliance_score=88.0,
                critical_test_failures=2,
            )
            result = evaluate(ctx)
            assert result.level == GateLevel.E
            assert result.passed is False
            assert result.score == 0.0
    
        def test_multiple_vetos(self):
            """多个否决项同时触发."""
            ctx = GateEvaluationContext(
                entity_id="EVO-multi",
                has_critical_security_issue=True,
                has_breaking_change=True,
                critical_test_failures=1,
            )
            result = evaluate(ctx)
            assert len(result.blocked_by) == 3
    
        # ── 边界情况 ────────────────────────────────────────
    
        def test_zero_scores(self):
            """全0分 → E级."""
            ctx = GateEvaluationContext(entity_id="EVO-zero")
            result = evaluate(ctx)
            assert 0.0 <= result.score <= 40.0
            assert result.level in (GateLevel.D, GateLevel.E)
    
        def test_perfect_scores(self):
            """满分 → A级."""
            ctx = GateEvaluationContext(
                entity_id="EVO-perfect",
                compliance_score=100.0,
                test_pass_rate=100.0,
                code_quality_score=100.0,
                security_issues=0,
                documentation_level=100.0,
                performance_impact=100.0,
            )
            result = evaluate(ctx)
            assert result.level == GateLevel.A
            assert result.score >= 95.0
    
        def test_high_security_issues(self):
            """大量安全问题 → 安全评分归零."""
            ctx = GateEvaluationContext(
                entity_id="EVO-badsec",
                compliance_score=80.0,
                test_pass_rate=90.0,
                code_quality_score=80.0,
                security_issues=10,
            )
            result = evaluate(ctx)
            # 安全占15%权重，大量问题拉低总分
            assert result.score < 70.0
    
        def test_negative_performance(self):
            """严重性能退化."""
            ctx = GateEvaluationContext(
                entity_id="EVO-perf",
                compliance_score=80.0,
                test_pass_rate=90.0,
                code_quality_score=80.0,
                security_issues=0,
                performance_impact=-80.0,
            )
            result = evaluate(ctx)
            # 性能评分应低于50
            assert result.score < 80.0
    
        # ── 确定性 ──────────────────────────────────────────
    
        def test_deterministic(self):
            """相同输入 → 相同输出 (纯函数)."""
            ctx = GateEvaluationContext(
                entity_id="EVO-det",
                compliance_score=75.0,
                test_pass_rate=85.0,
                code_quality_score=70.0,
                security_issues=1,
            )
            results = [evaluate(ctx) for _ in range(20)]
            scores = {r.score for r in results}
            levels = {r.level for r in results}
            assert len(scores) == 1
            assert len(levels) == 1
    
        # ── 便捷函数 ────────────────────────────────────────
    
        def test_evaluate_from_dict(self):
            result = evaluate_from_dict({
                "entity_id": "EVO-dict",
                "compliance_score": 65.0,
                "test_pass_rate": 75.0,
                "code_quality_score": 68.0,
            })
            assert isinstance(result, GateEvaluationResult)
            assert result.entity_id is None  # entity_id 不在 result 中
            assert result.score is not None
    
        def test_quick_evaluate(self):
            result = quick_evaluate(
                entity_id="EVO-quick",
                compliance_score=72.0,
                test_pass_rate=88.0,
                code_quality_score=75.0,
            )
            assert isinstance(result, GateEvaluationResult)
            assert 60.0 <= result.score <= 90.0
    
        def test_quick_evaluate_with_veto(self):
            result = quick_evaluate(
                entity_id="EVO-quick-veto",
                compliance_score=90.0,
                has_critical_security_issue=True,
            )
            assert result.level == GateLevel.E
            assert result.passed is False
    
    
    class TestDimensionScoring:
        """维度评分辅助函数测试."""
    
        def test_security_map_zero(self):
            assert _map_security_issues_to_score(0) == 100.0
    
        def test_security_map_one(self):
            assert 60.0 <= _map_security_issues_to_score(1) <= 80.0
    
        def test_security_map_many(self):
            assert _map_security_issues_to_score(5) == 0.0
            assert _map_security_issues_to_score(10) == 0.0
    
        def test_performance_map_positive(self):
            assert _map_performance_impact(100.0) == 100.0
    
        def test_performance_map_neutral(self):
            assert _map_performance_impact(0.0) == 50.0
    
        def test_performance_map_negative(self):
            assert _map_performance_impact(-100.0) == 0.0
    
        def test_weighted_score(self):
            scores = {
                "compliance_score": 80.0,
                "test_pass_rate": 90.0,
                "code_quality_score": 80.0,
                "security_score": 100.0,
                "documentation_level": 70.0,
                "performance_score": 60.0,
            }
            result = _compute_weighted_score(scores)
            assert 70.0 <= result <= 90.0
    
    
    class TestGateLevel:
        """等级映射测试."""
    
        def test_from_score_A(self):
            assert GateLevel.from_score(95.0) == GateLevel.A
            assert GateLevel.from_score(85.0) == GateLevel.A
    
        def test_from_score_B(self):
            assert GateLevel.from_score(84.9) == GateLevel.B
            assert GateLevel.from_score(70.0) == GateLevel.B
    
        def test_from_score_C(self):
            assert GateLevel.from_score(69.9) == GateLevel.C
            assert GateLevel.from_score(55.0) == GateLevel.C
    
        def test_from_score_D(self):
            assert GateLevel.from_score(54.9) == GateLevel.D
            assert GateLevel.from_score(40.0) == GateLevel.D
    
        def test_from_score_E(self):
            assert GateLevel.from_score(39.9) == GateLevel.E
            assert GateLevel.from_score(0.0) == GateLevel.E
    
    ```
    
    ### 文件: `src/backend/tests/test_template_variants.py`
    ```py
    # -*- coding: utf-8 -*-
    """模板变体注入测试 — Plaza 多模板 XSS、结构完整性及 CSS 一致性验证.
    
    覆盖:
    - 所有 Plaza 模板 (wabisabi, wabisabi-v2, dark, old, main)
    - XSS 注入抵抗 (script/event-handler 不会被嵌入)
    - HTML 结构完整性 (必需 DOM 元素存在)
    - CSS 变量命名一致性
    """
    
    from __future__ import annotations
    
    import html.parser
    import os
    import re
    import json
    from pathlib import Path
    from typing import List, Set
    
    import pytest
    
    
    # ── 模板清单 ────────────────────────────────────────────
    
    FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
    
    PLAZA_TEMPLATES = [
        "plaza.html",
        "plaza-dark.html",
        "plaza-old.html",
        "plaza-wabisabi.html",
        "plaza-wabisabi-v2.html",
    ]
    
    # ── XSS 注入负载 ────────────────────────────────────────
    
    XSS_PAYLOADS = [
        '<script>alert("xss")</script>',
        '<img src=x onerror=alert(1)>',
        '<svg onload=alert(1)>',
        'javascript:alert(1)',
        '<body onload=alert(1)>',
        '"-prompt(1)-"',
        "'-prompt(1)-'",
        '<iframe src="javascript:alert(1)">',
        '<a href="javascript:alert(1)">click</a>',
        '<div onclick="alert(1)">click</div>',
    ]
    
    # ── 必需 DOM 元素 (每个 Plaza 页面应包含的关键结构) ──
    
    REQUIRED_ELEMENTS = [
        "<html",
        "<head",
        "<body",
        "plaza",
        "讨论",  # 讨论管理功能
        "智能体",
    ]
    
    # ── CSS 变量命名规范 ─────────────────────────────────────
    
    CSS_VAR_PATTERN = re.compile(r'--[a-z][a-z0-9-]*', re.IGNORECASE)
    
    # 已知合法的 Plaza CSS 变量前缀
    KNOWN_PREFIXES = [
        '--bg', '--fg', '--card', '--line', '--dim', '--muted',
        '--accent', '--accent-', '--lime', '--gold', '--rose', '--sky',
        '--pink', '--purple', '--cyan', '--amber',
        '--inner', '--mid', '--outer', '--moderator',
        '--niche', '--seat', '--ring',
        '--wabi', '--ando', '--concrete',
        '--font', '--radius', '--shadow',
    ]
    
    
    class TemplateVariant:
        """表示一个 Plaza 模板变体."""
    
        def __init__(self, filename: str):
            self.filename = filename
            self.path = FRONTEND_DIR / filename
            self._content: str = ""
            self._css_vars: Set[str] = set()
            self._loaded = False
    
        def load(self) -> str:
            """加载模板内容."""
            if not self._loaded:
                if self.path.exists():
                    self._content = self.path.read_text(encoding="utf-8")
                else:
                    self._content = ""
                self._loaded = True
            return self._content
    
        @property
        def content(self) -> str:
            return self.load()
    
        @property
        def css_variables(self) -> Set[str]:
            if not self._css_vars and self.content:
                self._css_vars = set(CSS_VAR_PATTERN.findall(self.content))
            return self._css_vars
    
    
    # ════════════════════════════════════════════════════════════
    # 模板加载与基础结构测试
    # ════════════════════════════════════════════════════════════
    
    class TestTemplateLoading:
        """验证所有 Plaza 模板文件存在且可读."""
    
        @pytest.mark.parametrize("template_file", PLAZA_TEMPLATES)
        def test_template_exists(self, template_file):
            """每个模板文件应当存在."""
            path = FRONTEND_DIR / template_file
            assert path.exists(), f"模板文件不存在: {template_file}"
            assert path.stat().st_size > 0, f"模板文件为空: {template_file}"
    
        @pytest.mark.parametrize("template_file", PLAZA_TEMPLATES)
        def test_template_is_valid_html_like(self, template_file):
            """每个模板应包含基本 HTML 结构."""
            variant = TemplateVariant(template_file)
            content = variant.content
            # 检查 HTML doctype 或 html 标签
            has_doctype = "<!DOCTYPE html>" in content or "<!DOCTYPE HTML>" in content.upper()
            has_html_tag = "<html" in content
            has_head_tag = "<head" in content
            has_body_tag = "<body" in content
            assert has_doctype or has_html_tag, f"{template_file}: 缺少 DOCTYPE 或 <html>"
            assert has_head_tag, f"{template_file}: 缺少 <head>"
            assert has_body_tag, f"{template_file}: 缺少 <body>"
    
        @pytest.mark.parametrize("template_file", PLAZA_TEMPLATES)
        def test_template_has_required_elements(self, template_file):
            """每个模板应包含 Plaza 关键功能元素."""
            variant = TemplateVariant(template_file)
            content = variant.content
            # 至少包含 "plaza" 关键词（可变体不同命名）
            plaza_related = any(
                kw in content.lower()
                for kw in ['plaza', '智能体广', '智能体広', '讨论', 'discuss', 'agent']
            )
            assert plaza_related, f"{template_file}: 未发现 Plaza/讨论相关关键词"
    
    
    # ════════════════════════════════════════════════════════════
    # XSS 注入抵抗测试
    # ════════════════════════════════════════════════════════════
    
    class TestTemplateXSSResistance:
        """验证模板不会直接输出 XSS 负载（静态模板层面）."""
    
        @pytest.mark.parametrize("template_file", PLAZA_TEMPLATES)
        def test_no_inline_event_handlers(self, template_file):
            """模板不应包含内联事件处理器 (onclick=, onerror= 等) 用于动态注入点."""
            variant = TemplateVariant(template_file)
            content = variant.content
            # 查找 event handler 模式
            event_pattern = re.compile(r'\bon[a-z]+\s*=\s*["\']', re.IGNORECASE)
            matches = event_pattern.findall(content)
            # 允许少量固有的（如页面切换 onclick），但不应过多
            assert len(matches) < 50, (
                f"{template_file}: 发现 {len(matches)} 个内联事件处理器，"
                f"需审查是否安全: {matches[:10]}"
            )
    
        @pytest.mark.parametrize("template_file", PLAZA_TEMPLATES)
        def test_no_eval_or_innerhtml_direct(self, template_file):
            """模板中不应直接使用 eval() 或 innerHTML 赋值原始用户内容."""
            variant = TemplateVariant(template_file)
            content = variant.content
            # 检查 eval(
            assert "eval(" not in content, (
                f"{template_file}: 发现 eval() 调用"
            )
            # innerHTML 使用是可接受的，但需确认上下文
            # 此处仅报告，不阻断
            inner_html_count = len(re.findall(r'\.innerHTML\s*=', content))
            if inner_html_count > 0:
                # 警告级别：innerHTML 需 textContent 或 DOMPurify 保护
                pass  # 仅记录
    
        @pytest.mark.parametrize("template_file", PLAZA_TEMPLATES)
        def test_no_document_write(self, template_file):
            """模板不应使用 document.write (现代 HTML 规范禁止)."""
            variant = TemplateVariant(template_file)
            content = variant.content
            assert "document.write" not in content, (
                f"{template_file}: 发现 document.write() 调用"
            )
    
    
    # ════════════════════════════════════════════════════════════
    # CSS 变量一致性测试
    # ════════════════════════════════════════════════════════════
    
    class TestCSSVariableConsistency:
        """验证 Plaza 模板间 CSS 变量命名一致性."""
    
        def test_all_templates_have_css_variables(self):
            """所有模板应定义 CSS 自定义变量."""
            for template_file in PLAZA_TEMPLATES:
                variant = TemplateVariant(template_file)
                assert len(variant.css_variables) > 0, (
                    f"{template_file}: 未定义任何 CSS 变量"
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

# 技术方案：QA Gate 修复验证（PASS 不阻断流水线）

**方案版本**: 1.0  
**作者**: 系统架构师 (architect)  
**日期**: 2025-05-09  
**背景**: 验证已有修复或诊断残留缺陷，确保当 QA 门禁 (GateEvaluator) 判定为 `PASS`（即 `GateEvaluationResult.passed == True`）时，下游流水线 **不会被错误阻断**。

---

## 1. 目标与范围

- **验证目标**:  
  构造 PASS / FAIL 场景，驱动真实流水线运行（或单元化模拟），断言 PASS 场景下流水线继续执行，FAIL 场景下流水线被阻断。  
- **修复目标**:  
  若验证发现 PASS 场景仍被阻断，定位逻辑反转或误判代码并修正。  
- **范围**:  
  - `src/backend/agents/gate_evaluator.py` – 门禁纯函数（已验证正确性）  
  - `src/backend/agents/review_models.py` – `GateEvaluationResult` 数据模型  
  - **流水线调度代码**（待定位：`task_engine.py`, `merge_channel.py`, `system_evolution.py` 等）– 引用 `GateEvaluationResult` 并决策继续/阻断的部分  
  - 相关测试文件：`src/backend/tests/test_gate_evaluator.py` 以及新编写的流水线集成测试。

---

## 2. 现状分析

### 2.1 Gate Evaluator 行为

`evaluate(context)` 返回 `GateEvaluationResult`，其中关键字段：

- `score: float` – 综合评分（0~100）  
- `level: GateLevel` – A/B/C/D/E  
- `passed: bool` – 当 **无一票否决** 且 **综合评分 ≥ 40 (即 level ≤ D?)** 时为 `True`，否则 `False`  
- `blocked_by: List[str]` – 否决理由

详细规则（来自现有测试和源码）：

- 一票否决（`passed=False`，`score=0.0`）：  
  `has_critical_security_issue=True`  
  `has_breaking_change=True`  
  `critical_test_failures > 0`  
- 无否决时，基于加权平均分定级：
  - ≥ 85 → A（passed）  
  - 70-84 → B（passed）  
  - 55-69 → C（passed）  
  - 40-54 → D（**passed=?** 待确认）  
  - <40 → E（failed）

> ⚠️ 注意: 现有测试 `test_evaluate_moderate` 中有 `assert result.passed == (result.level != GateLevel.D)`，暗示 **D 级可能视为不通过**？需要结合 `GateLevel` 的 `from_score` 方法和 `passed` 判定逻辑确认。若 D 级对应 40-54 分，而 passed 条件为 `score >= 40` 且无否决，那么 D 级应为 PASS。若测试断言相反，可能是历史遗留或代码 bug 之一，需核实并统一。

### 2.2 流水线集成点

PM 分解建议搜索以下文件中的集成点：

- `src/backend/agents/task_engine.py` – 执行 agent 任务时的 gate 检查  
- `src/backend/channels/merge_channel.py` – 合并通道中的 gate  
- `src/backend/channels/system_evolution.py` – 系统演进流程  
- `src/backend/channels/evolution_executor.py` – 进化执行器

这些位置可能通过 `from agents.gate_evaluator import evaluate` 获取结果，并使用 `result.passed` 条件。潜在的误阻断模式包括：

- 直接使用 `if not result.passed: raise BlockException`（正确）  
- 错误使用 `if result.level == GateLevel.E`（但忽略 D 级可能也阻断）  
- 忽略 `result.passed` 而仅检查 `score < 60` 等额外条件  
- 条件反转：`if result.passed: block()`（低级错误）

### 2.3 现有测试覆盖

`test_gate_evaluator.py` 覆盖了评估器本身的 `passed` 逻辑，**但不包含流水线集成场景**。因此需要新增集成测试。

---

## 3. 修复 & 验证方案设计

### 3.1 第一步：定位流水线门禁消费代码

使用 `grep` 或代码搜索（AgentToolbox 可用）找出所有引用 `passed` 或 `GateEvaluationResult` 的位置：

```bash
grep -rn "GateEvaluationResult\|\.passed\|gate_evaluator\|evaluate(" src/backend/ --include="*.py" | grep -v test_
```

**预期结果**：列出所有消费 gate 结果的文件和行号。

### 3.2 第二步：审查流水线条件逻辑

逐个检查：

- 是否使用 `result.passed` 作为门禁条件？  
- 条件逻辑是否正确（`passed` → 继续，`not passed` → 阻断）？  
- 是否有额外的分数/等级判断覆盖了 `passed` ？  

**潜在缺陷示例**：

```python
# 错误 1：使用 level 但未正确处理 D 级
if gate.level in (GateLevel.D, GateLevel.E):
    block()
# 若 D 级实际为 PASS，则会导致 PASS（D）被阻断。

# 错误 2：重复判断导致冲突
if gate.passed and gate.score < 60:
    block()   # 若 passed 为 True 则 score 必然 ≥ 40，但可能误判
```

### 3.3 第三步：设计集成测试（待编写）

**测试框架**：`pytest`，挂接 `conftest.py` fixture 模拟上下文。

**测试用例**：

| 用例 ID | 场景描述 | Gate 输入 | 预期流水线行为 |
|--------|---------|----------|--------------|
| PIPE-01 | A 级全优 | compliance=95, test_pass=100, … | 继续执行 |
| PIPE-02 | B 级良好 | compliance=78, test_pass=88, security_issues=1 | 继续执行 |
| PIPE-03 | C 级基本 | compliance=60, security_issues=3 | 继续执行 |
| PIPE-04 | D 级临界（根据 passed 定义） | compliance=50, … 无否决 | **需先确认 D 级 passed 定义**，若应通过则继续；否则阻断 |
| PIPE-05 | E 级失败 | score <40（无否决） | 阻断 |
| PIPE-06 | 一票否决‑严重安全 | has_critical_security_issue=True | 阻断 |
| PIPE-07 | 一票否决‑破坏性变更 | has_breaking_change=True | 阻断 |
| PIPE-08 | 一票否决‑关键测试失败 | critical_test_failures>0 | 阻断 |
| PIPE-09 | PASS 但 score 刚好 40 | score 计算后恰好 40, 无否决 | 继续（如果 passed=True） |
| PIPE-10 | 多否决同时 | multiple veto flags | 阻断并上报所有 blocked_by |

**集成测试实现方式**：

- 使用 **monkeypatching** 或 **依赖注入** 替换真实的 `evaluate()` 调用，返回预先构造的 `GateEvaluationResult`，然后执行流水线入口函数，检查其是否抛出阻断异常或继续执行。  
- 建议在 `test_gate_evaluator.py` 同级新建 `test_gate_pipeline_integration.py`，复用 `conftest.py` 的测试环境。

**示例代码骨架**：

```python
# test_gate_pipeline_integration.py
import pytest
from agents.gate_evaluator import GateEvaluationResult, GateLevel
from agents.task_engine import execute_task   # 假设有此入口
from unittest.mock import patch

PASS_RESULT = GateEvaluationResult(
    score=85.0, level=GateLevel.A, passed=True, blocked_by=[]
)

def test_pipeline_does_not_block_on_pass(monkeypatch):
    # 模拟 gate 返回 PASS
    monkeypatch.setattr(
        "agents.task_engine.evaluate", lambda ctx: PASS_RESULT
    )
    # 假设 execute_task 内部会调用 evaluate，若阻断则 raise PipelineBlocked
    try:
        execute_task(some_task_context)
    except PipelineBlocked:
        pytest.fail("流水线在 PASS 时不应被阻断")
```

### 3.4 第四步：修复代码（如需要）

若发现流水线中的逻辑错误，应用 **最小修正**：

1. **统一门禁策略**：明确 D 级（40-54 分）是否通过。建议 `passed` 定义为：`not any_veto and score >= 40`，即 D 级为通过（低风险谨慎通过，可附加警告）。修改 `gate_evaluator.py` 中的 `passed` 计算，更新对应测试。  
2. **修正错误的阻断条件**：将 `if result.level in (D, E)` 改为 `if not result.passed`，或根据上述统一策略调整。  
3. **添加日志**：在阻断点打印 `result.blocked_by` 详情，便于运维。

### 3.5 第五步：回归测试与验证

运行全部相关测试：

```bash
cd src/backend
python -m pytest tests/test_gate_evaluator.py tests/test_gate_pipeline_integration.py -v
```

预期结果：

- 原有 `test_gate_evaluator.py` 全部通过（若未修改过 `evaluate`）  
- 新增集成测试通过，覆盖所有 PASS/FAIL 场景  
- 流水线行为与 `passed` 字段严格一致

---

## 4. 接口规范（无新增 API）

本任务不涉及新增 API，仅修正内部逻辑。数据模型 `GateEvaluationResult` 保持不变，接口契约：

- `passed: bool` – 当且仅当无否决且综合评分 ≥ 40 时为 `True`  
- 流水线消费者应 **仅通过 `result.passed` 判断**，禁止自行推断等级

---

## 5. 实施步骤（开发工程师指南）

1. **代码扫描**  
   - 在项目根执行：  
     `grep -r "GateEvaluationResult\|\.passed" src/backend/agents/ src/backend/channels/ --include="*.py"`  
   - 记录所有使用 `passed` 或等级判断的文件与行号。

2. **逻辑审查**  
   - 打开每个文件，确认阻断/放行逻辑是否与 `result.passed` 一致。  
   - 列出所有可疑点，与架构师确认 D 级通过策略。

3. **修正（若需要）**  
   - 在 `gate_evaluator.py` 中明确 `passed` 逻辑（仅修改此处以全局生效）。  
   - 在任何误阻断点替换为 `if not result.passed: block()`。  
   - 添加 Info 日志输出阻断原因。

4. **编写集成测试**  
   - 创建 `test_gate_pipeline_integration.py`，按 3.3 节表格编写 8-10 个用例。  
   - 使用 `monkeypatch` 模拟 `evaluate` 返回，确保测试不依赖真实外部状态。

5. **运行测试**  
   - 执行 `pytest -v tests/test_gate_evaluator.py tests/test_gate_pipeline_integration.py`  
   - 修复出现的失败，直至全绿。

6. **代码评审 & 上线**  
   - 提交 PR，附带测试结果截图。  
   - 合并后，在 Staging 环境手动触发一次演练：创建一个实体，确保其通过 QA gate，观察流水线状态。

---

## 6. 风险与回滚计划

- **风险 1**: 修改 `passed` 的判定可能影响已运行任务的历史数据——但 `passed` 为实时计算，无持久化依赖，风险可控。  
- **风险 2**: 集成测试可能因 mock 不匹配而遗漏真实集成问题。可在验收阶段增加一次 **端到端手动测试**：真实调用 `evaluate` 并检查后续任务状态。  
- **回滚**: 若修复导致新问题，回退 `gate_evaluator.py` 及相关流水线文件的改动，保留新增测试用于回归。

---

## 7. 附录：D 级通过策略建议

根据行业通行做法（如 DNV 等级），评分 40-54 视为“有条件通过”，建议 `passed=True`，但增加 `warnings` 提示“接近失败门限”。修改 `evaluate()` 在构建 `GateEvaluationResult` 时，若 `score < 55` 且 `passed=True` 则附加警告文本。此改进不强制，可在本任务之后作为增强。

---

**方案批准**：请 PM / Tech Lead 确认 D 级通过策略及集成测试范围后进入开发。

────────────────────────────────────────────────────────────
✅ deepseek-v4-pro 完成
