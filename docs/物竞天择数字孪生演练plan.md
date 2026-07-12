<!-- docs-signoff: author="Fable 5" kind="llm" doc="plan" ts="2026-07-12T02:00:00Z" -->
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

---

# 物竞天择数字孪生演练 Plan v3 — 三级赛制 · 遗传学化谱系 · 同比/环比/综合比

> 版本：v3.0 · 日期：2026-07-12 · 作者：Fable 5（Claude）
> 承接：v2.4（三级赛制之前的「分场锦标赛 / 同场混战」双赛制）。v2 的 XT-1~XT-10、XB-1~XB-8 已落地，本版**只重构赛制语义、评分、世代曲线、繁衍谱系**四件事，其余内核（eco_drill 代谢/信号/盲目学习/流动环境/timeline）全部复用，零重写。
> 入口：`http://localhost:5173/Agent-digital-twin.html?office3d=1`（办公室视图 = 试验田）。

---

## V3-0. 缘起（用户 2026-07-12 原话精神，本版最高约束）

用户对「物竞天择」菜单提出**赛制分层**的核心判断，全文精神必须贯穿实现：

1. **分场锦标赛 = 团队内部的 Agent 能力较量**。如同**家族内部的精英识别**过程——强调的是**个人能力**。
2. **同场混战 应改名「多队对抗」= 团队间的能力较量**。如同**不同种族间的精英团队竞争**，会出现**田忌赛马**（以己之强对彼之弱的排兵布阵）的情况——强调的是**团队内 Agent 之间的配合**。
3. 以地球为例，必然涌现一种**综合性更强**的竞争过程——即原「同场混战」的终极形态，应改名「**混合竞争**」。它是**螺旋上升**，充斥着**大小迭代**过程，这里**更要体现环境的选择**。
4. 由此：**赛制**要改、**评分**要改、**世代演化曲线**要改（要有**同比、环比、综合比**）。
5. **繁衍谱系**必须以**生物遗传学**为根——尤其借鉴**西方财阀家族对技能与知识传承**的学术视角（涉及**地理、学派、政治**），让人理解基因延续的复杂性；让「团队 + 技能集合 + 团队协作」能体现**自然选择性**，代表着对智能体能力**客观、冷静的判断**。

> 硬约束（承接 v1/v2 不变）：**生存时长（survival_ticks）是唯一原生适应度**。v3 新增的一切评分/曲线/谱系指标都必须是 survival_ticks 与**已观测行为**的**派生函数**，不得引入人工打分。协作靠涌现（只给协作基因 + 信号令牌 + 代谢成本），不写协作规则。

---

## V3-1. 三级赛制总表（取代 v2.4 的 tournament/melee 双档）

| 赛制 | 选择单元 | 生物学隐喻 | 竞争范围 | 强调 | 底层复用 |
|---|---|---|---|---|---|
| **① 分场锦标赛**（Divisional Tournament） | **个体** | 家族内部精英识别（近交 + 漂移 + 同类选配） | **单团队**，队内个体竞争 | **个人能力** | 单种群 drill（现有），改语义 |
| **② 多队对抗**（Multi-team Confrontation） | **团队** | 不同种族的精英团队对垒（异质谱系保持各自身份） | **多团队**作为离散单元同场 | **队内配合** + 田忌赛马 | melee 的多种群内核 + 团队级评分 |
| **③ 混合竞争**（Mixed Competition） | **个体 + 涌现的跨队谱系** | 地球级综合生态（基因流 + 杂种优势 + 均值回归 vs 棘轮） | **全部种群混合**，嵌套大小迭代 | **环境的选择**（最强） | melee 内核 + 纪元（era）嵌套 + 跨队交配 |

三档是**递增的综合度**：个体 → 团队 → 生态。前端 `_raceMode` 从二值（tournament/melee）升级为三值枚举 `division | confrontation | mixed`，`tournament/melee` 保留为兼容别名（`tournament→division`，`melee→confrontation`）以防外部调用与旧回归断裂。

### V3-1.1 ① 分场锦标赛（个体 · 家族内部）

- **语义修正**：v2.4 的 tournament 实为「多队各自独立跑再比冠军队」——那属于**多队对抗**语义。v3 的分场锦标赛回归用户定义：**单个团队**内，个体（Agent 化身 Creature）在同一生境里竞争生存，识别**家族精英**。
- **产出**：队内**精英阶梯**（Elite Ladder）——按 survival_ticks 排名的黄金适者榜，标注每位精英的技能基因 + 协作基因 + 世代。
- **遗传学镜头**：单团队反复交配 = **近交**风险（inbreeding depression）+ **奠基者效应**（初始 roster 决定整个家族基因池）+ **漂移**（小种群随机丢失技能多样性）；`mate_choosiness` 高 → **同类选配**（assortative mating）把优势基因往少数血系集中。面板给出「家族多样性指数」（存活个体的不同 skill 数 / 初始）随世代下降的告警。
- **后端影响**：几乎为零——就是 `extra_team_ids=[]` 的单种群 drill。仅需结果里补 `elite_ladder` 派生字段（前端也可自行从 `final_ranking` 计算，优先前端算，零后端改动）。

