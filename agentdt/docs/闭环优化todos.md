# 闭环优化 TODOS — 团队·场景·任务三层闭环（事无巨细 + 伪代码）

> **【2026-06-23 实测修正 · 必读】** 原 C1/C4 的前提（"5 场景是空壳、tasks:0、无评分"）**是错的**——当初查了错字段名。实测：
> - 5 个内置场景**已完整**：字段是 `taskflow`（非 `task_flow`），各有 6~8 个任务 + `roles` + `rubric.dimension_weights`（5 维领域化评分）。**C1（补任务流）/C4（领域评分）已存在，无需再做。**
> - 后端**已有** `match_team(spec, team)` 函数 + `GET /scenarios/{id}/match?team_id=`（按角色/技能覆盖算匹配度）。
> - **真正的断点**：`sexyPickScene` 列的是 **3D 房间/模式/SOP**，**根本没列场景库**（capacity_incident 等）；且 `_sx.scenarioId` **从未被赋值** → `createTrial` 永远发 `scenario_id:''` → 这些富场景从未进入任何试炼。
>
> **∴ 实际要做的（已重定向）**：把**场景库**接进选场景弹层、按团队匹配排序、选中即设 `_sx.scenarioId`。见下方 **C2′（实际实现）**。原 C1/C4 标注为"已存在"。


> 配套 `docs/闭环优化plan.md`。标注规则：
> **★★★ 关键**（闭环成立的地基，需人把关）｜**★★ 重要**｜**★ 一般**
> **[VSCode]** = 机械、低风险、可直接交给 VSCode/codebuddy 批量做｜**[人工]** = 需领域判断/设计决策，建议人来或人审。

---

## C1 · 场景任务流补全（5 场景 × task_flow + 领域 scoring）★★★ [人工设计 + VSCode 落 JSON]

> **为什么最重要**：5 个内置场景目前 `tasks: 0`，是空壳。没有任务流，"选场景→选任务→跑→评分"整条闭环对非 build 团队不成立。这是地基。
>
> **⚠ 数据非硬代码（架构红线）**：场景/任务流/评分权重一律是**可编辑的 JSON 数据**，绝不写进 Python 逻辑分支。分层如下，三条路径并存、内容永不焊死：
> 1. `config/scenarios/*.json` = **内置种子样例（demo fixtures，只读）**——开箱不空，相当于测试数据；
> 2. `storage/scenarios/*.json` = **用户自定义场景**（POST `/api/v1/scenarios` 保存，可增删改）；
> 3. **LLM 生成**：`generate_from_description(text, team_id)` 出草稿 → 用户确认 → 存为自定义。
> 系统逻辑（store/compiler/scoring 引擎）**只把它们当数据读**，权重也是 JSON 里的可调默认值。
> **禁止**：任何 `if team_id=='xxx': dimensions={...}` / 把 task_flow 硬编码进代码路径。本 C1 写的 5 个 JSON 仅是**种子样例**，等价于测试数据。

### C1.1 给每个场景补 `task_flow` 与 `scoring`（改 `config/scenarios/*.json`）
**[人工]** 任务流内容（角色/依赖/验收）需领域判断；**[VSCode]** 按下方 schema 把内容落成 JSON、校验通过。

