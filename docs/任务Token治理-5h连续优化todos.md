<!-- docs-signoff: author="Grok" kind="llm" doc="todos" ts="2026-07-16T06:10:00Z" -->
# cost-dashboard · 5 小时连续优化（R11）

> **状态：COMPLETE · 调度已停** — H0–H4 / P1–P3 全勾；无未完成 H 项；25m 任务已取消（停重复劳动）  
> **北极星**：任务 Token 治理页「一页闭环、高密度、可操作」  
> **页面**：`cost-dashboard.html` + `token-workbench.js` + `cost-dashboard.js`

## 时段目标（成功标准）

| # | 标准 | 状态 |
|---|------|------|
| G1 | 主轴 ①→⑤ 无重复大块、无侧支文案 | ✅ |
| G2 | 分析台四合一同一筛选窗口 | ✅ |
| G3 | 试跑中文说明 + 末尾预算建议 | ✅ |
| G4 | Taste 浅色密度统一 | ✅ |
| G5 | node --check + TG pytest 绿 | ✅ |

## 分时待办

### H0 · 基建与导航

- [x] **H0.1** 段锚点迷你导航  
- [x] **H0.2** 分析台筛选 sticky  
- [x] **H0.3** 统一 filter-window 刷新  
- [x] **H0.4** 清理 tgRefreshAll 冲突  

### H1 · 分析台密度

- [x] **H1.1** 效率/建议紧凑样式  
- [x] **H1.2** 图空状态中文  
- [x] **H1.3** 明细表 Taste + 空 run 提示  
- [x] **H1.4** 建议区可操作动词 + 总览动作  

### H2 · 杠杆与试跑

- [x] **H2.1** 窄屏旋钮换行  
- [x] **H2.2** 账单高亮  
- [x] **H2.3** 试跑后刷新账单  
- [x] **H2.4** 关 compress 试跑恢复 UI/dirty  

### H3 · 竞标与生产

- [x] **H3.1** 竞标区 tg-panel 视觉  
- [x] **H3.2** locked → 步骤 6 任务提交链  
- [x] **H3.3** open_eco deep-link 滚动+加载  

### H4 · 稳健与收口

- [x] **H4.1** loadDashboard / cost init 去抖  
- [x] **H4.2** levers/dashboard 失败可见提示  
- [x] **H4.3** node --check + pytest TG  
- [x] **H4.4** 本文件 COMPLETE + memory  

## 自设优化目标（已达成）

1. 单页闭环：杠杆 → 试跑/账单 → 竞标 → 分析，无散落「侧支」  
2. 预算可调且建议贴在试跑结果末尾，无独立验证菜单  
3. 失败路径可看见；settings 不被单测写脏  

## 接续（可选 polish）

- [x] **P1** 竞价席 focus 高亮 + 加载/404 可见错误  
- [x] **P2** 详情「重算质量门」按钮（POST quality-check）  
- [x] **P3** node --check + pytest 绿（调度验收）  

**调度结束**：019f66d64812 已 delete。需再开连续优化时新建 interval 即可。
