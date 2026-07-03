# 数字孪生收口 Plan — 闭环遗留收尾 + Tab 语义收口（系统状态/交互流 是否合并）

> 承接 `docs/闭环优化plan.md` / `docs/闭环优化todos.md`。本 plan 干两件事：
> **A. 把闭环优化里没干完的两项给个明确了结**（C5.2 / C6）。
> **B. 收口数字孪生的 5 个 Tab 语义，重点回答"系统状态 与 交互流 是否合并"。**

---

## A. 闭环遗留收尾

### A1. C5.2 —— `secsDevWorkflow` 绑定演练 session？**结论：不绑定，降级为独立预演（维持现状）。**
- **为什么不做**：评分演练（运行演练 → 沙箱推演 → twin-trial）**本身已经在 3D 房间里实时渲染**协作过程（流水线 L1→L4、奖励曲线、混沌事件已同步进/出 agent）。`secsDevWorkflow` 是另起一个 session 的**纯可视化预演**，与之重叠。强行把它"绑定到演练 session"= 把一个能用的独立功能拆掉重接，盲改风险高、收益低。
- **已做的等价收口**：UI 上已收敛为单一主入口「▶ 运行演练」（可评分+含 3D），`secsDevWorkflow` 降级为「🎬 仅可视化预演（不评分）」小按钮。**职责清晰即闭环达成**，不需要再合代码。
- **判据**：若未来发现"预演"与"演练"产生数据串台/双 session 冲突，再考虑绑定；目前无此问题 → 标 **WONTFIX（设计取舍）**。

### A2. C6 —— 六团队端到端验收。**结论：需联机 LLM，写成可执行验收脚本/清单，离线不可跑。**
```
for team in [build, ai_coding, aws_ops, cloud_ops, energy, xops]:
  选团队 → 场景库按匹配排序 → 选主挂场景(带 taskflow) → 运行演练
  → 3D 切到该场景房间 + 实时可视化 → 结束按"该场景 rubric 维度"五维评分
  → 评分>阈值 → SOP/反哺/进化 → cost_efficiency 棘轮可推进
  → 混沌(离开/故障/增援) 3D 与 协作拓扑 同步
断言：6 团队各自跑通；无 空场景/空任务/一把尺评分/两个割裂按钮/3D不同步
```
- 标 **[需联机]**：必须真实 LLM + 浏览器人工/脚本跑一遍，本地代码无法验证。建议接 `aws_ops_e2e` 同款 `ApiClient/Runner/step` 写 `scripts/twin_six_team_smoke.py`（不调 LLM 的部分可断言：场景匹配排序、scenario_id 透传、rubric 加载）。

---

## B. 数字孪生 Tab 语义收口（核心：系统状态 vs 交互流 是否合并）

### B0. 现状 5 个 Tab
| Tab(view) | 内容 | 数据本质 |
|---|---|---|
| 环境空间 environment | 3D 房间 + agent | 空间/场景 |
| **系统状态 architecture** | 子页①**实时仪表盘**(系统指标,10s刷新) + 子页②**协作拓扑**(节点=agent,边=交互频次) | ①系统健康 ②**交互(图视角)** |
| **交互流 interaction** | 消息时间线 + 流量统计 + 全部/序列图 | **交互(时间线视角)** |
| 编排管线 pipeline | L1→L4 流水线 | 执行编排 |
| CLI | 命令行 | 调试 |

### B1. 判断：**应该合并——但合的是"协作拓扑 + 交互流"，不是整个"系统状态 + 交互流"**

- **协作拓扑（系统状态子页②）** 与 **交互流** 是**同一份"agent 交互"数据的两个视角**：
  - 拓扑 = 空间/结构视角（**谁** 和 **谁** 交互、频次多粗）；
  - 时间线 = 时序视角（**何时** 发生了 **什么** 消息）。
  - 二者天然是一对（"图 + 时间线"是交互分析的标配双视图），现在被拆在两个 Tab，用户要在"系统状态"里看图、跳到"交互流"里看序列，割裂。
