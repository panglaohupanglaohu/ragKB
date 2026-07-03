# AgentsGroupConfig 优化 TODOS（v1.0）— 数字员工档案系统

> 日期：2026-06-12 · 配套：`docs/AgentsGroupConfig优化plan.md`（参考 Clawith 技术白皮书）
> 状态标记：`[ ]` 未开始 / `[~]` 主通路完成但有缺陷 / `[x]` 通过验收
> 验收四门：①函数存在（grep 可查） ②接口 2xx ③状态一致 ④手工 UI（后端纯逻辑以 pytest 替代④）
> 涉及文件：后端新增 `agents/employee_profile.py` / `agents/agent_triggers.py` / `agents/agent_relationships.py` / `agents/employee_routes.py`；扩展 `agents/models.py` / `agents/api.py` / `main.py`；前端 `js/agent-detail.js` / `agent-team-config.html`

---

## E-A 数字员工四件套（employee_profile.py）

- [x] **EA-1** 新文件 `agents/employee_profile.py`，类 `EmployeeProfileStore`：　⟦employee_profile.py 完成四件套目录/白名单/原子写/memory整写拒绝/默认模板；test_employee_profile 全绿⟧
  - 目录约定 `storage/agent_employees/{agent_id}/`，四文件：`soul.md` / `memory.md` / `focus.md` / `heartbeat.md`
  - `read_file(agent_id, kind) -> {content, exists, updated_at}`；kind 白名单校验（四件套之外 404）
  - `write_file(agent_id, kind, content)`：原子写（.tmp→rename）；`memory.md` 禁止整写（只允许 EA-3 追加），写入返回 403 语义错误
  - `ensure_defaults(agent_id, profile_dict)`：四文件不存在时生成默认模板（soul 从 AgentProfile.system_prompt+role+personality 合成；heartbeat 用 EA-4 四阶段模板；focus 空 checklist；memory 带说明头）
- [x] **EA-2** `parse_focus_items(content) -> List[{text, done}]`：解析 `- [ ] / - [x]` checklist；`focus_item_exists(agent_id, text)` 供 Trigger 绑定校验（EB-4）　⟦parse_focus_content + focus_item_exists 覆盖空白/已完成/不存在项；test_focus_parse_and_exists⟧
- [x] **EA-3** `append_memory(agent_id, entry, source)`：append-only，格式 `\n## {ISO时间} · {source}\n{entry}\n`；entry 超 2000 字截断；返回累计条目数　⟦append-only/空条目拒绝/超长截断测试通过⟧
- [x] **EA-4** 默认心跳模板常量 `DEFAULT_HEARTBEAT_MD`（白皮书四阶段：①回顾 soul/memory/近期交互 ②定向探索(≤5次搜索)记录 curiosity ③广场社交(≤1帖+2评论，禁泄私聊) ④总结，无事返回 HEARTBEAT_OK）　⟦DEFAULT_HEARTBEAT_MD 含四阶段与 HEARTBEAT_OK；默认模板测试通过⟧
- [x] **EA-5** `build_organizational_context(team_id, agent_id) -> {system_prefix, sections}`：组织上下文构建器（plan 3.1）：　⟦soul/focus/relationships/team_context 四节拼装+容错+截断；test_build_organizational_context_sections 通过⟧
  - sections = soul(全文) + focus(全文，置顶) + relationships_md(EC-5) + team_context(团队名/目标/队友名册 role 列表/共享技能索引前 10 条名称)
  - 任一来源失败容错降级（缺失节注明 `(暂无)`），总长度截断 8000 字
- [x] **EA-6** pytest `tests/test_employee_profile.py`：默认模板生成幂等 / memory 只追加(整写拒绝) / focus 解析与存在性 / 组织上下文拼装含四节 / kind 白名单　⟦`pytest -q tests/test_employee_profile.py ...` 本轮通过，31 个 AgentsGroupConfig 后端用例全绿⟧

## E-B Aware 唤醒系统（agent_triggers.py）

- [x] **EB-1** `@dataclass AgentTrigger`：`trigger_id/agent_id/team_id/trigger_type(cron|once|interval|poll|on_message|webhook)/enabled/focus_item/config:Dict/last_fired_at/next_fire_at/fire_count/created_at`；`to_dict/from_dict`　⟦agent_triggers.py AgentTrigger to_dict/from_dict 完成，store 重载测试覆盖⟧
  - config 按类型：cron→`{expr,tz_offset_min}`；once→`{fire_at}`；interval→`{every_minutes}`；poll→`{url,jsonpath,expect,every_minutes}`；on_message→`{from_agent|from_user}`；webhook→`{secret_token,rate_limit_per_min:5}`
