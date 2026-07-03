---
name: digital-twin-vision-center-refactor
overview: 将Agent-digital-twin.html进行四阶段深度重构：第一阶段实现视觉中心化（环境空间为主舞台）；第二阶段建立交互神经链路（全局联动+事件弹幕+动画控制闭环）；第三阶段构建混沌沙箱（故障注入增强+失败复现+收益曲线）；第四阶段实现进化反哺循环（萃取可视化+升级动效+分屏对比）。
design:
  architecture:
    framework: html
  styleKeywords:
    - Cyberpunk Dark UI
    - Holographic
    - Pulse Animation
    - Glassmorphism Panels
    - Neural Network Visualization
    - Data Flow Aesthetic
  fontSystem:
    fontFamily: "'Inter','Noto Sans SC',sans-serif"
    heading:
      size: 20px
      weight: 600
    subheading:
      size: 14px
      weight: 500
    body:
      size: 12px
      weight: 400
  colorSystem:
    primary:
      - "#22D3EE"
      - "#34D399"
      - "#FBBF24"
      - "#A78BFA"
    background:
      - "#0D1117"
      - "#111820"
      - "#161D27"
      - "#1E2636"
    text:
      - "#E2E8F0"
      - "#CBD5E1"
      - "#8B9AB5"
      - "#576375"
    functional:
      - "#F87171"
      - "#60A5FA"
      - "#F472B6"
todos:
  - id: p1-layout-reset
    content: 重构页面布局：nav顺序调整(环境空间置首)、center区域默认显示view-environment、view-architecture内容压缩为可折叠浮动卡
    status: completed
  - id: p1-room-fx
    content: 实现六房间CSS动效：room-pulse(能量脉冲)/room-alert(红色预警)/room-cracked(裂纹)，在SSE step事件中根据agent_actions和chaos_events动态切换class
    status: completed
  - id: p1-agent-move
    content: 实现Agent动态移动：新增animateAgentMove()函数，requestAnimationFrame插值动画，启动演练时Agent从休息区平滑过渡到目标房间
    status: completed
  - id: p2-global-linkage
    content: 建立全局上下文联动：点击左侧团队卡片调用flyToRoom定位房间；点击房间切换右侧场景配置；switchView函数增强联动逻辑
    status: completed
  - id: p2-event-barrage
    content: 实现事件弹幕层：env-3d-container上方叠加绝对定位弹幕容器，step事件生成气泡定位到Agent屏幕坐标，CSS动画floatIn→停留→fadeOut下沉控制台
    status: completed
  - id: p2-step-linkage
    content: 单步逻辑连线可视化：step事件messages数组驱动SVG连线(from→to)，stroke-dashoffset动画模拟信号传输，与sexyStepOnce()节奏闭环
    status: completed
  - id: p3-inject-enhance
    content: 故障注入增强：btn-inject-fault升级为dropdown菜单(模型幻觉/网络延迟/逻辑死锁/技能退化)，注入后房间进入room-unhealthy亚健康视觉态(暗红边框+抖动)
    status: completed
  - id: p3-history-replay
    content: 失败历史复现：演练历史红色标记失败记录，点击后在环境空间中回放session步骤，新增playbackStep(index)逐帧重放Agent分布
    status: completed
  - id: p3-reward-inline
    content: 收益曲线内嵌：将IO面板收益曲线SVG克隆到env-3d-container右下角浮动卡片，绑定_sx.rewardPoints实时更新，移除IO面板中原位置
    status: completed
  - id: p4-extract-viz
    content: 萃取可视化：SSE complete事件+评分达标触发萃取室房间节点上方CSS徽章(✦SOP)，点击展开策略摘要浮层
    status: completed
  - id: p4-upgrade-fx
    content: Agent升级动效：报告注入优化策略后Agent节点触发CSS @keyframes agentUpgrade光圈扩散+色相旋转动画(青→金渐变)
    status: completed
  - id: p4-parallel-view
    content: 并行演化对比：parallel模式下env-3d-container改为Grid分屏布局，每列独立canvas或分区渲染，提供branch标签切换器
    status: completed
---

## Product Overview

对 Agent-digital-twin.html 进行四阶段深度重构，将数字孪生页面从"数据展示面板"进化为"会呼吸、能试错、会进化的智能体数字沙箱"。

## Core Features

### 第一阶段：视觉中心化（Digital Twin First）

- **舞台重置**：环境空间（3D Canvas + 六房间视图）从导航第四位提升至默认主舞台，进入页面即见
- **仪表盘/拓扑降级**：原"系统状态"面板（仪表盘+协作拓扑）收缩为环境空间周边的浮动信息卡或底部状态条
- **房间动效**：六房间（议事厅/萃取室/工作坊/知识库/演练场/休息区）添加 CSS 动画 -- Agent 执行任务时房间有能量脉冲亮度变化；故障注入时红色预警裂纹效果
- **Agent 动态移动**：启动演练后，代表 Agent 的节点从休息区平滑过渡到工作坊等目标房间

