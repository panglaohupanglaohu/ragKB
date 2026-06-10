# Agent 数字孪生 — 按钮级功能 TODO 清单
# AgentsGroup2026 Digital Twin — Button-Level Functional TODOs

> 版本：v2.0 · 日期：2026-06-10  
> 配套文档：`Agent数字孪生优化plan.md`  
> 适用对象：CodeBuddy（先阅读 plan.md 理解试炼/演练/仿真概念）  
> 核心概念：**试炼 = 完整实验闭环（创建→分支→运行→评分→萃取→反哺），演练 = 运行中施加压力（故障注入→恢复力观测）**  
> 标记说明：`[x]` 已验证通过 / `[~]` 部分实现待验证 / `[ ]` 未实现或已知断裂

---

## 一、概念定义

### 1.1 试炼（Trial）vs 演练（Exercise）vs 仿真（Simulation）

| 概念 | 英文 | 定义 | 对应按钮前缀 |
|------|------|------|-------------|
| **试炼** | Trial | 完整的孪生实验：创建实验、分裂分支、运行推演、评分比较、萃取SOP、反哺Agent | `T-` |
| **演练** | Exercise/Drill | 在试炼运行中注入故障/扰动，测试团队恢复能力 | `X-` |
| **仿真** | Simulation | 在沙箱中推进step，是试炼和演练共用的底层执行机制 | 无独立前缀 |

三者关系：
```
试炼(Trial) ──创建──→ Branch ──运行仿真──→ Step序列
                              │
                    演练注入 ←┘  (在仿真中施加故障)
                              │
                    评分萃取 → SOP → 反哺现实
```

### 1.2 试炼六步闭环

```
1. 选择团队+模式 → 2. 创建试炼 → 3. 运行/分支 → 4. 评分评审 → 5. 萃取SOP → 6. 反哺Agent
```

### 1.3 演练四步闭环（在试炼步骤3中执行）

```
1. 选择故障类型 → 2. 注入运行中 → 3. 观察恢复力 → 4. 记录韧性得分
```

---

## 二、试炼导演台（Trial Director Panel）— 右侧面板

> HTML 位置：`id="trial-director-panel"`  
> 状态机对象：`window._DTS`  
> 状态转换函数：`transitionTrialStatus(from, to)`  
> 按钮渲染函数：`window._updateButtonStates(status)`  
> 按钮渲染目标：`id="dt-action-buttons"`

### 2.1 模式选择卡片（5种试炼模式）

| 编号 | 按钮文本 | 触发函数 | HTML位置 | 说明 |
|------|----------|----------|----------|------|
| T-M01 | 🔮 What-if 基线实验 | `selectMode('what_if')` | `.dp-mode-card` | 单分支基线推演 |
| T-M02 | 🌳 多分支对比 并行策略 | `selectMode('multi_branch')` | `.dp-mode-card` | 多Branch并行对比 |
| T-M03 | 🌀 混沌演练 压力测试 | `selectMode('chaos_drill')` | `.dp-mode-card` | 注入故障+测恢复力 |
| T-M04 | 🧬 演化试炼 进化搜索 | `selectMode('evolutionary')` | `.dp-mode-card` | 多代自动进化 |
| T-M05 | 📼 回放复盘 历史重放 | `selectMode('replay')` | `.dp-mode-card` | 基于历史重放 |

- [x] T-M01 **What-if 模式卡片**：点击后 `window._DTS.selectedMode = 'what_if'`，卡片高亮（`.dp-mode-card.active`），其他卡片取消高亮
  - 验收：点击卡片 → 高亮变为青色边框 → `console.log(window._DTS.selectedMode)` 输出 `"what_if"`
- [x] T-M02 **多分支对比模式卡片**：同逻辑，`selectedMode = 'multi_branch'`
  - 验收：点击后其他卡片取消高亮
- [x] T-M03 **混沌演练模式卡片**：同逻辑，`selectedMode = 'chaos_drill'`
- [x] T-M04 **演化试炼模式卡片**：同逻辑，`selectedMode = 'evolutionary'`
- [x] T-M05 **回放复盘模式卡片**：同逻辑，`selectedMode = 'replay'`
- [x] T-M06 **模式卡片联动**：SECS面板选择模式radio时，导演台卡片同步高亮
  - 验收：SECS选"What-if" → 导演台🔮卡片高亮；SECS选"混沌" → 🌀卡片高亮

### 2.2 导演台配置区

| 编号 | 组件 | 触发/同步 | HTML id | 说明 |
|------|------|-----------|---------|------|
| T-C01 | 团队显示 | 从 SECS `_selectedTeamId` 自动同步 | `dp-team-display` | 只读展示，1秒轮询同步 |
| T-C02 | 任务目标输入 | 用户输入 | `dp-task-name` | 默认"默认试炼" |
| T-C03 | 最大步数滑块 | 用户输入 + SECS同步 | `dp-max-steps` | 默认150 |
| T-C04 | 加速倍率 | 用户输入 + SECS同步 | `dp-acceleration` | 默认5 |

- [x] T-C01 **团队同步显示**：格式 `{团队名} ({N} 智能体)`，未选时显示"等待 SECS 选择团队"
  - 验收：SECS选"Build System" → 导演台显示"Build System (7 智能体)"
- [x] T-C02 **任务目标输入**：`createTrial()` 读取此值作为 `task_goal.name`
  - 验收：输入"测试任务" → 创建试炼 → 控制台日志显示任务名为"测试任务"