### V3-1.2 ② 多队对抗（团队 · 种族之间 · 田忌赛马）

- **语义**：多个团队作为**离散单元**进入**同一生境**竞争（沿用 melee 多种群内核），但**评分在团队层**，且**度量队内配合**。
- **可插拔排兵布阵策略**（用户澄清：田忌赛马**只是一个例子**，不要硬代码）：系统按个体 survival_ticks 给每队排出「梯队」（rank1/rank2/…），然后用**一组可插拔的策略**把双方梯队映射为「对位」，算出局分。**每个策略 = 一个纯函数**，注册进策略表即生效，新增策略无需改核心（见 V3-1.2b）。这是**分析/展示层**（教练视角的 what-if），**不改变生存内核**，只对已产出的 survival_ticks 做博弈论重排——严守「协作靠涌现、不写协作规则」（策略是**事后复盘镜头**，不是注入模拟的规则）。
- **队内配合度量（派生，非打分）**：`coordination_lift = 团队实际平均 survival_ticks − 该队个体「单飞基线」平均`。单飞基线 = 同一批个体在 `niche_capacity=∞ 且关闭信号响应` 的对照微跑（或用同配置单种群 drill 的历史均值近似）。lift>0 说明协作基因（share/signal/follow）在该环境净收益为正——**配合被环境正选择**；lift<0 说明利他在该环境是负担。全部由 survival_ticks 差值得出，符合「唯一适应度」原则。
- **遗传学镜头**：各队 = **异质 deme（地理隔离种群）**，保持血统身份；被选择的团队级可遗传结构 = **协作基因组**（collab_genome 的队内分布）。跨队暂不交配（保持对抗），交配仍在队内 → 各队独立演化出各自的协作风格。
- **后端影响**：melee 内核已支持 `extra_team_ids` 多种群（v2.3 XT-9.1）。v3 需：结果 `population_stats` 补 `coordination_lift`、`lineup`（梯队）字段；策略对位**全部前端计算**（拿 per-population 的 ranking 即可），后端零改。

### V3-1.2b 排兵布阵策略：可插拔策略表（用户澄清点）

> 用户 2026-07-12：「田忌赛马是举个例子，讲一下排布的策略，你不要硬代码，可以作为策略的一种，你再设计几个策略，可插拔的那种灵活度高一些。」

**策略接口（纯函数，前端）**：

```
Strategy = {
  id, name, icon, desc,
  // myRanked/oppRanked: 已按 survival_ticks 降序的梯队；ctx: {env, laneDemands, ...}
  arrange(myRanked, oppRanked, ctx) -> [{lane, mine, opp}]   // 双方对位安排
}
// 局分裁定统一由框架做：每个 lane 比 survival_ticks（同 lane 高者胜），汇总局分 W-L-D。
// 策略只负责“怎么排”，不负责“谁赢”——胜负永远由已产出的 survival_ticks 决定。
```

**策略表 `MATCHUP_STRATEGIES`（注册即生效，新增=加一个函数）**：

| id | 策略 | 排布逻辑 | 洞察 |
|---|---|---|---|
| `head_on` | ⚔️ 正面对决（基线） | rank-i vs rank-i，纯实力硬碰 | 总实力的诚实对比，作对照基准 |
| `tianji` | 🐎 田忌赛马（错位最优） | 求「最大化局分」的错位排列（弃最弱对其最强，其余错位上顶）——Kuhn-Munkres/贪心最优指派 | 弱队能否靠排兵翻盘；错位价值 = 最优局分 − 基线局分 |
| `spearhead` | 🔱 集中突破 | 把 top-k 主力全押到「最可能赢」的少数 lane，其余 lane 放弃 | 田忌的反面：赌局部碾压，看能否以少胜多守住关键生态位 |
| `balanced` | 🛡 均衡布防 | 最小化各 lane 胜率方差，杜绝爆冷失分 | 无短板打法；牺牲上限换稳定 |
| `attrition` | 🌊 梯次消耗 | 按实力升序上场（弱者先耗生态位名额/捕食压力，强者后收割） | 利用 niche_capacity 机制的时序博弈 |
| `skill_counter` | 🎯 克制反制 | 按 skill_genome 与各 lane 生态位需求的匹配度指派（不只看 survival 排名） | 技能相性 > 单纯强弱；专精克制 |
| `random` | 🎲 随机（对照） | 随机指派，多次取期望 | 一切策略的下限锚点 |

