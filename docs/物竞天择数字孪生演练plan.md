<!-- docs-signoff: author="Fable 5" kind="llm" doc="plan" ts="2026-07-11T00:00:00Z" -->
# 物竞天择数字孪生演练 Plan v2 — 办公室视图 = 自然选择试验田

> 版本：v2.0 · 日期：2026-07-11 · 作者：Fable 5（本轮，即 Claude Fable 5）
> 取代：v1.0（2026-07-10，Claude）。v1 的 ND-1~ND-6 已由 CodeBuddy 落地，本版在其之上重构。
> 前置：
> - [`Agent仿生生态运行时plan.md`](Agent仿生生态运行时plan.md) — PIB 认知闭环 + Health 代谢 + 交配/淘汰
> - [`Agent数字孪生场景演练与技能进化plan.md`](Agent数字孪生场景演练与技能进化plan.md) — SECS 演练管线
> - [`宠物团队生态仿真plan.md`](宠物团队生态仿真plan.md) — 猫鼠 PIB 原型
>
> **一句话目标**：把「办公室视图」变成物竞天择的**试验田**——用户点进办公室视图后，右侧演练菜单**全部**切换为自然选择生境控制台；Agent 以「感知→意图→行为」存在于生态中，Skill 与协作过程作为**可遗传基因**被环境持续选择，全过程可视化回放。

---

## 0. 世界观（用户核心思想，本 plan 的最高约束）

> 用户原话（2026-07-11）摘要，全文精神必须贯穿所有实现：

1. **Agent 不是人类的模仿**。Agent 应该有**自己的生态环境**，以自己独有的方式沟通、繁衍、生活与成长——只是背后的演化规律仍然是**物竞天择**。
2. **Agent 以「感知 - 意图 - 行为」的方式存在**于生态环境中，让物竞天择的客观规律驱动 Agent 的 skill 及协作的进化。
3. **Skill 被环境选择**：有的 Agent 因为合适的 skill 存活，有的 Agent 因为不合适的 skill 消亡。
4. **Agent 会主动学习**（主动进化自己的 Skill）——但它们**不知道**学的那么多 skill 是否适合这个生态。学习是盲目的，选择是客观的。
5. **协作过程同样是被选择的对象**：Agent 不知道哪种协作能够存活。它们应该有自己的种群、自己的协作过程——**适合环境的协作过程保留下来，不适合环境的协作过程消亡掉**。这是 Agent 仿生的最大奥秘——不是 skill 选路径、不是主动更换协作方式，而是**不停地被环境选择**。
6. **演练的定义**：演练 = 仿生化后的 Agent 通过孪生演练来尝试 skill 及协作进化的过程。

> 设计推论（从 1~6 推出的硬规则）：
> - 生境里**不存在**「协作规则引擎」——只有可遗传的**协作倾向基因**与极简**信号协议**，协作模式靠涌现、靠选择。
> - **生存时长是唯一隐式适应度**（继承 v1 原则），繁衍/淘汰/基因池全部由它驱动，不引入任何人工评分。
> - 主动学习（盲目学习）必须存在：个体会在生存过程中随机习得/练熟 skill，但习得的 skill 是否有用由环境判决。
> - 可遗传单元 = **skill 基因 + 协作基因**（双基因组），交配时双双交叉。

---

## 1. v1 落地现状与差距盘点

### 1.1 已就绪（不重造，直接用）

