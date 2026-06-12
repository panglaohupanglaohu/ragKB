# AgentsGroup2026 全局优化 TODOS（v1.0）

> 日期：2026-06-12 · 配套：`docs/全局优化计划.md`
> 状态标记：`[ ]` 未开始 / `[~]` 主通路完成但有缺陷 / `[x]` 通过验收
> 验收规则沿用四门：①函数存在 ②接口 2xx ③状态一致 ④手工 UI（后端纯逻辑以 pytest 替代④）

---

## P0 — 三个全局收口件（本轮实施）

### G-2 技能三类分类器（特有/通用/储备）

- [x] **G2-1** 新文件 `src/backend/agents/skill_classifier.py`：　⟦skill_classifier.py: classify + classify_with_history（毕业2连击/降级宽限），test_skill_classifier 全绿⟧
  - `Classification` 枚举：`EXCLUSIVE`(特有) / `GENERAL`(通用) / `RESERVE`(储备)
  - `classify(skill_dict, usage_evidence, trial_evidence, now) -> {classification, reasons, score_card}`
  - 判定规则（计划 3.1 表）：特有 = 单团队占比≥0.8 且 effectiveness≥0.6 且演练达标；通用 = ≥2 团队采用或 ≥2 场景类目达标且过门禁；储备 = 默认/低效(<0.4)/degraded/90 天未用
  - 防抖：`classify_with_history(prev, ...)` — 毕业（reserve→general/exclusive）需连续 2 周期达标，降级有 1 周期宽限
- [x] **G2-2** `ClassificationStore`：持久化 `storage/skill_classification/{team_id}.json`（含历史周期记录），原子写，对齐既有 store 模式　⟦ClassificationStore 原子写+重载测试通过⟧
- [x] **G2-3** `reclassify_team(team_id)` 批量重算：输入 skill_library.browse + proficiency_store + trial 证据；输出变更列表（含毕业/降级事件），降级技能自动产生"建议进化"标记　⟦reclassify_team 批量重算+毕业/降级事件+降级建议进化，测试通过⟧
- [x] **G2-4** API `src/backend/agents/skill_classifier_routes.py`，prefix `/api/v1/skill-classification`：　⟦skill_classifier_routes.py 三端点 + main.py 5.8 注册 + 豁免前缀；TestClient smoke 覆盖三端点 2xx⟧
  - `GET /teams/{team_id}` 当前分类视图（三池列表）
  - `POST /teams/{team_id}/reclassify` 触发重算，返回变更
  - `GET /teams/{team_id}/history?skill_id=` 分类变迁史
  - main.py 注册 + 豁免前缀
- [x] **G2-5** pytest `tests/test_skill_classifier.py`：三类判定各 ≥2 用例、防抖（首次达标不毕业/连续两次毕业）、降级宽限、批量重算变更事件　⟦12 用例全绿（三类判定/防抖/宽限/批量重算/持久化重载）⟧

### G-4 全局正向棘轮账本

- [x] **G4-1** 新文件 `src/backend/agents/ratchet_ledger.py`：　⟦ratchet_ledger.py: advance/get/history/list/force_reset，原子写+.bak 自愈⟧
  - `RatchetLedger.advance(metric_key, value, evidence={}, min_delta=0.0, tolerance=0.0) -> {advanced, generation, current, reason}`
  - 退步拒绝（value < current - tolerance）；持平按 min_delta 判定；推进则 generation+1 记账
  - `get(metric_key)` / `history(metric_key)` / `list_metrics(prefix="")` / `force_reset(metric_key, reason)`（留痕）
  - 持久化 `storage/ratchet/ledger.json`（原子写 + .bak 自愈，对齐 trial_store）