#### 名词与裁定（先说清楚地基，后面每个策略才有意义）

- **梯队（lineup / ranked roster）**：一支队按个体 survival_ticks 降序排成 a₁≥a₂≥…≥aₙ。这是策略的**唯一输入实力数据**，来自已产出的演练结果——不是新造的战力值。
- **赛道（lane）**：一场 1v1 对决槽。两队各出一名成员进同一 lane，**survival_ticks 高者赢下该 lane**。默认 n 条 lane（n=较少一队的人数，多出的成员轮空或按规则补位）。lane 可选带**生态位需求标签**（该环境 `demanded_skills` 之一），供 `skill_counter` 用。
- **局分（match score）**：赢的 lane 数 W、输 L、平 D。**比的是赢下的 lane 数，不是总 survival_ticks 之和**——这正是「田忌赛马」成立的前提（总和输、局分赢）。
- **策略只管「怎么排」，框架统一裁「谁赢」**：策略函数只输出双方成员到 lane 的映射（一个合法排列，无重复/遗漏），胜负永远由框架比 survival_ticks 得出。这条铁律保证任何新策略都不能作弊改变实力。
- **对手序**：默认对手梯队按 rank 顺序摆放（b₁在 lane1…），我方用策略应对；「全策略对比」里也可让双方都用各自策略，出一张对称的策略×策略矩阵。

#### 七个策略逐一说透（直觉 → 算法 → 何时赢 → 揭示什么 → Agent 团队语义）

**⚔️ `head_on` 正面对决（诚实基线）**
- 直觉：不耍花招，rank-i 打 rank-i，强的碰强的、弱的碰弱的。
- 算法：`arrange = [(laneᵢ, aᵢ, bᵢ)]`，i=1..n。O(n)。
- 何时赢：当且仅当你**逐档实力都不弱于**对手。赢得干净，输得也认。
- 揭示什么：**实力的诚实基准线**。其他所有策略的局分都要减去 head_on 的局分，才知道「策略本身」贡献了多少——head_on 是零点。
- Agent 团队语义：你的团队是不是**每一个能力档位都过硬**。head_on 赢=**厚度**（不是靠一两个明星撑）。

**🐎 `tianji` 田忌错位最优（战术上限）**
- 直觉：明知打不过就别硬拼——用最弱的去送给对方最强的，把自己每一档都错位上顶去咬对方低一档。
- 算法：对手序已知，求**最大化我方赢 lane 数**的指派。经典最优解（等价 LeetCode 870「优势洗牌」/ 二分图最大匹配的贪心特例）：两队各自排序；双指针从「对手最强」开始，用「我方仍能击败他的最弱者」去接；若我方最强都打不过当前对手，则**弃**——派我方最弱者去当炮灰。贪心即最优，O(n log n)。
- 何时赢：当你**总实力略逊但分布错位有利**时能偷局分；若你本就全面碾压，tianji 结果 = head_on（无花可耍）。
- 揭示什么：**战术腾挪空间** = `tianji_W − head_on_W`。这个差值大，说明你队的实力「没用在刀刃上」——**存在错配**，靠重排就能多赢。差值为 0 说明你已把实力发挥到极致（或毫无腾挪余地）。
- Agent 团队语义：能否靠**排兵**而非**加人**取胜。差值大 = 团队有**调度红利**未兑现；这本身是一条改进信号。

**🔱 `spearhead` 集中突破（赌局部碾压）**
- 直觉：不追求赢多数 lane，而是**主动放弃**弱 lane，把主力全部砸进少数几条最可能赢的 lane，形成碾压。
- 算法：算我方每人对各 lane 的赢面margin，选 top-k 主力 + 边际赢面最大的 k 条 lane 一一锁定，其余 lane 填我方最弱者（弃子）。k 可配（默认 = ⌈n/2⌉+1，即锁定「过半」即赢的最小集）。
- 何时赢：在**「赢下关键 lane 收益超额」**或**「只需过半即胜」**的规则下最优；在等权重纯 lane 计数里通常不如 tianji。
- 揭示什么：团队价值是**集中**还是**分散**——是否**明星驱动**。spearhead 能赢而 head_on 输 = 你队靠**尖子**，深度不足。
- Agent 团队语义：面对「必须拿下某个关键生态位」的任务（如唯一的高价值 niche），集中主力是否划算。反映团队的**攻坚（而非铺面）**能力。

