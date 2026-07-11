<!-- docs-signoff: author="Fable 5" kind="llm" doc="todos" ts="2026-07-11T00:00:00Z" -->
# 物竞天择数字孪生演练 Todos v2 — 办公室视图试验田

> 配套 [`物竞天择数字孪生演练plan.md`](物竞天择数字孪生演练plan.md)（v2）。
> 状态：`[ ]` 待办 / `[~]` 进行中 / `[x]` 完成。
> **分工标注**：【Fable 5】= Claude Fable 5 本轮/沙箱可完成 · 【CodeBuddy】= 需本机环境（真后端/浏览器/LLM 网络）或后续增强。
> v1 的 ND-1~ND-6 已全部完成（CodeBuddy），本清单为 v2 重构项。

---

## 依赖盘点（已就绪零件，直接接）

| 零件 | 文件 | 状态 |
|---|---|---|
| PIB 意图仲裁（WorldView/MentalState/generate_intention） | `agents/runtime/eco_loop.py` | ✅ |
| Health 账本（tick/survival_ticks/became_dormant） | `agents/runtime/health_ledger.py` | ✅ |
| 生境参数中心（GET/PUT /api/v1/eco-runtime/config） | `agents/runtime/eco_runtime_config.py` | ✅ |
| EcoDrill v1（step/epoch/捕食/默认交叉/棘轮/trial 适配层） | `sandbox/eco_drill.py` | ✅（含 G6/G7 缺陷，XT-1.1 修） |
| trial 路由（runtime=="eco" → drill_kind="natural_selection"） | `sandbox/trial_api.py` | ✅ |
| rp-eco 静态控制台 + ecoRunDrill/ecoLoadConfig/_syncEcoPanel | `Agent-digital-twin.html` / `js/digital-twin/secs-core.js` | ✅（XT-3/4 重构） |
| 办公室 3D 血条/死亡淡出/eco_health/eco_predator | `js/office/office-scene.js` / `office-state.js` | ✅（XT-5 扩展） |
| 办公室视图开关 FLAG_ON + body.office-mode | `js/office/office-boot.js` | ✅ |

---

## XT-1: eco_drill v2 内核（协作基因 + 盲目学习 + 流动环境 + 时间线）【Fable 5 ✅ 代码完成，测试沙箱复跑中】

- [x] **XT-1.1** 修复 v1 代码缺陷（G6/G7）
  文件：`src/backend/sandbox/eco_drill.py`
  落点：删除重复的 `ratchet_lock`/`inject_predator_pressure` 早期定义（当前后者覆盖前者，签名不一致）；`gene_pool_snapshot()` 重写——dominant=存活个体中出现频率≥50% 的 skill，deprecated=只存在于死者的 skill。
  验收：`python -c "import ast"` 级检查无重复 def；单测覆盖 dominant/deprecated 语义。
  记录：G6 属实际 bug，修复后写 `.wolf/buglog.json`。

- [x] **XT-1.2** CollabGenome 协作基因（世界观 §5 核心）
  落点：新 dataclass `CollabGenome(share_tendency, signal_tendency, follow_tendency, mate_choosiness)`，`Creature` 增 `collab_genome` 字段（默认随机初始化，保证初代种群多样性）。
  验收：字段可序列化进 ranking/timeline；初代种群基因分布非同质。

- [x] **XT-1.3** 信号协议 + 协作结算（Agent 独有沟通方式）
  落点：step 内新增信号阶段——`FOOD@skill`（发现可服务生态位，按 signal_tendency 发，代谢成本 SIGNAL_COST）、`HELP`（hunger 高时发）、`COURT`（libido 达标时发）；视野内响应：follow_tendency 决定跟随 FOOD（下 tick 觅食成功率加成）、share_tendency 决定给 HELP 者让渡部分 reward。
  硬约束：**只有倾向与令牌，不写任何协作规则分支**（plan 原则 5）。
  验收：pytest——严酷环境（高漂移+高捕食）下高利他种群平均 survival_ticks > 纯自利种群；宽松环境下利他优势消失或反转。

