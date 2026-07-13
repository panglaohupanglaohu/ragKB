<!-- docs-signoff: author="Grok" kind="llm" doc="plan" ts="2026-07-13T14:33:59Z" -->
# 物竞天择 v4 Plan — 任务闭环 · Skill 遗传与集成

> 版本：v4.0 · 日期：2026-07-13 · 作者：Grok（接手开发）  
> 状态：`current`（设计已冻结，实现按配套 todos）  
> 承接：[`物竞天择数字孪生演练plan.md`](物竞天择数字孪生演练plan.md)（v2 生境内核 + v3 三级赛制）  
> 配套：[`物竞天择任务闭环与Skill遗传todos.md`](物竞天择任务闭环与Skill遗传todos.md)  
> 入口：`http://localhost:5173/Agent-digital-twin.html?office3d=1`（可带 `&plan_id=`）

---

## 0. 缘起与问题

### 0.1 用户需求（2026-07-13）

1. **三级赛制**（分场锦标赛 / 多队对抗 / 混合竞争）形式上已改。
2. **判断轮次与步数应与各团队执行的任务关联**。任务链路：
   Plaza 讨论话题 → 收敛执行计划 → 拆解为各团队任务 → 形成闭环。
3. **调研生物遗传学**，使人深刻理解基因延续的复杂性；系统内强调 **Skill 的遗传与集成**。
4. 对系统做深入优化，交付 **事无巨细** 的 plan + todos。

### 0.2 现状与缺口（代码调研结论）

| 已有能力 | 缺口 |
| --- | --- |
| Plaza：讨论 → markdown 计划 → `ExecutionPlan` → approve → dispatch → `AgentTask` | 物竞天择路径 **不读** 计划/任务 |
| `plan_scenario_bridge`：计划 → SECS `ScenarioSpec` | 只服务 SECS，**不进** `eco_drill` |
| `eco_drill`：survival 适应度 + skill/collab 双基因 + 三档 UI | `max_steps` / `max_generations` 手填；`demanded_skills` = 团队技能目录，与计划无关 |
| 前端 `task_goal.era=true` | **`run_drill_via_trial` 未调用 `run_eras`**（混合竞争半成品） |
| `skill_genome = agent.skills` | 不经 skill_library/router；演练后 **默认不回写** 绑定 |
| 遗传学七图（前端） | 偏展示；与「计划技能需求」无联动 |
| OPTIMIZATION P5-4 孪生竞标 | 移交数字办公室 M4；物竞路径未承接 |

### 0.3 不可破坏的世界观（最高约束）

1. Agent 不是人类模仿；以 **感知→意图→行为** 存在于自有生态。
2. **Skill 与协作过程** 都是被环境选择的可遗传单元。
3. **主动学习是盲目的，选择是客观的**。
4. **生存时长（survival_ticks）是唯一原生适应度**——禁止引入人工评分。
5. 协作靠涌现：只给协作倾向基因 + 信号令牌 + 代谢成本，**不写协作规则引擎**。
6. **两阶段经济学**：Plaza 集体智慧阶段不做 token 优化；成本/竞标从 **执行计划产生之后** 开始。
7. 办公室视图 Agent 造型保持 **plaza 风格**；3D 窗口不可丢。
8. **演练默认不动真身**（写回技能/谱系需显式开关 + 确认）。

---

## 1. 一句话目标

把办公室视图的物竞天择，从「抽象生境沙盒」升级为：

> **执行计划驱动的 Skill 自然选择试验田**——同一份 Plaza 计划编译为任务生境契约；三级赛制在该契约下比较团队 × 技能 × 协作；选择结果驱动 Skill 遗传解释与集成建议，并可选回流生产派发。