- [x] T-C03 **最大步数**：`createTrial()` 和 `sexyCreateAndRun()` 读取此值
  - 验收：设置为50 → 创建试炼 → API请求中 `max_steps=50`
- [x] T-C04 **加速倍率**：传入 `createTrial()`

### 2.3 状态机操作按钮（8状态 × 14按钮）

#### 状态: idle（空闲）
| 按钮 | 触发函数 | 代码行 |
|------|----------|--------|
| 🧪 创建试炼 | `createTrial()` | ~3267 |

- [x] **T-B01 idle→创建试炼**：按钮显示"🧪 创建试炼"，点击调用 `createTrial()`
  - 验收：页面加载后导演台显示此按钮 → 点击 → 按钮变为"⏳ 创建中..." → API调用成功 → 变为 ready 状态按钮组
  - 验收（无团队）：未选团队时 → toast "请先在SECS面板选择团队" → 按钮恢复idle
  - 验收（超时）：API 15秒无响应 → toast "创建超时，请检查后端服务"
  - 验收（错误）：API返回错误 → toast显示错误信息 → 按钮恢复idle

#### 状态: creating（创建中）
| 按钮 | 触发函数 | 说明 |
|------|----------|------|
| ⏳ 创建中... | (disabled) | 不可点击 |

- [x] **T-B02 creating**：按钮显示"⏳ 创建中..."且禁用，`createTrial()` 正在调用 `/api/v1/twin-trials`
  - 验收：点击创建后立即显示此状态 → API返回后自动切换到 ready 或 failed
  - 验收：持续时间不超过15秒（有超时保护）

#### 状态: ready（就绪）
| 按钮 | 触发函数 | 说明 |
|------|----------|------|
| ▶ 单步 | `stepOnce()` | 推进一个step |
| ▶▶ 自动 | `autoRun()` | 自动运行到底 |
| 💥 注入 | `showInjectDropdown()` | 打开故障下拉菜单 |

- [x] **T-B03 ready→单步推演**：`stepOnce()` → 调用 `/api/v1/sandbox/sessions/{sid}/step` → 执行一步
  - 验收：点击"▶ 单步" → 控制台显示 step 日志 → step_index 连续不重复 → reward 更新
- [x] **T-B04 ready→自动推演**：`autoRun()` → 委托 `sexyAutoRun()` → 调用 `/run` → 全部step执行
  - 验收：点击"▶▶ 自动" → 状态切换到 running → 按钮变为"⏸ 暂停" → step持续产生
  - 验收：完成后状态切换到 evaluating → 自动评分
- [x] **T-B05 ready→注入事件**：`showInjectDropdown()` → 展开故障选择菜单
  - 验收：点击"💥 注入" → 下拉菜单弹出6个故障选项 → 菜单在 `.inject-menu` 中可见完整文字
  - 验收：点击菜单外部 → 菜单关闭

#### 状态: running（运行中）
| 按钮 | 触发函数 | 说明 |
|------|----------|------|
| ⏸ 暂停 | `pauseSim()` | 暂停当前运行 |
| 💥 注入 | `showInjectDropdown()` | 运行中注入故障 |
| ⑂ 分裂分支 | (见2.5) | 从当前step分裂新Branch |

- [x] **T-B06 running→暂停**：`pauseSim()` → `POST /sessions/{sid}/pause` → `transitionTrialStatus('running','paused')`
  - 验收：自动运行中点"⏸ 暂停" → step停止产生 → 按钮变为 paused 状态组
  - 验收：暂停后当前 step_index 保留，不丢失
- [ ] **T-B07 running→注入事件（运行时）**：在运行中注入故障，后端需在下一个step生效
  - 验收：自动运行中 → 点"💥 注入" → 选"网络延迟" → 控制台显示注入事件 → 受影响的Agent显示⏳
  - 验收：注入后 reward 短暂下降 → 系统尝试恢复
- [ ] **T-B08 running→分裂分支（运行时）**：从当前step创建新Branch
  - 验收：运行到step 10 → 点"⑂ 分裂分支" → 新Branch创建 → 曲线图出现两条线

#### 状态: paused（已暂停）
| 按钮 | 触发函数 | 说明 |
|------|----------|------|
| ▶ 继续 | `stepOnce()` | 单步继续 |
| ▶▶ 自动 | `autoRun()` | 恢复自动运行 |
| ⏹ 终止 | `terminate()` | 终止试炼 |

- [x] **T-B09 paused→继续（单步）**：`stepOnce()` 从暂停处执行一步
  - 验收：暂停在step 5 → 点"▶ 继续" → 执行step 6 → 日志显示 step_index=6
- [x] **T-B10 paused→自动继续**：`autoRun()` 恢复自动运行
  - 验收：暂停后点"▶▶ 自动" → 状态切换到 running → 继续产生step
- [x] **T-B11 paused→终止**：`terminate()` → abort `_DTS._abortCtrl` + `POST /sessions/{sid}/stop` + `transitionTrialStatus('paused','terminated')`
  - 验收：暂停状态下点"⏹ 终止" → 状态切换到 terminated → 按钮变为 idle 的"🧪 创建试炼"
  - 验收：无论后端 `/stop` 是否成功，前端都强制清理状态（_resetLaunchUI 全面清理）
  - 验收：terminated 后可以立即创建新试炼（`terminated → idle → creating`）

#### 状态: evaluating（评分中）
| 按钮 | 触发函数 | 说明 |
|------|----------|------|
| ⏳ 评分中... | (disabled) | 全部禁用 |

- [x] **T-B12 evaluating**：按钮不可操作，显示评分进度
  - 验收：自动运行完成后自动进入此状态 → 评分完成自动切换到 completed