- **实时仪表盘（系统状态子页①）** 是**系统健康指标**（运行时/会话/步数/吞吐…），与"谁和谁说话"无关 → **不应**和交互流合并。

> **一句话**：把"交互"这件事收到一个 Tab；把"系统指标"留在系统状态。**不是把系统状态整个并进交互流**，而是把系统状态里"错放"的协作拓扑挪去和交互流团聚。

### B2. 目标结构（5 Tab → 语义清晰）
```
环境空间   ——3D
系统状态   ——只留 实时仪表盘(系统指标)         ← 协作拓扑移出
协作·交互  ——【新】= 协作拓扑(图) + 交互时间线/序列(时序)，双子页切换   ← 协作拓扑 + 交互流 合并
编排管线   ——L1→L4
CLI
```
（Tab 数仍 5；若想更精简，可把 CLI 收进"更多"，但不在本次范围。）

### B3. 实施（事无巨细 + 伪代码）★★ 多为 [VSCode]，合并联动逻辑 [人工核]

```html
<!-- 1) nav：把"交互流"改名"协作·交互"，"系统状态"保留 -->
<div data-view="architecture">系统状态</div>     <!-- 子页只剩 实时仪表盘 -->
<div data-view="interaction">协作·交互 <span id="msg-count"></span></div>
```
```html
<!-- 2) view-interaction 内：顶部加子页切换（拓扑 / 时间线），复用现有渲染 -->
<div class="flow-btns">
  <button onclick="showInteractSub('topo',this)">协作拓扑</button>    <!-- 复用 renderTopology -->
  <button onclick="showInteractSub('timeline',this)" class="active">交互时间线</button>
  <button onclick="filterMsgs('all')">全部</button> ...               <!-- 时间线下的过滤保留 -->
</div>
<div id="interact-sub-topo" style="display:none"><svg id="topo-svg"></svg></div>  <!-- 把 topo-svg 搬来 -->
<div id="interact-sub-timeline"><div id="msg-timeline"></div></div>
```
```js
// 3) JS：协作拓扑从 architecture 子页迁到 interaction 子页
function showInteractSub(which,btn){
  document.getElementById('interact-sub-topo').style.display = which==='topo'?'':'none';
  document.getElementById('interact-sub-timeline').style.display = which==='timeline'?'':'none';
  if(which==='topo') renderTopology();           // 已有；混沌同步钩子 _dt2dRefreshTopo 也已就绪
  else renderInteractions('all');
}
// 4) 系统状态(architecture) 删掉 协作拓扑子页与其切换按钮，只保留 实时仪表盘
//    showArchSub 仅剩 'dashboard'；topo 相关 DOM/调用迁走
```
- **[人工核]**：`renderTopology` 读 `arch-sub-topo` 的可见性来决定是否刷新（`_dt2dRefreshTopo` 里 `getElementById('arch-sub-topo')`）——**迁移后要把这个可见性判断改成新容器 `interact-sub-topo`**，否则混沌同步刷新会失效。
- **数据**：两视图共用 `S.messages`（时间线）与 `S.agents+边`（拓扑），合并后**同源一致**，混沌增删已分别同步到 3D 与拓扑，时间线天然追加。
- **回退**：纯前端 DOM 迁移 + 改名；改前 `git commit`，异常 `git revert`。

### B4. 验收
```
- 系统状态 Tab：只剩 实时仪表盘，无协作拓扑。
- 协作·交互 Tab：顶部可切 协作拓扑 / 交互时间线；切到拓扑能渲染、混沌离开/增援节点同步；切到时间线消息流正常、过滤可用。
- 混沌(离开/增援) 时：3D、协作拓扑节点、msg-count 三处一致。
- node --check 前端无误；点击各 Tab 无 JS 报错。
```

---

## B'. 编排管线 Tab 优化（用户追加）

