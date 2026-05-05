# PM分解 — project_manager

任务: manual-start-check
步骤: pm_decompose
Agent: build_pm

---

📋 任务: dd0e3569-eb0
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
  manual-start-check
  validate pending start path
  
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
  src/backend/agents/teams/__init__.py
  src/backend/agents/teams/ai_coding_team.py
  src/backend/agents/teams/build_team.py
  src/backend/agents/teams/energy_team.py
  src/backend/agents/skills/__init__.py
  src/backend/agents/skills/greeting.py
  src/backend/agents/skills/hello.py
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
      except Exception as e:
          logger.warning(f"⚠️ Agent Config API failed: {e}")
  
      logger.info("🎉 AgentsGroup2026 ready")
  
  
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
              return {
                  "reply": "Chat channel 未注册，请检查后端配置。",
                  "urgency": "normal",
                  "source": "error",
              }
  
          result = await chat_ch.process_event({
              "type": "chat_message",
              "message": payload.message,
              "session_id": payload.session_id,
              "lang": payload.lang,
          })
          result["source"] = "bridge_chat_template"
          if task_id:
              result["task_id"] = task_id
      except Exception as e:
          logger.warning(f"[Chat] Template fallback failed: {e}")
          return {
              "reply": f"系统暂时无法处理请求: {str(e)[:100]}",
              "urgency": "normal",
              "source": "error",
          }
      return result
  
  
  @app.get("/api/v1/bridge-chat/history")
  async def bridge_chat_history(session_id: str = "default", limit: int = 20):
      """Get chat history."""
      from channels.marine_base import get_default_registry
  
      registry = get_default_registry()
      chat_ch = registry.get("bridge_chat")
      if not chat_ch:
          raise HTTPException(status_code=404, detail="Chat channe
  ```
  
  ### 文件: `src/backend/agents/agent_loop.py`
  ```py
  """Function-calling loop for Developer/QA agents.
  
  Drives a multi-turn conversation with DeepSeek V4 where each turn the model can
  call tools (read_file, grep, write_file, patch_file, run_python, run_pytest) to
  inspect and modify the codebase, then finishes with a `finish` tool call.
  
  This replaces the single-shot "emit a markdown blob with code fences" approach
  that produced hallucinated imports and truncated files.
  """
  from __future__ import annotations
  
  import http.client
  import json
  import logging
  import ssl
  import time
  from typing import Any, Dict, List, Optional
  from urllib.parse import urlparse
  
  from .agent_toolbox import (
      TOOL_SCHEMA,
      dispatch_tool_call,
      get_tools_for_role,
  )
  
  logger = logging.getLogger("AgentLoop")
  
  DEFAULT_MAX_ITERATIONS = 25
  DEFAULT_MAX_TOKENS = 65536
  DEFAULT_TEMPERATURE = 0.2
  
  # ── Safeguard constants ──
  # Safeguard 1: auto-finish nudge when approaching iteration cap
  _ITERATION_NUDGE_RATIO = 0.80  # at 80% of max_iterations, inject nudge
  # Safeguard 2: context budget — compress old tool results when messages grow
  _CONTEXT_BUDGET_CHARS = 100_000  # max combined chars in messages
  _TOOL_RESULT_TRUNC = 500  # truncate old tool results to this when over budget
  
  
  class AgentLoop:
      """Multi-turn function-calling driver against an OpenAI-compatible endpoint."""
  
      def __init__(
          self,
          *,
          api_key: str,
          api_base_url: str,
          model: str,
          role: str,
          system_prompt: str,
          max_iterations: int = DEFAULT_MAX_ITERATIONS,
          max_tokens: int = DEFAULT_MAX_TOKENS,
          temperature: float = DEFAULT_TEMPERATURE,
          on_event: Optional[Any] = None,
      ):
          self.api_key = api_key
          self.api_base_url = api_base_url.rstrip("/")
          self.model = model
          self.role = role
          self.max_iterations = max_iterations
          self.max_tokens = max_tokens
          self.temperature = temperature
          self.tools = get_tools_for_role(role)
          self.messages: List[Dict[str, Any]] = [
              {"role": "system", "content": system_prompt},
          ]
          self.on_event = on_event   # callable(event_type:str, payload:dict)
          self.files_changed: List[str] = []
          self.summary: str = ""
          self.tool_call_log: List[Dict[str, Any]] = []
  
      # ────────────────────────────────────────────────
      # HTTP plumbing
      # ────────────────────────────────────────────────
      _API_MAX_RETRIES = 3
      _API_RETRY_BACKOFF = [2, 5, 10]  # seconds between retries
      # Transient errors worth retrying
      _RETRYABLE = (
          ConnectionResetError, ConnectionAbortedError, ConnectionRefusedError,
          BrokenPipeError, TimeoutError, OSError,
          http.client.RemoteDisconnected, http.client.IncompleteRead,
      )
  
      def _post_chat(self) -> Dict[str, Any]:
          parsed = urlparse(self.api_base_url)
          host = parsed.hostname or "api.deepseek.com"
          port = parsed.port or (443 if parsed.scheme == "https" else 80)
          path = (parsed.path or "").rstrip("/") + "/chat/completions"
          ctx = ssl.create_default_context() if parsed.scheme == "https" else None
          conn_cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
  
          body_str = json.dumps({
              "model": self.model,
              "messages": self.messages,
              "tools": self.tools,
              "tool_choice": "auto",
              "max_tokens": self.max_tokens,
              "temperature": self.temperature,
              "stream": False,
          })
          headers = {
              "Authorization": f"Bearer {self.api_key}",
              "Content-Type": "application/json",
          }
  
          last_err: Optional[Exception] = None
          for attempt in range(self._API_MAX_RETRIES):
              try:
                  conn = conn_cls(host, port, context=ctx, timeout=300) if ctx \
                      else conn_cls(host, port, timeout=300)
                  conn.request("POST", path, body=body_str, headers=headers)
                  resp = conn.getresponse()
                  raw = resp.read().decode("utf-8", errors="replace")
                  conn.close()
                  if resp.status == 429 or resp.status >= 500:
                      # Server-side error — retryable
                      raise RuntimeError(f"LLM HTTP {resp.status}: {raw[:300]}")
                  if resp.status >= 400:
                      raise RuntimeError(f"LLM HTTP {resp.status}: {raw[:500]}")
                  return json.loads(raw)
              except self._RETRYABLE as e:
                  last_err = e
                  wait = self._API_RETRY_BACKOFF[min(attempt, len(self._API_RETRY_BACKOFF) - 1)]
                  logger.warning(
                      "[AgentLoop] Transient error on attempt %d/%d: %s — retrying in %ds",
                      attempt + 1, self._API_MAX_RETRIES, e, wait,
                  )
                  time.sleep(wait)
              except RuntimeError as e:
                  # HTTP 429 / 5xx — retry with backoff
                  if "HTTP 4" in str(e) and "HTTP 429" not in str(e):
                      raise  # 4xx (non-429) is not retryable
                  last_err = e
                  wait = self._API_RETRY_BACKOFF[min(attempt, len(self._API_RETRY_BACKOFF) - 1)]
                  logger.warning(
                      "[AgentLoop] Server error on attempt %d/%d: %s — retrying in %ds",
                      attempt + 1, self._API_MAX_RETRIES, e, wait,
                  )
                  time.sleep(wait)
          raise last_err or RuntimeError("_post_chat failed after retries")
  
      # ────────────────────────────────────────────────
      # Loop
      # ────────────────────────────────────────────────
      def run(self, user_prompt: str) -> Dict[str, Any]:
          """Run the agent loop. Returns {ok, summary, files_changed, iterations, log}."""
          self.messages.append({"role": "user", "content": user_prompt})
          self._emit("loop_start", {"role": self.role, "tools": [t["function"]["name"] for t in self.tools]})
  
          for it in range(self.max_iterations):
              # ── Safeguard 1: nudge agent when approaching iteration cap ──
              self._maybe_inject_nudge(it)
              # ── Safeguard 2: compact old tool results when context too large ──
              self._compact_old_tool_results()
  
              t0 = time.time()
              try:
                  resp = self._post_chat()
              except Exception as e:
                  logger.exception("[AgentLoop] HTTP error on iteration %d (after retries)", it)
                  self._emit("error", {"iteration": it, "error": str(e)})
                  # If we have already done useful work, don't discard it —
                  # treat as a graceful early stop instead of hard failure.
                  if self.files_changed or self.summary:
                      logger.info(
                          "[AgentLoop] Partial progress (%d files, %d chars summary) — "
                          "returning partial success",
                          len(self.files_changed), len(self.summary),
                      )
                      self._emit("loop_end", {"reason": "network_error_partial", "iteration": it})
                      return {
                          "ok": True, "error": str(e),
                          "summary": self.summary or f"(network error after {it} turns)",
                          "files_changed": self.files_changed,
                          "iterations": it, "log": self.tool_call_log,
                      }
                  return {
                      "ok": False, "error": str(e),
                      "summary": self.summary, "files_changed": self.files_changed,
                      "iterations": it, "log": self.tool_call_log,
                  }
  
              choice = (resp.get("choices") or [{}])[0]
              msg = choice.get("message", {}) or {}
              content = msg.get("content") or ""
              tool_calls = msg.get("tool_calls") or []
              finish_reason = choice.get("finish_reason", "")
  
              self._emit("model_turn", {
                  "iteration": it,
                  "elapsed": round(time.time() - t0, 2),
                  "content_chars": len(content),
                  "tool_call_count": len(tool_calls),
                  "finish_reason": finish_reason,
              })
  
              # Append assistant turn
              assistant_msg: Dict[str, Any] = {"role": "assistant", "content": content}
              if tool_calls:
                  assistant_msg["tool_calls"] = tool_calls
              self.messages.append(assistant_msg)
  
              # No tool calls → model is done talking
              if not tool_calls:
                  if not self.summary and content:
                      self.summary = content[:1000]
                  self._emit("loop_end", {"reason": "no_tool_call", "iteration": it})
                  return {
                      "ok": True, "summary": self.summary,
                      "files_changed": self.files_changed,
                      "iterations": it + 1, "log": self.tool_call_log,
                      "final_message": content,
                  }
  
              # Process each tool call
              finished = False
              for tc in tool_calls:
                  tc_id = tc.get("id", "")
                  fn = tc.get("function", {}) or {}
                  name = fn.get("name", "")
                  args_raw = fn.get("arguments", "") or "{}"
                  self._emit("tool_call", {"name": name, "args": args_raw[:500]})
  
                  if name == "finish":
                      try:
                          a = json.loads(args_raw or "{}")
                          self.summary = a.get("summary", "")
                          for fc in a.get("files_changed") or []:
                              if fc not in self.files_changed:
                                  self.files_changed.append(fc)
                      except Exception:
                          self.summary = args_raw[:500]
                      self.messages.append({
                          "role": "tool", "tool_call_id": tc_id, "name": name,
                          "content": json.dumps({"ok": True, "ack": "finished"}),
                      })
                      self.tool_call_log.append({"name": name, "args": args_raw, "ok": True})
                      finished = True
                      continue
  
                  result = dispatch_tool_call(name, args_raw)
                  # Track writes
                  if name in ("write_file", "patch_file") and result.get("ok"):
                      try:
                          a = json.loads(args_raw or "{}")
                          path = a.get("path", "")
                          if path and path not in self.files_changed:
                              self.files_changed.append(path)
                      except Exception:
                          pass
  
                  self.tool_call_log.append({
                      "name": name, "args": args_raw[:1000],
                      "ok": bool(result.get("ok")),
                      "summary": self._summarize_result(name, result),
                  })
                  self._emit("tool_result", {
                      "name": name, "ok": bool(result.get("ok")),
                      "summary": self.tool_call_log[-1]["summary"],
                  })
                  self.messages.append({
                      "role": "tool", "tool_call_id": tc_id, "name": name,
                      "content": json.dumps(result, ensure_ascii=False)[:32_000],
                  })
  
              if finished:
                  self._emit("loop_end", {"reason": "finish_called", "iteration": it})
                  return {
                      "ok": True, "summary": self.summary,
                      "files_changed": self.files_changed,
                      "iterations": it + 1, "log": self.tool_call_log,
                  }
  
          # Hit iteration cap
          # ── Safeguard 3: partial success if agent produced useful work ──
          if self.files_changed or self.summary:
              logger.info(
                  "[AgentLoop] Iteration cap hit but agent produced work "
                  "(%d files, %d chars summary) — treating as par
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

🔗 API: api.deepseek.com | 模型: deepseek-chat
────────────────────────────────────────────────────────────

好的，PM。我已经分析了任务“manual-start-check”和“validate pending start path”以及项目上下文。这是一个关于系统启动流程的验证和检查任务，需要确保手动启动流程的正确性，并验证待启动路径的有效性。

以下是我对该任务的分解和规划。

---

## 任务分解文档: manual-start-check & validate pending start path

**项目**: AgentsGroup2026
**任务ID**: TASK-20260503-PM-001
**负责人**: Project Manager (PM)
**日期**: 2026-05-03

### 1. 任务概述

本任务旨在对系统的“手动启动”流程进行全面的检查和验证。核心目标是确保当系统通过手动方式启动时，所有依赖的服务、组件和路径都能正确初始化并进入预期状态。这包括验证启动脚本、配置加载、依赖服务健康检查以及关键路径（如API路由、数据库连接、外部服务集成）的可用性。

### 2. 任务分解 (Work Breakdown Structure)

我们将此任务分解为以下四个主要阶段：

#### 阶段 1: 启动流程文档化与依赖分析 (Research & Analysis)

*   **目标**: 梳理并文档化当前系统的手动启动流程，识别所有关键依赖和潜在风险点。
*   **子任务**:
    1.  **分析启动入口**: 审查 `src/backend/main.py` 中的 `startup` 事件处理函数，列出所有初始化的子系统（如 `SystemEvolutionChannel`, `BridgeChatChannel`, `TeamManager`, `PlazaEngine` 等）。
    2.  **映射依赖关系**: 为每个子系统创建依赖图，明确其启动顺序和依赖项（例如，`agent_team_api.py` 依赖于 `evolution_engine` 的初始化）。
    3.  **识别配置依赖**: 检查 `main.py` 和 `agent_team_api.py` 中硬编码的配置、环境变量或外部服务地址（如API密钥、数据库URL等）。
    4.  **文档化启动步骤**: 编写一份清晰的、步骤化的手动启动指南，包括必要的环境准备、命令执行和预期输出。
*   **交付物**:
    *   `src/docs/workflow_artifacts/TASK-20260503-PM-001_startup_flow.md`: 包含启动流程图、依赖关系表和手动启动步骤文档。

#### 阶段 2: 核心路径验证 (Architecture & Development)

*   **目标**: 验证系统启动后，关键API路径和功能模块是否按预期工作。
*   **子任务**:
    1.  **验证健康检查端点**: 编写并执行测试，确保 `GET /api/v1/health` 返回 `status: "ok"` 且所有 `services` 状态为 `true`。
    2.  **验证核心API路由**:
        *   测试 `GET /api/v1/info` 端点，确认其返回正确的系统信息。
        *   测试 `GET /api/v1/agent-teams/overview` 端点，确认其能返回团队概览（即使某些团队为 `None`）。
        *   测试 `GET /api/v1/agent-teams/evolution/status` 端点，确认演进引擎已初始化。
    3.  **验证“待启动路径” (Pending Start Path)**:
        *   **定义**: “待启动路径”指那些在系统启动后，需要特定条件或事件触发才能完全激活的功能路径。例如，`BridgeChatChannel` 的 `process_event` 方法或 `EvolutionEngine` 的 `run_evolution_cycle` 方法。
        *   **验证方法**:
            *   检查 `main.py` 中 `startup` 函数，确认这些路径的初始化代码是否被正确执行且没有抛出异常。
            *   模拟触发这些路径的事件（如发送一个聊天消息到 `/api/v1/bridge-chat/send`），并验证其能正确路由到 `_agent_llm_chat` 或 `bridge_chat_template` 逻辑。
            *   检查 `agent_team_api.py` 中的 `evolution_*` 端点，确认它们在被调用时能正确访问 `_evolution_engine` 实例。
    4.  **验证前端静态资源加载**: 确保 `main.py` 中配置的静态文件服务（`StaticFiles`）能正确提供 `src/frontend/` 目录下的HTML、CSS和JS文件。
*   **交付物**:
    *   自动化测试脚本或手动测试用例集，用于验证上述路径。
    *   测试报告，记录每个端点的测试结果。

#### 阶段 3: 错误处理与边界情况测试 (Testing)

*   **目标**: 测试系统在启动过程中遇到错误或异常情况时的行为。
*   **子任务**:
    1.  **模拟依赖失败**: 模拟 `SystemEvolutionChannel` 或 `BridgeChatChannel` 初始化失败，验证 `main.py` 的 `startup` 函数是否能优雅地处理异常（如 `try...except` 块），并记录警告日志，而不是导致整个应用崩溃。
    2.  **测试配置缺失**: 模拟关键环境变量或配置文件缺失，验证系统是否能给出清晰的错误提示。
    3.  **测试API错误响应**: 验证当依赖服务（如 `_evolution_engine`）未初始化时，相关API端点（如 `GET /api/v1/agent-teams/evolution/status`）是否能正确返回 `503 Service Unavailable` 或 `404 Not Found` 错误。
    4.  **测试并发启动**: （如果适用）模拟多个启动请求同时发生，验证系统的并发处理能力。
*   **交付物**:
    *   错误处理测试报告。
    *   针对 `main.py` 和 `agent_team_api.py` 的改进建议，以增强其健壮性。

#### 阶段 4: 集成与最终验证 (Deploy & Verification)

*   **目标**: 在集成环境中执行完整的启动流程，并完成最终验证。
*   **子任务**:
    1.  **执行完整启动流程**: 按照阶段1文档化的步骤，在干净的集成环境中启动系统。
    2.  **运行自动化测试套件**: 执行阶段2和阶段3开发的测试用例。
    3.  **人工探索性测试**: 手动操作前端页面（如 `plaza.html`, `system-evolution.html`），验证其与后端的交互是否正常。
    4.  **生成最终报告**: 汇总所有测试结果，形成最终验证报告。
*   **交付物**:
    *   最终验证报告 (`src/docs/workflow_artifacts/TASK-20260503-PM-001_final_report.md`)。
    *   启动流程检查清单 (`src/docs/workflow_artifacts/TASK-20260503-PM-001_checklist.md`)。

### 3. 技术风险与依赖关系

| 风险/依赖 | 描述 | 缓解措施 |
| :--- | :--- | :--- |
| **外部API依赖** | `agent_loop.py` 中的 `_post_chat` 方法依赖于外部LLM API（如DeepSeek）。API不可用或限流会导致聊天功能失败。 | 1. 实现重试机制（已存在）。<br>2. 确保 `bridge_chat` 有模板回退方案（已存在）。<br>3. 在健康检查中加入对API可达性的检查。 |
| **配置硬编码** | `main.py` 和 `agent_team_api.py` 中存在一些硬编码的配置（如默认用户、API密钥）。 | 1. 将所有可变配置迁移到环境变量或配置文件中。<br>2. 在启动时进行配置校验。 |
| **模块导入顺序** | `main.py` 的 `startup` 函数中，模块导入和初始化顺序至关重要。错误的顺序可能导致 `ImportError` 或 `AttributeError`。 | 1. 严格遵守依赖图进行初始化。<br>2. 使用 `try...except` 包裹每个模块的初始化，确保单个模块失败不影响整体启动。 |
| **`_team_manager` 状态** | `agent_team_api.py` 中的 `set_teams` 函数在 `main.py` 启动时被调用。如果调用失败或顺序错误，后续API调用会返回503错误。 | 1. 在 `startup` 函数中确保 `set_teams` 在所有依赖初始化之后调用。<br>2. 在API端点中添加对 `_evolution_engine` 等全局变量的 `None` 检查。 |
| **前端与后端版本不匹配** | 前端JS代码（如 `i18n.js`）或HTML模板可能依赖于后端API的特定响应格式。 | 1. 建立前后端API契约（如OpenAPI规范）。<br>2. 在CI/CD流程中加入集成测试。 |

### 4. 后续工作指导

1.  **研究人员 (Researcher)**:
    *   请优先执行**阶段1**，深入分析 `main.py` 的启动逻辑，并绘制出完整的依赖关系图。
    *   研究 `agent_loop.py` 中 `_post_chat` 方法的错误处理机制，评估其对启动流程的影响。
    *   调研是否有更优雅的方式来管理配置，例如使用 `pydantic-settings`。

2.  **架构师 (Architect)**:
    *   基于阶段1的分析结果，审查当前的启动架构。是否存在循环依赖？启动顺序是否可以优化？
    *   设计一个更健壮的启动框架，例如引入“启动状态机”或“健康检查注册表”，使系统能更好地报告其启动进度和健康状况。
    *   评估将“待启动路径”设计为“懒加载”模式的可行性，以加快系统初始启动速度。

3.  **开发者 (Developer)**:
    *   根据阶段2和阶段3的测试结果，修复发现的Bug。
    *   实现阶段2中定义的自动化测试用例。
    *   根据架构师的建议，重构 `main.py` 的启动逻辑，使其更模块化和可测试。
    *   为 `agent_team_api.py` 中的每个端点添加更详细的日志，以便于问题追踪。

4.  **测试人员 (Tester)**:
    *   根据本任务分解文档，编写详细的测试用例。
    *   重点测试**阶段2**中定义的“待启动路径”和**阶段3**中的错误处理场景。
    *   在集成环境中执行**阶段4**的最终验证。

────────────────────────────────────────────────────────────
✅ deepseek-chat 完成
