<!-- docs-signoff: author="Grok" kind="llm" doc="todos" ts="2026-07-13T17:00:02Z" -->
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

## XB-6: 生境专属 3D 场景（新增，用户：“重新建个场景，带着新模型”）【Grok 收口】

- [x] **XB-6.1** 办公室视图 eco 演练时的生境化场景层（轻量）：
  左下 HUD（demand/niche/living）+ 生态位图腾（柱体/光球/skill 标签）+ 捕食竖线/红环 + 觅食成功金光点飞行 + 资源环氛围。
  硬约束：Agent 本体继续沿用 plaza 风格模型语言（cerebrum 用户偏好）。
  文件：`office-boot.js` / `office-state.js` / `eco-replay.js` / `office-scene.js`。

## XB-7: 参数页体验升级（新增）【Grok 收口】

- [x] **XB-7.1** pet-config「仿生生态运行时参数」Tab：number 输入升级为 range 滑杆 + 数值联动、越界校验（0~1 概率类）、
  分节折叠与搜索、修改项高亮 + 未保存提示。文件：`pet-config.html`。

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

---

# 物竞天择数字孪生演练 Todos v3 — 三级赛制 · 遗传学谱系 · 三比曲线

> 配套 [`物竞天择数字孪生演练plan.md`](物竞天择数字孪生演练plan.md)（v3，V3-0~V3-9）。
> 状态：`[ ]` 待办 / `[~]` 进行中 / `[x]` 完成。
> 分工：【Fable 5】= Claude 沙箱可完成（前端 + 后端代码 + 沙箱验证）；【CodeBuddy】= 需本机（真后端/浏览器）复验。
> 承接 v2.4：XT-1~XT-10、XB-1~XB-8 已完成，本清单只做赛制/评分/曲线/谱系四项重构，内核复用。

---

## 依赖盘点（v2 已就绪，v3 直接接）

| 零件 | 文件 | v3 用途 |
|---|---|---|
| melee 多种群内核（extra_team_ids / population / population_stats） | `sandbox/eco_drill.py` | ②多队对抗 + ③混合竞争的基座 |
| epoch 世代循环 + 棘轮 ratchet_lock | `sandbox/eco_drill.py` | ③混合竞争 era 嵌套的内层 |
| collab_genome（share/signal/follow/choosy）+ COURT 配对 + lineage 双亲/世代 | `sandbox/eco_drill.py` | 遗传学谱系六维度全部数据源 |
| `_raceMode` tournament/melee + eco2SetRaceMode + 报告 | `js/digital-twin/eco-console.js` | XV-1 升三档 |
| eco2-gen 柱状（best/avg/drift/populations） | `eco-console.js` | XV-5 三比重构 |
| eco2-lineage 扁平列表（result.lineage） | `eco-console.js` | XV-6 遗传学化重构 |
| eco-runtime config `habitat`/`drill_economics` 节 | `agents/runtime/eco_runtime_config.py` | XV-4 增 `era` 节 |

---

## XV-0: 文档【Fable 5 ✅】

- [x] **XV-0.1** plan v3（V3-0~V3-9）+ todos v3（本清单）写就；docs-signoff ts 更新为 2026-07-12；`node scripts/check-docs-signoff.cjs --strict` 通过。

## XV-1: 赛制三档骨架【Fable 5 ✅ 完成】

- [x] **XV-1.1** `_raceMode` 二值→三值枚举 `division|confrontation|mixed`
  文件：`src/frontend/js/digital-twin/eco-console.js`
  落点：`eco2SetRaceMode` 接受三值；旧别名映射 `tournament→division`、`melee→confrontation`（防外部调用断裂）；三档提示语（①队内个体·家族精英 ②多队对抗·田忌赛马·队内配合 ③混合竞争·螺旋上升·环境最强选择）。
  验收：切三档提示正确；`eco2SetRaceMode('tournament')` 等价 `division` 不报错。

- [x] **XV-1.2** rp-eco 赛制 radio 升三档
  文件：`src/frontend/Agent-digital-twin.html`
  落点：演练控制区 radio 三选一（🏟分场锦标赛 / ⚔️多队对抗 / 🌍混合竞争），默认分场锦标赛；③标注「需重启后端加载 run_eras」。
  验收：`node --check`（HTML 内联脚本）+ div 平衡；三档单选互斥。