```jsonc
// config/scenarios/capacity_incident.json （示例结构，其余 4 个同构）
{
  "scenario_id": "capacity_incident",
  "name": "容量事故演练",
  "team_tags": ["事故","容量","韧性","运维"],     // ← 用于团队匹配(C2)
  "domain_tags": ["aws_ops","cloud_ops"],          // ← 新增：可主挂的团队领域
  "task_flow": [                                    // ← 新增：DAG 任务流(原 tasks:0)
    {"task_id":"T1","title":"监控告警识别","role":"巡检监控员","depends_on":[],
     "acceptance":["识别出 P0 指标突变","定位受影响实例族/区域"]},
    {"task_id":"T2","title":"根因定位","role":"架构师","depends_on":["T1"],
     "acceptance":["给出根因假设≥2","附证据(指标/日志)"]},
    {"task_id":"T3","title":"容量评估","role":"成本优化成员","depends_on":["T1"],
     "acceptance":["稳定/弹性负载区分","RI/SP/按需 成本对比"]},
    {"task_id":"T4","title":"扩缩容决策","role":"运维Leader","depends_on":["T2","T3"],
     "acceptance":["决策含覆盖率/利用率/现金流","可回滚"]},
    {"task_id":"T5","title":"Cost Gate 复核","role":"成本优化成员","depends_on":["T4"],
     "acceptance":["覆盖率/利用率/预算阈值校验","超阈即阻断"]},
    {"task_id":"T6","title":"回滚预案+复盘","role":"运维Leader","depends_on":["T5"],
     "acceptance":["回滚步骤可执行","沉淀 SOP"]}
  ],
  "scoring": {                                       // ← 新增：领域化五维权重
    "dimensions":{"韧性":0.30,"时效":0.25,"成本":0.20,"准确":0.15,"协作":0.10},
    "pass_threshold":0.6
  }
}
```

**5 场景的 scoring 权重**（plan §4.2，[VSCode] 照抄）：
```
capacity_incident      韧性.30 时效.25 成本.20 准确.15 协作.10
code_review_delivery   质量.30 覆盖.20 时效.20 协作.20 成本.10
cs_ticket_surge        吞吐.30 时效.25 满意.20 韧性.15 成本.10
data_pipeline_recovery 恢复.35 数据完整.25 时效.20 韧性.10 成本.10
marketing_campaign     创意.25 转化.25 预算.20 时效.15 协作.15
```

### C1.2 schema 校验放行新字段 ★★ [VSCode]
- `scenario_models.py` 的 `ScenarioSpec` / `validate_scenario` 增加 `task_flow`、`domain_tags`、`scoring` 字段（可选，缺省兜底），保证旧场景不报错、新场景能存。
```python
# scenario_models.py
@dataclass
class ScenarioSpec:
    ...
    task_flow: List[Dict[str,Any]] = field(default_factory=list)
    domain_tags: List[str] = field(default_factory=list)
    scoring: Dict[str,Any] = field(default_factory=dict)
# validate_scenario: task_flow 内 depends_on 必须指向存在的 task_id，且无环(复用 compiler 的环检测)
```
- **验收**：`compile_scenario` 对 5 个场景都能编译出非空任务图、无环。

---

## C2 · 团队 ↔ 场景匹配过滤（选团队→只看相关场景）★★★ [VSCode]

> **为什么关键**：闭环可走通的前提。否则 6 团队面对 5 个不相关场景全靠猜。

### C2.1 后端：场景列表支持按团队过滤、相关性排序 ★★ [VSCode]
```python
# scenario_api.py  GET /api/v1/scenarios?team_id=aws-ops
def list_scenarios(team_id: str = ""):
    team = team_mgr.get_team(team_id) if team_id else None
    dom = set(getattr(team,"domain_tags",[]) or _infer_domain(team))   # 团队领域标签
    out=[]
    for s in store.list():
        tags=set(s.team_tags)|set(s.domain_tags)
        rel = 2 if (team and s.domain_tags and team_id_domain(team) in s.domain_tags) else \
              1 if (dom & tags) else 0                                  # 2=主挂 1=相关 0=无关
        out.append({**s.brief(), "relevance":rel})
    # 主挂置顶、相关次之、无关末尾(仍可选，灰显)
    return sorted(out, key=lambda x:-x["relevance"])
```
- **[人工]** 给 6 个团队工厂补 `domain_tags`（如 `aws_ops_team.domain_tags=["aws_ops","运维","成本"]`）——领域判断。

### C2.2 前端：选团队后刷新场景列表、主挂置顶 ★★ [VSCode]
```js
// secs-core.js sexyPickScene(): 带上当前团队
const tid = window._selectedTeamId || '';
const list = await fetch(`/api/v1/scenarios?team_id=${encodeURIComponent(tid)}`).then(r=>r.json());
// relevance=2 主挂(高亮“推荐”) / 1 相关 / 0 无关(灰显、可选)
renderSceneList(list);                       // 选团队变化时重新拉取
```
- **验收**：选 aws_ops→capacity_incident 置顶推荐；选 xops→cs_ticket_surge 置顶。

