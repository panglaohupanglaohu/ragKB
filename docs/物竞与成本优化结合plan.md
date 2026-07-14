<!-- docs-signoff: author="Grok" kind="llm" doc="plan" ts="2026-07-14T15:17:30Z" -->
# 物竞天择 × 演进式成本优化 — 结合设计

> 状态：current · **M0–M3 已落地**（含 XC-4.4 / 4.4b SkillRouter 静默绑定；验收见 `verify_eco_feedback_xf.py`）  
> 用户原则（2026-07-14）：**先选活得长的，再选花钱省的。**  
> 即：`T_i`（生存）定过线集 → token 在过线集内最小化。  
> 任务主轴：业务场景实例（团队任务）挂载 → 契约考卷 → 物竞 → 适者反馈 → 成本优化。  
> 实现：`sandbox/bid_candidate.py` · `eco-runtime/bid-candidates*` · ③ `ecoFeedbackPushBid` · cost-dashboard 候选面板。

---

## 1. 一句话

```
质量门 = 物竞（谁在任务考卷下活得久、skill/协作被环境选中）
成本门 = 演进式成本优化（在过线构型里谁 token 更省，棘轮锁定）
生产选用 = argmin token | 构型 ∈ 物竞过线集
```

禁止反过来：不能只因 token 低就上线（可能 residual 苟活、干不了 demand）。

---

## 2. 与既有阶段对齐

| 阶段 | 页面 / 能力 | 改什么 | 不改什么 |
| --- | --- | --- | --- |
| 0 讨论 | Plaza | 计划 | **不**优化 token |
| 1 任务实例 | 团队任务 / 派发 | 业务场景实例 | — |
| 2 物竞 | `?office3d=1` 演练控制 | 种群 + **必挂任务** + 加压 | 不写真身（除非 ③ 确认） |
| 3 适者反馈 | ③ 反馈台 | Skill + 协作写回智能体 | 不计量 token |
| 4 成本优化 | `cost-dashboard` | tokens_per_goal、效率、棘轮、Gate | **不**改人设 |
| 5 生产 | 任务执行 / SkillRouter | 用锁定构型跑 | — |

两阶段经济学不变：Plaza 无价；成本纪律从计划/任务进入执行与孪生竞标后开始。

---

## 3. 核心对象：竞标候选 BidCandidate

一场任务型物竞 + 反馈后，沉淀一条（或一批）**候选构型**：

```text
BidCandidate {
  candidate_id          // uuid
  team_id
  task_id               // 业务场景实例（必填，任务主闭环）
  plan_id / eco_fp      // 契约指纹
  race_mode             // division | confrontation | mixed
  // —— 物竞质量门 ——
  champion_agent_id
  best_T                // 最长生存 ticks
  ranking_summary[]     // top-k T_i / population
  dominant_skills[]     // 可读 name+id
  collab_profile        // 种群协作基因摘要
  survival_attribution  // top skill%/collab%/residual%
  feedback_status       // done | skipped
  skill_applied / collab_applied
  habitat_snapshot      // A4+B8 可选
  // —— 成本门（后填）——
  tokens_baseline       // 基线构型 token/任务
  tokens_candidate      // 本构型实测或估
  token_efficiency      // score/1k tokens 等
  cost_gate             // pass | fail | pending
  ratchet_state         // none | proposed | locked
  created_at / source
}
```

存储建议：`storage/eco_bid_candidates/{team_id}/{candidate_id}.json` 或团队 metadata 列表（实现期定）。

---

## 4. 质量门（物竞）— 「活得长」

### 4.1 过线条件（默认建议，可配置）

候选进入成本比较前，须满足（**全部**或产品选定子集）：

| 条件 ID | 规则 | 说明 |
| --- | --- | --- |
| Q1 | 已挂接 `task_id`（任务型） | 无任务空跑默认不进成本竞标 |
| Q2 | `feedback_status=done` 或显式 skipped+原因 | ③ 门禁 |
| Q3 | `best_T` ≥ 同契约历史分位或相对对照队 | 「活得长」 |
| Q4 | residual% 不主导 top 适者（可选阈值，如 top1 residual&lt;0.85） | 避免纯苟活 |
| Q5 | dominant 与任务 demand 有交集，或 skill 写回非空（可选） | skill 闭环 |

### 4.2 输出

- 过线 → `BidCandidate` 状态 `quality_passed`  
- 不过 → 停留试验田，提示加压/换队/补 skill  

---

## 5. 成本门 — 「花钱省」

### 5.1 比较集合

仅 `quality_passed` 的候选（同一 `task_id` / 同一 `eco_fp` 考卷族内比较）。

### 5.2 指标（与 cost-dashboard 对齐）