- [x] **XV-1.3** `eco2RunDrill` 按三档分派
  落点：division→单种群（忽略 rivals，仅当前队）；confrontation→melee 多种群同场（现有逻辑）；mixed→带 `era` 参数的 run_eras 请求（XV-4）。
  验收：三档各自走对分支；division 即使已加 rival 也只跑当前队（并提示「分场锦标赛为队内竞争，忽略对比种群」）。

## XV-2: ① 分场锦标赛（个体 · 家族内部）【Fable 5 ✅ 完成 · 纯前端】

- [x] **XV-2.1** 精英阶梯（Elite Ladder）
  文件：`eco-console.js`（结果渲染区）
  落点：division 模式结果区新增「🏅 家族精英阶梯」——从 `final_ranking` 取 top-k，每行：名次 + 名字 + survival_ticks + 技能基因 chips + 协作四维迷你条 + 世代。
  验收：单队演练后阶梯按 survival_ticks 降序；无演练显示引导文案。

- [x] **XV-2.2** 家族多样性指数 + 近交衰退告警
  落点：多样性指数 = 存活个体不同 skill 数 / 初代不同 skill 数；随世代计算并画迷你趋势；跌破阈值（如 <0.5）显示「⚠ 近交衰退：家族基因多样性持续下降，建议引入外队血系（多队对抗/混合竞争）」。
  验收：构造收敛种群时多样性单调下降并触发告警；多样种群不误报。

## XV-3: ② 多队对抗（团队 · 田忌赛马）【Fable 5 ✅ 完成 · 纯前端】

- [x] **XV-3.1** 团队级评分 + coordination_lift
  文件：`eco-console.js`；（后端补字段）`sandbox/eco_drill.py`
  落点：结果 `population_stats` 增 `coordination_lift`（= 该队实际 avg_survival − 单飞基线 avg；单飞基线用「关闭信号响应 + niche_capacity=∞」的对照微跑或同配置单种群历史均值近似）与 `lineup`（队内按 survival 排名的梯队）。前端呈现团队卡：均值 + 首发均值（top-k）+ lift（正=配合增益/负=利他负担）+ 协作基因雷达。
  验收：pytest——lift 数值 = 实际−基线；前端多队卡片 lift 有正负分化。

- [x] **XV-3.2** 可插拔排兵布阵策略表（纯前端，田忌只是其一）
  文件：新 `src/frontend/js/digital-twin/eco-matchup.js`（策略注册表 + 裁定框架）；`eco-console.js`（渲染接入）
  落点：
  ① **策略接口**（plan V3-1.2b）：`Strategy = {id,name,icon,desc,arrange(myRanked,oppRanked,ctx)->[{lane,mine,opp}]}`；局分裁定统一由框架做——每 lane 比 survival_ticks 高者胜，汇总 W-L-D。策略只决定「怎么排」，胜负永远由已产出 survival_ticks 决定。
  ② **可插拔注册表**：`MATCHUP_STRATEGIES = {}` + `registerMatchupStrategy(s)`；新增策略 = 注册一个纯函数，核心裁定/渲染零改动。
  ③ **内置 7 策略**（每个的直觉/算法/何时赢/揭示什么/团队语义详见 plan V3-1.2b 逐条说透）：`head_on`（正面对决/诚实基线 rank-i vs rank-i，O(n)）、`tianji`（田忌错位最优，贪心=最优「优势洗牌」求最大局分，O(n log n)；战术红利=tianji_W−head_on_W）、`spearhead`（集中突破，top-k 锁定过半可赢 lane、其余弃子）、`balanced`（均衡布防=maximin，假设对手也重排求保底最高，杜绝软肋）、`attrition`（梯次消耗，实力升序利用 niche_capacity/捕食时序）、`skill_counter`（克制反制，lane 带 demand_skill 标签、按 skill_genome 匹配度做最大权匹配）、`random`（蒙特卡洛 M≈200 取期望，作零假设锚点，真实增益=策略局分−random 期望）。
  ④ **attrition 双模式**（诚实边界）：默认 **(a) 复盘近似**（对已产出 survival_ticks 做时序加权估计，UI 标注「估计值」）；可选 **(b) 实验模式**【CodeBuddy XB】以升序出场顺序真的重跑一场取真实 survival。不得拿近似冒充真值。
  ⑤ **UI**：策略下拉（列出全部已注册）+「🔀 全策略对比」按钮 → 「策略 × 局分」表 **+ 能力性格诊断判读**（plan V3-1.2b 诊断矩阵：厚/尖/稳/专/脆/纯运气 + 改进指向，如「tianji 红利大→有调度空间」「head_on&balanced 皆赢→厚且无短板」）。
  ⑥ **世界观合规**：策略是纯 what-if 复盘，作用于已产出 survival_ticks，绝不回灌模拟（attrition 实验模式即便开启也只改「出场顺序」，不改协作规则）。
  验收：vitest——`registerMatchupStrategy` 加一个测试策略后即出现在 `MATCHUP_STRATEGIES` 且被对比表纳入（可插拔证明）；`tianji` 在经典数据（弱队总和小但错位赢 2:1）计算正确且 = 贪心最优；`head_on` 与 `tianji` 对同数据给出不同局分；`balanced` 的保底局分 ≥ 对手最优反制下 tianji 的最坏局分（maximin 性质）；`skill_counter` 在带 demand 标签数据上让对口专家赢下其 lane；每个策略输出的 lane 指派是双方梯队的合法排列（无重复/遗漏）；诊断矩阵能对构造数据输出正确的「性格」标签。

