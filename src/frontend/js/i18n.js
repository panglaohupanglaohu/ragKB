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
    ['健康', 'Health'],
    ['测试连接', 'Test Connection'],
    ['测試连接', 'Test Connection'],

    // ─── WorldMonitor / AR CAS ───
    ['碰撞风险', 'Collision Risk'],
    ['特殊场景预警', 'Special Scene Alerts'],
    ['峡谷航行警告', 'Canyon Navigation Warning'],
    ['前方进入峡谷水域', 'Entering canyon waters ahead'],
    ['航道狭窄', 'Narrow channel'],
    ['注意避让', 'Mind clearance'],
    ['冰山预警', 'Iceberg Alert'],
    ['检测到冰山', 'Iceberg detected'],
    ['保持安全距离', 'Keep safe distance'],
    ['减速航行', 'Reduce speed'],
    ['安全航速', 'Safe speed'],
    ['无特殊警告', 'No special warnings'],
    ['合规警告', 'Compliance Warnings'],
    ['无警告', 'No warnings'],
    ['暂无报警', 'No alarms'],
    ['本船信息', 'Own Ship Info'],
    ['位置', 'Position'],
    ['航线规划', 'Route Planning'],
    ['起点', 'Origin'],
    ['终点', 'Destination'],
    ['航点', 'Waypoint'],
    ['决策摘要', 'Decision Summary'],
    ['快捷命令', 'Quick Commands'],
    ['分析态势', 'Analyze Situation'],
    ['评估碰撞风险', 'Assess Collision Risk'],
    ['航线建议', 'Route Advice'],
    ['监控摄像头', 'Surveillance Camera'],
    ['前视摄像头', 'Forward Camera'],
    ['后视摄像头', 'Aft Camera'],
    ['实时直播', 'Live Feed'],
    ['叠加', 'Overlay'],
    ['轨迹预测', 'Track Prediction'],
    ['附近港口', 'Nearby Ports'],
    ['本船', 'Own Ship'],
    ['本船位置', 'Own Ship Position'],
    ['三亚附近', 'Near Sanya'],
    ['返回船长智能中控台', 'Back to Captain Cockpit'],
    ['驾驶台报警菜单', 'Bridge Alarm Menu'],
    ['航行菜单', 'Navigation Menu'],
    ['语义菜单', 'Semantic Menu'],
    ['等待环境同步', 'Awaiting Environment Sync'],
    ['同步中', 'Syncing'],
    ['未锁定', 'Unlocked'],
    ['环境', 'Environment'],
    ['普通海域', 'Open Sea'],
    ['正常监视', 'Normal Watch'],
    ['高风险', 'High Risk'],
    ['安全目标', 'Safe Target'],
    ['中风险目标', 'Medium Risk Target'],
    ['高风险目标', 'High Risk Target'],
    ['增强现实叠加', 'AR Overlay'],
    ['更新时间', 'Update Time'],
    ['狭窄水道中船舶应尽量靠右行驶', 'Vessels shall keep to starboard in narrow channels'],
    ['在冰山区域应使用安全航速', 'Use safe speed in iceberg zones'],

    // ─── Datacenter ───
    ['机房三维孪生', '3D Datacenter Twin'],
    ['物理对象映射', 'Physical Object Mapping'],
    ['实时设备列表', 'Live Device List'],
    ['能量链路', 'Energy Link'],
    ['触发闭环', 'Trigger Loop'],
    ['棘轮锁定', 'Ratchet Lock'],
    ['演进轮次', 'Evolution Round'],
    ['棘轮遗产', 'Ratchet Heritage'],
    ['节能累计', 'Energy Saved'],
    ['减排', 'Emission Reduction'],
    ['候选池', 'Candidate Pool'],
    ['遗产栈', 'Heritage Stack'],
    ['事件流', 'Event Stream'],

    // ─── General maritime terms ───
    ['三亚港', 'Sanya Port'],
    ['榆林港', 'Yulin Port'],
    ['八所港', 'Basuo Port'],
    ['深圳港', 'Shenzhen Port'],
    ['上海', 'Shanghai'],
    ['宁波', 'Ningbo'],
    ['寧波', 'Ningbo'],
    ['总部', 'HQ'],
    ['新加坡', 'Singapore'],
    ['英吉利海峡', 'English Channel'],
    ['北海', 'North Sea'],
    ['香港', 'Hong Kong'],

    // ─── DP Control ───
    ['动力定位 — AgentsGroup2026', 'DP Control — AgentsGroup2026'],
    ['緯度', 'Latitude'],
    ['經度', 'Longitude'],
    ['设定值', 'Setpoints'],
    ['设定値', 'Setpoints'],
    ['目标緯度', 'Target Latitude'],
    ['目标經度', 'Target Longitude'],
    ['目标船首向', 'Target Heading'],
    ['位置参考', 'Position Reference'],
    ['船首向', 'Heading'],
    ['位置偏差', 'Position Offset'],
    ['水深', 'Water Depth'],
    ['推力分配', 'Thrust Allocation'],
    ['艏側推', 'Bow Thruster'],
    ['艉側推', 'Stern Thruster'],
    ['左全回转', 'Port Azimuth'],
    ['右全回转', 'Stbd Azimuth'],
    ['功率总和', 'Total Power'],
    ['旋转半径', 'Turning Radius'],
    ['旋转半徑', 'Turning Radius'],
    ['保持模式', 'Hold Mode'],
    ['能力图', 'Capability Plot'],
    ['级别', 'Class'],
    ['級別', 'Class'],
    ['风浪角', 'Wind/Wave Angle'],
    ['风浪', 'Wind & Wave'],
    ['環境載荷', 'Environment Load'],

    // ─── CMS Health ───
    ['设备树', 'Device Tree'],
    ['设备樹', 'Device Tree'],
    ['推进系统', 'Propulsion'],
    ['主机', 'Main Engine'],
    ['辅机', 'Auxiliary'],
    ['辅机系统', 'Auxiliary System'],
    ['发电机', 'Generator'],
    ['应急发电机', 'Emergency Generator'],
    ['锚机', 'Windlass'],
    ['起重机', 'Crane'],
    ['主空调', 'Main AC'],
    ['机舱通风', 'ER Ventilation'],
    ['冷却水泵', 'CW Pump'],
    ['燃油泵', 'Fuel Pump'],
    ['压载泵', 'Ballast Pump'],
    ['舱底泵', 'Bilge Pump'],
    ['泵组', 'Pump Group'],
    ['甲板设备', 'Deck Equipment'],
    ['总设备', 'Total Devices'],
    ['注意', 'Caution'],
    ['告警', 'Critical'],
    ['振动趋势', 'Vibration Trend'],
    ['温度趋势', 'Temperature Trend'],
    ['轴承温度趋势', 'Bearing Temp Trend'],
    ['轴承温度', 'Bearing Temp'],
    ['维护计划', 'Maintenance Schedule'],
    ['项目', 'Item'],
    ['到期', 'Due'],
    ['滑油更换', 'Lube Oil Change'],
    ['气缸检查', 'Cylinder Inspection'],
    ['钢丝绳更换', 'Wire Rope Replace'],
    ['机封检查', 'Seal Inspection'],
    ['计划中', 'Planned'],
    ['逾期', 'Overdue'],
    ['即将', 'Upcoming'],
    ['健康评分', 'Health Score'],
    ['系统状态', 'System Status'],
    ['系统狀态', 'System Status'],
    ['设备健康助手', 'CMS Health Assistant'],
    ['设备维保', 'Equipment Maintenance'],
    ['振动分析', 'Vibration Analysis'],
    ['健康评分等问题', 'health score queries'],
    ['设备健康 AI 助手已就绪 — 可咨询设备维保', 'CMS Health AI ready — consult equipment maintenance'],
    ['齿轮箱', 'Gearbox'],
    ['艏推', 'Bow Thruster'],
    ['振动', 'Vibration'],

    // ─── HMI Console ───
    ['控制台交互', 'HMI Console'],
    ['系统总览', 'System Overview'],
    ['推进', 'Propulsion'],
    ['安全', 'Safety'],
    ['通信', 'Communication'],
    ['电力', 'Power'],
    ['系统正常', 'System Normal'],
    ['风速增大', 'Wind Speed Rising'],
    ['目标更新', 'Targets Updated'],
    ['航线同步完成', 'Route Sync Complete'],
    ['应急发电机月度测试到期', 'EDG Monthly Test Due'],
    ['应急发电机月度测試到期', 'EDG Monthly Test Due'],
    ['助手', 'Assistant'],
    ['指令已收到', 'Command Received'],
    ['收到指令', 'Received command'],
    ['正在处理中', 'Processing'],
    ['命令已执行', 'Command Executed'],
    ['指令已发送', 'Command Sent'],
    ['隨时为您提供航行支持和系统狀态查詢', 'Ready to assist with navigation and system queries'],
    ['当前航行狀态如何', 'Current navigation status?'],
    ['未发現异常', 'No anomalies detected'],
    ['風浪情況怎樣', 'How are wind and waves?'],
    ['有効波高', 'Significant wave height'],
    ['湧浪週期', 'Swell period'],
    ['未超出作业限制', 'Within operation limits'],
    ['但建议关注未來 6 小时風速可能增至 25 节的预报', 'but monitor forecast: wind may reach 25kn in 6h'],
    ['18 节', '18 kn'],
    ['12 节', '12 kn'],
    ['25 节', '25 kn'],
    ['自动', 'Auto'],

    // ─── Energy Compliance ───
    ['能效合规 — AgentsGroup2026', 'Energy Compliance — AgentsGroup2026'],
    ['评级', 'Rating'],
    ['限值', 'Limit'],
    ['监测', 'Monitoring'],
    ['1月', 'Jan'], ['2月', 'Feb'], ['3月', 'Mar'], ['4月', 'Apr'],
    ['5月', 'May'], ['6月', 'Jun'], ['7月', 'Jul'], ['8月', 'Aug'],
    ['9月', 'Sep'], ['10月', 'Oct'], ['11月', 'Nov'], ['12月', 'Dec'],

    // ─── Safety Emergency procedures ───
    ['壹 ', '① '],
    ['贰 ', '② '],
    ['叁 ', '③ '],
    ['肆 ', '④ '],
    ['伍 ', '⑤ '],
    ['大声呼叫', 'Shout alarm'],
    ['抛救生圈', 'Throw life buoy'],
    ['记录位置', 'Record position'],
    ['搜救', 'Search & Rescue'],
    ['发现火情', 'Detect fire'],
    ['报告驾驶台', 'Report to bridge'],
    ['按下火警按钮', 'Press fire alarm'],
    ['初期灭火', 'Initial firefighting'],
    ['关闭通风', 'Close ventilation'],
    ['船长下令', 'Captain orders'],
    ['穿救生衣', 'Don life jacket'],
    ['到集合站', 'Go to muster station'],
    ['清点人数', 'Head count'],
    ['放艇', 'Launch boats'],
    ['评估损害', 'Assess damage'],
    ['堵漏', 'Stop leak'],
    ['测量进水', 'Measure flooding'],
    ['启动舱底泵', 'Start bilge pump'],
    ['报告', 'Report'],
    ['停车', 'Stop engines'],
    ['测量水深', 'Sound depths'],
    ['检查舱底', 'Check bilge'],
    ['评估脱浅', 'Assess refloating'],
    ['请求拖带', 'Request tow'],
    ['停止泄漏源', 'Stop leak source'],
    ['布设围油栏', 'Deploy oil boom'],
    ['报告海事局', 'Report to MCA'],
    ['使用吸油材料', 'Use absorbents'],
    ['关闭水密门', 'Close watertight doors'],
    ['启动排水泵', 'Start drainage pump'],
    ['评估稳性', 'Assess stability'],
    ['评估伤情', 'Assess injury'],
    ['急救处理', 'First aid'],
    ['联系TMAS', 'Contact TMAS'],
    ['安排后送', 'Arrange medevac'],

    
    // ─── Agent Detail ───
    ['任务拆解', 'Task Breakdown'],
    ['工作流', 'Workflow'],
    ['步骤', 'Steps'],
    ['子任务', 'Subtasks'],
    ['全部完成', 'All Complete'],
    ['推进', 'Advance'],
    ['人格', 'Personality'],
    ['灵魂', 'Soul'],
    ['记忆文件', 'Memory Files'],
    ['工作日志', 'Work Log'],
    ['聊天', 'Chat'],
    ['发送', 'Send'],
    ['已发送', 'Sent'],
    ['创建时间', 'Created At'],
    ['创建者', 'Creator'],
    ['最后活跃', 'Last Active'],
    ['工具数', 'Tools'],
    ['技能数', 'Skills'],
    ['通道数', 'Channels'],
    ['模型配置', 'Model Config'],
    ['Agent 档案', 'Agent Profile'],
    ['近期活动', 'Recent Activity'],
    ['暂无活动记录', 'No activity records'],
    ['暂无关注项', 'No focus items'],
    ['暂无会话', 'No sessions'],
    ['暂无日志', 'No logs'],
    ['暂无记忆文件', 'No memory files'],
    ['系统提示词', 'System Prompt'],
    ['测试连接', 'Test Connection'],
    ['连接成功', 'Connection OK'],
    ['连接失败', 'Connection Failed'],

    // ─── Token Factory ───
    ['Token Factory', 'Token Factory'],
    ['确保就绪', 'Ensure Ready'],
    ['SSH 隧道', 'SSH Tunnel'],
    ['启动隧道', 'Start Tunnel'],
    ['停止隧道', 'Stop Tunnel'],
    ['Ollama 配置', 'Ollama Config'],
    ['Ollama 端点', 'Ollama Endpoint'],
    ['代理端口', 'Proxy Port'],
    ['可用模型', 'Available Models'],
    ['探测 Ollama', 'Probe Ollama'],
    ['云端 LLM 提供商', 'Cloud LLM Provider'],
    ['整体状态', 'Overall Status'],
    ['就绪', 'Ready'],
    ['不可用', 'Unavailable'],
    ['离线', 'Offline'],
    ['在线', 'Online'],
    ['运行中', 'Running'],
    ['已停止', 'Stopped'],
    ['启动中', 'Starting...'],

    // ─── Sessions & Runtime ───
    ['会话存档', 'Session Archive'],
    ['跨会话搜索', 'Cross-Session Search'],
    ['已保存的会话', 'Saved Sessions'],
    ['收集会话将自动出现在此处', 'Sessions will appear here'],
    ['路由匹配', 'Route Match'],
    ['引导会话', 'Bootstrap Session'],
    ['路由+对话', 'Route & Chat'],
    ['禁用工具', 'Deny Tools'],
    ['最大匹配数', 'Max Matches'],
    ['简单模式', 'Simple Mode'],
    ['包含 MCP 工具', 'Include MCP Tools'],

    // ─── Tasks ───
    ['待执行', 'Pending'],
    ['执行中', 'Running'],
    ['已完成', 'Completed'],
    ['已取消', 'Cancelled'],
    ['工作流已完成', 'Workflow Complete'],
    ['工作流失败', 'Workflow Failed'],

    // ─── Wizard ───
    ['基本信息', 'Basic Info'],
    ['技能配置', 'Skill Config'],
    ['工具绑定', 'Tool Binding'],
    ['权限与通道', 'Permissions'],
    ['上一步', 'Previous'],
    ['下一步', 'Next'],
    ['完成创建', 'Finish'],