| 零件 | 文件 | 归属 |
|---|---|---|
| PIB 感知→H/F/L 意图仲裁 | `src/backend/agents/runtime/eco_loop.py` | 【Claude 已有】 |
| Health 代谢账本 + survival_ticks | `src/backend/agents/runtime/health_ledger.py` | 【Claude 已有】 |
| 生境参数中心 `/api/v1/eco-runtime/config` | `src/backend/agents/runtime/eco_runtime_config.py` | 【Claude 已有】 |
| EcoDrill step/epoch/捕食/交叉/棘轮 | `src/backend/sandbox/eco_drill.py` | 【CodeBuddy ND-2~4】 |
| trial_api 按 `team.runtime=="eco"` 路由 `drill_kind="natural_selection"` | `src/backend/sandbox/trial_api.py` | 【CodeBuddy ND-1.2】 |
| `rp-eco` 生境控制台（静态版）+ `ecoRunDrill/ecoLoadConfig/_syncEcoPanel` | `Agent-digital-twin.html` + `js/digital-twin/secs-core.js` | 【CodeBuddy ND-5.1】 |
| 办公室 3D：血条 Sprite / 死亡淡出 / eco_health·eco_predator reducer | `js/office/office-scene.js` + `office-state.js` | 【CodeBuddy ND-5.2】 |
| 办公室视图开关（`?office3d=1` + `body.office-mode`） | `js/office/office-boot.js` | 【CodeBuddy 既有】 |

### 1.2 差距（本版要解决）

| # | 差距 | 后果 |
|---|---|---|
| G1 | eco 模式触发条件是 `team.runtime=="eco"`，与「办公室视图」无关 | 用户点办公室视图后右侧仍是 SECS 面板，试验田没有形成 |
| G2 | `rp-eco` 只在演练结束后渲染一次最终结果 | 看不到「感知-意图-行为」过程，物竞天择不可观测 |
| G3 | 只有 `skill_genome`，没有协作基因 | 违背世界观 §5——协作过程无法被环境选择 |
| G4 | 生态位固定不漂移，选择压力静态 | 环境不变则选择停滞，无军备竞赛 |
| G5 | 没有盲目学习：个体不会在生存中随机习得 skill | 违背世界观 §4 |
| G6 | `eco_drill.py` 存在**重复方法定义**（`ratchet_lock`×2、`inject_predator_pressure`×2，后者覆盖前者） | 代码缺陷，行为不可预期 |
| G7 | `gene_pool_snapshot()` 的 `dominant` 恒为空 | 基因池面板无信息量 |
| G8 | 双入口重复：`rp-secs` 内嵌 `eco-habitat-console` 与独立 `rp-eco` 并存 | UI 混乱 |

---

## 2. 目标形态：办公室视图 = 试验田（模式判定新规）

### 2.1 模式判定（v2 新规，取代 v1 §3.1）

```
进入办公室视图（?office3d=1，body.office-mode）
    → 右侧演练菜单【全部】切换为「物竞天择生境控制台」（rp-eco v2）
    → rp-secs 隐藏（不销毁，保证可逆）

旧版房间视图（无 office3d 参数）
    → 一切保持 CodeBuddy 现状：rp-secs 为默认；team.runtime=="eco" 时按 ND-5.1 旧逻辑切 rp-eco
    → 零回归硬约束
```

- 判定实现：`office-boot.js` 的 `FLAG_ON` 已是权威开关；新增 `window.__ECO_FIELD__ = FLAG_ON`，由页面级切换器统一显隐右面板。
- 团队 runtime 不再是办公室视图内的门槛：**任何团队**进办公室视图都进试验田（孪生演练本来就是沙箱，不动真身）。后端 trial 创建时若团队非 eco，则以「演练内临时 eco 化」处理（`drill_kind` 由前端显式传 `natural_selection` 覆盖，见 §5.2）。

### 2.2 双形态总览

| 区域 | 旧版房间视图（legacy，零回归） | 办公室视图（试验田，本版重构） |
|---|---|---|
| 左 3D | 房间 + SECS 协作热度 | 生境：血条/饥饿/生存时长 + 意图符号 + 觅食/求偶/死亡视觉事件 + 协作信号连线 |
| 右菜单 | SECS Pipeline / 导演台 / 五维评分（或旧 rp-eco） | **生境控制台 v2**（§4）：总览 KPI → 环境压力 → 种群 → 演练控制+回放 → 世代曲线 → 基因池 → 谱系 → 棘轮 |

---

## 3. 生境模型 v2（后端）

### 3.1 三层可遗传结构（世界观 §3/§5 落点）