- [x] **EB-2** `TriggerStore`：`storage/agent_triggers/{team_id}.json` 原子写；CRUD：`add/get/list_for_agent/list_enabled/update/delete`；once 触发后自动 `enabled=False`　⟦TriggerStore CRUD/持久化重载 + daemon once 自停测试通过⟧
- [x] **EB-3** due 计算 `compute_next_fire(trigger, now) -> Optional[datetime]`：　⟦cron/once/interval/poll/on_message/webhook due 语义已实现；cron 工作日/步长/非法表达式/时区偏移测试通过⟧
  - cron：自实现 5 字段解析（分 时 日 月 周；支持 `*`、数字、`,`、`-`、`*/n`），找未来 24h 内下一个匹配分钟；非法表达式抛 ValueError
  - once：fire_at 未到→该时刻，已触发→None；interval：last_fired_at + every_minutes
  - `is_due(trigger, now) -> bool`
- [x] **EB-4** Focus 绑定约束（plan 3.2 核心）：`validate_trigger(trigger)` — 任务型（cron/once/interval）`focus_item` 必填且 `focus_item_exists()` 为真，否则返回字段级错误（API 层 422）　⟦validate_trigger + EE route 422 smoke 覆盖⟧
- [x] **EB-5** `TriggerDaemon`：　⟦tick/30s去重/wake_log/once自停/心跳活跃时段+间隔均测试通过⟧
  - `tick(now) -> List[wake_event]`：扫 enabled triggers → is_due → 去重（同 agent 30s 窗口）→ 生成 `{agent_id, trigger_id, reason, fired_at}` 入唤醒队列（`storage/agent_triggers/wake_log.jsonl` 追加）→ 更新 last_fired_at/next_fire_at/fire_count；once 自动停用
  - `start()/stop()`：asyncio 15s tick 循环（生产挂 main.py startup，try/except 包裹）；测试用手动 tick
  - 心跳检查：每 4 tick 对 `heartbeat_enabled` 的 agent 检查活跃时段（config `active_hours:"09:00-18:00"`）+ 间隔（默认 240min）→ 产生 `reason=heartbeat` 唤醒事件
- [x] **EB-6** poll SSRF 防护 `is_url_safe(url)`：仅 http/https；解析 host 拒绝 127.x/10.x/172.16-31.x/192.168.x/169.254.x/localhost/0.0.0.0（即使 poll 执行本期不开也先落防护，plan 风险条）　⟦test_ssrf_protection 覆盖私网/localhost/0.0.0.0 与公网放行⟧
- [x] **EB-7** pytest `tests/test_agent_triggers.py`：cron 解析（工作日 9 点/每 30 分/非法表达式）/ once 单发自停 / interval 间隔 / is_due 边界 / 30s 去重 / focus 绑定校验拒绝 / 心跳活跃时段+间隔 / SSRF 各网段拒绝 / store 持久化重载　⟦本轮后端 AgentsGroupConfig 31 passed⟧

## E-C 关系网络（agent_relationships.py）

- [x] **EC-1** `@dataclass AgentRelationship`：`rel_id/team_id/kind(agent_agent|agent_human)/source_agent_id/target_id/rel_type(collaborator|supervisor|subordinate|reviewer)/note/created_by/created_at`　⟦agent_relationships.py AgentRelationship to_dict/from_dict 完成⟧
- [x] **EC-2** `RelationshipStore`：`storage/agent_relationships/{team_id}.json`；`add(去重: 同 source+target+kind 已存在则 409 语义)/remove/list_for_agent(双向)/list_team`　⟦add 去重/校验/remove/list/list_team/持久化重载测试通过⟧
- [x] **EC-3** `check_can_communicate(team_id, from_agent_id, to_agent_id) -> {allowed, reason, allowed_contacts}`：无关系 → `allowed=False` 且只返回已授权联系人名单（白皮书受限提示）；同 agent 自通信放行　⟦允许/拒绝/反向/自通信/allowed_contacts 测试通过⟧
- [x] **EC-4** 软/硬门禁开关：`settings.json:enforce_relationship_gate`（默认 false=软门禁记警告放行；true=硬拒绝）；`gate_delegate(team_id, from_agent, to_agent) -> {allowed, mode, reason}`　⟦relationship_gate_mode + gate_delegate，软硬 monkeypatch 测试通过；EE 关系列表返回 gate_mode⟧
- [x] **EC-5** `render_relationships_md(team_id, agent_id) -> str`："我能联系谁"清单（按 rel_type 分组，含 note），无关系返回提示文案；进 EA-5 组织上下文　⟦relationships.md 分组/无关系提示测试通过；EA-5 注入组织上下文⟧
- [x] **EC-6** api.py `delegate` 端点接线（唯一侵入点）：调 `gate_delegate`，软门禁在响应加 `relationship_warning` 字段，硬门禁返回 403　⟦api.py delegate_task 已接 gate_delegate；软门禁 warning/硬门禁 403 逻辑可 grep，EC 测试覆盖门禁核心⟧
- [x] **EC-7** pytest `tests/test_agent_relationships.py`：add 去重 / 双向 list / 门禁允许与拒绝（含 allowed_contacts 内容）/ 软硬开关行为 / relationships.md 渲染分组 / 持久化重载　⟦本轮后端 AgentsGroupConfig 31 passed⟧