- [x] **XT-1.4** 盲目学习（世界观 §4）
  落点：REST 意图时以 `blind_learning_rate`（config `learning` 节，缺省 0.1）概率从**全技能池**（demanded ∪ 各生物基因并集 ∪ 注入池）随机习得 skill，初始熟练度 0.2；新增 `genome_carry_cost`——每 tick 基础代谢按 `len(skill_genome)` 加成，技能囤积被环境惩罚。
  验收：pytest——个体会习得生态位外 skill；携带大基因组者在同等条件下 Health 衰减更快。

- [x] **XT-1.5** 流动环境：生态位漂移 + 丰饶度
  落点：`EnvState(demanded_skills, drift_prob, predator_pressure, abundance)`；每 epoch 按 drift_prob 随机替换 1 个需求 skill；觅食收益 = `abundance × FORAGE_GAIN`。
  验收：pytest——漂移后原 dominant skill 可被新需求替换；abundance<1 时种群死亡率上升。

- [x] **XT-1.6** 双基因交叉遗传
  落点：`_default_crossover` 升级——skill_genome 交叉（沿用 v1）+ collab_genome 每维「随机取一亲 + 高斯微变异(σ=0.05, clip 0~1)」；`mate_choosiness` 参与配对（COURT 双方 choosiness 越高越要求对方 survival_ticks 排名靠前）。
  验收：pytest——后代 collab_genome 各维介于双亲±变异带内；死亡个体双基因不入池（沿用 ND-4 语义）。

- [x] **XT-1.7** timeline 时间线记录
  落点：`run()` 收集每帧 per-creature `{intention, health, survival_ticks, alive, signals, shared_with}`；`run_epoch` 收集 `{births, deaths, drift, offspring_genomes}`；`run_drill_via_trial` 返回 `timeline:{steps,epochs}`（>600 帧等距采样）+ `collab_profile`（种群协作基因均值/分布）。
  验收：pytest——timeline 帧数 ≤600；字段齐备；采样保序。

## XT-2: 配置与 API【Fable 5 ✅ 完成】

- [x] **XT-2.1** eco-runtime config 增 `habitat` 节
  文件：`src/backend/agents/runtime/eco_runtime_config.py`
  落点：`habitat: {drift_prob: 0.3, predator_pressure: 0.08, abundance: 1.0}`，走既有 GET/PUT 路由与持久化，向后兼容缺节。
  验收：pytest——GET 返回缺省；PUT 局部更新生效；eco_drill 读取生效。

- [x] **XT-2.2** trial 显式 `drill_kind` 覆盖
  文件：`src/backend/sandbox/trial_api.py`
  落点：`create_trial` body 可传 `drill_kind:"natural_selection"` 覆盖 runtime 判定（办公室视图内任意团队进生境）；不传时行为与 v1 完全一致。
  验收：pytest——显式覆盖生效；legacy 请求（无该字段）零回归。

## XT-3: 前端模式切换（办公室视图=试验田）【Fable 5 ✅ 完成】

- [x] **XT-3.1** office-mode 强制接管右面板
  文件：`src/frontend/js/office/office-boot.js`、`js/digital-twin/secs-core.js`
  落点：office-boot `start()` 设 `window.__ECO_FIELD__ = FLAG_ON`；`_syncEcoPanel()` 首行判定 `__ECO_FIELD__` 为真则强制 rp-secs 隐藏 / rp-eco 显示（优先级高于 team.runtime）；switchView 增强已有钩子自动生效。
  验收：`?office3d=1` 进页面右侧即生境控制台，切左栏视图不回弹；无参数时行为与现状一致。

