<!-- docs-signoff: author="Copilot" kind="llm" doc="plan" ts="2026-07-06T20:45:36Z" -->
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