```python
Creature:
  skill_genome:   List[str]            # 技能基因（v1 已有）
  collab_genome:  CollabGenome         # 协作基因（v2 新增，可遗传、可变异）
  skill_proficiency: Dict[str, float]  # 表现型：练熟度（个体学习，不遗传原值，遗传取 max 衰减）

CollabGenome:                          # 协作倾向向量——不是协作规则！
  share_tendency:    float 0~1   # 觅食盈余分享倾向（利他）
  signal_tendency:   float 0~1   # 发信号倾向（发现生态位机会时广播）
  follow_tendency:   float 0~1   # 响应他人信号的倾向（跟随）
  mate_choosiness:   float 0~1   # 择偶挑剔度（影响与谁交配）
```

- **协作如何被选择**：分享/信号/跟随都有代谢成本（发信号耗 Health、分享让渡 reward），但在生态位错配时能救同伴的命。环境宽松时利他基因是负担会被淘汰；环境严酷（漂移快/捕食强）时利他种群整体活得久、后代多——**协作协议是选择的结果，不是设计的输入**。
- **信号协议（Agent 独有沟通方式，世界观 §1）**：不是自然语言，是 3 种协议令牌：`FOOD@skill_x`（此处有匹配生态位）、`HELP`（我快饿死了）、`COURT`（求偶展示）。生物只能感知**视野内**的信号（受限感知），是否发/是否响应由 collab_genome 概率决定。

### 3.2 盲目学习（世界观 §4 落点）

- 每 tick 以 `blind_learning_rate`（读 eco-runtime config `learning` 节）概率随机习得一个**全技能池**中的 skill（不是只从生态位需求中拿——学习是盲目的，可能学到无用技能）。
- 习得的 skill 初始熟练度低（0.2），带**携带代谢成本**（`genome_carry_cost × len(skill_genome)`，技能包越大代谢越贵）——环境自然惩罚囤积无用技能者，奖励精简适配者。
- v1 的变异注入（`mutation_rate` 时随机注入生态位 skill）**降级为次要来源**，盲目学习成为主要探索机制。

### 3.3 环境：漂移 + 捕食 + 丰饶度（世界观 §3/§5、G4 落点）

```
环境状态 EnvState:
  demanded_skills: List[str]   # 当前生态位（多样，可同 tick 多需求）
  drift_prob: float            # 每 epoch 生态位漂移概率：随机替换 1 个需求
  predator_pressure: float     # 捕食压力概率（v1 已有，参数化暴露给 UI）
  abundance: float 0.5~2.0     # 丰饶度：觅食收益倍率（艰难时期利他更贵也更关键）
```

- 生态位漂移让「上一代的最优基因」不保证下一代最优——持续选择压力，防止收敛僵化。
- 全部参数进 eco-runtime config 新 `habitat` 节，UI 可调（§4.2）。

### 3.4 每 tick 的「感知 → 意图 → 行为」循环（世界观 §2 落点）

```
for creature in 存活种群:
  view   = 受限感知（自身 Health/近期成败 + 视野内信号 + 可见生态位机会）   # eco_loop.WorldView + signals
  state  = H/F/L 心智（compute_hunger/fear/libido）                        # eco_loop（复用）
  intent = generate_intention(state, view)                                  # eco_loop（复用）
  action = 表达意图:
      FORAGE  → 匹配生态位则按熟练度概率获得 abundance×FORAGE_GAIN；
                盈余时按 share_tendency 分享给视野内 HELP 信号者
      AVOID   → 低代谢躲藏（捕食压力期存活率高，但不产出）
      MATE    → 发 COURT 信号；双方 libido 门槛 + mate_choosiness 匹配则登记待繁衍
      REST    → 静息 + 盲目学习掷骰
  信号阶段: 按 signal_tendency 发 FOOD/HELP 信号（有代谢成本）
  结算:    HealthLedger.tick(cost, reward)；health≤0 → 死亡（基因抹除）
每 epoch:
  survival_ticks 排序 → 存活者中按 COURT 配对交叉（skill+collab 双基因）→ 变异
  生态位漂移掷骰 → ratchet 锁定世代最优 → 时间线快照
```

### 3.5 时间线记录（G2 落点，回放的数据基础）