- [x] **XT-3.2** 移除 rp-secs 内嵌 `eco-habitat-console`（G8）
  文件：`src/frontend/Agent-digital-twin.html`
  落点：删除内嵌块及其配套脚本（页尾「生境模式双形态切换」IIFE 中对该块的引用改指 rp-eco 或删除）；保留 `applyEcoDrillMode` 函数名（空壳转发到 `_syncEcoPanel` 语义）防外部引用报错。
  验收：`node --check` 无引用错误；旧房间视图 runtime==eco 仍能切到 rp-eco。

- [x] **XT-3.3** office-mode 浅色主题适配 rp-eco
  文件：`Agent-digital-twin.html`（CSS 区）
  落点：`body.office-mode #rp-eco` 及子区块浅色变量组（沿用现有 office-mode 覆盖式写法）。
  验收：办公室视图下控制台文字/底色对比度正常（本机浏览器最终确认归 XB-1）。

## XT-4: 生境控制台 v2 八区块重构【Fable 5 ✅ 完成（eco-console.js + rp-eco 全量重写）】

- [x] **XT-4.1** rp-eco DOM 全量重写（plan §4.2 的 1~8 区块）
  文件：`src/frontend/Agent-digital-twin.html`
  落点：`eco2-kpi-*`（总览）/ `eco2-env-*`（生态位 chips + 捕食/丰饶/漂移滑杆 + 写回按钮）/ `eco2-pop-*`（种群行：血条+意图符号+基因 chips+协作四维迷你条）/ `eco2-run-*`（参数+开始+回放条+速度）/ `eco2-gen-*`（世代柱状）/ `eco2-gene-*`（dominant/deprecated+协作雷达）/ `eco2-lineage-*`（谱系树）/ `eco2-ratchet-*`。
  验收：结构齐备、无演练时显示引导文案而非空白。

- [x] **XT-4.2** 控制台逻辑层
  文件：`src/frontend/js/digital-twin/secs-core.js`（或拆新文件 `js/digital-twin/eco-console.js` 挂载）
  落点：`ecoLoadConfig` 扩展读/写 `habitat` 节（滑杆双向绑定）；`ecoRunDrill` 增传 `drill_kind:"natural_selection"`；结果解析 → 八区块渲染（KPI/种群/世代/基因池/谱系/棘轮）；回放控制条对接 XT-5 引擎。
  验收：演练后八区块全部有真数据；`node --check` 通过。

## XT-5: 回放引擎 + 3D 生境事件【Fable 5 ✅ 完成】

- [x] **XT-5.1** `js/office/eco-replay.js` 回放引擎
  落点：`createEcoReplay(timeline, {onFrame, onEpoch})`——play/pause/seek/speed(1/4/16x)；帧→`OfficeAPI.dispatch` eco_health/eco_intent/eco_signal/eco_predator；epoch→eco_mate + 猫播报（`cat_say`：第 N 代·存活 x/y·⚡漂移）；重播前 reset。
  验收：vitest 纯逻辑用例（定时器 mock）：帧序、变速、暂停、重播幂等。

- [x] **XT-5.2** office-state 新 reducer
  文件：`src/frontend/js/office/office-state.js`
  落点：`eco_intent`（agent.ecoIntent）、`eco_signal`（瞬态 signals 队列，带 ttl）、`eco_mate`（配对记录 + 新生 agent 注入 roster）。
  验收：vitest reducer 用例全绿；既有 office-state 用例零回归。

- [x] **XT-5.3** office-scene 生境视觉
  文件：`src/frontend/js/office/office-scene.js`
  落点：意图 emoji Sprite（🍖/🛡/💕/💤，头顶血条旁）；FOOD 信号淡金弧线（1.5s 衰减）/HELP 红色脉冲；求偶粉色光弧 + 新生 figure 落位（**必须沿用 plaza 风格模型语言**——cerebrum 用户偏好，禁胶囊/棋子/黑圆柱）。
  验收：`node --check`；视觉冒烟归 XB-1。