```
Plaza 话题
  → 多轮议事 → 结构化 ExecutionPlan（人批准）
  → TaskHabitatContract（步骤 → 生态位序列 + 步数预算 + 角色需求）
  → 三级赛制演练（division / confrontation / mixed）
  → Skill 遗传（交叉 / 盲目学习 / 杂优）+ 集成报告（dominant → 绑定建议）
  → 棘轮锁定该计划类型最优构型
  → 生产派发采用胜出构型（闭环）
```

---

## 2. 遗传学调研（Skill 中心映射）

> 公开学术概念的 **类比性借用**（Agent skill/collab 非生物 DNA），用于把「自然选择性」可解释化。

### 2.1 双遗传（Dual Inheritance / Gene–Culture Coevolution）

| 生物学 | 本系统 Skill 语义 |
| --- | --- |
| 基因垂直传递（亲→子） | 交配交叉：`skill_genome` 子集遗传 + 微变异 |
| 文化水平传递（师徒/同伴） | 盲目学习、信号跟随后的熟练度上升、生产侧 SkillRouter 注入 |
| 双通道互相约束 | 技能囤积有 `genome_carry_cost`；环境 `demanded_skills` 选择「有用」单元 |

**产品含义**：必须同时展示 **垂直遗传（谱系）** 与 **水平集成（学习 / 路由 / 入库）**。

### 2.2 数量遗传学

| 概念 | 映射 | 呈现 |
| --- | --- | --- |
| 表现型 P | survival_ticks（+ 报告用计划技能覆盖率，派生非适应度） | 排行榜 |
| 基因型 G | skill 集合 + collab 向量 | 基因 chips / 雷达 |
| 狭义遗传力 h² | 亲–子 survival / 关键 skill 持有回归 | 分 skill h² 条 |
| 上位（epistasis） | skill 组合（学派簇）匹配多步骤计划 | 学派热力 |
| 选择响应 R≈h²S | 棘轮抬升的 best survival | 棘轮面板 |

### 2.3 群体遗传学

| 概念 | 映射 |
| --- | --- |
| 等位基因频率 | skill 存活频率 → dominant / neutral / deprecated |
| 选择系数 | 持有 plan-demanded skill 者的相对 survival 优势 |
| 遗传漂变 | 小团队（分场）随机丢 skill |
| 奠基者 / 瓶颈 | 初代 roster；全灭 = 瓶颈 |
| 基因流 / 杂优 | 混合竞争跨队交配 |
| 均值回归 | 明星血系跨代拉回均值 |
| 连锁不平衡 | 常共现 skill 对 = 学派/工具链 |

### 2.4 Skill 遗传 vs 集成

```
遗传 (Inheritance)              集成 (Integration)
─────────────────────          ────────────────────────
亲代 skill_genome 交叉          盲目学习 / 信号跟随练熟
子代携带子集                    演练后 dominant → 绑定建议
谱系可追溯                      skill_library 固化 / router 反馈
默认不改生产真身                人确认或策略开关后才写回
```

**铁律**：集成不得绕过选择证据；不得引入「技能质量分」。

### 2.5 学术引用（公开来源，改写使用）

- 数量遗传学与遗传力：LibreTexts *Quantitative Genetics and Heritability*
- 同类选配与社会阶层持续性：PMC10629509
- 奠基者种群遗传力：PMC1226113
- 野生系谱与合作演化：PMC2386891
- 精英血统跨代与均值回归：Gregory Clark, *The Son Also Rises* (2014)
- 双遗传 / 基因–文化协同演化：Boyd & Richerson 传统综述

---

## 3. TaskHabitatContract（核心新契约）

### 3.1 数据结构

```text
TaskHabitatContract {
  plan_id, plaza_id, discussion_id, topic, goal, revision
  niches: [
    {
      step_id, index, title,
      demanded_skills: [...],
      responsible_role,
      acceptance,
      base_ticks: int,
      depends_on: [step_id],
      inferred_skills: bool
    }
  ]
  step_budget: {
    max_steps_per_generation,  # clamp(Σ base_ticks, 40, 500)
    max_generations,           # clamp(2 + ceil(n_niches/3), 1, 10)
    era: { ... }
  }
  skill_universe: [...],
  provenance: { source: "plan"|"tasks"|"manual", fingerprint }
}
```