---

## C3 · 任务选择器按场景带出 task_flow ★★ [VSCode]

> 选场景后，"选择演练任务"应直接列出该场景 `task_flow` 的任务（或"整条流程"），不再是空。

```js
// secs-core.js sexyPickTask(): 读已选场景的 task_flow
const scn = await fetch(`/api/v1/scenarios/${_sx.scenarioId}`).then(r=>r.json());
const tasks = scn.task_flow || [];
// 选项 = 「▶ 整条流程(T1..Tn)」+ 各单任务；默认整条流程
renderTaskOptions([{id:'__flow__',title:'整条流程'}].concat(tasks));
```
- 后端创建试炼时把 `task_flow`/选中任务透传进 world（让 agent 按 DAG 执行）。**[人工核]** world 是否消费 task_flow（不消费则退化为单任务，需在 `trial_api.create_trial` 接 `scenario.task_flow`）。
- **验收**：选场景后任务下拉非空；选"整条流程"跑出的步数/协作覆盖 ≥ task_flow 节点数。

---

## C4 · 领域化评分接入（score 按 scenario.scoring 加权）★★ [VSCode + 人工核]

> 让不同领域的 score→token 效率可比、可信，而不是一把尺量到底。

```python
# trial_api.py / evaluate: 评分时按场景权重加权
scn = scenario_store.get(trial.scenario_id)
weights = (scn.scoring or {}).get("dimensions") or DEFAULT_WEIGHTS
total = sum(dim_score[d]*w for d,w in weights.items())   # 加权总分
passed = total >= (scn.scoring or {}).get("pass_threshold", 0.6)
return {"total_score": total, "dimensions": dim_score, "weights": weights, "passed": passed, ...}
```
- 前端评分卡显示"按 <场景名> 维度加权"，雷达图轴名用该场景维度。**[VSCode]**
- **验收**：同一团队跑 capacity_incident vs marketing_campaign，评分维度名称/权重不同，雷达轴随场景变。

---

## C5 · 演练 ↔ 仿真合并（单一运行入口 + 可视化作实时视图）★★★ [人工设计 + VSCode 改 UI]

> plan §5 的落地。把两个大按钮收敛成一个，仿真降级为演练的可视化层。

### C5.1 UI 收敛 ★★ [VSCode]
- 删/隐藏 `🎬 房间任务流程仿真`(`secs-dev-btn`)；保留单一 `▶ 运行演练`(原 `沙箱推演`)。
- 运行模式开关：`◉ 评分演练（默认）  ○ 仅可视化（快速预演·不评分）`。
```js
// 运行演练统一入口
async function runDrill(){
  await sexyCreateAndRun();             // 建试炼(评分闭环)
  if (mode==='visual_only') window._trialNoScore = true;   // 仅可视化:跳过评分/进化
  startRoomVisualization(_sx.sessionId); // secsDevWorkflow 的渲染层，订阅同一 session 的 SSE
}
```

### C5.2 让 `secsDevWorkflow` 渲染绑定到演练 session ★★★ [人工]
> 关键改造：仿真原本自起一套；改成**订阅演练 session 的事件流**（同一 trial），边跑边在 3D 房间渲染对话/流水线，不再创建第二个 session。
```js
// secsDevWorkflow 改造要点：
//  - 不再自行 createSession；从 window._sx.sessionId 取当前演练 session
//  - 监听该 session 的 SSE step 事件 → 渲染房间对话流/L1→L4/奖励曲线
//  - 运行结束由演练主流程统一 finalize(评分/SOP/进化)
```
- **验收**：点一次「▶ 运行演练」→ 3D 房间实时演协作 **且** 结束后有五维评分；不再出现两个 session、两套数据。

### C5.3 回退保障 ★ [VSCode]
- 保留 `secsDevWorkflow` 函数（仅改数据源），异常时降级为纯动画不阻断评分。

