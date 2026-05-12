# 架构设计 — architect

任务: 构建聚合窗口引擎：基于滑动窗口的状态管理、持久化、双写过渡机制、窗口边界语义控制
步骤: architecture
Agent: build_architect

---

📋 任务: de6f9126-072
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
  构建聚合窗口引擎：基于滑动窗口的状态管理、持久化、双写过渡机制、窗口边界语义控制
  Architect, Developer
  
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
  src/docs/agent_handoffs/3f9494e1-96d_executor_started_20260509T074916.md
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
  ... (共 505 个 src/ 文件)
  
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
          return {"status": "already_running", "pid": _tts_process
  ```
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  
  ## 前序步骤的产出 (递进式摘要)
  
  ### 步骤 01: pm_decompose
  任务: 构建聚合窗口引擎：基于滑动窗口的状态管理、持久化、双写过渡机制、窗口边界语义控制
  步骤: pm_decompose
  📋 任务: de6f9126-072
  🤖 Agent: PM (project_manager)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ────────────────────────────────────────────────────────────
  你是 AgentsGroup2026 系统的 PM (project_manager)。
  你是项目经理 (PM)。请对以下任务进行分解和规划:
  构建聚合窗口引擎：基于滑动窗口的状态管理、持久化、双写过渡机制、窗口边界语义控制
  Architect, Developer
  ## 📂 项目上下文 (系统自动预加载)
  ### 项目文件结构 (src/ 目录)
  ### 文件: `src/frontend/js/i18n.js`
  ### 文件: `src/frontend/js/nav-sidebar.js`
  **子任务拆解:**
    - *目标**：构建一套可复用的**聚合窗口引擎**（Aggregation Window Engine），为监控指标、事件流等场景提供基于滑动窗口的状态管理、持久化、双写过渡及窗口边界语义控制能力。引擎需与现有监控采集管线 (`backend/monitoring/`) 无缝集成，支持在未来平滑替换旧版聚合逻辑。
    - 后端 Python 模块 (`src/backend/monitoring/aggregation_window.py`)  
    - 相关单元测试 (`src/backend/tests/test_aggregation_window.py`)  
    - 与 `collector.py`、`plaza_monitor.py` 的集成适配  
    - *相关文件**（已存在）  
    - 滑动窗口聚合：求 SUM/AVG/COUNT/MAX/MIN 等，支持时间窗（Tumbling/Sliding/Session）和计数窗。  
    - 状态管理：内存高效，需支持故障恢复（从持久化重建）。  
    - 双写过渡：新旧聚合逻辑并行运行，逐步切换流量，确保数据一致性。  
  
  ### 步骤 02: research (完整产出)
  
  # 研究分析 — researcher
  
  任务: 构建聚合窗口引擎：基于滑动窗口的状态管理、持久化、双写过渡机制、窗口边界语义控制
  步骤: research
  Agent: build_researcher
  
  ---
  
  📋 任务: de6f9126-072
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
    构建聚合窗口引擎：基于滑动窗口的状态管理、持久化、双写过渡机制、窗口边界语义控制
    Architect, Developer
    
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
    src/docs/agent_handoffs/3f9494e1-96d_executor_started_20260509T074916.md
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
    ... (共 505 个 src/ 文件)
    
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
                category=SC.DIGITAL_TW
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

## 聚合窗口引擎技术方案

### 1. 目标与范围
为现有监控采集管线 (`backend/monitoring/`) 构建一套可复用的**聚合窗口引擎**（Aggregation Window Engine），提供以下核心能力：
- 多种窗口类型（翻滚时间窗、滑动时间窗、计数窗）
- 高效的内存状态管理，支持从持久化存储恢复
- 双写过渡机制：新旧引擎并行运行，平滑迁移
- 明确的窗口边界语义（对齐、到期、清理）

### 2. 架构概览
```
                    ┌──────────────────────┐
                    │   Collector /        │
                    │   PlazaMonitor       │
                    └──────────┬───────────┘
                               │ 数据事件
                               v
              ┌────────────────────────────────┐
              │      WindowRouter (config)      │
              │  - 双写开关                     │
              │  - 流量分配策略                 │
              └───┬──────────────────┬─────────┘
                  │ (旧引擎)          │ (新引擎)
                  v                   v
      ┌─────────────────┐  ┌──────────────────────┐
      │ Legacy aggregator │  │ AggregationWindow    │
      └─────────────────┘  │ Engine (新)            │
                           │  - 窗口管理           │
                           │  - 状态存储           │
                           │  - 持久化 (文件/json) │
                           │  - 聚合函数库         │
                           └──────────┬───────────┘
                                      │
                                      v
                           ┌──────────────────────┐
                           │  Result Comparator    │
                           │  (双写期间对比)        │
                           └──────────────────────┘
```

### 3. 核心模块设计
#### 3.1 文件清单
| 文件 | 说明 | 操作 |
|------|------|------|
| `src/backend/monitoring/aggregation_window.py` | **新增** 聚合窗口引擎主体 | 新建 |
| `src/backend/tests/test_aggregation_window.py` | **新增** 单元测试 | 新建 |
| `src/backend/monitoring/collector.py` | 现有数据采集器 | 修改（集成路由） |
| `src/backend/monitoring/plaza_monitor.py` | 现有广场监控 | 修改（双写适配） |

#### 3.2 数据结构与接口定义
**窗口配置 (`WindowConfig`)**
```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional, List, Any

class WindowType(Enum):
    TUMBLING = "tumbling"       # 固定大小，无重叠
    SLIDING = "sliding"         # 固定大小+滑动步长
    SESSION = "session"         # 基于空闲间隔
    COUNT_BASED = "count_based" # 按条目数

class BoundaryAlign(Enum):
    EPOCH = "epoch"             # 基于 Unix epoch 对齐
    SYSTEM_TIME = "system_time" # 从引擎启动时刻对齐

@dataclass
class WindowConfig:
    window_type: WindowType
    size: float                  # 时间秒 或 条目数(计数窗)
    slide: Optional[float] = None  # 滑动步长（仅滑动窗需要）
    gap: Optional[float] = None    # 会话间隔（仅会话窗需要）
    boundary_align: BoundaryAlign = BoundaryAlign.SYSTEM_TIME
    late_tolerance: float = 0.0   # 乱序容忍，暂不实现

@dataclass
class AggregationSpec:
    name: str                     # 聚合名称，如 "temperature_avg"
    window_config: WindowConfig
    func: Callable[[List[float]], float]  # 聚合函数
    extractor: Callable[[Any], float]     # 从事件中提取数值

@dataclass
class WindowState:
    spec_id: str
    start: float                  # 窗口起始时间戳（或起始计数）
    end: float                    # 窗口结束时间戳
    events: List[Any] = field(default_factory=list)
    result: Optional[float] = None
    expired: bool = False
```

**持久化协议**
- 使用 JSON 文件（简单可靠），路径 `data/window_states/{spec_id}.json`
- 保存完整 `WindowState` 列表，便于恢复。
- 引擎启动时加载持久化文件，恢复活跃窗口。

**双写路由器 (`WindowRouter`)**
```python
class WindowRouter:
    def __init__(self, old_engine, new_engine, config):
        self.old_engine = old_engine
        self.new_engine = new_engine
        self.enable_new = config.get("enable_new", False)
        self.compare_results = config.get("compare_results", False)
        self.shadow_percentage = config.get("shadow_percentage", 0)
```

**核心引擎 API**
```python
class AggregationWindowEngine:
    def register_spec(self, spec: AggregationSpec) -> None
    def ingest(self, spec_name: str, value: float, timestamp: float) -> None
    def get_result(self, spec_name: str) -> Optional[float]
    def get_all_results(self) -> Dict[str, float]
    def checkpoint(self) -> None          # 持久化当前状态
    def recover(self) -> None             # 从持久化恢复
    def purge_expired(self) -> None       # 清理过期窗口
```

### 4. 详细设计
#### 4.1 窗口边界语义
- **Tumbling**: 根据 `boundary_align` 决定窗口起始边界。若为 `EPOCH`，则窗口边界为 `timestamp - (timestamp % size)`；为 `SYSTEM_TIME`，则以引擎初始化时间对齐（避免与机器时钟偏差异步）。窗口在 `end` 到达时封闭并生产结果，之后事件可丢弃。
- **Sliding**: 窗口大小 `size`，步长 `slide`。例如 size=60s, slide=10s。事件添加到所有覆盖此时间点的活动窗口中。每个窗口在 `end` 到达时一次性计算并输出。窗口边界同样依据对齐策略。
- **Session**: 维护一个动态窗口，当相邻事件间隔超过 `gap` 时关闭当前窗口，生成结果，并开始新窗口。新事件到来时，若与上一事件时间差 ≤ gap，则归入当前窗口。
- **Count-based**: 按事件数量划分，每 `size` 个事件触发一次计算。不考虑时间。

实现上，对于时间窗口，采用有序字典 `SortedDict`（或自定义最小堆）管理窗口队列，按结束时间排序。

#### 4.2 状态管理
- 每个 `spec` 维护一个活跃窗口列表（支持多个滑动窗口并发）。
- 事件到来时，将数值追加到所有包含事件时间戳的窗口中。
- 定期调用 `purge_expired()` 移除已关闭窗口，避免内存泄漏。可设定清理间隔（如每10秒自动触发）。
- 结果缓存在窗口对象内，读取即可。

#### 4.3 持久化
- `checkpoint()` 方法将当前所有未过期的 `WindowState` 序列化为JSON文件。
- 格式：
  ```json
  {
    "specs": {
      "cpu_avg": [
        {
          "start": 1700000000.0,
          "end": 1700000060.0,
          "events": [45.2, 46.1],
          "expired": false,
          "result": null
        }
      ]
    },
    "last_checkpoint": 1700000010.0
  }
  ```
- `recover()` 加载文件并重建窗口对象。若文件不存在或损坏，静默初始化。
- 建议使用 `atomicwrites` 库或先写临时文件再 `os.replace` 保证原子性。若不依赖外部库，可使用 `tempfile.NamedTemporaryFile` + `shutil.move`。

#### 4.4 双写过渡机制
- 在 `collector.py` 和 `plaza_monitor.py` 中注入 `WindowRouter`。
- `WindowRouter` 根据配置：
  - `enable_new=False`: 仅调用旧聚合逻辑，新引擎不接收数据。
  - `enable_new=True, shadow_percentage=0`: 完全切换到新引擎，旧逻辑停止。
  - `enable_new=True, shadow_percentage= X (0<X<100)`: 将 `X%` 的数据同时发给旧和新引擎，新引擎结果不对外暴露，仅用于对比日志。
  - `compare_results=True`: 在双写期间，对比新旧引擎计算结果，若差异超阈值，记录告警。
- 配置项通过环境变量或配置文件 `config/settings.json` 控制（可动态热加载）。
- 逐步提升 `shadow_percentage` 并观察对比日志，直至确认无误后完全切换。

### 5. 与现有模块的集成方案
#### 5.1 `collector.py`
目前该模块可能内部维护一些字典或直接计算指标。改动：
- 新增 `from .aggregation_window import AggregationWindowEngine, WindowRouter`。
- 在 `Collector` 初始化时创建引擎实例并注册聚合规格。
- 原聚合代码封装为旧引擎接口（若需要双写）。可以在 `Collector` 中创建一个兼容的 `old_engine` 对象，提供 `ingest` 和 `get_result` 方法。
- 数据流入处调用 `window_router.ingest(...)`。

#### 5.2 `plaza_monitor.py`
类似，在健康检查或性能指标采集中替换或追加聚合方式。

### 6. 实施步骤
#### Phase 1：核心引擎实现（无持久化）
1. 创建 `aggregation_window.py`，实现：
   - `WindowConfig`, `WindowState` 数据类
   - `AggregationWindowEngine` 基础框架（注册、摄入、结果查询）
   - 针对 Tumbling / Count 实现窗口创建、事件推送、到期计算逻辑
2. 编写对应单元测试，覆盖基本场景。

#### Phase 2：增加 Sliding/Session 窗口
1. 扩展引擎，实现滑动窗的多窗口管理算法（事件添加到所有重叠窗口）。
2. 实现会话窗口的动态开启关闭。
3. 补充测试。

#### Phase 3：状态持久化与恢复
1. 实现 `checkpoint()` 和 `recover()` 方法。
2. 在引擎初始化时调用恢复，在 `ingest` 后定期或手动触发检查点。
3. 测试保存/加载一致性，包括崩溃恢复。

#### Phase 4：窗口边界语义完善
1. 引入 `BoundaryAlign` 并调整窗口创建公式。
2. 清理过期窗口逻辑 (`purge_expired`)。
3. 添加边界对齐相关测试。

#### Phase 5：双写路由器与集成
1. 实现 `WindowRouter` 类及其配置驱动逻辑。
2. 在 `collector.py` 中集成路由器，封装旧聚合逻辑。
3. 在 `plaza_monitor.py` 中做同样适配。
4. 添加配置项及动态加载机制。

#### Phase 6：结果对比与灰度切换
1. 实现结果对比统计（平均值、差异百分比）。
2. 增加日志或指标输出，暴露对比结果。
3. 编写灰度计划文档，指导运维逐步切换。

### 7. 测试策略
- 单元测试：覆盖各种窗口类型、对齐方式、乱序处理（暂不实现）、过期清理、持久化。
- 集成测试：模拟 `collector` 数据流，验证双写模式下新旧结果一致。
- 压力测试：大量并发事件（10k QPS），验证内存和性能。

### 8. 配置示例
```json
// config/settings.json
{
  "aggregation": {
    "enable_new": false,
    "shadow_percentage": 0,
    "compare_results": false,
    "comparison_threshold": 0.01,
    "persist_interval": 10,
    "data_dir": "data/window_states/"
  }
}
```

该方案基于现有监控模块的上下文，清晰定义了模块职责、接口规范和迁移路径，开发工程师可依据此架构逐步实施。

────────────────────────────────────────────────────────────
✅ deepseek-v4-pro 完成