| 指标 | 用途 |
| --- | --- |
| `tokens_per_goal` / 任务 token | 主优化目标 |
| `token_efficiency` (score/1k tokens) | 效率榜 |
| skill 杠杆 vs 协作杠杆 | 指引萃取 vs 协同 |

### 5.3 成本棘轮

```
审查(审计候选与反馈) → 派发(用候选构型跑对照任务) → 验证(token↓ 且质量不劣)
  → 关闭 → 锁定(ratchet_state=locked)
```

锁定后：SkillRouter / 默认执行构型优先用该候选的 skill 包 + 团队。

### 5.4 与物竞生存棘轮的关系

| 棘轮 | 键/对象 | 含义 |
| --- | --- | --- |
| eco 生存 | `eco_plan:{fp}` / survival ticks | 考卷下谁更活 |
| cost | 成本页棘轮周期 | 谁更省 |

**顺序强制**：cost 锁定 ⊆ 曾 quality_passed 的集合。  
UI 文案：先适者，后省钱。

---

## 6. 页面与数据流

```
[演练控制]
  ① 选种群 → ② 挂载任务（XF-6）→ 物竞
       ↓
[③ 适者反馈] Skill/协作写回
       ↓ 创建 BidCandidate (quality 侧字段)
[「推送到成本竞标」按钮]
       ↓
[cost-dashboard]
  物竞候选条 + BidCandidate 列表（T_i / 质量门 / token / 棘轮）
  手填 tokens → cost_gate → 仅 quality_passed 可 lock
       ↓
[生产任务执行] apply_locked_config_to_task + SkillRouter 静默绑 skill
```

### 6.1 孪生页增量

- ③ 反馈台：写回成功后 **「推送到成本竞标」**（创建/更新 BidCandidate，跳转 cost 带 `candidate_id`）  
- 未过 Q1–Q2 不可推送  

### 6.2 成本页增量

- 候选面板：列表 BidCandidate（team/task/T_i/dominant/feedback/token 状态）  
- 对比：同 task 下多候选 token 柱状/表  
- 棘轮：仅对 quality_passed 操作  
- 链回孪生 ③：`office3d=1&team_id&task_id`  

---

## 7. API 草图（实现期）

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| POST | `/api/v1/eco-runtime/bid-candidates` | 从最近演练+反馈创建候选 |
| GET | `/api/v1/eco-runtime/bid-candidates?team_id&task_id` | 列表 |
| PATCH | `.../bid-candidates/{id}` | 填 token 结果、棘轮状态 |
| POST | `.../bid-candidates/{id}/quality-check` | 重算 Q1–Q5 |

成本聚合仍走现有 `/api/v1/cost*`；候选只引用 team/task/run_id。

---

## 8. 公式（产品口径）

\[
\mathcal{Q} = \{ c \mid \text{task 挂接} \land \text{反馈完成} \land T(c)\ \text{过线} \land \neg\text{纯 residual 苟活} \}
\]

\[
c^\* = \arg\min_{c \in \mathcal{Q}} \mathrm{Tokens}(c \mid \text{同一任务实例})
\]

\[
\text{生产采用} = \mathrm{RatchetLock}(c^\*)\ \text{仅当}\ \mathrm{Tokens}(c^\*) \le \mathrm{Tokens}(\text{baseline})\ \land \text{质量不劣}
\]

---

## 9. 非目标

- Plaza 讨论阶段不做 token 优化  
- 成本页不直接改 agent.skills / eco_collab  
- 不用 3D 觅食图腾表达 demand（见反馈台 todos XF-5）  
- 不自动把空跑随机生境结果推入成本竞标  

---

## 10. 分期

| 期 | 内容 | 依赖 |
| --- | --- | --- |
| **M0** | 任务挂载菜单 XF-6（试验田入口） | 本迭代已做/在做 |
| **M1** | BidCandidate 创建 API + ③「推送成本竞标」+ cost 列表只读 | 反馈台 P0/P1 |
| **M2** | 同 task 多候选 token 填入/对比 + 质量门 Q3–Q5 可配置 | cost 聚合 |
| **M3** | 成本棘轮仅锁 quality_passed；生产默认读 locked 构型 | 棘轮/执行路径 |

配套 todos：[`物竞与成本优化结合todos.md`](物竞与成本优化结合todos.md)。

---

## 11. 成功标准

1. 用户路径可复述：**挂任务 → 物竞 → 反馈 → 推送成本 → 省钱锁定**。  
2. 无任务/未反馈的结果 **不能** 静默进入成本锁定。  
3. cost-dashboard 能看到候选的 `best_T` 与 token，并理解「先活后省」。  
4. 文档与 UI 文案一致，无「生物觅食柱」污染办公室默认体验。  