**🛡 `balanced` 均衡布防（对抗性下限最优 / maximin）**
- 直觉：假设对手**也会重排来针对你**，那就选一个「无论对手怎么排，我最坏结果都最好」的阵型——**没有可被打爆的软肋**。
- 算法：与 tianji（假设对手序固定）相反，balanced 求 **maximin**：在对手对我方每种排布都最优反制的前提下，选我方**保底赢 lane 数最大**的排布（博弈论鞍点；小 n 用极小极大搜索，大 n 用「均摊 margin、消灭负 margin 峰值」的启发式）。
- 何时赢：在**对手同样聪明、且环境会漂移**（今天重要的 lane 明天可能换）时，balanced 的**保底最高**，不会爆冷崩盘。
- 揭示什么：团队的**鲁棒性/抗脆弱**——最坏情况有多坏。balanced 与 tianji 局分差距大 = 你的 tianji 赢是「吃对手不重排」的**脆弱胜利**，一旦对手也优化就崩。
- Agent 团队语义：环境不确定、对手会适应时，团队能不能**稳**。这是「厚度」之上再加「**无短板**」。

**🌊 `attrition` 梯次消耗（时序博弈，倚仗生境机制）**
- 直觉：弱者先上,故意消耗环境——先头部队耗光生态位名额/吸引捕食压力,主力随后收割空场。
- 算法：按 survival 升序排布（aₙ 先、a₁ 后）映射到**按时间推进**的 lane。
- 何时赢：**只有在生境的时序机制真实存在时**（`niche_capacity` 有限、捕食压力随消耗衰减）。
- 揭示什么：团队价值是否**依赖出场顺序**——存在「弃子换空间」的**牺牲式协作**红利。
- Agent 团队语义：真实任务里的**梯队投放**（先遣试探、主力收口）是否比一拥而上更优。
- ⚠️ **诚实边界**：attrition 的效果**本质是时间性的**，纯粹对「已产出的 survival_ticks」做事后重排**无法完整体现**它——因为 survival_ticks 是在某个既定出场环境下产生的。因此 attrition 有两种模式：**(a) 复盘近似**（默认，用 survival_ticks 做时序加权估计，仅供参考、会标注「估计值」）；**(b) 实验模式**（可选，【CodeBuddy】XB 级：真的以升序出场顺序**重跑一场**演练取真实 survival_ticks）。这条要对用户讲明，不能拿近似值冒充真值。

**🎯 `skill_counter` 克制反制（相性 > 强弱）**
- 直觉：不看谁强,看谁**对路**——每条 lane 有生态位需求(某 skill),派 skill_genome 最匹配那条 lane 的人去,哪怕他总排名不高。
- 算法：需 lane 带 `demand_skill` 标签（取自环境 `demanded_skills`）。对每条 lane，按「我方成员 skill_genome 与该 lane 需求的匹配度 × 该 skill 熟练度」排序指派，做二分图最大权匹配（匈牙利算法，O(n³)；n 小可暴力）。
- 何时赢：环境**奖励专精**时——一个中等强度的对口专家能在他的生态位里击败一个更强的通才。
- 揭示什么：团队实力是不是**对的那种实力**——**结构性匹配**而非绝对值。skill_counter 显著优于 head_on = 你队真正的武器是**专精配置**，且当前环境吃这一套。
- Agent 团队语义：把「谁去干哪件事」按**技能相性**而非**资历/总分**来派，能带来多大提升——直接对应真实任务派单的**人岗匹配**价值。

**🎲 `random` 随机（零假设 / 下限锚点）**
- 直觉：瞎排,多次取平均,看运气能到哪。
- 算法：蒙特卡洛 M 次随机排列（默认 M=200），取局分期望与分布。
- 何时赢：不为赢，为**定标**。
- 揭示什么：任何策略的「真实增益」= 该策略局分 − random 期望局分。若某策略并不显著高于 random，说明**在这两队之间它不起作用**（实力差距要么大到无所谓排布，要么小到全靠运气）。
- Agent 团队语义：**别把运气当能力**。random 是照妖镜，防止把噪声解读成战术天才。

#### 「🔀 全策略对比」= 团队能力性格的诊断矩阵（这才是重点）

把七个策略跑一遍，得到一张「策略 × 局分」表。**关键不是哪个策略赢，而是「赢的模式」揭示的团队性格**：