#### 状态: completed（已完成）
| 按钮 | 触发函数 | 说明 |
|------|----------|------|
| 📊 评分 | `viewReport()` | 查看五维评分 |
| 📋 SOP | `extractSop()` | 萃取标准操作程序 |
| 🔄 反哺 | `feedbackAgents()` | 反哺到Agent技能 |

- [ ] **T-B13 completed→查看评分**：`viewReport()` → 显示五维雷达图 + Branch对比柱状图
  - 验收：点击"📊 评分" → 显示五维评分（任务完成度/协作效率/韧性/成本控制/可萃取性）
  - 验收：多个Branch时显示对比
- [ ] **T-B14 completed→萃取SOP**：`extractSop()` → `POST /api/v1/twin-trials/{tid}/extract-sop`
  - 验收：点击"📋 SOP" → 显示SOP候选列表（名称/置信度/步骤数）
  - 验收：全局统计"提取SOP"数量+1
- [ ] **T-B15 completed→反哺Agent**：`feedbackAgents()` → `POST /api/v1/twin-trials/{tid}/feedback`
  - 验收：点击"🔄 反哺" → "已更新 N 个Agent的技能分数"
  - 验收：团队面板中对应Agent技能分数有变化

#### 状态: failed（失败）
| 按钮 | 触发函数 | 说明 |
|------|----------|------|
| 🔁 新试炼 | `resetForNew()` | 重置到idle |

- [x] **T-B16 failed→新试炼**：`resetForNew()` → 重置所有状态 → 回到 idle
  - 验收：试炼失败后点"🔁 新试炼" → 按钮恢复为"🧪 创建试炼"
  - 验收：失败原因在控制台可见

### 2.4 注入故障下拉菜单（6种故障 — 演练核心）

> HTML位置：`.inject-menu` > `.inject-menu-item` × 6  
> 触发函数：`doInjectEvent(eventType)`  
> CSS：`z-index: 9999` `left: 0`（已修复裁剪问题）

| 编号 | 按钮文本 | 事件类型 | 说明 | 等级 |
|------|----------|----------|------|------|
| X-01 | 🧠 模型幻觉 | `model_hallucination` | Agent产生错误决策 | 三级 |
| X-02 | 🌐 网络延迟 | `network_delay` | skill执行延迟 | 一级 |
| X-03 | 🔒 逻辑死锁 | `logic_deadlock` | 团队陷入决策循环 | 三级 |
| X-04 | ⬇️ 技能退化 | `skill_degraded` | Agent技能效率降低 | 一级 |
| X-05 | 👤 Agent离队 | `agent_leave` | Agent标记为offline | 二级 |
| X-06 | 📝 任务变更 | `task_change` | 中途修改任务目标 | 二级 |

- [x] **X-01~X-06 菜单可见性**：下拉菜单完整显示6个选项，文字不裁剪
  - 验收：点"💥 注入" → 6个故障完整可见（emoji+中文）
- [ ] **X-01 模型幻觉注入**：`doInjectEvent('model_hallucination')` → 后端接受事件 → 受影响Agent图标显示⚠️
  - 验收：注入后控制台记录事件 → reward曲线可能出现波动
- [ ] **X-02 网络延迟注入**：房间边框变橙，受影响Agent图标⏳
  - 验收：工作坊边框颜色变为橙色 → reward短暂下降后回升
- [ ] **X-03 逻辑死锁注入**：议事厅/工作坊出现🔴标注，reward停滞
  - 验收：注入后 reward 曲线出现平台期
- [ ] **X-04 技能退化注入**：Agent图标⚠️，技能标签变红，reward贡献×0.6
  - 验收：注入后对应Agent的每步贡献降低
- [ ] **X-05 Agent离队注入**：Agent图标变灰 → 移入休息区 → 房间计数-1
  - 验收：受影响Agent从工作坊移到休息区卡片
- [ ] **X-06 任务变更注入**：控制台显示任务变更事件 → 协作图可能重组
  - 验收：注入后控制台日志显示"任务已变更"
- [ ] **X-07 注入历史记录**：`id="inject-history"` 面板显示已注入事件列表
  - 验收：注入3个故障后 → 面板显示3条记录
- [ ] **X-08 恢复力评分**：评分结果中 `resilience` 维度反映恢复能力
  - 验收：有故障注入时 `resilience < 1.0`，无故障时 `resilience = 1.0`

### 2.5 分支管理面板

| 编号 | 功能 | 触发/调用 | 说明 |
|------|------|-----------|------|
| T-F01 | 分支列表显示 | `showBranchManager(trialId)` | 列出Trial下所有Branch |
| T-F02 | 切换活跃分支 | 点击分支条目 | 视图切换到该分支 |
| T-F03 | 分裂新分支 | `forkBranch()` | 从当前step创建新Branch |
| T-F04 | 分支颜色区分 | CSS `.branch-{color}` | 每个Branch独立颜色 |

- [ ] **T-F01 分支列表**：Trial创建后自动显示baseline分支
  - 验收：创建试炼 → 分支面板显示"baseline (蓝色) · 当前步: 0"
- [ ] **T-F02 切换分支**：点击分支条目 → UI切换（曲线/Agent位置/step计数）
  - 验收：切换到分支B → 曲线颜色变化 → Agent房间位置变化
- [ ] **T-F03 分裂分支**：`forkBranch()` → `POST /api/v1/twin-trials/{tid}/branches`
  - 验收：在step 10点"⑂ 分裂" → 新Branch出现 → reward曲线多一条线
