<!-- docs-signoff: author="Copilot" kind="llm" doc="plan" ts="2026-07-08T05:00:00Z" -->
# 宠物团队生态仿真模块 — Predator / Prey 行为模型 Plan

> 目标：将猫小虎（**Predator 捕食者**）+ 老鼠吱吱（**Prey 猎物**）重构为**自主智能体**，
> 参照 Tu & Terzopoulos《Artificial Fishes: Physics, Locomotion, Perception, Behavior》(SIGGRAPH '94)
> 的整体式（holistic）四层模型：**物理/运动 → 感知 → 行为（意图生成器 + 心理状态 + 单项记忆）→ 类型特化**。
> 行为不再是硬编码的"巡逻/逃跑"脚本，而是由内部心理状态（饥饿/恐惧）+ 感知驱动的**涌现行为**。
> 可插拔架构与配置页保持不变，仅将 `pet-behavior.js` 的行为内核升级为意图生成器。

## 1. 理论映射（论文四层 → 本模块）

| 论文（Artificial Fishes） | 本模块落点 | 状态 |
|---|---|---|
| Motor / Physics（弹簧-质点 + MC） | `pet-factory.js` 模型 + `pet-behavior.js` 的 walk/idle 动画 | 已有 |
| Perception（视觉 300° + 注意力） | `behavior.detect_radius` / `perception.vision_cone_deg` | 部分已有，需扩展 |
| Behavior（意图生成器 + 心理状态 + 单项记忆） | `pet-behavior.js` **行为内核（本次重写）** | 待做 |
| Fish Types（Predator / Prey / Pacifist） | 小虎=Predator，吱吱=Prey | 待做 |

> 说明：本项目只有 2 只宠物、办公室平面场景，因此**不做**流体力学、集群（schooling）、交配（mating）等
> 论文中的复杂子系统；只移植**对 2 智能体追逐场景真正有用**的三件事：
> ① 心理状态（饥饿 H / 恐惧 F）；② 带优先级的意图生成器 + 单项短期记忆（防抖动）；③ Predator 捕猎代价函数 + 捕获事件。

## 2. 心理状态（Mental State，论文 §4.2）

### 2.1 Predator 小虎 — 饥饿 H ∈ [0,1]
- 随"距上次捕获的时间"单调上升：`H = min(1, elapsed_since_catch / hunger_full_sec)`。
- H 越高，`hunt` 意图优先级越高、追逐速度越快、感知半径越大（饿了更凶）。
- 捕获吱吱后 H 归零，进入短暂满足期（`wander`）。

### 2.2 Prey 吱吱 — 恐惧 F ∈ [0,1]
- 基于与捕食者的距离：`F = min(1, D0 / d)`（论文 `F^i = min(D0/d^i, 1)`），D0 为恐惧尺度常数。
- `F > f_escape` → `escape` 意图；`F` 低于阈值 → `wander`。
- F 越高，逃逸速度倍率越大、警告光圈闪烁越急。

## 3. 意图生成器（Intention Generator，论文 §5）

优先级从高到低（**避碰最高**），每帧按序判定，命中即生成意图并退出：

- **Predator 小虎**：`avoid`（避障/避碰） → `hunt`（H 或视野内有猎物触发） → `wander`（巡游）
- **Prey 吱吱**：`avoid` → `escape`（F 触发） → `wander`

**单项短期记忆 `I_s`**（论文防抖动机制）：
- 当高优先级意图（如 `avoid`）打断进行中的意图（如 `hunt`）时，把被打断意图压栈；
- 打断结束后弹栈恢复，避免目标反复横跳（dithering）。
- 追逐目标切换加**持久化阈值**：新目标代价须比当前目标低超过 `persistence_threshold` 才切换（论文 fickle/devoted）。

## 4. Predator 捕猎（论文 §6.1）

### 4.1 猎物选择代价函数
$$C_k = d_k\,\bigl(1 + \beta_2\,E_k/\pi\bigr)$$

- $d_k$：小虎嘴部到吱吱身体中心的距离；$E_k \in [0,\pi]$：转向该猎物所需转角（转向代价）。
- 单猎物场景省略集群项 $\beta_1 S_k$；保留转向代价 $\beta_2$，使小虎**优先追正前方**的吱吱，转身追背后的更"费劲"。
- 代价最小者为当前追逐目标（多猎物时可扩展）。

### 4.2 捕获事件（suck-in 的简化）
- 当 $d < \text{catch\_radius}$：判定**捕获成功** → 触发 `onCatch`：
  - 吱吱**瞬移**到离小虎最远的安全角落（respawn），恐惧 F 清零、进入 `wander`；
  - 小虎 H 归零，念**得意台词**（LLM `cat-speak`，带"硕鼠"意象），TTS 播报；
  - 记一次 `catch` 事件（供后续统计/评分联动）。

## 5. Prey 逃逸（论文 §6.2，去集群版）

- `F > f_escape` → 进入 `escape`：选离小虎**最远的路点**为目标，速度 × `flee_speed_multiplier`，警告光圈闪烁。
- 安全后（F 低于 `f_calm`，带滞回避免抖动）→ `wander`：沿巡逻路线随机停留游走。

## 6. 配置 Schema 扩展（pet_config.json）

在现有 `model` / `behavior` / `speak` / `voice` / `click_action` 基础上，为行为内核新增两个块（**向后兼容**：缺省则退回旧 patrol/flee 逻辑）：

```jsonc
{
  "role": "predator",              // "predator" | "prey"（新增）
  "perception": {                  // 新增：感知
    "detect_radius": 4.0,
    "vision_cone_deg": 300
  },
  "mental_state": {                // 新增：心理状态
    "hunger_full_sec": 20,         // predator: H 从 0→1 所需秒数
    "fear_scale_D0": 6.0,          // prey: F = min(1, D0/d)
    "f_escape": 0.55,              // prey: 触发逃逸阈值
    "f_calm": 0.35                 // prey: 恢复平静阈值（滞回）
  },
  "intention": {                   // 新增：意图生成器参数
    "beta_turn_cost": 0.2,         // predator 代价函数 β2
    "persistence_threshold": 1.5,  // 目标切换持久化阈值
    "catch_radius": 0.8            // predator 捕获判定半径
  }
}
```

## 7. 前端页面（已存在，本次仅增字段）

- `/pet-config.html` — 宠物配置页：在现有模型/行为/台词/语音卡片上，为 Predator/Prey 增加
  **心理状态**（hunger/fear 阈值）与**意图**（β2/持久化/捕获半径）表单字段。

## 8. 实施步骤

### Phase A — 配置 Schema 扩展（Predator/Prey）
- `storage/pet_config.json`：小虎加 `role:"predator"` + `perception`/`mental_state`/`intention`；吱吱加 `role:"prey"` + 对应块。
- `pet_ecosystem.py`：新字段纳入深度合并与校验（向后兼容默认值）。

### Phase B — 行为内核重写（意图生成器）
- `pet-behavior.js`：把当前 `step()` 的硬编码巡逻/逃跑，重构为
  **心理状态更新 → 意图生成（带优先级 + 单项记忆）→ 行为例程（avoid/hunt/escape/wander）→ 运动动画**。
- Predator/Prey 分派由 `config.role` 决定，动画（walk/idle）复用现有实现。

### Phase C — 捕猎闭环
- 代价函数选目标 + `catch_radius` 捕获判定；`onCatch` 回调触发吱吱 respawn + 小虎台词/TTS + `catch` 事件。
- `pet-ecosystem.js`：接线 `onCatch`（复用现有 `_onPetDetect` 的 LLM/TTS 通路）。

### Phase D — office-scene.js 彻底解耦
- 移除 `buildCat`/`buildMouse`/硬编码猫鼠动画，改由 `PetEcosystem` 接管（延续 PE-9）。

### Phase E — 配置页字段补全
- `pet-config.html`：补 `mental_state`/`intention` 表单，与后端新 Schema 对齐。

> 已完成的可插拔地基（配置存储 / API / 工厂 / 配置页 / 生态管理器）见 todos 中 CodeBuddy 标记项，本次不重做。

## 9. Phase G — 页面配置唯一真相源（voice 兜底移除）

**目标**：TTS 完全由 `/pet-config.html` 页面配置驱动，移除前端代码里的所有 voice 配置兜底默认值。缺字段直接 `console.error` 报出缺什么，不静默用硬编码默认值掩盖问题——便于定位是页面配置遗漏还是代码缺陷。

**背景**：原 `catSpeak` 里散落 `?? 1.8` / `?? 1.1` / `?? 0.95` / `|| 15` 等兜底默认值，以及硬编码的「婷婷」→「Google 普通话」音色回退链。这些兜底掩盖了页面配置缺失，导致问题难定位。

**改动**：
1. 新增 [voice-config-validator.js](../src/frontend/js/office/voice-config-validator.js) — 纯函数 `validateVoiceConfig(vc)` 返回 `{ok, error}`，覆盖 4 种 provider（edge-tts/gpt-sovits/browser/unknown）的校验规则。
2. `catSpeak` 调用 `validateVoiceConfig`，不 ok 则 `console.error(v.error)` 并 return。
3. browser 模式下 `lang`/`rate`/`pitch`/`volume`/`preferred_voice`/`timeout_sec` 任一缺失即报错；`preferred_voice` 在浏览器 voices 列表找不到也报错。
4. edge-tts 模式下 `edge_voice` 缺失即报错（不再静默跳过）。
5. **保留**：`_catSpeakBackend` catch 块里 edge-tts 失败回退 browser（那是引擎容错，不是配置兜底）。

**数据清理**：删除 `storage/pet_config.json` 里 `pets[0]`（小虎）内部错误嵌套的 `pets` 数组和 `ecosystem` 对象（历史垃圾副本，与顶层配置不一致，混淆真相源）。

**测试**：
- 后端：[tests/test_pet_ecosystem.py](../tests/test_pet_ecosystem.py) — 9 个用例，覆盖配置文件完整性、嵌套副本清理、_DEFAULT_SEED 结构、默认值补全逻辑。
- 前端：[voice-config-validator.check.mjs](../src/frontend/js/office/__checks__/voice-config-validator.check.mjs) — 10 个 assert，覆盖缺 vc/缺 provider/edge-tts 缺 edge_voice/browser 缺字段/未知 provider/正常配置。

## 10. Phase I — 生态仿真范式泛化（Perception → Intention → Behavior 作为 Agent 通用运行时）

### 10.1 愿景与定位

**生态仿真不是"宠物模块"，是 Agent 的通用运行时范式。** 猫小虎 + 鼠吱吱的 Predator/Prey 演示（Phase A-H）只是这个范式的**第一个具体实例**，用来验证「感知-意图-行为」闭环在代码上跑得通。真正的目标是把这个闭环提升为**所有 Agent 的统一执行模型**，让 Plaza 议事、孪生演练、skill 调用、任务协作全都从生态仿真视角来看。

每个 Agent 在每个 tick 走统一闭环：

```
感知 (Perception)    →  从环境/上下文/他者提取信号（视野、消息流、状态、token 预算、他人意图…）
意图生成 (Intention) →  基于内部心理状态 + 感知信号，按优先级生成当前意图（avoid > hunt/escape > wander 的泛化）
行为 (Behavior)      →  执行意图对应的例程（工具调用、发言、移动、技能触发…），产出可观测动作 + 反馈回感知
```

关键要素的泛化：
- **心理状态**：Hunger/Fear → 紧迫度、信心、预算压力、协作意愿…（让 Agent 有内部驱动，非纯反应式）
- **意图优先级**：avoid（避碰/避冲突）> hunt/escape（主动目标）> wander（空闲巡游）→ 通用化为"安全 > 目标 > 空闲"
- **单项短期记忆 + 持久化阈值**：防意图横跳，适用于"任务切换/发言轮次/技能选择"等一切决策场景

### 10.2 现状与差距

| 子系统 | 现状（与范式无关） | 范式下的目标 | 差距 |
| --- | --- | --- | --- |
| **Agent 运行时** | `chat_harness` + `tool_loop` 走 plan→act→observe→reflect（4 步线性） | 改造为 perception→intention→behavior 闭环，plan/act 是"行为例程"的展开 | 大：需引入心理状态层与意图生成器，重构 tool_loop 主循环 |
| **skill 体系** | SkillRouter 用 BM25/TF-IDF 检索关键词注入 prompt | skill = "可复用行为例程库"，按**意图**路由而非关键词匹配 | 大：路由机制从"文本相似度"改为"意图匹配"，skill schema 要带 intention 字段 |
| **Plaza 协作** | 主持人 + 座席层级 + 结构化发言（流程驱动） | 多 Agent **意图协调**：感知他人意图 → 调整自己意图 → 协调行为 | 中：已有座席/轮次结构，需在发言前加意图声明 + 主持人做意图仲裁 |
| **孪生沙箱** | twin_loop spawn 副本做 What-if 推演（策略级对比） | What-if = "多 Agent 意图-行为"仿真，混沌注入 = 扰动感知/心理状态 | 中：已有 spawn/对比框架，需把混沌注入从"断网/离场"扩展到"感知扰动/心理状态扰动" |

### 10.3 设计原则

1. **范式先行，兼容并存**：不一次性推翻现有运行时，而是新建 `agents/runtime/eco_loop.py` 作为 perception→intention→behavior 的参考实现，先在 PetEcosystem 内验证，再逐步接到 chat_harness/tool_loop。新旧两套运行时并存，按 Agent 配置选用。
2. **意图是头等公民**：所有决策（用哪个工具、发什么言、追哪个目标）都先产出**意图对象** `{type, target, priority, memory}`，行为例程只负责执行意图。意图可被日志/统计/仿真复用。
3. **心理状态可配置可观测**：心理状态字段（Hunger/Fear 的泛化）由 Agent 配置定义，运行时可观测（供孪生沙箱做 What-if 扰动、供 Plaza 做意图协调）。
4. **skill 作为行为例程**：skill 不再只是"注入 prompt 的文本"，而是带 `intention` 标签的"可复用行为例程"，意图生成器按 `intention` 匹配路由。
5. **协作即意图协调**：Plaza 议事/任务协作的本质是"多 Agent 意图协调"——每个 Agent 先声明意图，主持人/协调者基于全局意图分布做仲裁，再让各方执行。

### 10.4 分阶段路线（粗粒度，细化见 todos Phase I）

- **I-1 抽象意图模型**：把 `pet-behavior.js` 的 `state.intention` + `generateIntention` + `memory` 抽象成 `IntentionAgent` 基类（Python 侧 `agents/runtime/eco_loop.py`），心理状态/感知/意图生成器为可重写方法。先在 PetEcosystem 后端跑通，保持猫鼠行为不变。
- **I-2 Agent 运行时接入**：`chat_harness` 在 plan→act 前加 perception→intention 步骤，tool_loop 的"下一步动作"改为"执行当前意图的例程"。保留旧路径作 fallback。
- **I-3 skill 带意图标签**：skill schema 加 `intention` 字段，SkillRouter 增加"按意图过滤"前置阶段（BM25/TF-IDF 仍作文本相似度辅助）。新技能入库必须标意图。
- **I-4 Plaza 意图协调**：发言前先声明意图（`declare_intention`），主持人收集全局意图分布做仲裁（谁先说、谁让步、谁补充），再进入结构化发言。
- **I-5 孪生沙箱意图仿真**：twin_loop 的混沌注入扩展到"感知扰动"（遮挡/延迟/噪声）与"心理状态扰动"（强行调高紧迫度/信心），观察意图-行为链路的鲁棒性。

### 10.5 验证标准

- 猫鼠场景行为零回归（I-1 完成后 `pet-behavior.check.mjs` 全过）。
- 一个非宠物 Agent（如 `pet_squad` 里的小虎作为 LLM Agent）能用 eco_loop 跑通"感知任务上下文 → 生成回应意图 → 执行发言/工具"闭环（I-2 验收）。
- skill 按 intent 路由的命中率 ≥ 关键词路由基线（I-3 验收）。
- Plaza 一轮议事产出的"意图分布"可被观测/统计（I-4 验收）。
- 孪生沙箱能注入"感知扰动"并观测到意图-行为变化（I-5 验收）。

### 10.6 不做什么

- **不做集群/交配/流体力学**：论文的复杂子系统对本平台无价值，只取"感知-意图-行为"三要素。
- **不一次性推翻现有运行时**：新旧并存，按 Agent 配置选用，避免大爆炸式重写。
- **不把心理状态做成万能解释**：心理状态是"内部驱动"的建模工具，不是要模拟人类情感；字段精简、可观测、可扰动即可。