| 观察到的模式 | 判读（客观冷静） |
|---|---|
| head_on 就赢，且 balanced 也赢 | **实力厚且无短板**——substantive + robust，最可靠的强队 |
| head_on 输、tianji 赢、balanced 输 | **脆弱的战术胜**——靠对手不重排；对手一优化就崩，别高估 |
| head_on 输、spearhead 赢 | **明星驱动**——深度不足，赢在尖子；关键攻坚可用，铺面易垮 |
| skill_counter 远超 head_on | **专精红利 + 环境吃专精**——该队武器是结构匹配，换环境需重估 |
| 各策略都≈random | **排布无关**——要么碾压/被碾压，要么纯运气；别过度解读 |
| attrition(实验模式) 明显超其他 | **时序/牺牲式协作**有真实红利——值得在真实任务里做梯队投放 |

- 这张表就是用户要的「对智能体能力**客观、冷静的判断**」：不是给一个分数，而是**刻画一支团队的能力性格**（厚/尖/稳/专/脆/纯运气），并指出改进方向（如「tianji 红利大 → 有调度空间」）。
- 全部读数都从**已产出的 survival_ticks + 已有的 skill_genome**派生，**零主观打分**，守住世界观铁律。

- **可插拔实现**：`MATCHUP_STRATEGIES` 是一个 `{id: Strategy}` 映射，UI 下拉列出全部已注册策略；加策略 = `registerMatchupStrategy(strategyObj)`，核心裁定/渲染零改动。田忌只是其中 `tianji` 一项。
- **对比视图**：可一键「全策略跑一遍」，出一张「策略 × 局分」表——直观看到「同样两队，换个排布，胜负如何变」，这正是用户要的「讲清排布策略」。
- **世界观合规**：策略是**事后复盘/what-if**，作用于已产出的 survival_ticks，**绝不回灌进模拟**（否则就成了「设计协作」）。可选进阶（【CodeBuddy】XB 级）：把某策略选定的阵型作为**新一场演练的初始投放顺序**做实验对照——但默认关闭，且即便开启也只影响「谁先入场」，不改协作规则。

### V3-1.3 ③ 混合竞争（生态 · 螺旋上升 · 大小迭代）

- **语义**：全部种群**混入同一生境**，去团队身份壁垒，**允许跨队交配**（基因流），并引入**嵌套迭代**：
  - **小迭代 = epoch（世代）**：现有 step→epoch 循环。
  - **大迭代 = era（纪元）**：若干 epoch 组成一个纪元；每跨一个纪元，环境**阶跃加压**（丰饶↓/捕食↑/漂移↑/生态位名额↓，即「军备竞赛」剧本自动递进），并用**棘轮**把上一纪元的世代最优基因带入下一纪元 → **螺旋上升**。
- **环境选择最强**（用户「更要体现环境的选择」）：混合竞争下，环境参数**不是静态配置**而是**逐纪元流动**；跨队交配带来**杂种优势**（heterosis：远缘血系后代往往更适应），但**均值回归**（regression to the mean）会把领先血系拉回种群均值——**棘轮 vs 回归**的张力就是螺旋上升的引擎。
- **遗传学镜头**：island-model **基因流** + **杂种优势** + **奠基者/瓶颈** + **均值回归**（Gregory Clark《The Son Also Rises》：精英血统优势跨代衰减但极慢，约 10–15 代才回归均值——本系统压缩为 era 尺度可视化）。
- **后端影响**：最大的一档。需在 `eco_drill` 外包一层 `run_eras()`：era 循环 + 环境阶跃 + 跨纪元棘轮 + 跨队交配开关（`allow_cross_population_mating`）。timeline 增加 `era` 维度。**这是 v3 唯一实质后端新代码**（其余复用）。

---

## V3-2. 评分模型重构（评分要改）

原则不破：**survival_ticks 是唯一原生适应度**。以下均为**派生指标**（survival_ticks + 已观测行为的函数），按赛制分层呈现：

| 赛制 | 主指标（个体/单元） | 派生洞察 |
|---|---|---|
| ① 分场锦标赛 | 个体 survival_ticks | 精英阶梯 top-k；家族多样性指数（Δ随世代）；近交衰退告警（多样性跌破阈值） |
| ② 多队对抗 | 团队 = 队内 survival_ticks 分布（均值 + 前 k 名「首发」均值） | **coordination_lift**（配合净收益）；**可插拔排兵策略**（田忌/正面/集中/均衡/梯次/克制/随机）的策略×局分对比表；团队协作画像（collab 基因均值雷达） |
| ③ 混合竞争 | 个体 survival_ticks（环境权重最高） | **综合指数**（见 V3-3）；纪元棘轮曲线；杂种优势 vs 近交对照；血系均值回归轨迹 |