- [ ] **T-F04 颜色区分**：baseline=蓝、chaos=橙、optimized=绿
  - 验收：3个Branch同时显示 → 曲线/标签颜色互不相同

---

## 三、SECS 演练面板（SECS Exercise Panel）— 统一入口

> HTML位置：SECS配置区域  
> **重要**：已与试炼导演台统一入口，`sexyCreateAndRun()` 内部调用 `createTrial()`  
> 统一后 `_sx.sessionId = window._currentSessionId`，两边按钮操控同一session

| 编号 | 按钮文本 | 触发函数 | 说明 | 与导演台关系 |
|------|----------|----------|------|-------------|
| S-01 | ▶ 沙箱推演 | `sexyCreateAndRun()` | 创建试炼统一入口 | → 调用 `createTrial()` |
| S-02 | ▶ 单步 | `sexyStepOnce()` | 单步推演 | 操作同一session |
| S-03 | ▶▶ 自动 | `sexyAutoRun()` | 自动运行 | → 由导演台 `autoRun()` 委托 |
| S-04 | ⏸ 暂停 | `sexyPauseResume()` | 暂停/恢复 | 操作同一session |
| S-05 | ⏹ 停止演练 | `sexyStopSim()` | 强制停止 | abort + `/stop` + 清理 |
| S-06 | 📄 报告 | 查看报告按钮 | 查看演练报告 | 使用 `_lastReportSessionId` |

### 3.1 沙箱推演按钮（统一入口）

- [x] **S-01 沙箱推演**：`sexyCreateAndRun()` → 读取SECS参数 → 同步到导演台 → 调用 `createTrial()`
  - 验收：选团队+模式 → 点"▶ 沙箱推演" → 控制台显示"统一入口 → 试炼导演台"
  - 验收：创建成功后 SECS面板显示"✅ 已就绪 (试炼导演台)" → sessionId与导演台一致
  - 验收：已存在session时 → toast "试炼已存在，请先终止" → 不重复创建
  - 验收：未选团队时 → toast "请先选择演练团队"
  - 验收：按钮loading态"⏳ 创建中..." → API返回后恢复"▶ 沙箱推演"

### 3.2 运行控制按钮

- [x] **S-02 SECS单步**：`sexyStepOnce()` → `POST /sessions/{sid}/step`
  - 验收：操作与导演台"▶ 单步"一致，step_index连续
- [x] **S-03 SECS自动**：`sexyAutoRun()` → 带AbortController + 同步导演台状态
  - 验收：点"▶▶ 自动" → SECS和导演台同步显示running状态
  - 验收：完成后自动 `transitionTrialStatus('running','completed')`
  - 验收：AbortError时前端优雅处理不报错
- [x] **S-04 SECS暂停/恢复**：`sexyPauseResume()` 
  - 验收：运行中显示"⏸ 暂停" → 点击后暂停 → 文字变为"▶ 继续"
  - 验收：暂停后点"▶ 继续" → 恢复运行
- [x] **S-05 SECS停止**：`sexyStopSim()` → abort `_sx._abortCtrl` + abort `_DTS._abortCtrl` + `POST /stop` + `_cleanupSim()`
  - 验收：运行中点"⏹ 停止演练" → fetch立即中断 → 发送/stop → 前端全面清理
  - 验收：停止后按钮恢复为"▶ 沙箱推演"，sessionId清空
  - 验收：停止后导演台同步切换到idle
  - 验收：CREATED/RUNNING/PAUSED/COMPLETED任意状态都能停止（后端已支持）
- [ ] **S-06 SECS报告**：停止后显示报告按钮，使用 `_lastReportSessionId`
  - 验收：停止后报告按钮出现 → 点击 → 显示步数/reward/评分

### 3.3 SECS 参数配置

| 编号 | 组件 | HTML id | 说明 |
|------|------|---------|------|
| S-P01 | 模式选择 Radio | `secs-mode-*` | what_if / parallel / evolutionary / chaos_drill |
| S-P02 | 最大步数 | `secs-steps` | 默认50 |
| S-P03 | 速度倍率滑块 | `secs-speed-slider` | 默认10 |

- [x] **S-P01 模式Radio**：选中的模式会同步到导演台 `window._DTS.selectedMode`
  - 验收：SECS选"混沌演练" → 导演台🌀卡片高亮
- [x] **S-P02 步数**：`sexyCreateAndRun()` 读取，同步到导演台 `dp-max-steps`
- [x] **S-P03 速度**：传入试炼参数

---

## 四、环境空间面板（Environment Space）— 主舞台

> HTML位置：`view-environment`  
> 六房间：议事厅(congress_hall) / 萃取室(extraction_room) / 工作坊(workshop) / 知识库(knowledge_base) / 演练场(arena) / 休息区(rest_area)

### 4.1 视图切换

| 编号 | 按钮 | 触发函数 | 说明 |
|------|------|----------|------|
| E-01 | 平面视图 | `switchEnvMode('grid', this)` | 网格布局 |
| E-02 | 网格视图 | `switchEnvMode('flat', this)` | 平面布局 |
| E-03 | 创建空间 | `createRoom()` | 创建新房间 |

- [ ] **E-01 平面/网格视图切换**：两种布局之间切换，保持Agent位置不变
  - 验收：点"平面视图" → 房间卡片排列为网格 → 点"网格视图" → 恢复
- [ ] **E-02 创建空间**：创建自定义房间
  - 验收：点"创建空间" → 弹出输入框 → 输入名称 → 新房间卡片出现

### 4.2 六房间卡片状态