---

## C6 · 6 团队端到端跑通验收（证明泛化成立）★★ [人工，联机]

> 需真实 LLM + 浏览器，离线不可完成；列为验收清单。

```
for team in [build, ai_coding, aws_ops, cloud_ops, energy, xops]:
  选团队 → 场景列表主挂置顶且相关 → 选主挂场景 → 任务下拉非空(带 task_flow)
  → 运行演练 → 3D 房间实时可视化 → 结束有"按该场景维度"的五维评分
  → 评分>阈值 → 产出 SOP/反哺/进化 → cost_efficiency 棘轮可推进
断言：6 个团队各自跑通，无"空场景/空任务/一把尺评分/两个割裂按钮"
```

---

## 落地顺序（建议）
```
1) C1 场景任务流+scoring 补全     ★★★ 地基(人工设计内容 → VSCode 落 JSON+校验)
2) C2 团队↔场景匹配过滤           ★★★ 闭环前提(VSCode + 人工补 domain_tags)
3) C3 任务带出 task_flow          ★★  (VSCode + 人工核 world 是否消费)
4) C5 演练↔仿真合并               ★★★ 体验闭环(人工设计 + VSCode 改 UI)
5) C4 领域化评分                  ★★  (VSCode + 人工核加权口径)
6) C6 6 团队端到端验收            ★★  (人工联机)
```

## 交给 VSCode 的明确清单（低风险机械活）
- C1.1 把人工给的 task_flow/scoring 内容写进 5 个 `config/scenarios/*.json`（按 schema）。
- C1.2 `scenario_models.py` 加 3 个可选字段 + 校验放行。
- C2.1/C2.2 场景列表 `?team_id=` 过滤 + 相关性排序 + 前端选团队刷新场景。
- C3 任务下拉读 `task_flow`。
- C4 评分按 `scoring.dimensions` 加权 + 前端轴名随场景。
- C5.1/C5.3 UI 收敛成单按钮 + 模式开关 + 回退降级。

## 必须人来把关（领域/架构判断）
- C1.1 每个场景**任务流的角色/依赖/验收**与 scoring 权重（领域知识）。
- C2.1 6 团队的 `domain_tags`。
- C3 / C5.2 world/trial 是否真正**消费 task_flow** 并把 `secsDevWorkflow` 绑到演练 session（架构改造，风险最高）。

---

## C2′ · 实际实现（2026-06-23 已落地）★★★

> 真正的断点不是"场景空壳"，而是**场景库根本没接进选场景弹层**、`_sx.scenarioId` 从未赋值。已修：

- [x] **后端** `scenario_api.list_scenarios` 支持 `?team_id=`：复用 `match_team` 给每个场景算 `skill_match_rate`/`missing_skills`，按匹配度降序返回。
- [x] **前端** `sexyPickScene` 顶部新增「🎯 演练场景库」：拉 `/api/v1/scenarios?team_id=<所选团队>`，列出真实场景（capacity_incident 等），显示 任务数/难度/团队匹配%/缺技能，按匹配度排序置顶。
- [x] **前端** `sexySelectScene` 选中真实场景即 `window._sx.scenarioId = <scenario_id>`（房间/模式/SOP 清空）。
- [x] **闭环贯通**（后端本就支持，现被喂到了）：`createTrial` 传 `scenario_id` → `trial_api.create_trial` `compile_scenario` 把 taskflow 编译进 world（L412）+ 评估用 `rubric.dimension_weights` 覆写五维权重做**领域化评分**（L340-345）。
- **C1/C4 结论**：场景的 `taskflow`+`rubric` **本就完整**，无需再补；本次只做"接通"。
- **验收（联机）**：选 aws_ops→场景库里 capacity_incident 类按匹配度靠前→选它→跑演练→评估雷达轴/权重 = 该场景 rubric；换 marketing_campaign 评分维度随之变。

> **剩余**：C5（演练↔仿真合并，把 `secsDevWorkflow` 绑到演练 session）——架构改造、风险最高，仍标 **[人工]**，建议单独一轮并人审。