- **归一化**：所有跨单元/跨代比较前，用「当前环境难度」归一（同一环境剧本内 survival_ticks 直接可比；跨纪元/跨剧本用 `survival_ticks / 该环境理论上限步数` 归一为 0~1 的**适应率**）。
- **绝不**引入「技能质量分」「协作质量分」这类主观量——配合好不好只由「活得久不久」的差值说话。

---

## V3-3. 世代演化曲线：同比 / 环比 / 综合比（曲线要改）

现有 `eco2-gen` 只有「每代最长/平均」柱状，本质是**环比**的一半。v3 三比齐全：

| 比法 | 定义（本系统落地） | 适用赛制 | 视觉 |
|---|---|---|---|
| **环比**（QoQ，逐代） | 第 G 代 vs 第 G−1 代：Δ最长、Δ平均、Δ多样性 | 全部 | 柱状 + Δ 箭头（↑绿/↓红/→灰）+ 百分比 |
| **同比**（YoY，同相位） | **同一世代序位**的跨维对比：混合竞争=纪元 N 的 G_k vs 纪元 N−1 的 G_k；多队对抗=各队第 G 代并排 | ②③ | 分组折线（一条线一纪元/一队），同相位对齐 |
| **综合比**（Composite） | 单一**归一化上升指数** = w₁·适应率(最长) + w₂·适应率(平均) + w₃·多样性 + w₄·棘轮进度；权重随环境压力自适应（越严酷，适应率权重越高） | 全部（③最有意义） | 一条主曲线 + 分量堆叠可切换；螺旋上升可见 |

- 数据来源：`generations[]`（已含 best/avg/drift/populations）+ v3 补的 `diversity`、`era`、`ratchet_best`、`fitness_rate`。
- **前端优先算**：环比、同比、综合比全部可从 `generations[]` 数组在前端计算，后端仅需补齐上述逐代字段（大多已有，补 `diversity`/`era`/`fitness_rate`）。

---

## V3-4. 繁衍谱系遗传学化（谱系要改 — 本版重头戏）

目标：把现有「后代→双亲」扁平列表升级为**遗传学化的血系分析面板**，体现「团队+技能集合+团队协作」的**自然选择性**，做出**客观冷静的能力判断**。全部指标可计算、可解释、可引用学术概念。

### V3-4.1 六个遗传学维度（每个都映射到已有数据，附学术出处）

| # | 维度 | 学术根据（出处见文末引用） | 本系统计算 | 呈现 |
|---|---|---|---|---|
| D1 | **遗传力 h²**（narrow-sense 加性遗传） | 数量遗传学：可遗传变异是选择改良的前提 [QG-1] | 亲–子 survival_ticks / collab 基因的回归斜率（parent-offspring regression） | 「该血系哪些性状真被传下来」条形：高 h² 性状高亮 |
| D2 | **同类选配（门当户对）** | Fisher：亲属相关性 = 遗传力 × 系谱系数 × 选配强度；精英与精英结合放大优势 [QG-2] | COURT 配对双方 survival_ticks 排名相关系数（mate_choosiness 驱动） | 配偶适应度散点/相关系数；「精英联姻」连线加粗 |
| D3 | **近交衰退 vs 杂种优势** | 奠基者种群与近交系数；远缘杂交（异质血系）产生杂种优势 [QG-3] | 血系内平均系谱系数（coefficient of relationship）随代变化；跨队后代 vs 队内后代 survival 对照 | 近交系数曲线 + 杂种优势 Δ 标记（混合竞争专属） |
| D4 | **均值回归** | Clark《The Son Also Rises》：精英血统优势跨代衰减但极慢（约 10–15 代回归均值），持续的是**可传承的底层能力**而非单纯财富 [SM-1] | 领先血系的世代 survival 轨迹 vs 种群均值的收敛速度 | 血系轨迹线向种群均值收敛动画；标注「回归半衰期（代）」 |
| D5 | **奠基者/瓶颈效应** | 小奠基种群的遗传力与多样性受初始个体主导 [QG-3] | 初始 roster 基因对末代基因池的贡献占比 | 「家族奠基者」溯源；瓶颈世代（存活骤降）标记 |
| D6 | **系谱协作演化** | 系谱数据用于研究合作与近交回避的演化 [QG-4] | collab_genome（share/signal/follow/choosy）沿血系的传递与选择方向 | 协作基因血系热力图；「哪支血系把利他传了下去」 |

### V3-4.2 用户点名的三条财阀传承维度 → 模型映射