- `EcoDrill.run()` 逐 tick 收集 `step_summary`（已有）并新增：每生物 `intention/health/signals/shared_with`；每 epoch 收集 `births/deaths/genomes/drift`。
- `run_drill_via_trial` 返回 `timeline: {steps: [...], epochs: [...]}`（步数超限时按等距采样降到 ≤600 帧，防 payload 爆炸）。
- 前端**剧场回放**：拿到 timeline 后按可调速度逐帧驱动 3D 与种群面板（§4.4）——不依赖 SSE，先把过程可观测做出来；真 SSE 直播列为 CodeBuddy 增强项（XB-2）。

### 3.6 代码修缮（G6/G7）

- 删除 `eco_drill.py` 重复的 `ratchet_lock`/`inject_predator_pressure` 早期定义，保留统一签名。
- `gene_pool_snapshot()` 重写：dominant = 存活个体中出现频率 ≥50% 的 skill；deprecated = 只存在于死亡个体的 skill；附 `collab_genome` 均值分布。

---

## 4. UI 全面重构：生境控制台 v2（前端）

### 4.1 面板切换（G1/G8 落点）

- `office-mode` 激活时：`rp-secs` → `display:none`；`rp-eco` → `display:block`；`eco-habitat-console`（rp-secs 内嵌旧块）**删除**（其功能已被 rp-eco v2 覆盖；旧房间视图的 runtime==eco 分支仍走 `_syncEcoPanel` 显示 rp-eco，不受影响）。
- `secs-core.js` 的 `_syncEcoPanel()` 增加最高优先级判定：`if (window.__ECO_FIELD__) { 强制 eco }`——防止 switchView 把 rp-secs 翻回来。
- 办公室浅色主题（`body.office-mode` CSS）为 rp-eco 补一组浅色适配样式。

### 4.2 生境控制台 v2 结构（自上而下）

| # | 区块 | 元素 id 前缀 | 内容 |
|---|---|---|---|
| 1 | 🌍 生境总览 KPI | `eco2-kpi-*` | 世代 / 存活÷总数 / 最长生存 ticks / 基因多样性（不同 skill 数） |
| 2 | 🌡 环境压力台 | `eco2-env-*` | 生态位 chips（当前 demanded_skills）· 捕食压力滑杆 · 丰饶度滑杆 · 漂移概率滑杆 · 「写回配置」按钮（PUT eco-runtime config `habitat` 节） |
| 3 | 🫀 种群面板 | `eco2-pop-*` | 每生物一行：名字 + Health 迷你条 + 意图符号（🍖觅食/🛡避险/💕求偶/💤静息）+ survival_ticks + skill 基因 chips + 协作基因四维迷你条；死亡行置灰划线 |
| 4 | ▶ 演练控制 + 回放 | `eco2-run-*` | 步数/世代数输入 · 「🧬 开始物竞天择」· 回放进度条 + 播放/暂停 + 速度(1x/4x/16x) · 状态文案 |
| 5 | 📈 世代曲线 | `eco2-gen-*` | 每代 avg/best survival 迷你柱状 + 出生/死亡数 + 漂移标记 ⚡ |
| 6 | 🧬 基因池 | `eco2-gene-*` | dominant（存活高频）/ deprecated（随死者消亡）skill 列表 + 协作基因均值雷达（share/signal/follow/choosy 四维） |
| 7 | 🌳 繁衍谱系 | `eco2-lineage-*` | 后代 → 双亲缩进树，标注世代与继承的基因 |
| 8 | 🔒 棘轮 | `eco2-ratchet-*` | 历代最优生存时长，只进不退 |

### 4.3 左 3D 生境化（办公室视图内）

复用已有：血条 Sprite（ND-5.2）、死亡淡出、`eco_health`/`eco_predator` reducer。新增：