| 编号 | 房间 | 数据来源 | 显示内容 |
|------|------|----------|----------|
| E-R01 | 议事厅 | `roomAgentMap.congress_hall` | Agent数量+头像列表 |
| E-R02 | 萃取室 | `roomAgentMap.extraction_room` | Agent数量+头像列表 |
| E-R03 | 工作坊 | `roomAgentMap.workshop` | Agent数量+头像列表 |
| E-R04 | 知识库 | `roomAgentMap.knowledge_base` | Agent数量+头像列表 |
| E-R05 | 演练场 | `roomAgentMap.arena` | Agent数量+头像列表 |
| E-R06 | 休息区 | `roomAgentMap.rest_area` | Agent数量+头像列表 |

- [ ] **E-R01~06 房间Agent数量**：每张卡片显示 `{房间名} — {N} 个智能体`
  - 数据唯一来源：`roomAgentMap[room_id].length`
  - 验收：选择Build System+工作坊演化 → 工作坊=7，其他=0 或 空
- [ ] **E-R07 Agent头像列表**：卡片内显示最多5个头像，超出显示"+N"
  - 验收：工作坊7个Agent → 显示5个头像+"+2"
- [ ] **E-R08 空间标题同步**：标题"环境空间 — {总Agent数} 个智能体"与房间卡片一致
  - 验收：工作坊7个 → 标题显示"— 7 个智能体"
  - **不允许**出现标题28但卡片0的bug
- [ ] **E-R09 房间颜色与状态对应**：
  - 工作坊有Agent活动 → 背景微亮
  - 萃取室有Agent进入 → `sop-extract-badge` ✦SOP徽章触发
  - 演练场有Agent → 混沌注入时边框变色
  - 休息区有Agent → 表示有Agent失败/离队

### 4.3 视觉反馈

| 编号 | 功能 | 触发条件 | 视觉效果 |
|------|------|----------|----------|
| E-V01 | Reward热力反馈 | reward变化 | 上升→绿地/下降→红底/峰值→金色光晕 |
| E-V02 | 故障注入视觉 | doInjectEvent() | 见X-01~X-06各条 |
| E-V03 | Agent迁移动画 | roomAgentMap变化 | 300ms ease过渡 |
| E-V04 | SOP萃取徽章 | extractSop()完成 | `.sop-extract-badge` ✦闪烁 |

- [ ] **E-V01 Reward热力反馈**：reward上升时活跃房间背景微绿(`rgba(52,211,153,0.2)`)，下降时微红，峰值金色光晕1.5s
  - 验收：自动运行中 → 观察工作坊/演练场背景颜色随reward变化
- [ ] **E-V02 故障视觉效果**：对应X-02~X-05
- [ ] **E-V03 Agent迁移动画**：Agent从房间A移到房间B时，300ms过渡
  - 验收：注入"Agent离队" → 受影响Agent从头像列表消失 → 休息区头像列表增加
- [ ] **E-V04 SOP徽章**：萃取完成后萃取室显示✦SOP徽章
  - 验收：完成萃取 → 萃取室卡片出现✦徽章 → 点击展开策略摘要

### 4.4 浮动组件

| 编号 | 组件 | HTML id | 功能 |
|------|------|---------|------|
| E-F01 | 系统状态浮动卡 | `env-status-float` | 四指标一览 |
| E-F02 | 事件弹幕层 | `env-barrage-layer` | step事件气泡 |
| E-F03 | SVG连线层 | `env-linkage-svg` | Agent协作连线 |
| E-F04 | 收益浮动卡 | `env-reward-float` | 迷你reward图表 |

- [ ] **E-F01 系统状态浮动卡**：显示沙箱会话/仿真步数/SOP数/最优评分
  - 验收：创建试炼后浮动卡更新 → `_updateEsFloat()` 与 `loadSecsStats()` 联动
- [ ] **E-F02 事件弹幕**：每次step产生弹出气泡 `showBarrageBubble()` → floatIn→停留→fadeOut
  - 验收：自动运行中 → 环境空间出现step事件气泡
- [ ] **E-F03 连线动画**：Agent协作时 `drawLinkageLine()` → stroke-dashoffset 动画 → 3秒自动清除
  - 验收：Agent之间有协作 → SVG连线出现 → 动画流动 → 3秒后消失
- [ ] **E-F04 收益浮动卡**：右下角显示迷你reward曲线 + 实时数值
  - 验收：自动运行中 → 右下角reward卡实时刷新

---

## 五、智能体团队面板（Agent Team Panel）— 左侧

> HTML位置：左侧智能体团队区域

| 编号 | 按钮 | 触发函数 | 说明 |
|------|------|----------|------|
| A-01 | 团队卡片选择 | 点击卡片 | 选择团队（Build System/AI编程/公有云xOPs） |
| A-02 | ⚡ 部署 | 部署按钮 | 部署Agent到环境空间 |
| A-03 | 🔄 召回 | 召回按钮 | 从环境空间召回Agent |
| A-04 | Agent技能标签 | 点击标签 | 查看技能详情 |

- [x] **A-01 团队选择**：点击团队卡片 → `_selectedTeamId` 更新 → SECS面板和导演台同步显示
  - 团队卡片数据：`_teamsData` 数组（name/agents/skills/scenarioLabel/agentCount）
  - 验收：点击"Build System" → SECS面板团队名更新 → 导演台 `dp-team-display` 更新 → `_agentCountForTeam` 更新
  - 验收：场景标签更新（如"工作坊演化"、"议事厅聚焦"、"多场景协作"）
