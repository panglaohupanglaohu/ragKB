# 闭环优化 Plan — 团队 · 场景 · 任务 三层闭环（6 领域通用化）

> 北极星：**用最少的 Token 把事办成**。本 plan 解决数字孪生「演练配置」三段式 **团队 → 场景 → 任务** 闭环目前只对 build 团队成立、其余 5 个领域是空壳的问题，并回答「演练 vs 仿真两个按钮是否合并」。

---

## 1. 现状诊断（实测）

**有什么：**
- **6 个团队工厂**：`build_team` / `ai_coding_team` / `aws_ops_team` / `cloud_ops_team` / `energy_team` / `xops_team`。
- **5 个内置场景**（`config/scenarios/*.json`）：`capacity_incident`(容量事故)、`code_review_delivery`(代码评审交付)、`cs_ticket_surge`(客服工单高峰)、`data_pipeline_recovery`(数据管道故障恢复)、`marketing_campaign`(营销活动投放)。
- 三段式 UI：`选择演练团队 → 选择演练场景 → 选择演练任务`，下接 `仿真参数`、`沙箱推演`、`房间任务流程仿真`。

**断在哪（核心问题）：**
1. **5 个场景全是空壳**：每个 scenario 只有 `team_tags`（领域标签），**`tasks: 0`**——没有任务流（task flow），所以"选场景→选任务"这一段在非 build 团队下选不出东西、跑不出有意义的评分。
2. **团队↔场景无匹配关系**：选了团队，场景列表不会按该团队领域过滤；6 个团队和 5 个场景没有显式映射，用户全靠猜。
3. **评分维度不分领域**：五维评分对所有场景一把尺，营销活动和容量事故用同一套评判，产出的 score→token 效率不可比、不可信。
4. **演练 / 仿真两个大按钮语义重叠**：`沙箱推演`(可评分闭环) 与 `房间任务流程仿真`(纯 3D 可视化) 并列，用户分不清点哪个、产出有何不同。

**结论**：build 之所以"看着闭环"，是因为它恰好有内容垫底；其余 5 个领域要把 **场景任务流 + 团队映射 + 领域化评分** 补齐，闭环才真正成立。

---

## 2. 设计目标（闭环成立的判据）

对**任意一个团队**，用户应当能够：

```
选团队(领域已知) → 系统只列该领域相关场景 → 选场景 → 自动带出该场景的任务流(有 DAG/验收)
→ 跑演练 → 按"该场景的评分维度"打分 → 产出 SOP/反哺/进化 → 达标推进 cost_efficiency 棘轮
→ 全程在 3D 房间里可视化(对话流 + 流水线 L1→L4 + 奖励曲线)
```

即把"团队-场景-任务"从 build 专属，泛化成 **6 领域通用的、可评分的、可视化的闭环**。

---

## 3. 三层数据模型（team ↔ scenario ↔ task）

```
Team(领域 domain)
  └── 关联 Scenario[]（按 domain/tags 匹配，1 团队 N 场景，1 场景可跨团队）
        └── task_flow: Task[]（DAG：依赖、角色、验收标准）
              └── scoring: 该场景的评分维度与权重（领域化）
```

**领域 → 场景映射建议**（按 `team_tags`/领域）：

| 团队 | 领域 | 主场景（建议主挂） | 可复用场景 |
|------|------|--------------------|------------|
| build_team | 构建/发布 | code_review_delivery（代码评审交付） | capacity_incident |
| ai_coding_team | AI 编程 | code_review_delivery | data_pipeline_recovery |
| aws_ops_team | AWS 运维降本 | capacity_incident（容量事故） | data_pipeline_recovery |
| cloud_ops_team | 云运维 | capacity_incident | data_pipeline_recovery |
| energy_team | 能源 | data_pipeline_recovery（数据管道恢复） | capacity_incident |
| xops_team | xOps 运营 | cs_ticket_surge（客服工单高峰） | marketing_campaign |
| （营销向团队，如有） | 营销 | marketing_campaign | cs_ticket_surge |

