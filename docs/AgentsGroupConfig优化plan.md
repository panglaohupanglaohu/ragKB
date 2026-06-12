# AgentsGroupConfig 优化计划（v1.0）— 从"配置面板"到"数字员工档案系统"

> 日期：2026-06-12
> 参考：[Clawith Technical Whitepaper](https://www.clawith.ai/blog/clawith-technical-whitepaper)
> 目标页面：`agent-team-config.html`（前端 `js/agent-team-config.js` 1278行 + `js/agent-detail.js` / `js/wizard.js` / `js/tools-skills.js`）
> 目标后端：`agents/api.py`（/api/v1/agent-config/*）、`agents/models.py:AgentProfile`、`team_manager.py`、`team_store.py`
> 配套执行清单：`docs/AgentsGroupConfig优化todos.md`

---

## 一、Review 结论：现状 vs Clawith 白皮书的差距

### 1.1 现有能力（不重做）

| 能力 | 位置 | 状态 |
|---|---|---|
| 团队/Agent/模型/工具/技能 CRUD | `agents/api.py` 60+ 端点 | ✅ 完整 |
| AgentProfile（角色/人格/权限/渠道/工具/技能） | `models.py:412` | ✅ 静态档案完整 |
| Agent 模板、向导建团队、委派(delegate)、搜索 | api.py + wizard.js | ✅ |
| Token 用量记账 | `agents/budget/store.py`(sqlite) | ✅ 有记账无预算分配 |
| 团队级技能库/分类（v4+全局P0 完成） | skill_library/skill_classifier | ✅ |
| relationships 只读查询 | api.py:1862（从委派历史推断） | ⚠️ 无显式关系模型 |

### 1.2 对照白皮书的六大结构性缺口

Clawith 的核心论断：**MAS 框架的致命缺陷是"阅后即焚的临时工模型"——Agent 随任务生灭，没有积累、没有主动性、没有组织治理。** 对照检查 AgentsGroup2026 的 Agent 配置系统：

| # | 白皮书概念 | 本系统现状 | 缺口 |
|---|---|---|---|
| 1 | **数字员工四件套**：soul.md（角色灵魂）/ memory.md（经验库）/ focus.md（工作记忆）/ HEARTBEAT.md（心跳协议） | AgentProfile 只有一段静态 system_prompt，无私有目录、无可积累文件 | **高** |
| 2 | **Aware 自主唤醒**：Trigger 六类（cron/once/interval/poll/on_message/webhook）+ 15s daemon + 30s 去重 + "Trigger 必须绑定 Focus 项" | 无任何 per-agent 唤醒机制，Agent 纯被动 | **高** |
| 3 | **显式关系网络**：Agent-Agent / Agent-Human 双表，无关系则 A2A 拒绝，relationships.md 注入"我能联系谁" | delegate 不校验关系；relationships 是从历史推断的只读视图 | **高** |
| 4 | **组织治理**：per-Agent Token 预算 + L1-L4 自主权限边界 + 高危操作审批 | permissions 是布尔开关列表；budget 模块只记账不限额、不与 Agent 绑定 | **中** |
| 5 | **双模型降级**：primary_model + fallback_model，主模型不可用自动切换 | model_id 单字段，无降级 | **中** |
| 6 | **组织上下文 Organizational Context**：唤醒时注入"我是谁(soul)+我在跟进什么(focus)+我能联系谁(relationships)+团队共享认知" | chat_harness 只注入 system_prompt | **高** |

### 1.3 一句话目标

> 把 agent-team-config 从"团队配置面板"升级为"数字员工档案系统"：每个 Agent 拥有可积累的人格档案（四件套）、自主唤醒能力（Trigger+Focus 绑定）、显式关系网络（无关系不通信）、组织治理参数（预算/自主等级/降级模型），并在唤醒时获得完整的组织上下文。

---

## 二、目标架构

```
┌────────────────────────── agent-team-config.html ──────────────────────────┐
│ 团队列表 │ Agent 列表 │ ★数字员工档案抽屉                                    │
│          │            │  ├ 灵魂 soul.md（角色锚定，可编辑）                  │
│          │            │  ├ 记忆 memory.md（只读追加，经验积累）              │
│          │            │  ├ 聚焦 focus.md（checklist 工作记忆）               │
│          │            │  ├ 心跳 heartbeat.md（四阶段协议模板）               │
│          │            │  ├ ★Trigger 管理（六类唤醒 + Focus 绑定校验）        │
│          │            │  ├ ★关系网络（agent↔agent / agent↔human，人工建立）  │
│          │            │  └ ★治理参数（token预算/L1-L4自主等级/降级模型）     │
└──────────────┬──────────────────────────────────────────────────────────────┘
               ▼ /api/v1/agent-employee/*
┌───────────────────────────── 后端新增三模块 ────────────────────────────────┐
│ employee_profile.py  四件套文件管理 (storage/agent_employees/{agent_id}/)    │
│                      + build_organizational_context() 组织上下文构建器       │
│ agent_triggers.py    AgentTrigger 模型 + TriggerStore + TriggerDaemon        │
│                      (15s tick / 30s 去重 / Focus 绑定约束 / due 计算)        │
│ agent_relationships.py  双关系表 + check_can_communicate 通信门禁            │
│                      + render relationships.md                               │
├──────────────────────────── 既有模块扩展 ───────────────────────────────────┤
│ models.py:AgentProfile  + autonomy_level(L1-L4) + token_budget               │
│                         + fallback_model_id                                  │
│ api.py:delegate      接关系门禁 (settings.enforce_relationship_gate)         │
│ chat_harness         上下文注入组织上下文（接线点，渐进启用）                 │
│ budget/store         预算超限检查挂 token_budget                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

设计原则（继承白皮书 + 项目惯例）：

1. **文件即记忆**：四件套用 md 文件存储（`storage/agent_employees/{agent_id}/`），Agent 可通过工具自我维护，人也能直接看——这是"可积累"的物质基础。
2. **Trigger 必须绑定 Focus**：每个任务型 Trigger 必须关联 focus.md 中的一个条目，杜绝"无目的闹钟"（白皮书 3.2 的核心约束）。
3. **关系只能人工建立**：Agent 不能自己加关系；无关系的 A2A 通信被拒绝（默认软门禁兼容存量，settings 可切硬门禁）。
4. **治理参数渐进生效**：autonomy_level/token_budget 先作为档案字段+校验函数落地，执行面（真实拦截）通过 settings 开关渐进启用，不破坏既有流程。
5. **复用既有设施**：预算记账用 budget/UsageStore；心跳的"广场社交阶段"用既有 plaza；技能索引用 skill_library——只加胶水不造轮子。

---

## 三、核心设计

### 3.1 数字员工四件套（EmployeeProfile）

| 文件 | 语义 | 写入方 | 上下文注入位置 |
|---|---|---|---|
| `soul.md` | 角色灵魂锚定：我是谁、价值观、行事风格（替代/增强 system_prompt） | 人工编辑为主 | system prompt 最前 |
| `memory.md` | 不可磨灭的经验库：跨任务教训、成功模式（append-only + 章节化） | Agent/系统追加 | 摘要注入（最近 N 条） |
| `focus.md` | 工作记忆 checklist：当前跟进事项（Trigger 锚点） | Agent 自维护 + 人工 | 优先注入，唤醒第一反应 |
| `heartbeat.md` | 心跳协议：四阶段（回顾→探索→广场社交→总结） | 默认模板 + 人工定制 | 心跳唤醒时作为指令 |

`build_organizational_context(team_id, agent_id)` 返回拼装好的组织上下文：soul + focus + relationships.md + 团队共享认知（团队目标/共享技能索引摘要/队友名册），供 chat_harness 与孪生演练消费。

### 3.2 Aware 唤醒系统（AgentTrigger + Daemon）

- 六类 trigger：`cron`（5 字段表达式）/ `once`（一次性，触发后自动 disable）/ `interval`（固定间隔）/ `poll`（HTTP 探针 + JSONPath，内置 SSRF 防护：拒绝私网 IP）/ `on_message`（等待特定 agent/human 消息）/ `webhook`（反向接入点，5 req/min 限流）。
- TriggerDaemon：asyncio 后台任务 15s tick；同一 Agent 30s 去重窗口；唤醒动作 = 构建组织上下文 + 投递唤醒事件（实际执行接 chat_harness，首期记录唤醒队列）。
- **Focus 绑定约束**：创建任务型 trigger（cron/interval/once）时校验 `focus_item` 必填且存在于 focus.md，否则 422。
- 心跳：daemon 每 4 tick 检查启用心跳的 Agent（活跃时段内、距上次心跳超过间隔默认 240min）→ 注入 heartbeat.md 指令。

### 3.3 关系网络（AgentRelationship）

- 双表：`agent_agent`（A2A 前置）与 `agent_human`（IM 人类前置），字段：source/target/type(collaborator|supervisor|subordinate|reviewer)/note/created_by/created_at。
- `check_can_communicate(team_id, from_agent, to_agent) -> {allowed, reason}`；未建关系 → 拒绝并返回"已授权联系人列表"（白皮书的受限错误提示）。
- 门禁接线：`delegate` 端点 + 孪生 A2A 消息（twin_loop offer_help 不拦——仿真内自由，真实委派才管）。`settings.enforce_relationship_gate` 默认 false（软门禁：只记警告），true 时硬拒绝。
- `render_relationships_md(agent_id)` 生成"我能联系谁"清单，进组织上下文。

### 3.4 组织治理参数

- `AgentProfile.autonomy_level`: int 1-4（L1 只读建议 / L2 可执行低危工具 / L3 可执行高危需审批 / L4 全自主），`check_action_allowed(agent, action_risk) -> {allowed, needs_approval}`。
- `AgentProfile.token_budget`: 日 token 限额（0=不限），`check_budget(agent)` 联 budget/UsageStore 当日用量。
- `AgentProfile.fallback_model_id`: 主模型失败时降级目标；档案+API+前端配置先行，harness 自动切换为接线点。

### 3.5 前端改造（agent-team-config 页面）

Agent 详情（agent-detail.js）新增"数字员工"区块：四件套 tab 编辑器（soul/focus 可写、memory 只读+追加框、heartbeat 模板重置按钮）；Trigger 列表卡（类型徽章/下次触发时间/启停/Focus 绑定项显示）；关系网络卡（双列表 + 添加关系弹窗，下拉选同团队 agent / 输入 human id）；治理参数卡（预算输入、L1-L4 滑块、降级模型下拉）。所有写操作走新 API，复用页面既有 `api()` 封装与 toast。

---

## 四、分阶段路线

| 阶段 | 内容 | 验收 |
|---|---|---|
| **C0**（本轮） | 后端三模块（employee_profile / agent_triggers / agent_relationships）+ AgentProfile 三字段 + employee_routes API + main.py 注册 + 纯逻辑 pytest | 离线测试全绿 |
| **C1**（本轮尽量） | 前端数字员工区块（四件套/Trigger/关系/治理四卡）+ delegate 软门禁接线 + 组织上下文预览端点 | JS 语法 + 手测指引 |
| **C2**（下轮） | chat_harness 注入组织上下文 + TriggerDaemon 接真实唤醒执行 + 双模型降级 harness 接线 + poll/webhook 真实联测 | 本机联测 |
| **C3**（下轮） | 心跳四阶段真实执行（web_search/plaza 接入）+ 审批卡 UI + SCIM 式人类成员映射 | 端到端 |

---

## 五、风险与边界

- **不动 api.py 既有 60+ 端点的行为**：新能力全部走新前缀 `/api/v1/agent-employee`，对 api.py 只做 delegate 软门禁一处侵入（默认关）。
- **AgentProfile 加字段必须向后兼容**：dataclass 默认值 + team_store 序列化兼容（缺字段给默认）。
- **TriggerDaemon 不在沙箱常驻**：daemon 以可启停类实现，测试用手动 tick；生产由 main.py startup 挂载（try/except 包裹）。
- **poll 的 SSRF 防护**必须在首版就有（拒绝 10.x/172.16-31.x/192.168.x/127.x/169.254.x），即使 poll 执行本期不开。
- **不做**：Feishu/Slack 渠道映射、SCIM、多租户隔离（本系统单租户）、审批卡推送 IM——留给 C3+。