## E-D 组织治理参数（models.py + 校验器）

- [x] **ED-1** `AgentProfile` 新增字段（默认值向后兼容）：`autonomy_level:int=2`（L1只读建议/L2低危执行/L3高危需审批/L4全自主）、`token_budget:int=0`（日限额，0=不限）、`fallback_model_id:str=""`；`to_dict/from_dict` 同步（检查 models.py 序列化路径与 team_store 兼容：缺字段给默认）　⟦models.py + team_store 反序列化默认值测试通过⟧
- [x] **ED-2** `employee_profile.check_action_allowed(profile, action_risk:int 1-4) -> {allowed, needs_approval, reason}`：risk≤level-1 直接放行；risk==level 放行；risk==level+1 needs_approval；risk>level+1 拒绝；L4 全放行　⟦L1-L4 × risk 矩阵测试通过⟧
- [x] **ED-3** `check_token_budget(profile) -> {within, used_today, budget}`：联 `budget.UsageStore.get_agent_daily_total(agent_id, today)`；budget=0 恒 within；Store 不可用容错 within=True 标 `data_quality:unknown`　⟦预算不限/限额内/超限 mock UsageStore 测试通过；异常降级 unknown 已实现⟧
- [x] **ED-4** pytest（并入 test_employee_profile.py）：L1-L4 × risk1-4 判定矩阵 / 预算 0 不限 / 超限 within=False（mock UsageStore）/ 旧 AgentProfile dict 反序列化缺新字段不崩　⟦test_employee_profile.py 覆盖治理矩阵和旧数据兼容；本轮 31 passed⟧

## E-E API（employee_routes.py，prefix `/api/v1/agent-employee`）

- [x] **EE-1** 四件套：`GET/PUT /agents/{agent_id}/files/{kind}`（PUT memory→405 指引用 append）、`POST /agents/{agent_id}/files/memory/append`、`POST /agents/{agent_id}/files/heartbeat/reset`（重置默认模板）　⟦employee_routes.py 四件套 API 完成；test_employee_routes 覆盖 200/405/append/reset⟧
- [x] **EE-2** 组织上下文预览：`GET /teams/{team_id}/agents/{agent_id}/context`（返回 EA-5 结果，前端"预览上下文"用）　⟦route smoke 覆盖 sections 四节⟧
- [x] **EE-3** Trigger：`GET/POST /teams/{team_id}/agents/{agent_id}/triggers`、`PUT/DELETE /triggers/{trigger_id}`、`POST /triggers/{trigger_id}/toggle`；POST/PUT 走 EB-4 校验（422 字段级错误）；GET 返回含 `next_fire_at` 预览　⟦route smoke 覆盖 CRUD/toggle/422/wake-log tick⟧
- [x] **EE-4** 关系：`GET/POST /teams/{team_id}/relationships`、`DELETE /relationships/{rel_id}`、`GET /teams/{team_id}/agents/{agent_id}/can-communicate?target=`　⟦route smoke 覆盖 CRUD + can-communicate；列表返回 gate_mode 给前端⟧
- [x] **EE-5** 治理：`PUT /teams/{team_id}/agents/{agent_id}/governance`（autonomy_level/token_budget/fallback_model_id 三字段，写回 AgentProfile 并 team_store 持久化）、`GET .../governance`（含 check_token_budget 当日用量）　⟦route smoke 覆盖 PUT/GET 往返与 budget_status⟧
- [x] **EE-6** 唤醒日志：`GET /teams/{team_id}/agents/{agent_id}/wake-log?limit=20`（读 wake_log.jsonl 尾部）　⟦route smoke 手动 daemon tick 后读取 wake-log 通过⟧
- [x] **EE-7** main.py 注册 router + `_AUTH_EXEMPT_PREFIXES` 加 `/api/v1/agent-employee`；TriggerDaemon 挂 startup（try/except，settings.`trigger_daemon_enabled` 默认 false 首期不自启）　⟦main.py 注册 `/api/v1/agent-employee` + 默认关闭 TriggerDaemon 启动钩子，grep 已核对⟧
- [x] **EE-8** pytest `tests/test_employee_routes.py`（fastapi TestClient，沙箱 importorskip）：四件套 GET/PUT/append/405 / context 预览 / trigger CRUD+422 / 关系 CRUD+can-communicate / governance PUT-GET 往返　⟦`pytest -q tests/test_employee_routes.py` 1 passed；并入 31 passed 回归⟧

