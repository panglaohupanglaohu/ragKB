# Frontend Big Change Smoke Report
- 日期: 2026-06-13
- 测试用户: regr_1781315262341
- 浏览器: Chromium (headless)
- 后端: http://127.0.0.1:8080
- 结果: 30 PASS / 1 FAIL / 0 SKIP

## 按钮回归清单
- [x] 🟢 注册: user=regr_1781315262341
- [x] 🔑 登录: undefined
- [x] 📄 页面加载: title="智能体数字孪生 — AgentsGroup2026"
- [x] 📏 HTML行数 <1500: lines=1148
- [x] 🏗️ _DTS 初始化: undefined
- [x] 🏗️ _sx 初始化: undefined
- [x] 👥 获取团队列表: count=6, first="build_system"
- [x] 👥 选择团队: team_id=build_system
- [x] 🧪 创建试炼: status=ready, trialId=OK
- [x] ▶ 单步推演: step=0
- [x] ▶▶ 自动推演启动: run started
- [x] ▶▶ 自动推演暂停: paused
- [x] ⏸ pauseSim: undefined
- [x] 🔀 分裂分支: 1 → 2 branches
- [x] 💥 注入:network_delay: undefined
- [x] 💥 注入:agent_leave: undefined
- [x] 💥 注入:task_change: undefined
- [x] 💥 注入:skill_degraded: undefined
- [x] 💥 注入:model_hallucination: undefined
- [x] 💥 注入:logic_deadlock: undefined
- [x] 📊 评分 evaluateTrial: total_score=36%, resilience=100%
- [x] 📋 SOP 提取: sops=1
- [x] 🔄 反哺 feedback: undefined
- [x] ⏹ 终止 terminate: status=idle
- [x] 🏥 roomAgentMap 单源诊断: same_ref=true, positions=0
- [x] 🔲 平面视图切换: undefined
- [x] 🔲 3D视图切换回: undefined
- [x] 🏗️ 系统状态视图: undefined
- [x] 💻 CLI 视图: undefined
- [x] 🔀 交互流视图: undefined
- [!] 🚨 Console Errors: 1 errors

## Console Errors
- Loading the stylesheet 'https://cdn.jsdelivr.net/npm/lucide-static@0.263.1/font/lucide.min.css' violates the following Content Security Policy directive: "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com". Note that 'style-src-elem' was not explicitly set, so 'style-src' is used as a fallback. The action has been blocked.

## 后端版本
- commit: unknown