### 第二阶段：交互神经链路（Neural Linkage）

- **全局联动**：点击左侧团队卡片 → 环境空间自动 Fly-to 到该团队所在房间；点击环境空间中的房间 → 右侧场景自动适配
- **事件弹幕**：在 3D 空间或平面视图中叠加"弹幕层"，Agent 关键决策（Developer 修复 Bug / 收益值变化）以气泡形式在对应位置弹出，随后下沉到日志
- **动画节奏闭环**：单步执行时，空间内显示当前步的"逻辑连线"（谁给谁发消息的 SVG 连线）；暂停时冻结所有动画；自动运行时按 speed_factor 调节动画速率

### 第三阶段：混沌沙箱（Chaos Sandbox）

- **故障注入增强**：💥 注入故障按钮升级为下拉菜单（模型幻觉/网络延迟/逻辑死锁/技能退化）；注入后受影响房间进入"亚健康"视觉态（暗红边框+抖动+降低透明度）
- **失败历史复现**：演练历史列表中失败记录用红色标记；点击后在环境空间中"回放"崩溃时刻的 Agent 分布和最后一步状态
- **收益曲线内嵌**：将右侧 IO 面板中的收益曲线迷你图移到环境空间右下角浮动卡片，实时反映空间行为→价值产出

### 第四阶段：进化反哺（Darwinian Loop）

- **萃取可视化**：演练完成且评分达标时，萃取室房间节点上方浮现"精华产出"图标（✦ SOP徽章），点击展开提取的策略摘要
- **策略升级动效**：报告中点击"注入优化策略"后，对应 Agent 节点触发光圈变色升级动画（青→金渐变脉冲）
- **并行演化对比**：开启 parallel 模式时，环境空间提供分屏/图层切换视图，同时观察多组分支策略在同一房间的演化差异

## Tech Stack

- **前端框架**: 纯 HTML + Vanilla JS（现有架构不变，不引入 React/Vue）
- **3D 渲染**: 现有 `digital-twin-cli-3d.js` (Three.js module)
- **样式**: 内联 CSS（`Agent-digital-twin.html` 第10-349行） + CSS 变量体系
- **状态管理**: 全局对象 `S` (`digital-twin-cli.js`) + `_sx` (SECS 会话状态) + `window.S` (3D 状态)
- **后端 API**: FastAPI（已有 `/step`, `/pause`, `/run`, `/inject` 端点）

## Implementation Approach

### 核心设计决策

1. **布局重构策略**：采用"中心舞台 + 浮动辅助"布局模式。将 `.center` 区域从"多 View 切换"改为"环境空间为主 + 其他 View 为覆盖层/抽屉"。具体做法：

- 默认激活 `view-environment` 而非 `view-architecture`
- 原 view-architecture 内容压缩为可折叠的底部状态栏或左上角浮动卡
- 导航栏顺序调整：[环境空间] [交互流] [编排管线] [系统状态] [CLI]

2. **房间动效实现方案**：

- 使用纯 CSS `@keyframes` 定义 `room-pulse`（能量脉冲）、`room-alert`（红色预警）、`room-cracked`（裂纹闪烁）三类动画
- 通过 JS 在 SSE step 事件中根据 `agent_actions` 和 `chaos_events` 切换房间 CSS class
- 不依赖 Three.js 做房间级动效（保持性能），3D 引擎仅负责 Agent 节点和连线渲染

3. **Agent 移动实现方案**：

- 在 3D Canvas 中利用已有的 `flyToRoom()` / `switchRoom()` 机制扩展
- 新增 `animateAgentMove(agentId, fromRoom, toRoom)` 函数
- 使用 `requestAnimationFrame` 驱动插值动画（线性插值 + easeOutCubic 缓动）
- 移动路径沿房间坐标的直线/贝塞尔曲线

4. **事件弹幕层**：

- 在 `env-3d-container` 上方叠加绝对定位的 `<div id="event-barrage">`
- 每个 step 事件生成一个 `.barrage-bubble` 元素，定位到对应 Agent 的屏幕坐标
- CSS animation: `barrageFloatIn` → 3秒停留 → `barrageFadeOut` 下沉到控制台

5. **单步逻辑连线**：

- 在 3D 场景或 2D 平面图中叠加临时 SVG/SVG layer
- step 事件的 `messages` 数组决定连线（from → to）
- 使用 `stroke-dashoffset` 动画模拟信号传输效果
- 单步结束后保留连线直到下一步（或 2 秒后淡出）

6. **故障注入增强**：