// ─── Poseidon Config ───
    ['系统配置 — AgentsGroup2026', 'System Configuration — AgentsGroup2026'],
    ['模型选择', 'Model Selection'],
    ['模型', 'Model'],
    ['参数', 'Parameters'],
    ['网络通信', 'Network'],
    ['网絡通信', 'Network'],
    ['安全设置', 'Security Settings'],
    ['运行状态', 'Runtime Status'],
    ['运行狀态', 'Runtime Status'],
    ['旗舰', 'Flagship'],
    ['多模态', 'Multimodal'],
    ['代码优化', 'Code Optimization'],
    ['推理增强', 'Reasoning'],
    ['开源', 'Open Source'],
    ['中文优化', 'Chinese Optimized'],
    ['阿里通义', 'Alibaba Tongyi'],
    ['本地部署', 'Local Deploy'],
    ['波特率', 'Baud Rate'],
    ['终端', 'Terminal'],
    ['串口', 'Serial Port'],
    ['路径', 'Path'],
    ['强制', 'Force'],
    ['強制', 'Force'],
    ['请求自动重定向到', 'Auto redirect to'],
    ['限制未授权', 'Block unauthorized'],
    ['设备接入', 'device access'],
    ['数据库大小', 'Database Size'],
    ['请求', 'Requests'],
    ['已切换模型', 'Switched model'],
    ['配置已保存', 'Config saved'],
    ['测试连接中', 'Testing connection'],
    ['连接成功', 'Connection OK'],
    ['连接失败', 'Connection Failed'],
    ['连接超时', 'Connection Timeout'],
    ['后端连接失败', 'Backend connection failed'],
    ['不可用', 'Unavailable'],
    ['可用', 'Available'],
    ['客户端', 'Client'],
    ['无应答', 'No response'],
    ['未找到', 'Not found'],
    ['通信错误', 'Comms error'],
    ['网络不可达', 'Network unreachable'],
    ['基于气象数据自动优化航线', 'Auto optimize route from weather data'],
    ['启用 L3 决策编排器自动建议', 'Enable L3 decision orchestrator auto-suggest'],
    ['自动计算避碰方案', 'Auto compute COLREG maneuver'],
    ['验证流程', 'Verify pipeline'],
    ['休息时间自动合规检查', 'Work/rest auto-compliance check'],
    ['你是 AgentsGroup2026 海事智能助手', 'You are AgentsGroup2026 Maritime AI Assistant'],
    ['基于 IMO/SOLAS/COLREGs 等国际海事标准提供专业建议', 'Professional advice based on IMO/SOLAS/COLREGs'],

    // ─── WorldMonitor extras ───
    ['实时数据', 'Live Data'],
    ['加载气象数据', 'Loading weather data'],
    ['加载 AIS 数据', 'Loading AIS data'],
    ['初始化地图', 'Initializing map'],
    ['添加本船标记', 'Adding own ship marker'],
    ['聚焦到目标', 'Focus on target'],
    ['更新列表', 'Update list'],
    ['更新计数', 'Update count'],
    ['风险', 'Risk'],

    // ─── Misc additions ───
    ['按下', 'Press'],
    ['执行', 'Execute'],
    ['阈值', 'Threshold'],
    ['工具', 'Tools'],
    ['会话', 'Session'],
    ['本地', 'Local'],
    ['技能', 'Skills'],
    ['团队', 'Team'],
    ['确认?', 'Confirm?'],
    ['应急预案:', 'Emergency Plan:'],
    ['任务已创建', 'Task created'],

    
    // ─── Agent Team Config UI ───
    ['团队概览', 'Team Overview'],
    ['仪表盘', 'Dashboard'],
    ['模型池', 'Model Pool'],
    ['工具管理', 'Tool Management'],
    ['技能管理', 'Skill Management'],
    ['并发任务', 'Concurrent Tasks'],
    ['会话存档', 'Session Archive'],
    ['PortRuntime', 'PortRuntime'],
    ['Token 工厂', 'Token Factory'],
    ['团队成员', 'Team Members'],
    ['新建智能体', 'New Agent'],
    ['模型与连接', 'Models & Connections'],
    ['LLM 配置', 'LLM Config'],
    ['可用工具', 'Available Tools'],
    ['可用技能', 'Available Skills'],
    ['调度器', 'Scheduler'],
    ['运行中', 'Running'],
    ['已停止', 'Stopped'],
    ['自我演进', 'Self Evolution'],
    ['系统合规状态', 'System Compliance'],
    ['创建团队', 'Create Team'],
    ['添加模型', 'Add Model'],
    ['搜索工具名称或描述', 'Search tool name or description...'],
    ['搜索', 'Search'],
    ['编辑', 'Edit'],
    ['删除', 'Delete'],
    ['保存', 'Save'],
    ['取消', 'Cancel'],
    ['刷新', 'Refresh'],
    ['导出', 'Export'],
    ['导入', 'Import'],
    ['批量提交', 'Batch Submit'],
    ['提交任务', 'Submit Task'],
    ['测试连接', 'Test Connection'],
    ['连接成功', 'Connection OK'],
    ['连接失败', 'Connection Failed'],
    ['正在测试连接', 'Testing connection...'],
    ['后重试', 'retry'],
    ['暂无模型', 'No models'],
    ['暂无工具', 'No tools'],
    ['暂无技能', 'No skills'],
    ['暂无任务', 'No tasks'],
    ['暂无会话', 'No sessions'],
    ['暂无日志', 'No logs'],
    ['加载中', 'Loading'],
    ['就绪', 'Ready'],
    ['待命中', 'Idle'],
    ['工作中', 'Working'],
    ['汇报中', 'Reporting'],
    ['阻塞', 'Blocked'],
    ['全部', 'All'],
    ['智能体团队', 'Agent Team'],
    ['系统演进', 'System Evolution'],
    ['技能萃取/赋予', 'Skill Extract'],
    ['数字孪生', 'Digital Twin'],
    ['SECS沙箱', 'SECS Sandbox'],
    ['议事广场', 'Plaza'],
    ['仪表盘', 'Dashboard'],
    ['运行时', 'Runtime'],
    ['创建', 'Create'],
    ['添加', 'Add'],
    ['关闭', 'Close'],
    ['名称', 'Name'],
    ['描述', 'Description'],
    ['角色', 'Role'],
    ['状态', 'Status'],
    ['设置', 'Settings'],
    ['提交', 'Submit'],
    ['全体', 'All'],
    ['登录', 'Login'],
    ['注册', 'Register'],
    ['密码', 'Password'],
    ['用户名', 'Username'],
    ['配置已保存', 'Config saved'],
    ['保存失败', 'Save failed'],
    ['编辑模型', 'Edit Model'],
    ['模型名称', 'Model Name'],
    ['提供商', 'Provider'],
    ['基础信息', 'Basic Info'],
    ['人格设定', 'Personality'],
    ['技能配置', 'Skill Config'],
    ['工具绑定', 'Tool Binding'],
    ['权限与通道', 'Permissions'],
    ['上一步', 'Previous'],
    ['下一步', 'Next'],
    ['完成创建', 'Finish'],