| 用户维度 | 现实学术意象 | 本系统落地（复用已有字段，不新造机制） |
|---|---|---|
| **地理** | 地理隔离 deme、island-model 基因流、区域生态位专精 | 团队 = deme；多队对抗=隔离（无基因流），混合竞争=基因流开启；生态位漂移 = 区域环境差异 |
| **学派** | 技能基因簇作为「门派」；师承 = 纵向 + 斜向的熟练度传递（memetic，非纯基因） | skill_genome 的高频共现簇识别为「学派」；`skill_proficiency` 的师徒传递（盲目学习 + 遗传取衰减 max）= 师承 |
| **政治** | 协作/联盟资本可传承；联姻结盟 | collab_genome 的 follow/signal/choosy = 可遗传「政治资本」；同类选配 = 门阀联姻；联盟涌现于信号响应网络 |

### V3-4.3 谱系面板结构（`eco2-lineage` 重构）

自上而下：① 血系树（多代缩进树 + 系谱系数着色）→ ② 遗传力条（D1）→ ③ 联姻散点（D2）→ ④ 近交/杂优曲线（D3，混合竞争显示杂优对照）→ ⑤ 均值回归轨迹（D4）→ ⑥ 奠基者溯源（D5）→ ⑦ 学派/政治血系热力图（学派=skill 簇、政治=collab 传递，D6）。每图一句**冷静判词**（如「blade 血系遗传力 0.62，属强传承；但已进入均值回归，领先优势预计 3 代内消解」）。

---

## V3-5. 数据流与改动面（最小化后端）

| 层 | 改动 | 归属 | 后端/前端 |
|---|---|---|---|
| 赛制枚举 | `_raceMode` 二值→三值（division/confrontation/mixed，含旧别名兼容） | 【Fable 5】 | 前端 |
| ① 分场锦标赛 | 单种群 drill + 前端算 `elite_ladder`/多样性指数 | 【Fable 5】 | 纯前端 |
| ② 多队对抗 | melee 内核（已有）+ 结果补 `coordination_lift`/`lineup`；**可插拔排兵策略表**（7 策略，纯前端） | 【Fable 5】(前端) / 【CodeBuddy】(后端补字段+重启验证) | 前后端 |
| ③ 混合竞争 | `run_eras()` 纪元嵌套 + 环境阶跃 + 跨纪元棘轮 + 跨队交配开关；timeline 增 `era` | 【Fable 5】 | 后端（唯一实质新代码） |
| 评分派生字段 | `generations[]` 补 `diversity`/`era`/`fitness_rate`；`final_ranking` 已够 | 【Fable 5】 | 后端补字段 |
| 曲线三比 | eco2-gen 重构：环比 Δ / 同比分组线 / 综合比主曲线 | 【Fable 5】 | 纯前端 |
| 谱系遗传学化 | eco2-lineage 重构七图 + 判词；h²/系谱系数/回归等前端从 lineage+ranking 计算 | 【Fable 5】 | 纯前端（后端 lineage 已带双亲/世代） |
| 参数页 | `habitat` 增 `era` 节（era_count/step_per_era/env_ramp/cross_pop_mating） | 【Fable 5】 | 后端 config + pet-config 前端 |

> 关键：三档里只有**混合竞争的 `run_eras()`** 是后端实质新增；分场锦标赛、多队对抗的评分/田忌赛马、以及三比曲线、遗传学谱系**几乎全在前端**从已有结果字段计算——符合「surgical、最小改动」原则。

---

## V3-6. 分阶段路线（XV = v3 阶段号）

| 阶段 | 主题 | 交付 | 归属 |
|---|---|---|---|
| **XV-0** | 文档 | 本 plan v3 + todos v3 | 【Fable 5】 |
| **XV-1** | 赛制三档骨架 | `_raceMode` 三值 + UI radio 三档 + 提示语 + 旧别名兼容 | 【Fable 5】 |
| **XV-2** | ① 分场锦标赛 | 单种群语义修正 + 精英阶梯 + 家族多样性/近交告警（前端算） | 【Fable 5】 |
| **XV-3** | ② 多队对抗 | 团队级评分 + coordination_lift + 田忌赛马对位矩阵/最优排兵 + 协作雷达 | 【Fable 5】(前端) |
| **XV-4** | ③ 混合竞争后端 | `run_eras()` 纪元嵌套 + 环境阶跃 + 跨纪元棘轮 + 跨队交配 + timeline.era | 【Fable 5】 |
| **XV-5** | 世代曲线三比 | eco2-gen 重构：环比/同比/综合比 + 逐代 diversity/era/fitness_rate 字段 | 【Fable 5】 |
| **XV-6** | 谱系遗传学化 | eco2-lineage 七图 + 六维度指标 + 冷静判词 + 学派/政治/地理映射 | 【Fable 5】 |
| **XV-7** | 沙箱验证 | pytest（run_eras/字段）+ node --check + vitest（曲线/谱系/田忌计算纯函数） | 【Fable 5】 |
| **XV-8** | 本机验收 | `./start.sh` 起真后端，浏览器三档各跑一场：分场精英榜 / 多队田忌矩阵 / 混合纪元螺旋 + 谱系七图；全量 pytest 回归 | 【CodeBuddy】 |