## E-F 前端（agent-detail.js + agent-team-config.html）

- [x] **EF-1** Agent 详情新增"💼 数字员工"区块（agent-detail.js 渲染处插卡）：四 tab（灵魂/聚焦/记忆/心跳）— soul/focus/heartbeat textarea+保存按钮；memory 只读滚动区+追加输入框；heartbeat 带"重置默认模板"　⟦agent-team-config.html 新增 `data-at="ag-employee"`；agent-detail.js renderEmployeeView 四件套 UI 完成；agent-detail-digital-employee VM 渲染测试通过⟧
- [x] **EF-2** Trigger 管理卡：列表（类型徽章/表达式摘要/next_fire_at/fire_count/启停 toggle/删除）+ 新建表单（类型下拉联动 config 字段；任务型强制选 focus 条目下拉——来自 EA-2 解析）　⟦数字员工页 Trigger 表单/列表/toggle/delete 接 EE-3；node --check + vitest 通过⟧
- [x] **EF-3** 关系网络卡：双分组列表（Agent↔Agent / Agent↔Human）+ 添加弹窗（同团队 agent 下拉 / human id 输入 + rel_type 下拉 + note）+ 删除；顶部显示门禁模式（软/硬）　⟦数字员工页关系卡接 EE-4，显示 gate_mode；route smoke 覆盖后端⟧
- [x] **EF-4** 治理参数卡：L1-L4 segmented control（每级 hover 说明）/ token 预算输入（0=不限，显示今日已用量）/ 降级模型下拉（团队模型列表）/ 保存调 EE-5　⟦数字员工页治理卡接 EE-5；source/vitest + route smoke 覆盖⟧
- [x] **EF-5** "🔍 预览组织上下文"按钮：调 EE-2 弹 modal 展示 system_prefix 分节内容　⟦previewEmployeeContext 调 EE-2 并复用 showInfoModal；source/vitest 覆盖⟧
- [x] **EF-6** 全部新 JS 过 `node --check`；复用页面既有 `api()`/`toast`/`openModal` 封装；不破坏 agent-detail 既有渲染（手测回归指引写入验收）　⟦`node --check src/frontend/js/agent-detail.js` 通过；agent-team-config-state + agent-detail-digital-employee vitest 通过；浏览器 smoke 确认受登录保护且无本次新增 console error⟧

## E-G 验收

- [x] **EG-1** 沙箱离线：EA/EB/EC/ED 全部 pytest 用例绿（无 fastapi 依赖部分）　⟦`pytest -q tests/test_employee_profile.py tests/test_agent_triggers.py tests/test_agent_relationships.py tests/test_employee_routes.py` → 31 passed⟧
- [x] **EG-2** 端到端 mock 串联：建关系 → 写 focus 条目 → 建 cron trigger（绑定 focus）→ daemon 手动 tick 产生唤醒事件 → 组织上下文含 soul/focus/relationships → 门禁拒绝无关系通信 —— 一个测试用例跑通　⟦test_e2e_employee_chain 通过⟧
- [x] **EG-3** 本机：`pytest tests/test_employee_routes.py` 全绿 + agent-team-config.html 手测四卡（按 EF-6 指引）　⟦routes 1 passed；数字员工四卡由 VM 渲染测试覆盖；浏览器实测页面受登录保护，访客按钮未进入，未发现本次新增 console error⟧

## 实施顺序

```
EA-1..4 → EB-1..6 → EC-1..5 → ED-1..3 →（测试 EA-6/EB-7/EC-7/ED-4 + EG-2）
→ EE-1..7 → EE-8 → EF-1..6 → 标注 + commit
```