- [ ] **A-02 部署Agent**：点"⚡ 部署" → Agent进入环境空间 → `roomAgentMap` 更新
  - 验收：选Build System → 点部署 → 工作坊显示7个Agent → 房间卡片更新
- [ ] **A-03 召回Agent**：点"🔄 召回" → Agent移出环境空间 → `roomAgentMap` 更新
  - 验收：召回后房间卡片Agent数量减少
- [ ] **A-04 技能标签**：Agent卡片的技能标签可点击 → 查看技能详情
  - 验收：点"Python开发"标签 → 显示技能描述/得分

---

## 六、导航栏与视图切换（Navigation & Views）

> HTML位置：`.header-nav` 区域

| 编号 | 按钮 | 触发函数 | 说明 |
|------|------|----------|------|
| N-01 | ★ 环境空间 | `switchView(this)` data-view="environment" | 主舞台 |
| N-02 | 系统状态 | `switchView(this)` data-view="architecture" | 仪表盘+协作拓扑 |
| N-03 | 交互流 | `switchView(this)` data-view="interaction" | Agent通信记录 |
| N-04 | 编排管线 | `switchView(this)` data-view="pipeline" | SECS Pipeline |
| N-05 | CLI | `switchView(this)` data-view="cli" | 命令行终端 |

### 6.1 视图切换

- [x] **N-01 环境空间视图**：切换到主舞台，`.nav-primary` 特殊高亮（渐变背景+发光下划线）
  - 验收：点击"★ 环境空间" → 主舞台可见 → 导航项高亮
- [x] **N-02~N-05 视图切换**：点击切换对应面板，`switchView` 内部 hook `_origSwitchView` 联动全局上下文
  - 验收：每个视图切换后对应面板可见，其他面板隐藏

### 6.2 系统状态子面板

| 编号 | 子面板 | 触发函数 | 说明 |
|------|--------|----------|------|
| N-A01 | 实时仪表盘 | `showArchSub('dashboard', this)` | 系统指标 |
| N-A02 | 协作拓扑 | `showArchSub('topo', this)` | 协作图可视化 |

- [ ] **N-A01 实时仪表盘**：显示系统指标（CPU/内存/会话数等）
  - 验收：切换到系统状态 → 点"实时仪表盘" → 指标卡片显示
- [ ] **N-A02 协作拓扑**：显示Agent之间的协作连线图（MADCG）
  - 验收：点"协作拓扑" → SVG图显示Agent节点和连线 → 反哺后连线加粗

### 6.3 交互流子面板

| 编号 | 过滤器 | 触发函数 | 说明 |
|------|--------|----------|------|
| N-I01 | 全部 | `filterMsgs('all')` | 显示所有消息 |
| N-I02 | 工具调用 | `filterMsgs('tool-call')` | 仅工具调用 |
| N-I03 | LLM推理 | `filterMsgs('llm-call')` | 仅LLM调用 |
| N-I04 | 任务交接 | `filterMsgs('handoff')` | 仅任务交接 |
| N-I05 | 时间线视图 | `switchFlowView('timeline', this)` | 时间线布局 |
| N-I06 | 序列图视图 | `switchFlowView('sequence', this)` | 序列图布局 |

- [ ] **N-I01~I04 消息过滤**：点击过滤按钮 → 消息列表按类型筛选
  - 验收：选"工具调用" → 仅显示tool-call类型消息
- [ ] **N-I05~I06 视图切换**：时间线和序列图两种Agent通信可视化
  - 验收：点"序列图" → 显示Agent间时序交互

---

## 七、CLI 面板命令（Command Line Interface）

> HTML位置：`.cli-quick-btns` 快捷按钮区域  
> 触发函数：`execCmd(command)`

| 编号 | 按钮 | 命令 | 说明 |
|------|------|------|------|
| C-01 | status | `execCmd('status')` | 系统状态 |
| C-02 | agents | `execCmd('agents')` | Agent列表 |
| C-03 | skills | `execCmd('skills')` | 技能列表 |
| C-04 | rooms | `execCmd('rooms')` | 房间信息 |
| C-05 | pipeline | `execCmd('pipeline show')` | 管道状态 |
| C-06 | flow last | `execCmd('flow last 10')` | 最近10条交互流 |
| C-07 | simulate | `execCmd('simulate random')` | 随机仿真 |
| C-08 | stress | `execCmd('stress simple')` | 压力测试 |
| C-09 | discuss | `execCmd('discuss architecture')` | 讨论模式 |
| C-10 | config | `execCmd('config show')` | 查看配置 |
| C-11 | export | `execCmd('export snapshot')` | 导出快照 |

- [ ] **C-01~C-11 CLI命令**：每个快捷按钮发送对应命令到CLI终端，终端显示结果
  - 验收：点"agents" → CLI终端显示Agent列表
  - 验收：点"simulate" → 终端显示仿真结果
- [ ] **C-12 Trial扩展命令**：支持 `trial create/list/show/fork/inject/eval/extract-sop/feedback/archive`
  - 验收：输入 `trial list` → 显示历史试炼列表

---

## 八、顶部工具栏（Topbar）

| 编号 | 按钮 | 触发函数 | 说明 |
|------|------|----------|------|
| T-01 | 导入 | `importSnapshot()` | 导入团队快照 |
| T-02 | 导出 | `execCmd('export snapshot')` | 导出当前快照 |
| T-03 | 登出 | `window._agLogout()` | 退出登录 |

- [ ] **T-01 导入快照**：导入之前导出的团队快照JSON
  - 验收：点"导入" → 选择JSON文件 → 团队/Agent/房间恢复