- `eco_intent` dispatch：Agent 头顶意图符号（emoji Sprite，随回放帧更新）。
- `eco_signal` dispatch：信号可视化——发 FOOD 信号时该 Agent 脚下光圈短促闪烁并向视野内响应者画一条淡金色弧线（衰减 1.5s）；HELP 信号为红色脉冲。
- `eco_mate` dispatch：求偶配对成功时两 Agent 间粉色光弧 + 新生 Agent 以小号 figure 落位（沿用 plaza 风格模型语言，遵守 cerebrum 用户偏好：不做胶囊/棋子）。
- 猫解说员接入回放：回放期间猫气泡播报「第 N 代 · 存活 x/y · ⚡生态位漂移」等（复用 `cat_say`）。

### 4.4 回放引擎（前端新文件 `js/office/eco-replay.js`）

```
EcoReplay(timeline, {onFrame, onEpoch, speed})
  - 按 speed 定时器逐帧: onFrame(step) → OfficeAPI.dispatch(eco_health/eco_intent/eco_signal/eco_predator)
                              + 更新种群面板 DOM
  - epoch 边界: onEpoch(ep) → 世代曲线追加 + 谱系追加 + 猫播报 + eco_mate 派发
  - 播放/暂停/跳进度/变速；重复播放幂等（先 reset 状态）
```

---

## 5. 数据流与 API 变更

### 5.1 现有链路（保留）

```
ecoRunDrill → POST /api/v1/twin-trials（mode=evolutionary）
           → POST /api/v1/twin-trials/{id}/branches/{bid}/run
           → trial.drill_kind=="natural_selection" → eco_drill.run_drill_via_trial → 返回最终结果
```

### 5.2 v2 变更

| 变更 | 落点 | 说明 |
|---|---|---|
| trial 创建支持显式 `drill_kind` | `trial_api.py::create_trial` | body 传 `drill_kind:"natural_selection"` 可覆盖（办公室视图内任意团队都走生境）；不传则维持 runtime 判定（零回归） |
| 演练结果新增 `timeline` | `eco_drill.run_drill_via_trial` | `{steps:[…≤600 帧], epochs:[…]}`；每帧含 per-creature `intention/health/survival_ticks/signals/shared_with/alive` |
| 结果新增 `collab_profile` | 同上 | 种群协作基因均值 + 分布（供基因池雷达） |
| eco-runtime config 增 `habitat` 节 | `eco_runtime_config.py` | `drift_prob/predator_pressure/abundance`（GET/PUT 走既有路由，无新端点） |
| （增强，非本轮）SSE 直播 | `trial_api` 事件总线 | 长演练逐步推送，替代回放 → XB-2 |

---

## 6. 分阶段路线（XT=Fable 5 · XB=CodeBuddy）

| 阶段 | 主题 | 关键交付 | 归属 |
|---|---|---|---|
| **XT-0** | 文档 | 本 plan v2 + todos v2 重写 | 【Fable 5】 |
| **XT-1** | eco_drill v2 内核 | 去重缺陷修复；CollabGenome + 信号协议 + 分享/跟随结算；盲目学习；生态位漂移 + 丰饶度；timeline 记录；基因池 v2；双基因交叉遗传 | 【Fable 5】 |
| **XT-2** | 配置与 API | eco-runtime config `habitat` 节；trial 显式 `drill_kind` 覆盖；结果带 timeline/collab_profile | 【Fable 5】 |
| **XT-3** | 前端模式切换 | 办公室视图 → rp-eco 强制接管；删内嵌 eco-habitat-console；office-mode 浅色适配 | 【Fable 5】 |
| **XT-4** | 生境控制台 v2 | rp-eco 八区块全量重构（§4.2） | 【Fable 5】 |
| **XT-5** | 回放引擎 + 3D 生境事件 | `eco-replay.js`；office-state 增 `eco_intent/eco_signal/eco_mate` reducer；office-scene 意图符号/信号弧线/求偶光弧/新生落位；猫播报 | 【Fable 5】 |
| **XT-6** | 沙箱可跑验证 | pytest eco_drill v2 用例；`node --check`；office-state vitest | 【Fable 5】 |
| **XB-1** | 本机全量验收 | `./start.sh` 起真后端 → 浏览器进办公室视图跑一场演练：回放/3D/八区块逐项冒烟；`pytest src/backend/tests -q` 全量回归 | 【CodeBuddy】 |
| **XB-2** | SSE 实时直播（增强） | eco_drill 逐步事件接 trial SSE 总线，前端直播模式（回放作为兜底） | 【CodeBuddy】 |
| **XB-3** | LLM 生物语（增强） | 猫解说/生物信号的 LLM 润色（沙箱无 LLM 网络，必须本机做） | 【CodeBuddy】 |
| **XB-4** | 生产谱系落盘 | eco_drill `mate_fn` 注入 `team_manager.mate`，演练繁衍谱系可选写回 AgentProfile.metadata.lineage（默认关闭，演练默认不动真身） | 【CodeBuddy】 |