- [x] **G4-2** 接线一：trial evaluate 完成 → `advance(f"scenario_best:{scenario_id}:{team_id}", total_score)`，结果写入 evaluation 响应 `ratchet` 字段（advanced/generation/reason）　⟦trial_api.evaluate 已接线；tests/test_v4_apis.py 断言 evaluation.ratchet 字段通过⟧
- [x] **G4-3** 接线二：evolution_bridge.apply_winner → 推进 `skill_effectiveness:{skill_name}:{team_id}`（以 winner.fitness 为值）；**推进失败时阻断写回**并把 reason 记入 run.error（棘轮作为晋升门禁的一环）　⟦evolution_bridge.apply_winner 棘轮门禁：退步阻断写回（mock 联动测试 test_evolution_bridge_ratchet_gate_blocks_regression 通过）⟧
- [x] **G4-4** API `prefix /api/v1/ratchet`：`GET /metrics`、`GET /metrics/{key}/history`、`POST /metrics/{key}/force-reset`；main.py 注册　⟦ratchet_routes.py + main.py 注册；TestClient smoke 覆盖 metrics/history/force-reset 2xx⟧
- [x] **G4-5** pytest `tests/test_ratchet_ledger.py`：推进/拒绝/持平/tolerance/force_reset/持久化重载/与 evolution_bridge 阻断联动（mock）　⟦9 用例全绿（推进/拒绝/持平/min_delta/tolerance/force_reset/持久化/门禁联动）⟧

### G-5 Token 可持续性评估器

- [x] **G5-1** 新文件 `src/backend/agents/sustainability.py`：　⟦sustainability.py: evaluate_team + 四规则建议引擎，测试通过⟧
  - `TeamUsage` 输入模型：`{team_id, tokens_consumed, trials: [{trial_id, scenario_id, total_score, tokens}], model_tier, agent_count, budget_tokens}`（数据来源标注 measured | estimated）
  - `evaluate_team(usage) -> {token_efficiency, sustainability_score, grade(A-D), trend, recommendations[]}`
  - `token_efficiency = Σscore / (Σtokens/1000)`；`sustainability_score = 0.5*efficiency_norm + 0.3*trend + 0.2*budget_headroom`
  - 建议引擎规则：低效×高档模型→降档；agent_count>场景 roles 需求→缩编/转储备；预算余量<20%→降演练频率；某 skill 高调用低成功率→路由/进化建议
- [x] **G5-2** `evaluate_group(usages) -> 排名 + 整体可持续评分 + 资源再分配建议`（把 token 从低效团队挪给高效团队的量化建议）　⟦evaluate_group 排名+D级20%预算再分配建议，测试通过⟧
- [x] **G5-3** 数据适配层：优先从 `cost_aggregator`/`cost_models` 拉真实消耗，不可用时接受估算输入（evolution_run.cost_tokens、trial 步数×系数），输出标注 `data_quality`　⟦collect_team_usage_async 接 cost_aggregator + TeamManager + UsageStore；cost_usd/data_sources 标注；测试覆盖 CostAggregator cache 实测路径⟧
- [x] **G5-4** API `prefix /api/v1/sustainability`：`POST /evaluate`（显式传 usage）、`GET /teams/{team_id}`（自动聚合）、`GET /group`；接线：评估完成尝试推进棘轮 `cost_efficiency:{team_id}`；main.py 注册　⟦sustainability_routes.py 三端点+cost棘轮推进(2%容忍)+main.py 注册；新增 POST /weekly-plaza-topics dry-run 议题预览测试通过⟧
- [x] **G5-5** pytest `tests/test_sustainability.py`：效率计算、等级边界、各规则建议触发、group 排名与再分配、估算降级标注　⟦10 用例全绿（效率/等级边界/四规则/group/估算标注）⟧

---

## P1 — 链路联通（下一轮）