- [ ] **T-02 导出快照**：导出当前团队状态为JSON
  - 验收：点"导出" → 下载JSON文件
- [ ] **T-03 登出**：清除登录状态
  - 验收：点"登出" → 跳转到登录页

---

## 九、P0 Bug 修复清单（按紧迫度排序）

> 标记基于 2026-06-10 实际修复状态

### 已修复

- [x] **BUG-001** Session状态卡住 → 添加 `transitionTrialStatus` + 15秒超时 + `_resetLaunchUI` 清理 `window._currentSessionId`
- [x] **BUG-002** Step编号不一致 → 统一使用后端 `step_index`，前端不自行计数
- [x] **BUG-003** 停止不工作（仅RUNNING可停） → `stop_simulation` 支持 CREATED/PAUSED/COMPLETED 任意状态
- [x] **BUG-004** 注入菜单文字被裁 → `.inject-menu` CSS `right:0→left:0` + `z-index:9999`
- [x] **BUG-005** 试炼导演台按钮全部不工作 → 初始化 `window._DTS` + 补充 `transitionTrialStatus`/`handleTrialEvent`
- [x] **BUG-006** Trial API 路由不加载 → `trial_api.py` 语法错误修复（缩进+重复行删除+Request导入）
- [x] **BUG-007** 导演台与SECS重复团队选择 → 导演台团队改为只读，从SECS `_selectedTeamId` 同步

### 待修复

- [ ] **BUG-008** 获取会话详情 HTTP 500 → `GET /sessions/{id}` 在 evaluating 状态时需返回 200+partial data
- [ ] **BUG-009** 空间状态不同步 → 环境空间标题与房间卡片数据来源不一致，需统一到 `roomAgentMap`
- [ ] **BUG-010** Metrics 不同步 → session 创建后全局统计未实时更新
- [ ] **BUG-011** 演练历史不显示 → 历史记录仅在completed写入，需创建后立即写入
- [ ] **BUG-012** SSE/API 事件重复 → step 通过 API response 和 SSE 两个通道到达未去重

---

## 十、API 接口清单

> 前端调用路径 | 后端路由 | 当前状态

### 试炼相关 (Trial API)

| 方法 | 路径 | 前端调用函数 | 状态 |
|------|------|-------------|------|
| POST | `/api/v1/twin-trials` | `createTrial()` | [x] 路由已加载，Pydantic v2兼容 |
| GET | `/api/v1/twin-trials` | 试炼历史列表 | [ ] 待验证 |
| GET | `/api/v1/twin-trials/{id}` | 试炼详情 | [ ] 待验证 |
| POST | `/api/v1/twin-trials/{id}/branches` | `forkBranch()` | [ ] 待验证 |
| POST | `/api/v1/twin-trials/{id}/branches/{bid}/step` | `stepOnce()` | [ ] 待验证 |
| POST | `/api/v1/twin-trials/{id}/branches/{bid}/run` | `autoRun()` | [ ] 待验证 |
| POST | `/api/v1/twin-trials/{id}/branches/{bid}/pause` | `pauseSim()` | [ ] 待验证 |
| POST | `/api/v1/twin-trials/{id}/branches/{bid}/events` | `doInjectEvent()` | [ ] 待验证 |
| POST | `/api/v1/twin-trials/{id}/evaluate` | 评分 | [ ] 待验证 |
| POST | `/api/v1/twin-trials/{id}/extract-sop` | `extractSop()` | [ ] 待验证 |
| POST | `/api/v1/twin-trials/{id}/feedback` | `feedbackAgents()` | [ ] 待验证 |
| GET | `/api/v1/twin-trials/{id}/events/stream` | SSE连接 | [ ] 待验证 |

### 沙箱相关 (Sandbox API)

| 方法 | 路径 | 前端调用函数 | 状态 |
|------|------|-------------|------|
| POST | `/api/v1/sandbox/sessions` | 创建session | [x] 已验证 |
| POST | `/api/v1/sandbox/sessions/{sid}/run` | `sexyAutoRun()` | [x] 已验证 |
| POST | `/api/v1/sandbox/sessions/{sid}/stop` | `sexyStopSim()` / `terminate()` | [x] 全状态已验证 |
| POST | `/api/v1/sandbox/sessions/{sid}/pause` | `pauseSim()` | [x] 已验证 |
| POST | `/api/v1/sandbox/sessions/{sid}/step` | `sexyStepOnce()` | [x] 已验证 |
| GET | `/api/v1/sandbox/sessions/{sid}` | 会话详情 | [ ] 待验证（evaluating状态需修复） |

### 统计相关

| 方法 | 路径 | 前端调用函数 | 状态 |
|------|------|-------------|------|
| GET | `/api/v1/sandbox/stats` | `loadSecsStats()` | [ ] 待验证即时更新 |
| GET | `/api/v1/sandbox/history` | `loadExerciseHistory()` | [ ] 待验证创建即写入 |

---

## 十一、验收测试矩阵

### 11.1 试炼最小闭环（T-closed-loop）

