---
name: agent-digital-twin-button-level-refactor
overview: 对 Agent-digital-twin.html 页面进行按钮级交互重构，覆盖五大模块：运行时自检、实体联动、仿真执行可视化、报表回溯持久化、优化闭环。修复"加载中"卡死、报表无法展示、场景与空间失联等核心断层。
todos:
  - id: runtime-state
    content: 运行时三态管理：移除硬编码"加载中"，实现loading/在线/离线三态，离线可点击重连，自检按钮控制台流式输出诊断+修复建议
    status: pending
  - id: force-sync
    content: 刷新按钮增强：调用 /api/v1/sandbox/world/sync 强制同步世界状态，同步后刷新stats/history/agent-list
    status: pending
    dependencies:
      - runtime-state
  - id: team-scene-link
    content: 团队-场景全局联动：左侧团队卡片点击同步右侧选择器+Fly-to动画；场景选中触发Layout Reset+Agent瞬移；启动按钮disabled状态管理
    status: pending
  - id: sim-controls
    content: 仿真控制增强：加速倍率改为滑块1x-20x实时生效；新增暂停/继续按钮；新增单步执行按钮
    status: pending
  - id: report-charts
    content: 报告增强：分项评分替换为SVG柱状图；底部增加「下载JSON」「再次运行」「注入优化策略」按钮
    status: pending
  - id: console-streaming
    content: 控制台流式优化：确保SSE步进事件驱动DOM实时更新，非仿真结束后一次性输出
    status: pending
---

## 需求概述

对 Agent-digital-twin.html 页面进行"按钮级交互重构"，解决5大功能断层，将页面从被动看板升级为可交互、可调试、可回溯的智能体指挥中心。

## 核心功能

### 一、系统初始化与自检链路

- **运行时状态标签**：移除硬编码"加载中"，改为三态（在线绿色/离线黄色可点击重连/加载中spinner）
- **自检按钮**：点击后在控制台实时流式输出诊断信息（API、Redis、3D引擎），异常时生成修复建议指令
- **刷新按钮**：增加强制同步功能，调用 `/api/v1/sandbox/world/sync` 校准位置坐标和技能缓存

### 二、实体选择与全局联动

- **左侧团队卡片点击**：自动同步右侧「选择演练团队」按钮，触发环境空间Fly-to动画
- **场景选择弹窗**：重构为场景卡片式，选中后执行环境空间Layout Reset
- **「选择此团队」按钮**：关闭弹窗后自动激活「启动演练」按钮，增加disabled状态管理

### 三、仿真执行与过程可视化

- **启动按钮**：未选团队时disabled状态（灰色不可点击），运行中变为暂停状态
- **单步执行**：新增「⏯ 单步执行」按钮，逐步观察Agent行为
- **加速倍率滑块**：从固定10x改为1x-20x可拖动滑块，拖动实时生效
- **控制台流式输出**：确保SSE事件驱动DOM逐行更新

### 四、报表回溯与数据持久化

- **历史刷新**：检查本地缓存完整性
- **报表图标**：内存失效时通过session_id重新fetch后唤醒报告弹窗
- **报告弹窗**：分项评分替换为SVG柱状图，底部增加「下载JSON」和「再次运行此配置」按钮

### 五、优化循环

- **「注入优化策略」按钮**：将报告建议自动转换为CLI指令填入CLI输入框

## 技术方案

### 实现策略

基于现有纯HTML/CSS/JS架构，通过修改内联脚本实现所有功能。不引入外部依赖库。SSE流式输出已存在，本次优化确保其在控制台中逐行实时更新。SVG柱状图使用原生SVG DOM操作。

### 关键实现点

**1. 运行时三态管理**

- 新增 `_runtimeStatus` 状态变量：`{loading: true, online: false, mode: ''}`
- `loadRuntimeStatus()` 成功时设置 online=true，mode显示；异常时设置 online=false，"离线"标签可点击重试
- 初始加载时显示 spinner 动画（CSS keyframes）

**2. 自检诊断流**

- `runRuntimeSelfCheck()` 中逐步骤 `_logConsole()` 输出检测结果
- 每次检测后 `await new Promise(r => setTimeout(r, 200))` 模拟逐步输出
- 检测项：API可达性 → 运行时模式 → Docker状态 → 3D引擎状态
- 异常时自动输出 `<span class="cmd">fix --xxx</span>` 格式的修复建议

**3. 刷新同步**

- 扩展 `loadRuntimeStatus()` 为 `forceSync()`，调用 `/api/v1/sandbox/world/sync` 同步世界状态
- 同步后刷新所有依赖数据（stats, history, agent list）

**4. 团队-场景联动**

- 左侧团队卡片点击事件中，先调用 `sexySelectTeam(teamId, teamName)` 同步右侧，再调用 `_executeSceneScript` 执行Fly-to
- 场景选择时：先 `_executeSceneScript(sceneId)` 执行Layout Reset，再调用 DigitalTwin3D 的 `flyToRoom()` 动画
- 启动按钮 disabled 管理：`_selectedTeamId` 为空时 `btn.disabled=true; btn.style.opacity='0.4'`

**5. 仿真控制增强**

- 新增 `_simSpeed` 变量替代硬编码 `speed=10`
- 加速倍率滑块：`<input type="range" min="1" max="20" value="10" oninput="...">`
- `sexyCreateAndRun()` 中 `speed_factor = _simSpeed`
- 暂停/继续功能复用 `sexyStopSim()` 和重新调用 `run` API

**6. 报告增强**

- 分项评分SVG柱状图：5个柱子（任务完成/通信效率/资源利用/冲突避免/收敛速度），高度对应评分值，颜色红-黄-绿渐变
- 底部按钮：「📥 下载JSON」下载 session 数据为 JSON 文件；「🔄 再次运行」复制当前配置并重新启动
- 「⬆ 注入优化策略」将 `ev.recommendations[0]` 转为 CLI 指令填入 `#cli-input`

### 目录结构

```
src/frontend/
├── Agent-digital-twin.html  # [MODIFY] 主修改文件，内联CSS/JS
```