- [x] **G3-1** `twin_loop` 决策策略化：session 级 `routing_strategy`（proficiency_first/affinity_first/round_robin/cost_aware），决策时按策略选择 skill 执行人　⟦twin_loop: session.routing_strategy 下发 twin + 四策略任务选择（proficiency_first/cost_aware/round_robin确定性打散）；test_routing_strategy 6 用例全绿⟧
- [x] **G3-2** 路由对照试炼：trial 创建支持 `routing_strategy` 参数，多策略 fork 分支同场景对比，评分差异即路由收益　⟦trial_api 新增 routing_comparison/routing_benefit（baseline 对照 + 分支策略收益）；`GET /twin-trials/{id}/branches` 暴露 routing_strategy；新增 test_routing_strategy_fork_comparison，`pytest -q tests/test_v4_apis.py` 14 passed⟧
- [x] **G3-3** 路由结果写回 `skill_router.submit_feedback`，affinity 随演练进化；路由建议进入 sustainability 建议引擎　⟦evaluate 后按 agent×skill 成功率写回 skill_router.submit_feedback(rating=1+4*成功率, ≥3样本)；sustainability 规则4已含路由建议；新增 test_trial_evaluate_writes_skill_router_feedback 本机 smoke 通过⟧
- [x] **G1-1** plaza 共识事件钩子：plan finalized → 自动创建 extraction pipeline（source=`plaza:{discussion_id}`），settings 开关 `auto_extract_on_consensus`（默认 true）　⟦plaza_engine.run_discussion CLOSED 后挂 _auto_extract_on_consensus：自动建萃取管线(created_by=plaza:{id})；新增 test_plaza_consensus_auto_creates_extraction_pipeline 本机 smoke 通过⟧
- [x] **G1-2** 萃取产物默认入储备池（classification=RESERVE）→ skill_verifier 验证 → G2 分类器周期重算决定毕业　⟦管线 tags 携带 classification:reserve；skill_extractor.approve_item 自动调用 ClassificationStore.seed_reserve_from_extraction 写入初始储备记录（幂等）；新增 test_seed_reserve_from_extraction_idempotent 覆盖通过⟧
- [x] **G1-3** sustainability 周报自动生成议事广场议题（低效团队整改议题，附数据）　⟦双通路完成：nightly_global_loops 自动建议题(settings.auto_plaza_sustainability_topics) + POST /api/v1/sustainability/weekly-plaza-topics(支持 dry_run，test_weekly_plaza_topics_endpoint_dry_run)⟧
- [x] **GP1-4** 三收口件接真实 cost_aggregator / teams 数据联测（替换估算路径）　⟦collect_team_usage_async 接 cost_aggregator(cost_usd)+budget.UsageStore(近7天token)，data_sources 标注；test_collect_team_usage_async_reads_cost_aggregator 覆盖（需本机 pydantic）⟧

## P2 — 可视化与自动化（再下一轮）

- [x] **GP2-1** system-evolution.html 接 `/api/v1/ratchet/metrics` 渲染系统演进史曲线（账本即演进史）　⟦system-evolution.js loadRatchetMetrics：/api/v1/ratchet/metrics → 演进史曲线(renderRatchetLedgerCurve)+指标卡片⟧
- [x] **GP2-2** cost-dashboard.html 增加"效率视角"（score per 1k tokens 排名、sustainability 等级）　⟦cost-dashboard.js 效率视角：/api/v1/sustainability/group → token_efficiency 排名+等级渲染(renderEfficiencyView)⟧
- [x] **GP2-3** agent-team-config / skill 页面三池视图（特有/通用/储备 tab + 毕业/降级动画）　⟦tools-skills.js 技能三池：特有/通用/储备 tab + 重新分类按钮接 /api/v1/skill-classification⟧
- [x] **GP2-4** nightly 任务：每日 reclassify_team 全量重算 + sustainability 报告落盘（复用 launchd 机制）　⟦scripts/nightly_global_loops.py 已有全量重分类+可持续评估+报告落盘；新增 config/launchd/com.agentsgroup.nightly-global-loops.plist 模板，未自动加载到用户 launchd⟧
- [x] **GP2-5** Agent-digital-twin.html 导演台显示当前场景棘轮 generation 与历史最佳（创建试炼时可见"要打破的纪录"）　⟦导演台 onScenarioChange 显示棘轮纪录（gen+历史最佳'要打破的纪录'）；新增 digital-twin-ratchet vitest 源码 smoke 通过⟧

---

## 验收（P0 出口）

- [x] **GE-1** 三个新模块 pytest 全绿（离线纯逻辑），`main.py` 注册三个 router 且既有测试不回归　⟦三模块+路由 smoke 36 用例全绿；main.py 注册完成；v4 API 14 用例全绿；新增全局 hook smoke 2 用例全绿；前端回归见本轮最终验证⟧
- [x] **GE-2** 端到端串联（mock 数据）：trial 评分 → 棘轮推进 → 分类重算（某 skill 毕业）→ 可持续评估给出建议 → 全链路在一个测试用例中跑通　⟦test_e2e_mock_chain_trial_to_sustainability：评分→棘轮→分类毕业→可持续建议→cost棘轮 全链路通过⟧
- [x] **GE-3** 本机 venv：`pytest tests/ -k "classifier or ratchet or sustainability"` + `pytest tests/test_v4_apis.py` 全绿　⟦2026-06-13 本机执行：36 passed, 170 deselected；test_v4_apis 14 passed；test_global_optimization_hooks 2 passed⟧