- [ ] **V-T01** 页面对话 → 选团队 → 选What-if模式 → 点"🧪 创建试炼" → 3秒内进入ready状态
- [ ] **V-T02** ready状态 → 点"▶ 单步" → 控制台出现Step 1日志，step_index=1
- [ ] **V-T03** ready状态 → 点"▶▶ 自动" → step持续产生 → 状态变为running → 按钮变为"⏸ 暂停"
- [ ] **V-T04** running状态 → 点"⏸ 暂停" → step停止 → 状态变为paused → 按钮组变化
- [ ] **V-T05** paused状态 → 点"▶ 继续" → step继续从暂停处执行
- [ ] **V-T06** paused状态 → 点"⏹ 终止" → 状态变为terminated → 按钮恢复"🧪 创建试炼"
- [ ] **V-T07** 自动运行完成 → 状态变为evaluating → evaluating → completed
- [ ] **V-T08** completed状态 → 显示 [📊 评分] [📋 SOP] [🔄 反哺]
- [ ] **V-T09** 全局统计更新：会话数/步数/SOP数/评分随操作更新
- [ ] **V-T10** 试炼历史：创建/运行/完成三个阶段都出现在历史列表

### 11.2 演练最小闭环（X-closed-loop）

- [ ] **V-X01** 运行中 → 点"💥 注入" → 下拉菜单6选项完整可见
- [ ] **V-X02** 选"🌐 网络延迟" → 工作坊边框变橙 → 控制台记录注入事件
- [ ] **V-X03** 注入后 reward短暂下降 → 逐步恢复 → 恢复力得分记录
- [ ] **V-X04** 注入历史面板显示已注入事件列表
- [ ] **V-X05** 评分结果中 resilience 维度反映实际恢复情况

### 11.3 统一入口验证（Unified Entry）

- [ ] **V-U01** SECS点"▶ 沙箱推演" → 与导演台点"🧪 创建试炼"效果一致
- [ ] **V-U02** 创建后 `_sx.sessionId === window._currentSessionId`
- [ ] **V-U03** SECS点"▶ 单步" → 导演台状态同步为 running
- [ ] **V-U04** 导演台点"⏹ 终止" → SECS面板同步恢复
- [ ] **V-U05** 停止后两边都能重新创建新试炼

### 11.4 环境空间验证（Environment）

- [ ] **V-E01** 选Build System → 部署 → 工作坊显示7个Agent
- [ ] **V-E02** 工作坊标题 = "工作坊 — 7 个智能体"
- [ ] **V-E03** Agent列表的"空间"字段与 roomAgentMap 一致
- [ ] **V-E04** 注入Agent离队 → Agent从头像列表消失 → 休息区+1
- [ ] **V-E05** reward上升/下降 → 房间背景色变化

### 11.5 回归验证（Regression）

- [ ] **V-R01** 原有单步/自动运行功能正常，无退步
- [ ] **V-R02** 控制台日志无重复 step 事件
- [ ] **V-R03** 页面无 JS 报错（控制台无 error 级别日志）
- [ ] **V-R04** 重新加载页面后，历史列表正确还原
- [ ] **V-R05** 不同浏览器 tab 同时打开页面，互不干扰
- [ ] **V-R06** pytest 92/92 passed

### 11.6 按钮完整性统计

| 区域 | 按钮数 | 已实现 | 部分实现 | 未实现 |
|------|--------|--------|----------|--------|
| 试炼导演台-模式卡片 | 5 | 5 | 0 | 0 |
| 试炼导演台-状态按钮 | 14 | 11 | 3 | 0 |
| 试炼导演台-故障注入 | 6 | 0 | 6 | 0 |
| 试炼导演台-分支管理 | 4 | 0 | 0 | 4 |
| SECS演练面板 | 6 | 5 | 1 | 0 |
| 环境空间 | 8 | 0 | 2 | 6 |
| 智能体团队 | 3 | 1 | 0 | 2 |
| 导航栏 | 9 | 7 | 0 | 2 |
| CLI命令 | 11 | 0 | 11 | 0 |
| 顶部工具栏 | 3 | 0 | 0 | 3 |
| **总计** | **69** | **29** | **23** | **17** |

---

## 十二、附录

### A. 数字孪生产品原则（始终牢记）

1. **能力不靠声明，靠演练数据证明。**
2. **环境空间是状态机，不是装饰。**
3. **每次试炼都必须留下可追溯的历史记录。**
4. **失败路径也是数据，不能丢弃。**
5. **仿真推进路径，演练施加压力，试炼选择未来。**
6. **SOP 是从数字孪生提炼出来的现实智慧，是整个系统的最终产出。**

### B. 已有增强功能（P1-P4）

以下功能在 v1.0 阶段已实现，保留记录：

- [x] P1-A01~A04 视觉中心化（主舞台标记 + 浮动仪表卡 + 环境容器增强）
- [x] P1-F01~F03 六房间动效（智能房间检测 + Reward热力 + 峰值光晕）
- [x] P2-L01~L02 交互神经链路（switchView增强 + flyToRoom定位）
- [x] P2-B01~B02 事件弹幕层（barrage气泡 + emitStepBarrage）
- [x] P2-S01~S02 SVG连线层（drawLinkageLine + clearLinkageLines）
- [x] P3-I01~I02 注入下拉菜单（initInjectDropdown + injectHistory + injectChaos）
- [x] P3-H01~H02 历史回放（播放失败记录 + playbackSession逐帧回放）
- [x] P3-R01~R02 收益浮动卡（env-reward-float + 迷你SVG图表）
- [x] P4-E01~E02 SOP萃取徽章（sop-extract-badge + 萃取室pulse动画）
- [x] P4-U01~U02 Agent升级动画（playUpgradeAnimation + upgrade-ring光圈）
- [x] P4-P01~P02 并行可视化（showParallelView Grid分屏）

---

*文档版本：v2.0 · 2026-06-10 · 基于 plan.md v1.0 完全重写*
*标记总计：69个按钮功能 | 29已实现 | 23部分实现 | 17未实现 | 6项P0 Bug待修复*