> 映射不写死代码，而是 **scenario.team_tags ∩ team.domain_tags ≥1 即视为匹配**；选团队后场景列表据此过滤、排序（主挂场景置顶）。

---

## 4. 每个场景要补的两样东西

### 4.1 任务流 task_flow（DAG）
每个场景定义 3~6 个任务，含 `task_id / title / role(执行角色) / depends_on[] / acceptance(验收要点)`。例（capacity_incident）：

```
T1 监控告警识别(巡检监控员) → T2 根因定位(架构师) → T3 容量评估(成本优化成员)
→ T4 扩缩容决策(运维Leader, depends T2,T3) → T5 Cost Gate 复核(成本优化成员, depends T4)
→ T6 回滚预案+复盘(运维Leader, depends T5)
```

### 4.2 领域化评分维度 scoring
每个场景给 5 维各自的**含义与权重**，让 score 在该领域内可比：

```
capacity_incident:   韧性0.3 时效0.25 成本0.2 准确0.15 协作0.1
code_review_delivery: 质量0.3 覆盖0.2 时效0.2 协作0.2 成本0.1
cs_ticket_surge:     吞吐0.3 时效0.25 满意0.2 韧性0.15 成本0.1
data_pipeline_recovery: 恢复0.35 数据完整0.25 时效0.2 韧性0.1 成本0.1
marketing_campaign:  创意0.25 转化0.25 预算0.2 时效0.15 协作0.15
```

---

## 5. 演练 vs 仿真 —— 关系与「是否合并」

**两者本质：**
- **演练（沙箱推演 / 试炼，`sexyCreateAndRun`→`createTrial`）**：team+scene+task → 跑 → reward/五维评分 → SOP/反哺/进化 → 棘轮。**产出可评分证据，是北极星闭环的发动机。**
- **仿真（房间任务流程仿真，`_sexyRoomSim`→`secsDevWorkflow`）**：team+task → 在 3D 房间里把 agent 协作"演"出来（对话日志 + 房间动画）。**只可视化、不评分、不沉淀。**

**判断：应当合并（强烈建议）。** 理由：
1. 两者都是"让这个团队在沙箱里把这个任务跑一遍"，并列两个大按钮制造选择困难。
2. **可视化本就该是演练的"实时视图"**——你跑一次有评分的演练时，本来就该边跑边在 3D 房间里看到协作过程，而不是分两次、两套数据。
3. 现在的割裂导致：点"仿真"看得见但没分；点"沙箱推演"有分但可视化弱。用户要的是**又看得见又有分**。

**合并方案：**
> 收敛成**一个入口「▶ 运行演练」** = `沙箱推演(可评分)` 为主干，`secsDevWorkflow` 的 3D 房间渲染/对话流降级为**演练运行时的可视化层**（边跑边演）。再给一个轻量开关「仅可视化（不评分/快速预演）」满足纯演示需求。运行结束统一产出评分/SOP/进化。

效果：**一次运行 = 看得见的协作过程 + 可评分的闭环证据**，消除"两个按钮、两套结果"的割裂。

---

## 6. 落地优先级

```
P0 场景任务流补全(5 场景 × task_flow + 领域 scoring)  ——闭环的"内容地基"，最重要
P0 团队↔场景匹配过滤(选团队→只看相关场景)            ——闭环可走通的前提
P1 领域化评分接入(评分按 scenario.scoring 加权)        ——让 score→token 效率可信
P1 演练↔仿真合并(单一运行入口 + 可视化作实时视图)      ——消除割裂，体验闭环
P2 每个团队端到端跑通验收(6 领域各一遍)                ——证明泛化成立
```

> 详细任务拆解（事无巨细 + 伪代码 + 重要度/可托管标注）见 `docs/闭环优化todos.md`。