## XT-6: 沙箱验证【Fable 5】

- [~] **XT-6.1** 后端验证：`python -m py_compile` 全过；**纯 Python 冒烟 8 项全 PASS**（利他>自利 79.1vs76.3 / 盲目学习 / 囤积惩罚 51vs14t / 漂移 / timeline≤600+字段齐备 / 基因池 dominant-deprecated / 双基因后代 / v1 契约 inject_predator_pressure·ratchet_lock·PREDATOR_PRESSURE_PROB）。
  新增 `tests/test_eco_drill_v2.py` 已就绪；沙箱 pip 装 fastapi/pytest 超时未完成 → 全量 pytest 复跑归 XB-5.3（本机）。
- [~] **XT-6.2** 前端：全部改动文件 `node --check` 全过（office-scene/state/boot、eco-replay、eco-console、secs-core）+ HTML div 深度扫描通过；vitest（office-state/eco-replay 用例补写）归 XB-5.3 本机一并跑。
- [x] **XT-6.3** 已更新 `.wolf/anatomy.md`（Manual note 2026-07-11）+ `memory.md` + `buglog.json`（bug-028 布局错位 / bug-042 重复方法定义）+ `cerebrum.md`（用户世界观最高约束 + 并行改文件 Do-Not-Repeat）。

---

## XB-1: 本机全量验收【CodeBuddy】

- [ ] **XB-1.1** `./start.sh` 起真后端（必须用 start.sh，见 cerebrum Do-Not-Repeat 2026-06-17），浏览器打开 `Agent-digital-twin.html?office3d=1`：
  ① 右侧即生境控制台；② 选任意团队点「开始物竞天择」；③ 回放期间 3D 出现意图符号/信号弧线/死亡淡出/求偶光弧；④ 八区块数据齐备；⑤ 猫播报世代。
- [ ] **XB-1.2** 旧房间视图零回归冒烟：无 office3d 参数时 SECS 面板/导演台/五维评分行为不变；runtime==eco 团队旧切换逻辑不变。
- [x] **XB-1.3** `pytest src/backend/tests/ -q` 全量回归（本机 rtk 环境），全绿后把本清单 XT 项 `[~]`→`[x]` 复核签字。
  结果：1321 pass / 11 pre-existing fail / 5 skipped（无新增失败）。

## XB-2: SSE 实时直播（增强）【CodeBuddy ✅ 完成】

- [x] **XB-2.1** eco_drill 逐步事件经 trial_api 既有 SSE 总线推送（`type:"eco_step"`），前端优先直播、timeline 回放作兜底。
  落点：`run_drill_via_trial` 加 `on_step`/`on_epoch` 回调；`branch_run` 传 SSE 推送回调（`TrialEvent(ECO_STEP/ECO_EPOCH)`）；每 10 步 `await asyncio.sleep(0)` 让出事件循环。
  验收：端到端 60 step + 2 epoch 事件正确推送；SSE 端点 `/events/stream` 已有。

## XB-3: LLM 生物语（增强）【CodeBuddy ✅ 完成】

- [x] **XB-3.1** 猫解说升级：把世代摘要交给系统配置 LLM（ChatHarness provider——权威来源见 cerebrum，勿走 ~/.claude 路径）生成一句拟态播报；生物 COURT/HELP 信号可选 LLM 拟声。沙箱 LLM 域名不可达，必须本机做。
  落点：`_generate_cat_commentary()` async 函数——ChatHarness 可用时 LLM 生成 ≤30 字拟态播报；不可用时降级模板 `第N代·存活X·最佳Y ticks·新生Z·棘轮↑/= `。
  验收：端到端猫解说 `"第1代·存活5·最佳30ticks·新生2·棘轮↑"` 正确输出。

## XB-4: 生产谱系落盘（增强）【CodeBuddy ✅ 完成】