依赖：XT-1→XT-2→(XT-3∥XT-4)→XT-5→XT-6→XB-1→(XB-2∥XB-3∥XB-4)。

---

## 7. 验收标准

| 阶段 | 验收 |
|---|---|
| XT-1 | pytest：①利他基因在严酷环境（高漂移+高捕食）下的种群平均生存时长 > 純自利种群；②盲目学习会习得生态位外 skill 且携带成本可观测；③死亡个体双基因均不入下一代；④漂移后旧 dominant skill 可被替换；⑤timeline 帧数 ≤600 且含意图/信号字段 |
| XT-2 | GET/PUT `habitat` 节生效；显式 `drill_kind` 覆盖生效且不传时行为与 v1 一致（零回归） |
| XT-3 | `?office3d=1` 进页面右侧即 rp-eco，切视图不回弹；无 office3d 时 rp-secs/旧逻辑零变化 |
| XT-4 | 八区块齐备，演练后各区块有真数据（非占位文案） |
| XT-5 | 回放期间 3D 可见：意图符号变化、信号弧线、死亡淡出、求偶光弧、猫播报世代 |
| XT-6 | 沙箱内 pytest 新增用例全绿 + `node --check` 全过 + vitest office-state 通过 |
| XB-1 | 本机浏览器端到端一场演练全流程通过；全量 pytest 无回归 |

---

## 8. 设计原则（承接 v1，新增 6~8）

1. **不回归 legacy**：旧房间视图 SECS 路径零改动；办公室视图是并行试验田。
2. **复用优先**：eco_loop/health_ledger/eco_runtime_config/twin 事件钩子/办公室 3D 全部复用，只做编排与扩展。
3. **生存时长是唯一适应度**：任何新机制不得引入人工评分。
4. **繁衍 = 双基因交叉**：skill_genome 与 collab_genome 一起遗传、一起变异。
5. **协作靠涌现**：只给协作倾向基因 + 信号令牌 + 代谢成本，绝不写协作规则。
6. **学习是盲目的，选择是客观的**：主动学习不感知生态位正确答案。
7. **环境必须流动**：生态位漂移 + 捕食 + 丰饶度波动，静态环境不产生持续选择。
8. **过程必须可观测**：没有回放/直播的物竞天择等于没有发生——观测层（3D+控制台）与内核同等优先级。

---

## 9. 实施记录（v2.1 增补，2026-07-11）

### 9.1 已落地（Fable 5，本轮）

| 项 | 落点 |
|---|---|
| eco_drill v2 内核 | `sandbox/eco_drill.py`：CollabGenome 双基因 + FOOD/HELP/COURT 信号协议 + 分享/跟随结算 + 盲目学习/基因携带成本 + EnvState（漂移/捕食/丰饶）+ timeline（≤600 帧）+ 基因池语义化 + G6 去重修复 |
| 配置扩容 | `eco_runtime_config.py`：新 `habitat`、`drill_economics` 节；`learning` 增 blind_learning_rate/genome_carry_cost（参数页可调项 18→30） |
| drill_kind 覆盖 | `trial_api.py::CreateTrialRequest.drill_kind`——办公室视图内任意团队进生境，不传零回归 |
| 前端试验田切换 | `__ECO_FIELD__` 旗标（office-boot/eco-console 双保险）；`_syncEcoPanel` 最高优先级；内嵌 eco-habitat-console 移除 |
| 生境控制台 v2 | `rp-eco` 八区块全量重写 + `js/digital-twin/eco-console.js`（逻辑层）+ office-mode 浅色适配 |
| 剧场回放 | `js/office/eco-replay.js`（play/pause/seek/1-4-16x）+ office-state 新 reducer（eco_intent/eco_signal/eco_mate/eco_reset）+ office-scene 意图符号/信号配色/新生长大动画 |
| 3D 保障 | 种群直注 3D（_seedSceneRoster）+ 回放期轮询保护（__ECO_REPLAY_ACTIVE__）+ **bug-028 修复**（rp-eco 曾在布局容器外，挤没 3D 区） |
| 测试 | `tests/test_eco_drill_v2.py`（利他选择/盲目学习/漂移/timeline/基因池/habitat 配置） |