// ─── Common unit/context phrases (safe multi-char) ───
    ['低风险', 'Low risk'], ['高风险', 'High risk'], ['中风险', 'Medium risk'],
    ['低速', 'Low speed'], ['高速', 'High speed'], ['中速', 'Medium speed'],
    ['低压', 'Low pressure'], ['高压', 'High pressure'],
    ['船员', 'Crew'], ['人员', 'Personnel'], ['人数', 'Headcount'],
    ['秒/次', 'sec/time'], ['每秒', '/sec'], ['分钟', 'min'],
  ]);

  /* ── Single-char icon map: zh char → en icon ── */
  const ICON_MAP = new Map([
    ['舵', '⚓'], ['航', '🧭'], ['定', '📍'], ['推', '⚙'],
    ['安', '🛡'], ['能', '⚡'], ['演', '🔄'], ['智', '🤖'],
    ['孪', '🔮'], ['域', '🌐'], ['岸', '📡'], ['洋', '🌊'],
    ['员', '👥'], ['维', '🔧'], ['作', '🏗'], ['训', '🎯'],
    ['海', '🌊'], ['球', '🌐'], ['舶', '🚢'], ['港', '⚓'],
    ['气', '☁'], ['话', '💬'], ['樹', '🌳'], ['问', '❓'],
    ['令', '⌘'], ['停', '⛔'], ['报', '📊'], ['燈', '💡'],
    ['笛', '📯'], ['统', '📋'], ['誌', '📝'], ['讯', '📡'],
    ['设', '⚙'], ['象', '🌤'], ['錨', '⚓'], ['録', '📝'],
    ['火', '🔥'], ['弃', '🚤'], ['落', '🆘'], ['碰', '💥'],
    ['搁', '⚠'], ['水', '💧'], ['污', '☢'], ['医', '🏥'],
    ['健', '💚'], ['峰', '🏔'], ['库', '🗄'], ['态', '📈'],
    ['星', '⭐'], ['机', '🖥'], ['紫', '🟣'], ['网', '🌐'],
    ['腦', '🧠'], ['调', '🎛'], ['键', '🔑'], ['駝', '🦙'],
    ['龍', '🐉'], ['冊', '📖'], ['勤', '⏰'], ['証', '📜'],
    ['班', '👮'], ['危', '⚠'], ['查', '🔍'],
    ['流', '〰'], ['浪', '🌊'], ['環', '♻'], ['風', '🌬'],
    ['景', '🏞'], ['介', '📋'], ['待', '⏳'], ['鎖', '🔒'],
    // Numeral seals
    ['壹', '①'], ['贰', '②'], ['叁', '③'], ['肆', '④'], ['伍', '⑤'],
  ]);
  const ICON_REV = new Map();
  for (const [zh, en] of ICON_MAP) ICON_REV.set(en, zh);

  /* ── Inline emoji → Chinese char map (Wabi Sabi restoration) ──
     Used to replace hardcoded emoji in multi-char text nodes during zh mode.
     Curated: one Chinese char per emoji, chosen for best semantic fit. */
  const EMOJI_ZH = new Map([
    ['⚓', '舵'], ['🧭', '航'], ['📍', '定'],
    ['🛡', '安'], ['🛡️', '安'],
    ['⚡', '能'], ['⚡️', '能'],
    ['🔄', '演'], ['🤖', '智'],
    ['🔮', '孪'], ['🌐', '域'],
    ['📡', '岸'], ['🌊', '浪'],
    ['👥', '员'], ['🔧', '维'],
    ['🏗', '作'], ['🏗️', '作'],
    ['🎯', '训'],
    ['☁', '气'], ['☁️', '气'],
    ['🌤', '象'], ['🌤️', '象'],
    ['🌬', '風'], ['🌬️', '風'],
    ['🏞', '景'], ['🏞️', '景'],
    ['📊', '报'], ['📋', '统'],
    ['📈', '态'], ['📝', '誌'],
    ['🖥', '机'], ['🖥️', '机'],
    ['🧠', '腦'], ['🎛', '调'], ['🎛️', '调'],
    ['⚠', '危'], ['⚠️', '危'],
    ['🔥', '火'], ['💥', '碰'],
    ['🆘', '落'], ['🚤', '弃'],
    ['💧', '水'], ['☢', '污'], ['☢️', '污'],
    ['🏥', '医'], ['💚', '健'],
    ['⚙', '设'], ['⚙️', '设'],
    ['💡', '燈'], ['🔑', '键'], ['🔒', '鎖'],
    ['🔍', '查'], ['💬', '话'], ['❓', '问'],
    ['⌘', '令'], ['⛔', '停'],
    ['🚢', '舶'], ['⭐', '星'],
    ['🟣', '紫'], ['🐉', '龍'], ['🦙', '駝'],
    ['🌳', '樹'], ['📖', '冊'], ['⏰', '勤'],
    ['📜', '証'], ['👮', '班'],
    ['〰', '流'], ['♻', '環'], ['♻️', '環'],
    ['⏳', '待'], ['📯', '笛'],
    ['🗄', '库'], ['🏔', '峰'], ['🏔️', '峰'],
    ['①', '壹'], ['②', '贰'], ['③', '叁'], ['④', '肆'], ['⑤', '伍'],
    // Additional inline emoji found across pages
    ['📥', '入'], ['📤', '出'], ['🏭', '厂'],
    ['📁', '档'], ['👤', '人'], ['📅', '日'],
    ['🧬', '因'], ['📦', '包'], ['🗑', '删'],
    ['💾', '存'], ['📄', '页'], ['🔴', '活'],
    ['🎮', '戏'], ['👁', '目'],
  ]);
  /* Fast emoji detection: any char from EMOJI_ZH keys */
  const _emojiChars = [...EMOJI_ZH.keys()].map(e =>
    e.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&')
  ).join('|');
  const EMOJI_PATTERN = new RegExp(_emojiChars);

  /* ── Reverse map: en → zh ── */
  const REV_MAP = new Map();
  for (const [zh, en] of TEXT_MAP) REV_MAP.set(en, zh);

  /* ── Legacy DICT for data-i18n attribute compatibility ── */
  const DICT = {
    'nav.captain':     { zh: '船长总览', en: 'Captain' },
    'nav.navigation':  { zh: '导航',   en: 'Navigation' },
    'nav.dp':          { zh: '动力定位', en: 'DP Control' },
    'nav.thruster':    { zh: '推进控制', en: 'Thruster' },
    'nav.monitor':     { zh: '全船监控', en: 'Monitor' },
    'nav.cms':         { zh: '设备健康', en: 'CMS Health' },
    'nav.hmi':         { zh: '控制台',  en: 'HMI Console' },
    'nav.offshore':    { zh: '海工作业', en: 'Offshore Ops' },
    'nav.weather':     { zh: '气象海洋', en: 'Weather' },
    'nav.crew':        { zh: '船员管理', en: 'Crew Mgmt' },
    'nav.sim':         { zh: '仿真训练', en: 'Simulation' },
    'nav.energy':      { zh: '能效合规', en: 'Energy' },
    'nav.datacenter':  { zh: '船载数据中心', en: 'Datacenter' },
    'nav.safety':      { zh: '安全应急', en: 'Safety' },
    'nav.shore':       { zh: '船岸协同', en: 'Ship-Shore' },
    'nav.twin':        { zh: '数字孪生', en: 'Digital Twin' },
    'nav.agents':      { zh: '智能体',  en: 'AI Agents' },
    'nav.evolution':   { zh: '系统演进', en: 'Evolution' },
    'nav.kb':          { zh: '知识库',  en: 'Knowledge' },
    'nav.llm-config':  { zh: 'LLM 配置', en: 'LLM Config' },
    'ui.language':     { zh: '中/EN',  en: 'EN/中' },
  };

  function getLang() {
    const saved = localStorage.getItem(STORAGE_KEY);
    return (saved && LANGS.includes(saved)) ? saved : 'zh';
  }

  function setLang(lang) {
    if (!LANGS.includes(lang)) return;
    localStorage.setItem(STORAGE_KEY, lang);
    applyAll();
    window.dispatchEvent(new CustomEvent('px-lang-change', { detail: { lang } }));
  }

  function toggleLang() {
    setLang(getLang() === 'zh' ? 'en' : 'zh');
  }

  function t(key) {
    const entry = DICT[key];
    if (!entry) return key;
    return entry[getLang()] || entry.zh || key;
  }

  /* Register legacy data-i18n keys */
  function register(translations) {
    for (const [key, val] of Object.entries(translations)) DICT[key] = val;
  }

  /* Add text pairs to TEXT_MAP: { 'zh': 'en', ... } */
  function addTexts(pairs) {
    for (const [zh, en] of Object.entries(pairs)) {
      TEXT_MAP.set(zh, en);
      REV_MAP.set(en, zh);
    }
  }

  /* ── Sort keys by length descending for greedy matching ── */
  let _sortedZh = null, _sortedEn = null;
  function getSortedKeys(map, minLen) {
    return [...map.keys()].filter(k => k.length >= minLen).sort((a, b) => b.length - a.length);
  }

  /* ── Check if string contains Chinese ── */
  const HAS_ZH = /[\u4e00-\u9fff]/;

  /* ── Translate a text string ── */
  function translateText(text, toLang) {
    if (!text || !text.trim()) return text;
    if (toLang === 'en') {
      if (!HAS_ZH.test(text)) return text;
      // Only match keys with length >= 2 to avoid single-char corruption
      if (!_sortedZh) _sortedZh = getSortedKeys(TEXT_MAP, 2);
      let result = text;
      for (const zh of _sortedZh) {
        if (result.includes(zh)) {
          result = result.split(zh).join(TEXT_MAP.get(zh));
        }
      }
      return result;
    } else {
      // For zh mode: allow mixed text (Chinese icon char + English) to be translated.
      // Only skip if there are NO English letter sequences (2+ chars) at all.
      const hasEnglish = /[a-zA-Z]{2,}/.test(text);
      if (!hasEnglish) return text;
      // Only match keys with length >= 2 to avoid empty/short key corruption
      if (!_sortedEn) _sortedEn = getSortedKeys(REV_MAP, 2);
      let result = text;
      for (const en of _sortedEn) {
        if (result.includes(en)) {
          result = result.split(en).join(REV_MAP.get(en));
        }
      }
      return result;
    }
  }

  /* ── Walk DOM text nodes and translate ── */
  function walkAndTranslate(root, lang) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const p = node.parentElement;
        if (!p) return NodeFilter.FILTER_REJECT;
        const tag = p.tagName;
        if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'NOSCRIPT') return NodeFilter.FILTER_REJECT;
        if (node.textContent.trim().length < 1) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      let text = node.textContent;
      const trimmed = text.trim();
      // Single-char icon replacement (standalone icon text nodes)
      if (trimmed.length === 1) {
        if (lang === 'en' && ICON_MAP.has(trimmed)) {
          node.textContent = text.replace(trimmed, ICON_MAP.get(trimmed));
          continue;
        } else if (lang === 'zh' && ICON_REV.has(trimmed)) {
          node.textContent = text.replace(trimmed, ICON_REV.get(trimmed));
          continue;
        }
      }

      let modified = text;

      // ── Wabi Sabi: inline emoji ↔ Chinese char replacement ──
      if (lang === 'zh' && EMOJI_PATTERN.test(text)) {
        // zh mode: replace inline emoji with Chinese characters
        for (const [emoji, zh] of EMOJI_ZH) {
          if (modified.includes(emoji)) {
            modified = modified.split(emoji).join(zh);
          }
        }
        // Strip leftover variant selectors (U+FE0F) after emoji replacement
        modified = modified.replace(/\uFE0F/g, '');
      }

      // ── Text translation (phrase-level) ──
      const translated = translateText(modified, lang);
      if (translated !== modified) modified = translated;

      // ── en mode: restore leading icon char to emoji ──
      if (lang === 'en') {
        const lead = modified.trimStart().charAt(0);
        if (ICON_MAP.has(lead) && modified.trimStart().length > 1) {
          const idx = modified.indexOf(lead);
          modified = modified.slice(0, idx) + ICON_MAP.get(lead) + modified.slice(idx + 1);
        }
      }

      if (modified !== text) node.textContent = modified;
    }
  }

  /* ── Translate attributes: placeholder, title, aria-label ── */
  function translateAttrs(root, lang) {
    const attrs = ['placeholder', 'title', 'aria-label'];
    root.querySelectorAll('[placeholder],[title],[aria-label]').forEach(el => {
      for (const attr of attrs) {
        const val = el.getAttribute(attr);
        if (val) {
          const tr = translateText(val, lang);
          if (tr !== val) el.setAttribute(attr, tr);
        }
      }
    });
  }

  /* ── Translate <option> text ── */
  function translateOptions(root, lang) {
    root.querySelectorAll('option').forEach(opt => {
      const tr = translateText(opt.textContent, lang);
      if (tr !== opt.textContent) opt.textContent = tr;
    });
  }

  /* ── Main apply function ── */
  function applyAll() {
    const lang = getLang();
    _sortedZh = null;
    _sortedEn = null;

    // 1. Legacy data-i18n attributes
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const entry = DICT[key];
      if (entry) el.textContent = entry[lang] || entry.zh || el.textContent;
    });
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
      const key = el.getAttribute('data-i18n-title');
      const entry = DICT[key];
      if (entry) el.title = entry[lang] || entry.zh || el.title;
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      const entry = DICT[key];
      if (entry) el.placeholder = entry[lang] || entry.zh || el.placeholder;
    });

    // 2. DOM text walker — translate all visible text
    if (document.body) walkAndTranslate(document.body, lang);

    // 3. Translate attributes
    if (document.body) translateAttrs(document.body, lang);

    // 4. Translate <option> elements
    if (document.body) translateOptions(document.body, lang);

    // 5. Update <title>
    if (document.title) document.title = translateText(document.title, lang);

    // 6. Update html lang
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';

    // 7. Font stack switch — WS Rubber consistent
    applyFontStack(lang);

    // 8. Update language toggle button
    const btn = document.getElementById('px-lang-btn');
    if (btn) btn.textContent = lang === 'zh' ? '中/EN' : 'EN/中';
  }

  /* ── Font stack switching for WS Rubber consistency ── */
  const FONT_STYLE_ID = 'px-i18n-fonts';
  function applyFontStack(lang) {
    let style = document.getElementById(FONT_STYLE_ID);
    if (lang === 'en') {
      // English: put Latin-optimized fonts first, Chinese fallback after
      const css = `
        /* PX i18n: English font overrides — WS Rubber aesthetic */
        body, [class*="name"], [class*="label"], [class*="desc"],
        .m-name, .emit-info .name, .rating-name, .rating-desc,
        td, th, span, p, div, li, a, button, input, select, textarea {
          font-family: 'Noto Sans', 'Noto Sans SC', system-ui, sans-serif !important;
        }
        h1, h2, h3, h4, h5, h6, .sigil, .m-seal,
        [class*="seal"], [class*="title"], [class*="header"],
        .ob-topbar-title, .ob-sidebar-label {
          font-family: 'Noto Serif', 'Noto Serif SC', Georgia, serif !important;
        }
        code, pre, .subtitle, .status, .foot, .enter-btn,
        [class*="mono"], [class*="code"], [class*="badge"],
        [class*="stat"], [class*="val"], [class*="num"],
        .ob-tag, .doc-table th {
          font-family: 'JetBrains Mono', 'IBM Plex Mono', Menlo, monospace !important;
        }
      `;
      if (!style) {
        style = document.createElement('style');
        style.id = FONT_STYLE_ID;
        document.head.appendChild(style);
      }
      style.textContent = css;
    } else {
      // Chinese: remove overrides, let page CSS handle it
      if (style) style.textContent = '';
    }
  }

  window.PX_I18N = {
    t, getLang, setLang, toggleLang, register, addTexts, applyAll, translateText, DICT, TEXT_MAP
  };

  function onReady() { applyAll(); }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', onReady);
  } else {
    onReady();
  }
})();