### B'0. 现状诊断（实测）
数字孪生页其实有**三个叫"pipeline"的东西**，职责串了：
| 位置 | 实际内容 | 问题 |
|---|---|---|
| **编排管线 Tab**(`renderPipeline`) | 居然是**技能萃取管线**：草稿→萃取→评审→批准→发布，读 `/api/v1/extraction/pipelines` | **与「技能萃取/赋予」页完全重复**；名叫"编排"却是萃取阶段；放在数字孪生页**驴唇不对马嘴** |
| 右侧 **SECS 演练 PIPELINE** | L1 MADTwin→L2 AAS→L3 TwinLoop→L4 MADCG→Loop | 这才是**演练执行的真·编排层** |
| 技能进化面板 `evo-pipeline` | 识别→反思→变体→A/B→晋升 | 进化子流程，正常 |

> **结论**：编排管线 Tab **当前内容是错的**——它把萃取页的管线搬来了，既重复又文不对题。应**重构为"本次演练的任务编排"**。

### B'1. 优化方案：编排管线 Tab = 当前演练的**任务编排 DAG**（活的）
> 在"团队→场景→任务"闭环里，编排管线最该展示的是：**所选场景的 taskflow 任务图（T1→…→Tn，含依赖）+ 实时执行状态**（哪个任务在跑、谁在执行、完成/待办/失败），并叠加 L1→L4 的层进度。这样它才是数字孪生上"看团队怎么把任务编排着干完"的视图，而非萃取阶段的复制品。

```js
// renderPipeline 重构要点（伪代码）
async function renderPipeline(){
  var sid = window._sx && window._sx.scenarioId;
  if(!sid){ showHint('选择演练场景后显示任务编排'); return; }
  var scn = await fetch('/api/v1/scenarios/'+sid).then(r=>r.json());
  var tf = scn.taskflow||[];                       // T1..Tn + depends_on + room_id + required_skills
  // 1) 画 DAG：按 depends_on 分层(拓扑序)，节点=任务，连线=依赖
  renderTaskDAG(tf, layoutByDepends(tf));
  // 2) 叠加实时状态：从当前 trial/session 的 step 事件标记 任务 running/done/failed + 执行 agent
  var prog = await fetch('/api/v1/twin-trials/'+window._DTS.activeTrialId).then(r=>r.json()).catch(()=>null);
  applyLiveTaskStatus(prog);                        // 完成绿/进行中青/待办灰/失败红 + agent 名
  // 3) 顶部保留 L1→L4 层进度条(复用右侧 spipe-* 状态)，点层看说明
}
```
- **数据源**：场景 `taskflow`（已存在）+ 运行中 trial 的步进/任务事件（SSE/`/twin-trials/{id}`）。
- **[人工核]**：trial/session 是否暴露"每个 taskflow 节点的状态"；若没有，先用"步数/已完成任务数"近似，后续再细化到节点级。
- **去重**：萃取阶段图**只留在技能萃取页**；数字孪生的编排管线不再读 `/extraction/pipelines`。

### B'2. 验收
```
- 编排管线 Tab：未选场景→提示选场景；选了场景→显示该场景 taskflow 的 DAG(依赖连线)。
- 运行演练时：任务节点按执行进度变色(待办/进行/完成/失败)，标注执行 agent；顶部 L1→L4 层进度同步。
- 不再出现 草稿/萃取/评审/批准/发布 这套萃取阶段(那是萃取页的)。
```

---

## C. 执行顺序 & 标注
```
A1 C5.2 → WONTFIX（写明取舍，不动代码）
A2 C6   → [需联机] 写 smoke 脚本骨架(非LLM断言)，LLM 验收人工
B  Tab 收口 → 迁移协作拓扑到交互 Tab + 改名(主要 [VSCode]，可见性判断迁移 [人工核])
B' 编排管线重构 → renderPipeline 改读场景 taskflow DAG + 实时状态，去掉萃取阶段复制品([人工核]任务级状态来源)
```
> **重点回答用户问题**：**合并——把"协作拓扑"从系统状态挪去与"交互流"合成一个 Tab（图+时间线双视图）；"实时仪表盘"留在系统状态。不是把系统状态整体并进交互流。**