### 9.2 并行协作说明

CodeBuddy 与 Fable 5 于 2026-07-11 并行开发同一批文件。Fable 5 重写 `eco_drill.py` 时覆盖了 CodeBuddy 的 XB-2/XB-3/XB-4 工作树实现，已按契约在 v2 内核复原（on_step/on_epoch SSE、cat_commentary、mate_fn/write_lineage）；差异以 CodeBuddy 本机复验为准（todos XB-5.2）。**教训：并行改同一文件前先 git 提交或分工到不同文件。**

### 9.2b v2.2 增补（2026-07-11 晚，用户："简单参数配置不能反映物竞，也不能反映天择"）

**物竞做实——生态位容量竞争**（`habitat.niche_capacity`，默认 2，0=不限）：同一 tick 生态位只有 N 份食物，
有觅食意图且有匹配 skill 的生物按「熟练度+随机波动」竞争名额，败者白耗 0.75×miss 代谢（🥊 outcompeted）。
关键设计决策：竞争失败**不入恐惧窗口**——被挤掉≠能力失败，否则触发"恐惧螺旋→全员 avoid→集体饿死"的病态吸收态（烟测实证）。
涌现效应（烟测观察）：早期运气+练熟(+0.02/次)形成马太效应，赢家垄断生态位、败者淘汰——路径依赖是真实生态特征，非 bug。

**天择组合成剧本**：环境压力台新增「环境剧本」一键预设（🌿温和/🏜严酷/🌋剧变/⚔️军备竞赛），
组合 丰饶度×捕食×漂移×竞争名额 四维选择压力并写回配置；另新增 🥊竞争名额滑杆（0=∞）。

**同轮修复**：bug-045 猫解说降级泄漏（LLM 未连接时 harness 中文降级文案原样进猫气泡——现检测降级特征后换本地 Mei Ling 风格兜底；根因是 bug-043 密钥被抹的连带症状）；
eco-console 适配 create_trial 真实返回形状 `{trial_id,branch_id}`（此前读 `id/branches[0]` 导致「创建试炼失败」）；
演练开始时全体生物强制归位（打断咖啡/跑步机/马桶）。

### 9.2c v2.3 第二批（2026-07-11 深夜，用户离场期间的自主优化轮）

**多种群同场竞争（团队协作竞争力对比，用户核心诉求）**：`Creature.population` 标签 + 控制台「＋添加对比种群」
（截获 sexySelectTeam 的追加选择模式）→ `task_goal.extra_team_ids` 透传 → 后端多团队组装进同一生境；
结果带 `population_stats`（各种群 存活/平均/最长）；种群面板按种群分组、世代记录附各种群对比行、
报告含「🏆 种群竞争裁决」表（平均生存时长=协作竞争力，冠军 👑，灭绝 💀）。
综合冒烟：build_system(2/8 存活,avg 131.9t) vs xops(2/6,avg 103.5t) 裁决可判。

**修复三个观测保真 bug**：
① timeline 等距采样丢死亡帧 → 事件保真采样（死亡/捕食帧必保留，其余等距）——此前 3D 回放里被淘汰个体永远等不到死亡帧，动画与淘汰对不上；
② 世代号未盖进时间线帧 → run_drill 直接在帧上盖 generation（回放世代边界不再均分猜测）；
③ 回放中"尚未出生"的后代提前出现在种群面板 → 按帧 generation 过滤。

