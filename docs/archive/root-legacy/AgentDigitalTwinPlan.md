# Agent Digital Twin 全局优化计划

## 核心理念

以 **团队 + 场景** 为基础，驱动 Agent 的 **演练 → 评估 → 进化** 闭环。

```
选团队 ──→ 选场景 ──→ 启动演练 ──→ 仿真运行 ──→ 评分/SOP ──→ 策略注入 ──→ 再演练
  │          │           │            │             │              │
  ▼          ▼           ▼            ▼             ▼              ▼
左栏联动   3D房间切换   SSE流启动   Pipeline动画  结果展示       SECS Loop回流
```

---

## 一、页面布局

```
┌─────────────────────────────────────────────────────────┐
│ 顶栏导航: 智能体团队 | 广场 | 技能 | 数字孪生 | 演进 | 成本 │
├──────────┬───────────────────────────────┬──────────────┤
│ 左栏 240 │       中心区 (6 Tab)           │ 右栏 280     │
│          │                               │              │
│ 团队标签  │ 📡 系统状态                    │ 🎯 演练控制   │
│ Build    │ ⇄ 交互流                      │  KPI 条      │
│ AI Coding│ ▷ 编排管线                     │  团队选择     │
│ ...      │ 🌐 环境空间 (3D + 演练联动)     │  场景选择     │
│          │ ⌨ CLI                        │  仿真参数     │
│ 智能体   │ 🎯 SECS 演练 (完整面板)        │  ▶ 启动演练   │
│ 列表     │   Pipeline L1→L4              │  收益图       │
│          │   I/O Grid                    │  仿真结果     │
│          │   协作图                       │              │
└──────────┴───────────────────────────────┴──────────────┘
```

---

## 二、核心数据流

### 2.1 团队选择 → 全局同步

```
用户操作                数据流向                  UI 反馈
───────                ────────                 ───────
左栏点团队标签    →    window.S.selectedTeams    →  右栏按钮文字更新
右栏弹窗选团队    →    window.S.selectedTeams    →  左栏标签高亮
                    →    renderAgentList()       →  智能体列表刷新
                    →    secs-team-select下拉    →  右栏原生下拉同步
```

### 2.2 场景选择 → 3D 联动

```
用户操作                数据流向                  UI 反馈
───────                ────────                 ───────
右栏弹窗选场景    →    _dt3dBuildRoom(room)     →  3D 场景切换
                    →    flyToRoom(room)        →  摄像机飞入
                    →    右栏标签更新           →  场景名显示
切换环境空间Tab   →    _currentRoomId          →  右栏自动同步当前场景名
```

### 2.3 演练运行 → 实时反馈

```
▶ 启动演练
  │
  ├─ POST /api/v1/sandbox/sessions  创建会话 (带 team_id + sync_dt)
  ├─ POST /sessions/{id}/run        触发运行
  └─ EventSource /sessions/{id}/stream  SSE 流
       │
       ├─ type: step
       │   ├─ 收益曲线更新 (中心 + 右栏双图表)
       │   ├─ Pipeline L1→L4 步进动画 (pending → running → done)
       │   ├─ 步数计数器
       │   └─ 协作图通信脉冲 (如有 agent_actions)
       │
       └─ type: complete
           ├─ Pipeline 全部 done + EVOLVE 节点高亮
           ├─ 综合评分展示
           ├─ SOP 提取结果
           └─ 策略注入按钮
```

---

## 三、SECS 演练 Tab 面板内容

### 3.1 中心面板

| 区域 | 内容 | 数据源 |
|------|------|--------|
| Pipeline 条 | L1 MADTwin → L2 AAS → L3 TwinLoop → L4 MADCG → SECS Loop 回流 | SSE step 事件 |
| Session Bar | 沙箱 ID / 步数 / 状态 (空闲→运行中→完成) | SSE + API |
| I/O Grid 左 | 任务描述 / 仿真参数 (模式+步数) | session 详情 |
| I/O Grid 右 | 收益曲线 SVG (400×60) + 步数/最大值 | SSE step |
| 协作图 | 5 角色 SVG (Planner/Retriever/Coordinator/Executor/Critic) [5v7] | SSE agent_actions |
| 启动/停止 | ▶ 启动演练 / ⏹ 停止 | 右栏参数同步 |

### 3.2 右栏控制面板 (始终可见)

| 区域 | 内容 |
|------|------|
| KPI | 沙箱会话 / 总仿真步 / 最优评分 |
| 团队选择 | 👥 按钮 → Modal 弹窗 → 全团队列表 → 联动左栏 |
| 场景选择 | 🏟️ 按钮 → Modal 弹窗 → 6 房间 → 联动 3D |
| 仿真参数 | What-if/并行/演化 + 步数滑块 |
| 收益图 | 迷你折线图 (240×60) |
| 仿真结果 | 综合评分 + 五维指标 + SOP + 建议 + 注入按钮 |

---

## 四、Pipeline 动画规则

```
步进进度           Pipeline 状态
────────          ─────────────
0%     (启动)     L1 running, L2-L4 pending
25%               L1 done, L2 running
50%               L2 done, L3 running
75%               L3 done, L4 running
100%   (完成)     全部 done + EVOLVE done (绿色高亮)
```

---

## 五、已修复的问题

1. ~~KPI id 不匹配 (strip-sessions → kpi-sessions)~~ 已修复
2. ~~Runtime 抽屉渲染目标错误~~ 已合并到新页面
3. ~~双重团队选择器不联动~~ 已联动 (setInterval + MutationObserver)
4. ~~rp-default 删除导致 JS 崩溃~~ 保留隐藏占位 div
5. ~~重复图表 ID~~ 分拆为 secs-reward-chart / rp-reward-chart
6. ~~场景选择不切 3D~~ 已接入 _dt3dBuildRoom / flyToRoom

---

## 六、待实现

| 优先级 | 功能 | 说明 |
|--------|------|------|
| P0 | 协作图通信脉冲 | SSE step 中 agent_actions → 连线高亮 |
| P0 | SOP 提取展示 | complete 事件显示 best_sop |
| P1 | 策略注入 | inject → POST /sessions/{id}/inject |
| P1 | 演练历史 | 在 SECS 面板底部显示近 20 次历史 |
| P1 | 评分五维雷达 | 任务完成率/通信效率/资源利用/冲突避免/收敛速度 |
| P2 | 3D 场景 Agent 位置同步 | 仿真步骤驱动 Agent 在 3D 场景中移动/发光 |
| P2 | 语音对话 | TTS 播报仿真对话 |

---

## 七、文件清单

```
src/frontend/Agent-digital-twin.html    ← 合并后的主页面 (950 行)
src/frontend/js/digital-twin-cli.js     ← 数字孪生逻辑 (不变)
src/frontend/js/digital-twin-cli-3d.js  ← 3D 引擎 (不变)
src/backend/sandbox/api.py              ← SECS API (不变)
src/backend/sandbox/orchestrator.py     ← 编排器 (不变)
```

所有其他页面导航已指向 `Agent-digital-twin.html`。