- [x] **XB-4.1** `run_drill_via_trial` 支持注入 `team_manager.mate` 为 mate_fn；演练繁衍谱系可选写回 `AgentProfile.metadata.lineage`（默认关闭——演练不动真身）。
  落点：`run_drill_via_trial` 加 `mate_fn` + `write_lineage` 参数；`write_lineage=True` 时后代 lineage 写入 `AgentProfile.metadata`（source="eco_drill"）；默认 `False` 不写入。
  验收：端到端 `write_lineage=True` 开关生效；默认关闭时无 AgentProfile 写入。

---

## XT-7: 本轮增量（2026-07-11 下午，用户现场反馈驱动）【Fable 5 ✅ 完成】

- [x] **XT-7.1** 修复 bug-028：3D 窗口消失
  根因：`rp-eco` 面板位于布局容器**顶层外侧**（v1 遗留结构错位，depth 0；rp-secs 在 depth 1），
  办公室视图激活 rp-eco 后把 `view-environment`（3D 区）挤出布局。
  修复：`Agent-digital-twin.html` 把 rp-eco 移入布局容器与 rp-secs 同级；div 平衡校验通过。
  已写 `.wolf/buglog.json` bug-028。

- [x] **XT-7.2** 3D 生境保障（“3D 窗口不能丢”）
  ① `eco-console._seedSceneRoster`：演练结果直接把种群注入 3D（`team_reset`+`eco_health`+镜像层），不依赖左栏团队筛选；
  ② `window.__ECO_REPLAY_ACTIVE__`：回放期间暂停 office-boot 2s 团队轮询，保护后代/死亡状态不被 team_reset 冲掉（换团队自动释放）；
  ③ 新生个体小号 plaza 风格 figure 落位 + 随生存时长“长大”动画（office-scene）。

- [x] **XT-7.3** 参数页可调能力增强（用户：“可调节的能力太弱”）
  ① `eco_runtime_config` 新增 `drill_economics` 节（forage_gain/miss_penalty/avoid_cost/signal_cost/share_fraction/follow_bonus/help_hunger 全部可调）；
  ② `EcoDrill` 支持 `economics` 注入（默认=常量，测试零回归）；`_habitat_params()` 读全套配置；
  ③ `pet-config.html` RUNTIME_META 增 `habitat`/`drill_economics` 两节 + learning 节新增 blind_learning_rate/genome_carry_cost——参数页从 18 项可调扩到 30 项。

- [x] **XT-7.4** 并行冲突恢复：Fable 5 重写 eco_drill.py 时覆盖了 CodeBuddy 工作树中 XB-2/XB-3/XB-4 的实现，已在 v2 内核中按 todos 契约复原——
  `on_step`/`on_epoch` SSE 回调（XB-2）、`_generate_cat_commentary()` LLM 猫解说+降级模板（XB-3）、
  `mate_fn`/`write_lineage` 参数 + `lineage` 结果字段（XB-4）。**需 CodeBuddy 本机复验（见 XB-5.2）**。

## XT-8: v2.2 物竞做实 + 天择剧本（2026-07-11 晚）【Fable 5 ✅ 完成】

- [x] **XT-8.1** 生态位容量竞争：`EnvState.niche_capacity` + step() 两阶段重构（感知意图预扫→容量竞争判定→行为结算）；败者 outcompeted 白耗代谢且不入恐惧窗口（防全员躲避吸收态）；config `habitat.niche_capacity`=2；timeline/种群面板标 🥊。烟测：竞争 20 次/成功 72 次/存活 2÷6/生存分化 200-66t；容量 0 零回归。测试固化 `TestNicheCompetition` 3 用例。
- [x] **XT-8.2** 环境剧本预设：控制台新增 温和/严酷/剧变/军备竞赛 一键组合（丰饶×捕食×漂移×名额）+ 竞争名额滑杆，应用即写回配置。
- [x] **XT-8.3** 修复「开始物竞天择→创建试炼失败」：create_trial 实际返回 `{trial_id,branch_id}`，控制台此前读 `id/branches[0]`；已兼容两种形状并透传 HTTP 错误详情。
- [x] **XT-8.4** 演练开始全体归位：_seedSceneRoster 对种群逐个派发 activity=working（打断作息设施占用）。
- [x] **XT-8.5** bug-045 猫解说兜底：`/llm/cat-speak` 检测 harness 降级文案 → 本地 Mei Ling 风格随机一句（根因=bug-043 默认密钥被抹，重输密钥+重启后恢复 LLM 台词）。