**修复「恐惧永锁」系统性全灭（重大生态 bug）**：恐惧窗口只在觅食尝试时更新——个体连败进 AVOID 后
窗口冻结、恐惧永不消退（滞回出口永远达不到），锁死躲藏至饿死；沙箱实验证实任何丰饶度都救不回
（全参数组合平均存活≈0/7）。修复=躲藏时最旧失败记忆逐 tick 淡出。修复后参数恢复意义
（gain8/cap0→3.2/7 存活；利他优势从 +2.8t 拉大到 +7.7t）。

**平衡定档（沙箱网格实验）**：config 默认 `forage_gain` 6→8、`niche_capacity` 2→3（严酷剧本 2/军备竞赛 1 不变）。

**观测体验**：📜 生境报告（回放结束自动弹出+回放条随时回看）——环境判词/🏅个体生存排行（点名最长存活者，
全灭时亦然）/种群裁决/世代纪事(含猫解说)/基因池裁决/幸存者协作画像；回放期 KPI 逐帧刷新 + 3D 左下角生态位提示；
R5 技能名可读化（hex ID→中文名，覆盖生态位/基因 chips/基因池/报告/回放标签）；
「纷纷退场」修复（演练后作息欠账一次性放行导致全员涌向咖啡机/马桶——回放期冻结作息并重置错峰计时）；
死亡淡出可逆（重跑时死者恢复不透明度回到工位，不再是幽灵场）。

### 9.2d v2.4 赛制（2026-07-11，用户："恐龙队的霸王龙获胜，但恐龙队与人类队比较，人类完胜"）

多种群竞争分为两种赛制（演练控制区 radio 切换）：

**🏟 分场锦标赛（默认，用户直觉语义）**：各队**独立**进入同一环境配置的生境，依次上场演练——
3D 中先看 A 队全程（回放完整播完），再自动换 B 队入场演练；每队各自产出 🏅 黄金适者；
全部结束后自动弹「🏟 锦标赛冠军裁决」：按平均生存时长排名（👑 冠军团队 / 💀 全灭），
附各队黄金适者的技能基因+协作基因对比（解释"为什么冠军是冠军"）。
实现为前端编排（逐队创建单队 trial + 顺序回放），**不依赖后端多种群代码，旧后端即可用**。

**⚔️ 同场混战（高级）**：v2.3 的同一生境直接竞争（同生态位抢名额），依赖后端 extra_team_ids（需重启后端）。
用户报告的"对比种群没参与"正是因为后端未重启——混战模式已加诊断提示。

### 9.2e 小虎 Mei Ling 彻查结论（2026-07-11）

链路证据：气泡中的英文正是按「猫发言提示词」skill 拼出的请求原文——**skill 读取链路是通的**；
断点在 LLM 调用：`cat_speak` 走 harness **全局默认 provider** 的密钥槽（`__default__`），
它在 bug-043 中被抹掉；用户重配的 key 存进的是 `build_system.codebuddy` **模型槽**——两个槽不同。
且 bug-045 的 Mei Ling 兜底代码需重启后端才生效。
根治（todos XB-8，CodeBuddy）：cat_speak 凭据解析升级为三级回退
pet_squad 默认模型 key → 全局默认 provider key → provider env；
并核查「设为默认模型」保存时 `_sync_default_model_to_harness` 是否把 api_key 同步进 harness 默认配置。

### 9.3 后续（CodeBuddy，见 todos XB-5/6/7）

本机浏览器复验（bug-028 + 契约恢复 + 全量回归）→ 生境专属 3D 场景层（生态位图腾/捕食者动画/觅食光点，Agent 本体保持 plaza 风格）→ 参数页滑杆化与校验。

---

*配套执行清单见：[`物竞天择数字孪生演练todos.md`](物竞天择数字孪生演练todos.md)（v2，含 Fable 5 / CodeBuddy 分工标注）*