依赖：XV-1 →(XV-2 ∥ XV-3)→ XV-4 → XV-5 →(XV-6)→ XV-7 → XV-8。混合竞争(XV-4)先于同比曲线(XV-5，需 era 维度)与杂优谱系(XV-6，需跨队交配数据)。

---

## V3-7. 验收标准

| 阶段 | 验收 |
|---|---|
| XV-1 | 三档 radio 可切，提示语正确；`tournament/melee` 旧调用不报错（映射到 division/confrontation） |
| XV-2 | 单团队分场：精英阶梯按 survival 排序；近交——多样性指数随世代单调下降时出现告警文案 |
| XV-3 | 多队：coordination_lift 有正有负且=实际均值−单飞基线；策略表≥7 项可插拔（`registerMatchupStrategy` 加一项即出现在下拉与对比表，核心零改）；田忌（tianji）能出现「总分弱队靠错位赢局分」的算例；「全策略对比」表同两队不同策略给出不同局分 |
| XV-4 | pytest：`run_eras(era_count=3)` 逐纪元环境加压；跨队交配开启时出现父母来自不同 population 的后代；棘轮跨纪元只增不减；timeline 每帧带 era |
| XV-5 | 环比 Δ 箭头/百分比正确；同比分组线同相位对齐（纪元或队）；综合比单曲线随螺旋上升 |
| XV-6 | 七图有真数据：h²=亲子回归斜率、系谱系数曲线、均值回归轨迹向均值收敛、杂优 Δ（混合竞争）、学派=skill 簇、政治=collab 传递；每图有判词 |
| XV-7 | 沙箱 pytest 新增用例全绿 + 全部改动文件 node --check + vitest 纯函数（田忌/三比/h²）通过 |
| XV-8 | 本机三档端到端；全量 pytest 无新增失败 |

---

## V3-8. 设计原则（承接 v2 §8，新增 9~12）

9. **赛制是递增综合度**：个体(①)⊂团队(②)⊂生态(③)；不做三套内核，是**同一内核的三种编排/评分视角**。
10. **评分只做减法不做加法**：任何新指标都是 survival_ticks 的派生；发现要引入主观分时，停手，改用生存差值表达。
11. **遗传学是解释框架不是新机制**：h²/近交/杂优/均值回归全部从**已有的 lineage+ranking 数据**事后计算，不为出图而新增生物学机制。
12. **谱系要冷静**：判词基于计算证据，陈述事实与预测（如回归半衰期），不褒不贬——体现「对智能体能力客观、冷静的判断」。

---

## V3-9. 学术引用（谱系遗传学化的依据）

- [QG-1] 数量遗传学与遗传力（narrow/broad-sense）综述：Introduction to Animal Science, Quantitative Genetics and Heritability, LibreTexts. https://bio.libretexts.org/Courses/Aurora_University/Introduction_to_Animal_Science/07%3A_Animal_Breeding_and_Genetics/7.07%3A_Quantitative_Genetics_and_Heritability
- [QG-2] Fisher 亲属相关性 = 遗传力 × 系谱系数 × 选配（同类选配放大相关）：The heritability and persistence of social class in England, PMC10629509. https://pmc.ncbi.nlm.nih.gov/articles/PMC10629509/
- [QG-3] 奠基者种群的窄/广义遗传力（Hutterites）：Broad and Narrow Heritabilities of Quantitative Traits in a Founder Population, PMC1226113. https://pmc.ncbi.nlm.nih.gov/articles/PMC1226113/
- [QG-4] 系谱数据用于合作与近交回避演化：Wild pedigrees: the way forward, PMC2386891. https://pmc.ncbi.nlm.nih.gov/articles/PMC2386891/
- [SM-1] 精英血统跨代持续与均值回归（约 10–15 代）：Gregory Clark, The Son Also Rises: Surnames and the History of Social Mobility, Princeton UP, 2014. https://en.wikipedia.org/wiki/The_Son_Also_Rises_(book)

> 说明：以上为设计参照的公开学术观点，均经改写以符合内容合规（未逐字摘录）。本系统对遗传学概念做**类比性借用**（Agent 的 skill/collab 基因非生物 DNA），用于把「自然选择性」可解释化，不主张生物学等价。

---

*配套执行清单见：[`物竞天择数字孪生演练todos.md`](物竞天择数字孪生演练todos.md)（v3，XV-0~XV-8）*