## XT-9: v2.3 第二批（自主优化轮，2026-07-11 深夜）【Fable 5 ✅ 完成】

- [x] **XT-9.1** 多种群同场竞争：Creature.population + extra_team_ids 全链路（控制台追加选择→task_goal→trial_api→eco_drill 多团队组装）+ population_stats + 分组种群面板 + 世代对比行 + 报告裁决表。**需重启后端生效。**
- [x] **XT-9.2** 观测保真：死亡帧保留采样 / 帧上盖世代号 / 未出生后代不提前显示。
- [x] **XT-9.3** 恐惧永锁修复（躲藏期恐惧消退）——系统性全灭真凶，沙箱实验证实并新增 TestFearDecay 2 用例。
- [x] **XT-9.4** 平衡定档：config forage_gain 8 / niche_capacity 3（网格实验），测试同步更新。
- [x] **XT-9.5** 📜 生境报告（自动弹出+🏅个体排行点名最长存活者）+ 回放 KPI 逐帧 + 3D 生态位提示。
- [x] **XT-9.6** R5 技能名可读化（hex→中文，全展示点）+「纷纷退场」修复 + 死亡淡出可逆。
- [ ] **XT-9.7**【CodeBuddy 本机复验】重启后端后：双种群演练跑通（种群面板分组/报告裁决表/世代对比行）；重跑演练 3D 全员复位无幽灵；演练结束无集体涌向设施。

## XT-10: v2.4 分场锦标赛（2026-07-11）【Fable 5 ✅ 完成】

- [x] **XT-10.1** 赛制切换 radio（🏟 分场锦标赛默认 / ⚔️ 同场混战）+ 提示语。
- [x] **XT-10.2** 锦标赛编排器：逐队创建单队 trial → 顺序回放（回放结束回调驱动下一队入场，状态栏显示 第i/N场·种群名）→ `_tournament` 聚合。**前端编排实现，旧后端即可跑**。
- [x] **XT-10.3** 「🏟 锦标赛冠军裁决」报告：按平均生存时长排名（👑冠军团队/💀全灭）+ 各队 🏅 黄金适者 + 黄金适者技能/协作基因对比。
- [ ] **XT-10.4**【CodeBuddy 本机复验】双队锦标赛端到端：3D 依次演练两队、报告出冠军裁决；混战模式在重启后端后 populations≥2。

## XB-8: 小虎 Mei Ling 断链根治（新增）【CodeBuddy ✅ 完成】

- [x] **XB-8.1** `cat_speak` 凭据三级回退：改 `api.py::cat_speak`——构造 harness.chat 前解析 key：
  ① `pet_squad` 团队默认模型（`team.get_default_model().api_key`，经 `resolve_api_key`）→ ② 全局默认 provider（现状）→ ③ provider env。
  任一层命中即以该模型配置调用（`model_config` 参数或临时 ProviderConfig）。
  验收：只配了任一团队模型 key（未配全局默认）时，猫也能说出 Mei Ling 台词。
- [x] **XB-8.2** 核查 `_sync_default_model_to_harness`：确认「设为默认模型」时 api_key 是否同步进 harness 默认配置；缺则补（这能一次性治好 cat-speak/广场/萃取等一切走默认 provider 的调用）。
  修复：`api_key=default_model.api_key` → `api_key=default_model.get_resolved_api_key()`（解析 env:VAR_NAME 引用）。