### 3.2 编译规则（默认）

| 输入 | 输出 |
| --- | --- |
| `len(plan.steps)` | `n_niches` |
| 每步 `required_skills` | 该 niche 的 demand |
| 缺 skills | 角色默认映射或 title 关键词推断，`inferred_skills=true` |
| `base_ticks` | `max(8, 12 + 4 * len(skills))` |
| `max_steps_per_generation` | `clamp(Σ base_ticks, 40, 500)` |
| `max_generations` | `clamp(2 + ceil(n_niches/3), 1, 10)`（UI 可覆盖） |
| 依赖 | 拓扑序决定 niche 切换顺序 |

### 3.3 生境内选择压力（仍唯一适应度）

1. **Niche 序列化**：demand 按计划步骤拓扑序推进。
2. **步骤时钟**：每 niche 有 `base_ticks` 窗口。
3. **角色亲和（软）**：role 匹配时熟练度系数略高（如 ×1.1）。
4. **漂移降权**：绑定计划后默认降低 `drift_prob`。
5. **零合同回退**：未绑定计划时完整保持 v3 行为。

---

## 4. 三级赛制 × 任务契约

| 赛制 | 任务关联语义 | 步数 / 轮次 |
| --- | --- | --- |
| **① 分场锦标赛** `division` | 单团队在该计划生境下家族内精英识别 | budget 来自 Contract；**强制忽略 rivals** |
| **② 多队对抗** `confrontation` | 多团队同一 Contract 同场抢生态位 | 同 budget；`extra_team_ids` ≥1 |
| **③ 混合竞争** `mixed` | 同 Contract + 纪元加压 + 跨队 skill 重组 | 必须走 `run_eras` |

兼容别名：`tournament→division`，`melee→confrontation`。

---

## 5. Skill 遗传与集成流水线

### 5.1 演练内遗传（强化）

| 阶段 | v4 优化 |
| --- | --- |
| 初始化 | Skill 身份归一；proficiency 可 seed |
| collab | 可选历史 seed，仍可变异 |
| 选择 | niche = 计划技能序 |
| 交叉 | 记录重组事件（skill 来自父/母） |
| 盲目学习 | 池 = plan skill_universe ∪ 团队库 |
| 杂优 | 对照计划技能覆盖率 |

### 5.2 演练后集成

```text
SkillIntegrationReport {
  plan_id,
  dominant_skills,
  missing_plan_skills,
  deprecated_skills,
  recommended_bindings: [{ agent_id, add_skills[], reason }],
  school_clusters,
  write_policy: "suggest_only" | "apply_with_confirm" | "auto"
}
```

| 动作 | 默认 |
| --- | --- |
| 绑定建议展示 | 开 |
| skill_router 反馈 | 可选 |
| 写回 `agent.skills` | **关** |
| `write_lineage` | 关 |
| library 固化草稿 | 关 |

### 5.3 遗传学 UI 增量

1. 计划技能覆盖热力  
2. 垂直 vs 水平传递比（`skill_origin`）  
3. 分 skill 遗传力  
4. 集成抽屉  

---

## 6. 与生产任务闭环

```
A. 计划批准 → 「进物竞试验田」→ ?office3d=1&plan_id=...
B. 演练结束 → 计划适者报告 + IntegrationReport → ratchet eco_plan:{fingerprint}
C. 可选按胜出构型派发；已有任务可从 metadata 反编译 Contract
```

---

## 7. 架构与改动面

### 7.1 新模块