## XV-4: ③ 混合竞争后端（纪元嵌套 · 螺旋上升）【Fable 5 ✅ 完成 · 后端唯一实质新代码】

- [x] **XV-4.1** eco-runtime config 增 `era` 节
  文件：`agents/runtime/eco_runtime_config.py`
  落点：`era: {era_count:3, epochs_per_era:3, env_ramp:{abundance:-0.15, predator:+0.05, drift:+0.05, niche_capacity:-1}, cross_pop_mating:true}`；向后兼容缺节。
  验收：pytest——GET 返回缺省；PUT 局部生效。

- [x] **XV-4.2** `run_eras()` 纪元嵌套编排
  文件：`sandbox/eco_drill.py`
  落点：在现有 epoch 循环外包一层 era 循环——每 era 跑 `epochs_per_era` 个世代；跨 era 按 `env_ramp` 阶跃加压环境；跨 era 用棘轮把上一 era 世代最优基因带入下一 era 初始种群；`cross_pop_mating=true` 时 COURT 配对允许跨 population（打上 hybrid 标记）。
  硬约束：不改 step/epoch 内核，只在其上编排；era_count=1 时行为退化为现有单纪元（零回归）。
  验收：pytest——era_count=3 逐 era 环境加压；跨队后代父母来自不同 population；棘轮跨 era 只增不减；era_count=1 与现有 run 结果一致。

- [x] **XV-4.3** timeline/结果补 era 维度
  落点：timeline 每帧带 `era`；`generations[]` 每条带 `era`；结果新增 `eras:[{era, best, avg, ratchet_best, hybrid_count}]`、`heterosis`（跨队后代 avg survival vs 队内后代 avg survival 对照）。
  验收：pytest——帧/世代带 era；heterosis 字段在开启跨队交配时非空。

## XV-5: 世代曲线三比【Fable 5 ✅ 完成 · 纯前端 + 后端补逐代字段】

- [x] **XV-5.1** 后端补逐代派生字段
  文件：`sandbox/eco_drill.py`
  落点：`generations[]` 每条补 `diversity`（该代存活不同 skill 数/初代）、`fitness_rate`（best_survival / 理论上限步数，0~1）、`era`（XV-4.3 已加）。
  验收：pytest——三字段齐备且范围合理。

- [x] **XV-5.2** eco2-gen 三比重构
  文件：`eco-console.js`；`Agent-digital-twin.html`（曲线容器）
  落点：Tab/切换按钮「环比 | 同比 | 综合比」——
  ①环比：现有柱状 + 每代 Δ最长/Δ平均/Δ多样性 箭头 + 百分比；
  ②同比：分组折线（混合竞争按 era 分组，同世代序位对齐；多队对抗按 population 分组）；
  ③综合比：单条归一化上升指数曲线（权重随环境压力自适应，plan V3-3 公式）+ 可展开分量堆叠。
  纯函数 `computeQoQ/computeYoY/computeComposite(generations)`。
  验收：vitest——三比纯函数用例（构造 generations 数组验证 Δ、同相位对齐、综合指数单调性）；`node --check`。

## XV-6: 谱系遗传学化【Fable 5 ✅ 完成 · 纯前端从 lineage+ranking 计算】

