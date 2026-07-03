# 试炼页(数字孪生 SECS 试炼导演台)优化 Plan

> 目标:数字孪生页右侧「试炼导演台 / 沙箱推演」+ 实时控制台 + 技能进化链路。
> 前端:`src/frontend/js/digital-twin/secs-core.js`(创建试炼/run/控制台)、`director.js`、`v4-evolution.js` / `v4-scenarios.js`、`Agent-digital-twin.html`
> 后端:`src/backend/sandbox/twin_loop.py`(仿真+奖励)、`trial_api.py`(_compute_evaluation/evaluate/skill-stats)、`evolution_bridge.py`(identify_weak_skills/进化门禁)
> 编写日期:2026-06-14
> 分派:**【Claude(沙箱可做)】** 前端代码 + 纯 python,node--check/vitest/py_compile 可验;**【Reasonix(本机/浏览器)】** 起服务/真 LLM/浏览器点测

---

## 0. 截屏暴露的两个真问题(已核查根因)

**现象**:What-if 试炼跑了 26 步,**每步 reward=0.0000**,却显示 `总步数 26 · 评分 0.315`;技能进化点「发起进化」→ `✗ rejected: no_weak_skills_identified`。

**根因 1 — 无场景空跑,评分误导**:
- 该次试炼**没有选「演练场景」**(只有 baseline 分支)。`twin_loop` 无场景任务时走 `_generate_default_tasks`(按 agent 技能兜底造任务),这些任务**没有 scenario taskflow 的 reward/failure_penalty**,智能体"动作"但几乎不产生任务奖励 → `step.global_reward = sum(step_rewards)/n ≈ 0`。
- 而 `trial_api._compute_evaluation`:`task_completion = best_reward`(此时≈0),但 `cost_efficiency / resilience / extractability` 有**基础分**(无故障 resilience=1.0、步数占比给 cost 基础分…),按场景默认权重加权 → 总分≈0.3。**所以"全 0 却 0.315"是无场景基线分,不代表真实表现** —— 这对用户是误导。

**根因 2 — 进化门禁拒绝但不可操作**:
- `发起进化` → `evolution_bridge.identify_weak_skills(team, scenario, trial_ids)`:聚合最近 window 个 trial 的 `usage` 记录,挑成功率 < 期望(默认 0.6)或趋势连续下滑的弱 skill;`if not all_usages: return []` → 无弱 skill → `run.error = "no_weak_skills_identified"`。
- 当前没有跑过"带技能使用的场景试炼"(usage 为空)→ 必然拒绝。UI 只甩一句 `rejected: no_weak_skills_identified`,**没告诉用户为什么、怎么办**(应:先选场景跑试炼积累 usage,再发起进化)。

---

## 1. P0 — 无场景空跑治理(评分不再误导)

- **创建试炼前置校验**:`创建试炼`/`沙箱推演` 若未选「演练场景」,弹确认:"未选场景将使用兜底默认任务,评分仅为基线参考、不反映真实能力,是否继续?",或直接引导去选场景。
- **评分语义标注**:无 scenario_id 的试炼,控制台/历史里把评分标为「基线分(无场景)」灰显,不与真实场景分混排;有场景才显示「综合评分」。
- **后端可选**:`_compute_evaluation` 在 `task_completion≈0 且无 scenario` 时,在返回里加 `meaningful=false` + `note`,前端据此标注(纯附加字段,不改算法)。

## 2. P1 — 评分透明化(五维 breakdown)

- 控制台「评分: 0.315」改为**展开五维**:任务完成 / 协作效率 / 韧性 / 成本 / 可萃取 + 各自权重,让用户一眼看出"task_completion=0,分数来自基础维度"。
- `evaluate` 接口已返回五维(`trial_api._compute_evaluation` 的 TrialEvaluation),前端只是没展开 → 纯前端改。

## 3. P1 — 进化拒绝可操作化

- `no_weak_skills_identified` 不再只甩英文 code,改为中文可操作提示 + 引导:
  「未发现弱技能:本团队最近无带技能使用的试炼数据。请先①选演练场景②创建并运行试炼(产生 skill usage)→ 再发起进化。」
- 技能进化链路 UI(识别→反思→变体→A/B→晋升):拒绝时高亮「识别」步为失败态 + 展示被扫描的 trial 数 / usage 数(0)作为证据。
- 后端可选:`identify_weak_skills` 空结果时返回结构化原因(`{reason:'no_usage', scanned_trials:n, usages:0}`),前端据此精准提示。

## 4. P2 — reward 可读性 + 控制台体验

- 每步 `reward=0.0000` 刷屏且令人不安:无场景时在首行提示"⚠ 无场景:以下为兜底任务,奖励多为 0";有场景时正常。
- 累计奖励 / 当前步进度条;`仿真完成` 时给"本次为基线分/真实分"的明确结论句。

## 5. P2 — 其它

- 「分支管理 baseline」「注入历史」「沙箱进料/出料」「种子技能/运行参数」tab 的空态文案统一(现"启动仿真后显示任务"等);
- 模式卡(What-if/多分支/混沌/演化/回放)与右侧运行参数联动核查(选演化试炼→步数默认 200 等,sexySelectScene 已有部分逻辑)。

---

## 6. 实施顺序
1. P0 无场景校验 + 评分语义标注(前端为主,Claude)
2. P1 五维 breakdown(前端,Claude)+ 进化拒绝可操作(前端 Claude + 后端结构化原因 Claude)
3. P2 控制台可读性、空态文案(Claude/Reasonix)
4. 真 LLM 进化闭环 + 浏览器逐项(Reasonix 本机)

详见 `docs/试炼页优化todos.md`。