| 文件 | 职责 |
| --- | --- |
| `src/backend/sandbox/plan_eco_bridge.py` | plan/tasks → TaskHabitatContract |
| `src/backend/sandbox/skill_identity.py` | skill id/name/slug 归一 |
| `src/backend/sandbox/skill_integration.py` | IntegrationReport + 可选 apply |

### 7.2 修改模块

| 文件 | 改动 |
| --- | --- |
| `eco_drill.py` | niches 窗口、contract、**接线 run_eras**、skill_origin |
| `trial_api.py` | 透传 contract；mixed → run_eras |
| `execution_plan.py` / `plaza_routes.py` | required_skills；eco 审查 |
| `eco_runtime_config.py` | `task_coupling` 节 |
| `eco-console.js` / `Agent-digital-twin.html` | 绑定计划、预算、赛制、集成报告 |
| `eco-genetics.js` | Skill 中心纯函数 |
| `plaza.js`（轻） | 深链按钮 |

### 7.3 复用

`ExecutionPlan`、`plan_scenario_bridge`、eco_loop/health_ledger、SSE/replay/matchup/三比曲线。

---

## 8. 分阶段路线

| 阶段 | 主题 |
| --- | --- |
| **XG-0** | 文档落盘（本文件 + todos） |
| **XG-1** | 计划技能数据质量 |
| **XG-2** | TaskHabitatContract 编译器 + API |
| **XG-3** | Skill 身份归一 |
| **XG-4** | eco_drill 任务生境 |
| **XG-5** | run_eras 生产接线 |
| **XG-6** | trial_api 透传 |
| **XG-7** | 前端绑定 / 预算 / 赛制语义 |
| **XG-8** | Skill 集成报告 |
| **XG-9** | 遗传学 Skill UI |
| **XG-10** | 棘轮 + 生产派发闭环 |
| **XR-1** | 本机全量验收 |

依赖：XG-0 → XG-1 → XG-2 → XG-3 → XG-4 →（XG-5 ∥ XG-6）→ XG-7 → XG-8 → XG-9 → XG-10 → XR-1。

---

## 9. 验收标准（总）

1. **闭环**：批准计划 → 绑定 plan_id → 生态位=步骤技能 → 步数/世代由契约生成 → 三档可跑 → 集成建议可见。  
2. **任务关联**：缺计划技能团队平均 survival 显著低于技能覆盖良好团队（pytest 构造）。  
3. **遗传学**：垂直/水平传递、分 skill h²、覆盖热力有真数据。  
4. **安全默认**：无计划 = v3 行为；集成默认 suggest_only。  
5. **混合竞争**：`eras` 非空；纪元环境变化可观测。  
6. **回归**：pytest 无新增失败；无 office3d 时 SECS 零回归。

---

## 10. 非目标

- Plaza 讨论阶段做 token 优化或物竞。  
- LLM 每 tick 决策生物。  
- 重写 SECS orchestrator。  
- 排兵策略回灌模拟内核。  
- 无确认自动改写生产 agent 技能绑定。

---

## 11. 风险与缓解

| 风险 | 缓解 |
| --- | --- |
| 计划无 required_skills | eco 审查 + 角色默认映射 + inferred 标记 |
| 步数公式不合理 | clamp + UI 可覆盖 + config scale |
| 写回污染真身 | 默认 suggest_only + 审计 |
| 适应度变相多目标 | 坚持 survival only |
| 并行改同一文件 | 局部 Edit；契约测试先行 |

---

## 12. 与 v3 文档关系

- v3（赛制 / 三比 / 谱系七图）**全部保留**，本 plan **不重写** 内核世界观。  
- v3 遗留本机项（XV-8.2/8.3、mixed run_eras 等）并入配套 todos 的 XG-5 / XR-1。  
- 行为真值以本文件 + [`VALIDATION.md`](VALIDATION.md) 为准；历史 plan 可能滞后。

---

*配套执行清单：[`物竞天择任务闭环与Skill遗传todos.md`](物竞天择任务闭环与Skill遗传todos.md)*