- 将 `btn-inject-fault` 从单一按钮改为带 dropdown 的复合按钮（CSS only dropdown，无额外库依赖）
- 注入类型映射到后端 `/inject` 接口的 `event_type` 参数
- 房间亚健康态通过新增 CSS class `room-unhealthy` 实现

7. **历史回放**：

- 利用已有的 session 详情 API（`GET /sessions/{id}`）获取完整 steps 数据
- "回放模式"下按时间轴逐帧重放 step 状态到环境空间
- 新增 `playbackStep(index)` 函数，复用 `renderEnvironment` + Agent 位置更新逻辑

8. **收益曲线内嵌**：

- 将 `sub-reward` 中的 SVG 图表克隆到 `env-3d-container` 右下角浮动卡
- 数据源直接绑定 `_sx.rewardPoints` 数组
- 每次 step/pause 更新时同步刷新

9. **萃取可视化 & 升级动效**：

- SSE `complete` 事件 + `evaluation.global_score > threshold` 触发萃取图标
- 萃取图标为绝对定位的 CSS 徽章元素，附带动效
- Agent 升级使用 CSS `@keyframes agentUpgrade`（光圈扩散 + 色相旋转）

10. **并行演化对比**：

    - parallel 模式下将 `env-3d-container` 改为 CSS Grid 2列/3列布局
    - 每列是一个独立的 canvas 或共享 canvas 的分区渲染
    - 提供标签切换器切换不同 branch 的视角

## Architecture Design

```
重构后的页面结构:
┌──────────────────────────────────────────────────────────────┐
│ Header Nav: [🌐环境空间★] [⇄交互流] [▷管线] [◈系统] [>CLI] │
├──────────┬─────────────────────────────────┬─────────────────┤
│ Left     │ Center Stage                    │ Right          │
│ Panel    │                                 │ SECS Panel     │
│ (240px)  │  ┌───────────────────────────┐  │ (580px)        │
│          │  │  ┌─────┐ ┌─────┐ ┌─────┐  │  │ ┌───────────┐  │
│ 团队列表  │  │  │议事厅│ │萃取室│ │工作坊│  │  │ KPI 条     │  │
│ + 选择器  │  │  └─────┘ └─────┘ └─────┘  │  │ Runtime    │  │
│          │  │  ┌─────┐ ┌─────┐ ┌─────┐  │  │ Pipeline   │  │
│ Agent    │  │  │知识库│ │演练场│ │休息区│  │  │ Session    │  │
│ 卡片列表  │  │  └─────┘ └─────┘ └─────┘  │  │ 配置       │  │
│          │  │         3D / 平面视图        │  │ 参数+注入   │  │
│          │  │  [弹幕气泡层] [收益曲线☆]   │  │ [▶][⏸][⏯] │  │
│          │  │  [逻辑连线SVG层]            │  │ 实时控制台  │  │
│          │  │  [萃取图标✦] [升级光环]     │  │ IO面板      │  │
│          │  └───────────────────────────┘  │  │ 历史记录   │  │
│          │  ── 浮动: 仪表盘摘要 ──        │  │ 协作图     │  │
│          │                                  │               │  │
├──────────┴─────────────────────────────────┴─────────────────┤
│  底部状态栏 (collapsible): 运行指标 | 任务队列 | 拓扑缩略图    │
└──────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
src/frontend/
├── Agent-digital-twin.html      # [MODIFY] 主文件：布局重构+CSS动效+JS逻辑
│   ├── CSS (line 10-349)        # 新增: room 动效/barrage/upgrade/parallel 样式
│   ├── HTML layout              # 重构: nav顺序/center stage/right panel
│   └── JS inline                # 新增: 联动/弹幕/回放/对比逻辑
├── js/digital-twin-cli.js       # [MODIFY] 核心 JS: switchView/renderEnvironment 增强
└── js/digital-twin-cli-3d.js    # [MODIFY] 3D引擎: Agent移动/连线/分屏支持
```

## Key Implementation Notes

1. **向后兼容**：所有原有功能保持可用（CLI、Pipeline、Interaction Flow 等 View 通过 Nav 切换）
2. **性能约束**：房间动效用 CSS（GPU 加速），避免每帧 JS 计算；弹幕数量上限 20 个，超出 FIFO 淘汰；3D 场景 Agent 数 >30 时降级为 2D 模式
3. **渐进式加载**：3D 渲染器懒加载（仅在切换到环境空间时初始化），避免首屏阻塞
4. **SSE 事件驱动**：所有空间视觉效果通过已有的 SSE `step` 事件链路触发，不引入新轮询

## SubAgent

- **code-explorer**
- Purpose: 用于探索 digital-twin-cli-3d.js 中 Agent 渲染和移动相关 API，确认 flyToRoom/switchRoom 的接口签名和 3D 坐标系
- Expected outcome: 明确 3D 引擎暴露的方法列表，为 Agent 动画和分屏对比功能提供精确接口