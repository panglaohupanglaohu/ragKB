<!-- docs-signoff: author="Grok" kind="llm" doc="plan" ts="2026-07-14T23:03:06Z" -->
# 任务 Token 治理 — 设计（cost-dashboard 主轴）

> 状态：current · 本页主题 = **任务上耗费的 token 治理**  
> 用户校准（2026-07-15）：物竞竞标**折叠为侧支**；全产品序号 1–6；本页 = **⑤ 成本竞标（token 治理）**。  
> 原则：Plaza 讨论阶段不做 token 优化；成本纪律从执行计划产生后开始（既有铁律）。

---

## 1. 全产品闭环序号（固定）

| # | 阶段 | 主入口 |
| --- | --- | --- |
| **1** | 创建 agent 及团队 | `agent-team-config.html` |
| **2** | 业务讨论 / 任务制定 | `plaza.html` |
| **3** | 寻技能 | `skill-extract.html` |
| **4** | 孪生演练（演化：物竞天择） | `Agent-digital-twin.html?office3d=1` |
| **5** | **成本竞标 · Token 治理（本页）** | `cost-dashboard.html` |
| **6** | 生产注入 | 任务 submit + locked BidCandidate / SkillRouter |

物竞「先适者后省钱」只是 ⑤ 内的一条**候选路径**（质量门后比 token），不是本页视觉主轴。

---

## 2. 本页主轴：任务 Token 治理

### 2.1 选型（业界方案裁剪）

| 能力 | 选型 | 理由 |
| --- | --- | --- |
| **计量** | 复用 `TokenLedger` + `usage.db`；增 **by_task**（`scenario_id` / `run_id` 作任务键） | 已有归因 contextvar，不引入第二账本 |
| **上下文缓存** | 进程内 LRU + 内容指纹（规范化后 SHA-256）；命中返回缓存响应元数据/跳过重复 system 段 | 无外部 Redis 依赖；可后续换 Redis |
| **内容压缩** | 确定性规则：消息去重、长 system 截断、重复 tool 结果折叠 | 不调用 LLM 做摘要（避免递归烧 token） |
| **智能路由** | 复用 `ModelRouter` 三档 economy/standard/frontier + 预算降档 | 已与 tool_loop 对齐 |
| **效果验证** | Token Gate `evaluate` + 缓存 hit 节省估计 + 同 task 前后对比 | 接 `token_policy` / ledger |
| **预算闭环** | `BudgetGuard` session/agent/team 日限额 + 本页读写 + 告警/halt | 已有 store；UI 原 localStorage 预算升级为真预算 |

### 2.2 数据流

```
任务执行 (phase=task, scenario_id≈task_id)
    → chat_harness 记账 UsageRecord
    → [可选] PromptCache 查/写 + compress 前后 token 估计
    → ModelRouter 按预算档位选 model
    → BudgetGuard.check 超限 warn|halt
    → TokenLedger 聚合 → cost-dashboard ⑤ 主轴面板
```

### 2.3 UI 结构（自上而下）

1. **全链进度条** 1–6，⑤ 高亮  
2. **Token 治理主轴**（默认展开）：计量 · 缓存/压缩 · 路由 · 效果验证 · 预算  
3. **既有 KPI / 目标 / 图表**（任务 token 视角强化）  
4. **`<details>` 折叠：物竞竞标候选**（默认关；deep-link `candidate_id` 时自动展开）  
5. **副轴说明**：通用达尔文棘轮 ≠ 任务预算门

---

## 3. API（增量）

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/v1/cost/tokens/by-task` | 任务维 token 聚合 |
| GET/POST | `/api/v1/cost/token-governance/budget` | 读写 BudgetGuard 限额 |
| GET | `/api/v1/cost/token-governance/cache-stats` | 缓存命中/节省 |
| POST | `/api/v1/cost/token-governance/compress-preview` | 压缩预览（不调用 LLM） |
| GET | `/api/v1/cost/token-governance/router-status` | ModelRouter 档位状态 |
| POST | `/api/v1/cost/token-governance/verify` | 效果验证（ledger + gate） |

复用既有：`/cost/tokens/*`、`/cost-gate/token/*`、BidCandidate 路由。

---

## 4. 非目标

- Plaza 讨论阶段 token 优化  
- 外部 Redis / 供应商 prompt-cache 协议（本期进程内）  
- 用 LLM 做上下文摘要压缩（防递归烧 token）  
- 把物竞 3D 图腾搬进成本页  

---

## 5. 成功标准

1. 打开 cost 页首屏是 **Token 治理**，全链 1–6 序号正确，⑤ 为本页。  
2. 物竞竞标默认折叠；有 `candidate_id` 时才自动展开。  
3. 可见：任务 token 表、缓存统计、路由档位、预算限额读写、验证结果。  
4. 单测覆盖 cache 命中、compress 缩减、by_task、budget roundtrip。  

配套 todos：[`任务Token治理todos.md`](任务Token治理todos.md)。