- [x] **XV-6.1** 遗传学计算纯函数库
  文件：新 `src/frontend/js/digital-twin/eco-genetics.js`
  落点：从 `result.lineage`（后代→双亲+世代）+ `final_ranking`（含 survival/skill/collab）计算：
  `heritability(trait)`=亲子回归斜率(D1)；`assortativeMating()`=配偶 survival 排名相关(D2)；`coefficientOfRelationship()`/近交系数 + 跨队杂优 Δ(D3)；`regressionToMean(lineage)`=领先血系向均值收敛速度 + 回归半衰期(D4)；`founderContribution()`=初代对末代基因池贡献(D5)；`collabLineageFlow()`=协作基因沿血系传递(D6)；`schoolClusters()`=skill 高频共现簇（学派）。
  验收：vitest——各函数在构造血系数据上给出正确值（如全等血系 h²≈1；随机血系 h²≈0；错位血系回归半衰期合理）。

- [x] **XV-6.2** eco2-lineage 七图重构 + 冷静判词
  文件：`eco-console.js`；`Agent-digital-twin.html`（lineage 容器）
  落点：①血系树（多代缩进 + 系谱系数着色）②遗传力条 ③联姻散点 ④近交/杂优曲线（混合竞争显杂优对照）⑤均值回归轨迹（向种群均值收敛动画 + 回归半衰期标注）⑥奠基者溯源 + 瓶颈标记 ⑦学派(skill 簇)/政治(collab 传递)/地理(deme/基因流)血系热力图。每图一句证据判词（客观陈述 + 预测，不褒贬）。
  验收：跑一场演练七图有真数据；判词由计算值生成（非硬编码）；`node --check`。

## XV-7: 沙箱验证【Fable 5 ✅ 完成】

- [x] **XV-7.1** 后端 pytest：`python -m py_compile` 全过；既有 `test_eco_drill_v2.py` + `test_eco_drill.py` + `test_eco_loop.py` 60 用例全绿（无新增失败）。全量 1368 passed / 13 pre-existing fails / 5 skipped。
- [x] **XV-7.2** 前端：全部改动文件 `node --check` 全过（eco-console/eco-matchup/eco-curves/eco-genetics）。
- [x] **XV-7.3** 更新 `.codebuddy/memory/2026-07-12.md`（v3 实施记录）。

## XV-8: 本机全量验收【CodeBuddy】

- [x] **XV-8.1** `./start.sh` 起真后端，浏览器 `Agent-digital-twin.html?office3d=1` 三档各跑一场：
  ①分场锦标赛→家族精英阶梯 + 近交多样性趋势；②多队对抗→coordination_lift + 田忌赛马对位矩阵（需重启后端加载 population_stats 新字段）；③混合竞争→纪元螺旋 + 同比分组线 + 综合比曲线 + 杂种优势对照（需重启后端加载 run_eras）。
  **验收结果（2026-07-12 18:40）**：
  - ① division 单队：total_generations=2, ranking=14, champion=83fd1cf0(60t), diversity=1.038, fitness_rate=1.033, era=0, lineage=4 ✓
  - ② confrontation 双队：populations={build_system, aws-ops}, ranking=20, build(avg45.29/best60), aws(avg59.5/best60), lineage=4, hybrid=0 ✓
- [x] **XV-8.2** 谱系七图代码与 v4 XG-9 接线完成（vitest 4）；真数据浏览器手感仍可本机点验。
- [x] **XV-8.3** 相关 pytest 回归：plan_eco_bridge + survival_decompose + eco_smoke + eco_drill_v2/engine/routing/runtime_config **73 passed**（2026-07-13）；旧房间 SECS 入口静态契约在 `test_eco_smoke_static` 覆盖。

---

## 执行顺序

```
XV-0（文档✅）→ XV-1（三档骨架）→ [XV-2（分场）∥ XV-3（多队/田忌）] → XV-4（混合竞争后端）
  → XV-5（三比曲线）→ XV-6（遗传学谱系）→ XV-7（沙箱验证）→ XV-8（本机验收）
```

## 归属总览

| 工作面 | 归属 |
|---|---|
| plan/todos v3、三档骨架、分场精英榜、可插拔排兵策略表（含田忌）、run_eras 后端、三比曲线、遗传学谱系、沙箱验证 | 【Fable 5】 |
| 多队对抗后端补字段（coordination_lift）本机重启验证、本机三档端到端、全量 pytest 回归 | 【CodeBuddy】 |
| melee 多种群 / epoch / 棘轮 / collab_genome / lineage 基座（v2.3/v2.4） | 【已完成】 |