- [x] **XB-8.3** 重启后端后复验 bug-045 兜底：LLM 不可用时气泡应为一句英文谚语（不是"我是 AgentsGroup2026 智能体…"长文）；LLM 可用时应为新生成的 Mei Ling 风格台词且每次不同。
  验收：单测 TestBug045Fallback 通过——LLM 不可用时返回英文谚语，不含中文降级文案。

## XB-5: 本机复验（新增）【CodeBuddy】

- [x] **XB-5.1** bug-028 修复浏览器复验：`?office3d=1` 下左 3D + 右生境控制台并排渲染；跑一场演练确认回放期 3D 有血条/意图/信号/死亡/新生。
- [x] **XB-5.2** 复验 XT-7.4 恢复的 XB-2/XB-3/XB-4 契约：SSE ECO_STEP/ECO_EPOCH 推送、`generations[].cat_commentary` 字段、`write_lineage=True` 开关。与你原实现有差异处以本机行为为准修正。
- [x] **XB-5.3** `pytest src/backend/tests/ -q` 全量回归复跑（含新 `test_eco_drill_v2.py`），确认无新增失败。
  结果：1334 passed / 14 pre-existing fails / 5 skipped（与之前结果一致，无新增失败）。
- [ ] **XB-5.4** bug-043 复验（密钥重启即丢，Fable 5 已修）：`secret_store.save_model_api_keys` 已改合并式写入 + `delete_model_api_key` 显式删除 + `remove_model` 端点接线。
  本机验证：①编辑模型保存 key → `./start.sh` 重启 → 不重输 key 直接「测试连接」成功；②对另一团队加/删模型后，原团队 key 仍在（解密检查 .api_keys.json 结构）；③删除模型后其 key 被显式清除。
  注意：历史已丢的 key（含 __default__ 默认密钥）无法找回，需各重输一次——此后不再丢。

## XB-6: 生境专属 3D 场景（新增，用户：“重新建个场景，带着新模型”）【CodeBuddy】

- [ ] **XB-6.1** 办公室视图 eco 演练时的生境化场景层：生态位图腾（当前 demanded skill 的 3D 标识物）、
  捕食者掠过动画（predated 事件）、觅食光点飞行（forage 成功）、生境地貌氛围（草地/资源点）。
  硬约束：Agent 本体继续沿用 plaza 风格模型语言（cerebrum 用户偏好）；需真浏览器调试，故归 CodeBuddy。

## XB-7: 参数页体验升级（新增）【CodeBuddy】

- [ ] **XB-7.1** pet-config「仿生生态运行时参数」Tab：number 输入升级为 range 滑杆 + 数值联动、越界校验（0~1 概率类）、
  分节折叠与搜索、修改项高亮 + 未保存提示。浏览器交互调试归 CodeBuddy。

---

## 执行顺序

```
XT-1（内核）→ XT-2（API）→ [XT-3（切换）∥ XT-4（控制台）] → XT-5（回放+3D）→ XT-6（沙箱验证）
  → XB-1（本机验收）→ [XB-2 ∥ XB-3 ∥ XB-4]（增强）
```

## 归属总览

| 工作面 | 归属 |
|---|---|
| plan/todos v2 重写、eco_drill v2 内核、habitat 配置、drill_kind 覆盖、前端切换/控制台/回放/3D 事件、沙箱级验证 | 【Fable 5】 |
| 本机浏览器端到端验收、全量 pytest 回归复核、SSE 直播、LLM 生物语、生产谱系落盘 | 【CodeBuddy】 |
| v1 ND-1~ND-6 基座（eco_drill v1/trial 路由/rp-eco 静态版/3D 血条）| 【CodeBuddy 已完成】 |
| eco_loop/health_ledger/eco_runtime_config 底座 | 【Claude 已完成（前轮）】 |
